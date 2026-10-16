import time, json, random, os, math
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883, 60)

def lire_config():
    if os.path.exists("config_pipeline.json"):
        with open("config_pipeline.json", "r") as f:
            try: return json.load(f)
            except: pass
    return {"running": True, "nb_machines": 4, "seuil_critique": 320}

# Initialisation des états pour simuler l'inertie physique
etats_machines = {}

print("🏭 Injection du modèle physique de Raffinerie en cours...")

while True:
    config = lire_config()
    
    if config["running"]:
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        nb_machines = config["nb_machines"]
        
        for i in range(1, nb_machines + 1):
            machine_id = f"pipe-10{i}"
            
            # Initialisation de la machine avec des valeurs de base industrielles
            if machine_id not in etats_machines:
                etats_machines[machine_id] = {
                    "tick": 0,
                    "base_temp": random.uniform(210.0, 240.0), # Vraie température de process
                    "en_panne": False
                }
            
            etats_machines[machine_id]["tick"] += 1
            t = etats_machines[machine_id]["tick"]
            base = etats_machines[machine_id]["base_temp"]
            
            # SCÉNARIO D'EXAMEN : On déclenche volontairement une panne d'encrassement sur la machine 2
            if machine_id == "pipe-102" and t > 20:
                etats_machines[machine_id]["en_panne"] = True
            
            if etats_machines[machine_id]["en_panne"]:
                # Dérive thermique métier : hausse continue + augmentation forte des vibrations
                facteur_derive = (t - 20) * 2.5
                temp = round(base + 15.0 * math.sin(t / 8) + facteur_derive + random.uniform(-0.5, 0.5), 2)
                vib = round(random.uniform(3.8, 5.5), 2) # Seuil critique mécanique dépassé
            else:
                # Régime nominal stable avec inertie (Sinus) et micro-bruit industriel
                temp = round(base + 4.0 * math.sin(t / 10) + random.uniform(-0.3, 0.3), 2)
                vib = round(random.uniform(1.1, 1.9), 2)
            
            # Envoi du message MQTT pour la température
            msg_temp = json.dumps({
                "machine_id": machine_id,
                "valeur": temp,
                "timestamp": now,
                "type_capteur": "temperature"
            })
            client.publish("raffinerie/temp", msg_temp)
            
            # Envoi du message MQTT pour la vibration
            msg_vib = json.dumps({
                "machine_id": machine_id,
                "valeur": vib,
                "timestamp": now,
                "type_capteur": "vibration"
            })
            client.publish("raffinerie/vib", msg_vib)
            
            print(f"📡 {machine_id} -> Temp: {temp}°C | Vib: {vib} mm/s | Anomalie: {etats_machines[machine_id]['en_panne']}")
            
    time.sleep(2)

