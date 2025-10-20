const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 8080;
const TELEMETRY_URL = process.env.TELEMETRY_URL || '/telemetry';
const CESIUM_ION_TOKEN = process.env.CESIUM_ION_TOKEN || '';

// In development mode, disable caching for live updates
if (process.env.NODE_ENV === 'development') {
  app.use((req, res, next) => {
    res.set('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.set('Pragma', 'no-cache');
    res.set('Expires', '0');
    next();
  });
}

app.use(express.static(path.join(__dirname, 'public')));
app.get('/health', (req, res) => res.send('ok'));
app.get('/cesium-token', (req, res) => res.send(CESIUM_ION_TOKEN));
app.get('/telemetry', async (req, res) => {
  try {
    const fetch = require('node-fetch');
    const r = await fetch(TELEMETRY_URL);
    const json = await r.json();
    res.json(json);
  } catch (e) {
    res.status(502).json({error: 'failed to fetch telemetry', detail: String(e)});
  }
});

app.listen(port, () => {
  console.log(`Visualizer listening on port ${port}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'production'}`);
  if (process.env.NODE_ENV === 'development') {
    console.log('Development mode: Static files will be served fresh from volume mount');
  }
});
