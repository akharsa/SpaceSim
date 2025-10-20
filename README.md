SpaceSim — educational space mission simulator

Overview
- One-satellite prototype
- Containers for satellites and ground services
- MQTT bus (Mosquitto)
- InfluxDB for telemetry
- Grafana for dashboards
- Python-based satellite and groundstation services

Run
1. Install Docker and Docker Compose
2. From workspace root:
   docker compose up --build

Components
- services/satellite: satellite container code
- services/groundstation: groundstation subscriber and InfluxDB writer
- infrastructure/docker-compose.yml: compose file to run Mosquitto, InfluxDB, Grafana, satellite, and groundstation

Next steps
- Add Loki for logs
- Add timewarp control and CLI
- Add more satellite models (power, attitude, comms)
