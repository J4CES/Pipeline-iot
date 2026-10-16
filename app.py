import streamlit as st
import json, os, time
import psycopg2
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Raffinerie IoT - Random Forest IA", layout="wide", page_icon="🏭")

st.title("🏭 Supervision IA Prédictive par Random Forest")
st.markdown("---")

# 1. Barre latérale de Configuration
st.sidebar.header("🕹️ Contrôle de la Ligne")
status = st.sidebar.selectbox("État de la production", ["DÉMARRÉ", "ARRÊTÉ"])
nb_capteurs = st.sidebar.slider("Nombre d'appareils en ligne :", 1, 10, 4)
seuil_ia = st.sidebar.slider("Seuil d'alerte maximal (°C) :", 180, 320, 260)

# Sauvegarde de la configuration pour le simulateur
with open("config_pipeline.json", "w") as f:
    json.dump({"running": status == "DÉMARRÉ", "nb_machines": nb_capteurs, "seuil_critique": seuil_ia}, f)

# 2. ENTRAÎNEMENT DU MODÈLE RANDOM FOREST (Simulé mathématiquement pour l'exercice)
# On apprend à l'IA la physique de l'usine :
## 2. ENTRAÎNEMENT DU MODÈLE RANDOM FOREST (Profils nettoyés et complets)
# Features = [Température, Pente, Temps_depuis_allumage]
# Classes : 0 = Nominal, 1 = Phase Allumage, 2 = Risque de Panne
X_train = np.array([
    [150, 4.5, 2], [180, 5.0, 5], [210, 3.5, 8],   # Profils d'allumage (Forte pente, temps faible)
    [220, 0.2, 30], [222, -0.1, 40], [218, 0.5, 50], # Profils nominaux (Stable, temps long)
    [260, 2.8, 45], [285, 3.2, 55], [310, 4.1, 60]  # Profils de pannes (Forte pente, température haute, temps long)
])
y_train = np.array([1, 1, 1, 0, 0, 0, 2, 2, 2])

rf_model = RandomForestClassifier(n_estimators=10, random_state=42)
rf_model.fit(X_train, y_train)

# 3. Récupération du flux de données depuis TimescaleDB
@st.cache_data(ttl=1)
def obtenir_donnees_ia():
    try:
        conn = psycopg2.connect(host="localhost", database="tsdb", user="tsadmin", port="5432")
        query = """
            SELECT timestamp, machine_id, valeur, type_capteur 
            FROM mesures_filtrees 
            ORDER BY timestamp DESC LIMIT 100;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame(columns=["timestamp", "machine_id", "valeur", "type_capteur"])

df_flux = obtenir_donnees_ia()

# 4. Affichage des Appareils et Prédictions de l'IA
st.subheader("🔮 État des Équipements analysés par Random Forest")
cols = st.columns(4)

# Dictionnaire pour suivre le temps depuis l'allumage de chaque machine en mémoire locale
if "ticks_allumage" not in st.session_state:
    st.session_state["ticks_allumage"] = {}

for i in range(1, nb_capteurs + 1):
    m_id = f"pipe-10{i}"
    
    if m_id not in st.session_state["ticks_allumage"]:
        st.session_state["ticks_allumage"][m_id] = 0
        
    if status == "DÉMARRÉ":
        st.session_state["ticks_allumage"][m_id] += 1
        
    t_allumage = st.session_state["ticks_allumage"][m_id]
    df_m = df_flux[(df_flux["machine_id"] == m_id) & (df_flux["type_capteur"] == "temperature")]
    
    with cols[(i-1) % 4]:
        st.markdown(f"### ⚙️ Appareil `{m_id}`")
        
        if not df_m.empty:
            derniere_temp = float(df_m.iloc[0]["valeur"])
            
            # Calcul du gradient (pente)
            pente = float(df_m.iloc[0]["valeur"] - df_m.iloc[1]["valeur"]) if len(df_m) > 1 else 0.0
            
            # PRÉDICTION VIA RANDOM FOREST
            # Vecteur d'entrée : [Température, Pente, Temps écoulé]
            vecteur_test = np.array([[derniere_temp, pente, t_allumage]])
            prediction = rf_model.predict(vecteur_test)[0]
            
            # Affichage de la métrique
            st.metric(label="Température", value=f"{derniere_temp} °C", delta=f"{round(pente,2)} °C/s")
            
            # Rendu visuel basé sur la classification de la forêt aléatoire
            if prediction == 1:
                st.info(f"🚀 PHASE D'ALLUMAGE\n\nTemps : {t_allumage}s. La forte hausse est normale.")
            elif prediction == 2:
                st.error("⚠️ ALERTE : RISQUE DE PANNE\n\nRandom Forest détecte une dérive hors allumage !")
            else:
                st.success("✅ ÉTAT NOMINAL\n\nModèle stabilisé à haute température.")
        else:
            st.info("En attente du flux MQTT...")

st.markdown("---")
st.subheader("📊 Graphiques de Supervision")
st.link_button("🚀 Ouvrir le Dashboard Grafana", "http://localhost:3000")
# À insérer dans app.py sous la section de l'entraînement Random Forest
from sklearn.metrics import accuracy_score

# Évaluation du modèle sur les données d'entraînement 
y_pred = rf_model.predict(X_train)
precision = accuracy_score(y_train, y_pred) * 100
taux_erreur = 100 - precision

# Affichage des métriques de fiabilité sur le bandeau latéral
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Fiabilité de l'IA")
st.sidebar.metric(label="Précision du Modèle (Accuracy)", value=f"{round(precision, 1)} %")
st.sidebar.metric(label="Taux d'Erreur Global", value=f"{round(taux_erreur, 1)} %")

