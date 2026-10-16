# Raffinerie IoT

Projet de pipeline IoT pour une raffinerie avec MQTT, Kafka, Spark, MinIO, TimescaleDB et Grafana.

## Stack
- Python
- MQTT
- Kafka
- Apache Spark
- MinIO
- PostgreSQL / TimescaleDB
- Docker Compose
- Grafana

## Structure
- `app.py` : point d’entrée principal de l’application
- `mqtt_to_kafka.py` : publication des données MQTT vers Kafka
- `simulateur_capteurs.py` : génération de données de capteurs
- `config_pipeline.json` : configuration du pipeline
- `spark/traitement_kpi.py` : traitement streaming Spark et KPI
- `docker-compose.yml` : orchestration des services

## Démarrage
1. Créer et activer un environnement virtuel
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Lancer les services Docker :
   ```bash
   docker compose up -d
   ```
4. Démarrer les scripts Python selon le besoin.

## Objectif
Collecter, filtrer, agréger et visualiser des données IoT provenant de capteurs industriels.
