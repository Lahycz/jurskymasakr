// server.js
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('.')); // Servíruj soubory

let playerPosition = { lat: 961.5, lng: 960 };
let markers = [];

app.get('/api/position', (req, res) => {
  res.json(playerPosition);
});

app.post('/api/markers', (req, res) => {
  markers.push(req.body);
  console.log('Marker:', req.body);
  res.json({ success: true });
});

app.post('/api/position', (req, res) => {
  playerPosition = req.body;
  res.json({ success: true });
});

app.listen(3000, () => console.log('Server: http://localhost:3000'));
