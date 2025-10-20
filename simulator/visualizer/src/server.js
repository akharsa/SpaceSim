const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 8080;
const TELEMETRY_URL = process.env.TELEMETRY_URL || '/telemetry';

app.use(express.static(path.join(__dirname, '../public')));
app.get('/health', (req, res) => res.send('ok'));
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
});
