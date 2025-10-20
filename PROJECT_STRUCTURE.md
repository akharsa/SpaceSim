# SpaceSim Project Structure

After reorganization, the project now follows this structure:

```
SpaceSim/
├── simulator/                    # Core simulation infrastructure
│   ├── docker-compose.yml        # Main orchestration file
│   ├── telemetry_bridge.yml      # Telemetry bridge compose fragment  
│   ├── visualizer.yml            # 3D visualizer compose fragment
│   ├── compose.mission.yml        # Auto-generated mission satellites (gitignored)
│   ├── mission_time/             # Centralized mission clock service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/main.py
│   ├── telemetry_bridge/         # MQTT-to-HTTP bridge
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/main.py
│   ├── visualizer/               # Cesium.js 3D visualization
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── server.js
│   │   └── public/index.html
│   ├── grafana/                  # Dashboard configuration
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── mosquitto/                # MQTT broker configuration
│       └── config/
├── modules/                      # Reusable mission components
│   ├── satellite/                # Satellite simulation module
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/main.py
│   └── groundstation/            # Ground segment module
│       ├── Dockerfile
│       ├── requirements.txt
│       └── src/main.py
├── missions/                     # Mission definitions
│   └── example_mission.yaml
├── scripts/                      # Automation and utilities
│   ├── generate_compose_mission.py
│   └── setup_env.sh
├── Makefile                      # Build and deployment commands
├── README.md
├── CESIUM_SETUP.md
└── .env                          # Environment variables
```

## Key Changes

1. **simulator/** - Contains all core simulation infrastructure (formerly `infrastructure/`)
   - Mission time service moved here from modules
   - All visualization and telemetry bridge components
   - Configuration files for supporting services

2. **modules/** - Contains reusable mission components (formerly `services/`)
   - Satellite simulation modules
   - Ground station modules
   - Can be reused across different missions

3. **Mission Time Service** - Moved to `simulator/mission_time/`
   - Now part of core simulation infrastructure
   - Provides unified timing for all mission components
   - Centralized mission clock authority

This structure better reflects the architecture:
- **Simulator**: Core infrastructure that runs any mission
- **Modules**: Pluggable components that can be configured per mission  
- **Missions**: Configuration files that define specific scenarios
