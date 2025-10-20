# SpaceSim — Educational Space Mission Simulator

## Overview
- Multi-satellite mission simulation with containers
- Real-time orbital propagation with time scaling
- MQTT telemetry bus (Eclipse Mosquitto)
- InfluxDB time-series storage
- Grafana dashboards with satellite selection
- 3D visualization with Cesium.js
- Mission configuration via YAML
- Docker Compose orchestration

## Quick Start

1. **Set up Cesium Ion token** (optional, for high-quality 3D visualization):
   ```bash
   export CESIUM_ION_TOKEN="your_token_here"
   ```
   See [CESIUM_SETUP.md](CESIUM_SETUP.md) for detailed instructions.

2. **Start the simulation**:
   ```bash
   MISSION=example_mission make up
   ```

3. **Access the interfaces**:
   - **3D Visualizer**: http://localhost:8081 (Cesium.js 3D satellite tracking)
   - **Grafana Dashboard**: http://localhost:3000 (admin/admin)
   - **InfluxDB**: http://localhost:8086

## Components
- `modules/satellite`: Lightweight orbital propagation with configurable parameters
- `modules/groundstation`: MQTT subscriber writing telemetry to InfluxDB
- `simulator/telemetry_bridge`: MQTT-to-HTTP bridge for visualizer
- `simulator/visualizer`: Cesium.js 3D frontend with real-time updates
- `simulator/mission_time`: Centralized mission clock service
- `missions/`: YAML mission definitions with satellite initial conditions
- `scripts/`: Dynamic compose generation for variable satellite counts

## Mission Configuration
Missions are defined in YAML files under `missions/`. Example:
```yaml
satellites:
  - sat_id: 1
    alt_km: 500
    inc_deg: 0
  - sat_id: 2
    alt_km: 700
    inc_deg: 45
```

## Make Targets
- `make up`: Start the full stack
- `make down`: Stop all services
- `make logs`: Show container logs
- `make clean`: Remove volumes and networks

## Next Steps
- Add Loki for centralized logging
- Implement realistic attitude dynamics
- Add power system modeling
- Enhance communication link budget simulation
