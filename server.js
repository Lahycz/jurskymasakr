const express = require('express');
const cors = require('cors');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('.')); // Servíruj index.html a mapa.jpg

let playerPosition = { lat: 961.5, lng: 960 };
let markers = [];

// Tvoje pozice
app.get('/api/position', (req, res) => {
  res.json(playerPosition);
});

// Přidat marker
app.post('/api/markers', (req, res) => {
  markers.push(req.body);
  console.log('Nový marker:', req.body);
  res.json({ success: true });
});

// Aktualizovat tvou pozici (volej z jiné aplikace)
app.post('/api/position', (req, res) => {
  playerPosition = req.body;
  res.json({ success: true });
});

app.listen(3000, () => {
  console.log('Server běží na http://localhost:3000');
});
