# Cesium Ion Token Setup

The 3D visualizer uses Cesium.js to display satellites on a 3D globe. To use Cesium's high-quality imagery and terrain, you need a free Cesium Ion access token.

## Getting a Cesium Ion Token

1. Go to [https://cesium.com/ion/](https://cesium.com/ion/)
2. Sign up for a free account
3. Navigate to "Access Tokens" in your dashboard
4. Copy your default access token

## Setting the Token

### Option 1: Environment Variable (Recommended)
```bash
export CESIUM_ION_TOKEN="your_token_here"
MISSION=example_mission make up
```

### Option 2: Set in Shell Profile
Add to your `~/.zshrc` or `~/.bashrc`:
```bash
export CESIUM_ION_TOKEN="your_token_here"
```

### Option 3: Use the .env File (Recommended for Development)
Edit the `.env` file in the project root:
```bash
CESIUM_ION_TOKEN=your_token_here
```

Then start normally (the .env file is loaded automatically):
```bash
MISSION=example_mission make up
# or for development mode with live file updates:
MISSION=example_mission make dev
```

## Verification

1. Start the stack: `MISSION=example_mission make up`
   - For development with live updates: `MISSION=example_mission make dev`
2. Open the visualizer: http://localhost:8081
3. You should see a high-quality 3D Earth with satellite markers

## Development Mode

Use `make dev` instead of `make up` for development:
- **Live file updates**: Edit files in `simulator/visualizer/public/` and refresh the browser
- **Cache disabled**: No need to hard refresh to see changes
- **Volume mounted**: Frontend files are served directly from your filesystem

```bash
MISSION=example_mission make dev
```

## Troubleshooting

- **No token set**: The visualizer will show a basic Earth without Cesium Ion imagery
- **Invalid token**: Check the browser console for 401 authentication errors
- **Token endpoint**: Visit http://localhost:8081/cesium-token to verify the token is being served correctly

## Rate Limits

Free Cesium Ion accounts have monthly usage limits. For production use or high-traffic scenarios, consider upgrading to a paid plan.
