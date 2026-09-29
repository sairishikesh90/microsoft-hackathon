const API_URL = "http://127.0.0.1:8000";

let map = null;
let primaryLayer = null;
let alternativeLayer = null;
let hazardLayer = null;

const btn = document.getElementById("checkBtn");
const message = document.getElementById("message");

function getLocation(idLat, idLng) {
  return {
    lat: Number(document.getElementById(idLat).value),
    lng: Number(document.getElementById(idLng).value)
  };
}

function statusClass(status) {
  if (status.includes("HIGH")) return "high";
  if (status.includes("MEDIUM")) return "medium";
  return "good";
}

function showHazards(primary, alternative) {
  const container = document.getElementById("hazards");
  container.innerHTML = "";

  const all = [...primary, ...alternative];
  const unique = [];
  const ids = new Set();

  for (const hazard of all) {
    if (!ids.has(hazard.id)) {
      ids.add(hazard.id);
      unique.push(hazard);
    }
  }

  if (!unique.length) {
    container.innerHTML = "<p>No hazards detected near the demo routes.</p>";
    return;
  }

  unique.forEach(h => {
    const div = document.createElement("div");
    div.className = "hazard";
    div.innerHTML = `
      <strong>${h.type} — ${h.severity.toUpperCase()}</strong>
      <span>${h.description}</span><br>
      <small>${h.distance_from_route_km} km from route</small>
    `;
    container.appendChild(div);
  });
}

function drawMap(data) {
  const origin = [data.origin.lat, data.origin.lng];
  const destination = [data.destination.lat, data.destination.lng];

  if (!map) {
    map = L.map("map").setView(origin, 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
  }

  if (primaryLayer) map.removeLayer(primaryLayer);
  if (alternativeLayer) map.removeLayer(alternativeLayer);
  if (hazardLayer) map.removeLayer(hazardLayer);

  const primaryCoords = data.primary_route.points.map(p => [p.lat, p.lng]);
  const alternativeCoords = data.alternative_route.points.map(p => [p.lat, p.lng]);

  primaryLayer = L.polyline(primaryCoords, {
    weight: 6
  }).addTo(map);

  alternativeLayer = L.polyline(alternativeCoords, {
    weight: 5,
    dashArray: "10 8"
  }).addTo(map);

  L.marker(origin).addTo(map).bindPopup("Origin");
  L.marker(destination).addTo(map).bindPopup("Destination");

  const hazards = [
    ...data.primary_route.hazards,
    ...data.alternative_route.hazards
  ];

  const seen = new Set();

  hazardLayer = L.layerGroup().addTo(map);

  hazards.forEach(h => {
    if (seen.has(h.id)) return;
    seen.add(h.id);

    L.circleMarker([h.lat, h.lng], {
      radius: 9
    })
      .bindPopup(`<b>${h.type}</b><br>${h.description}`)
      .addTo(hazardLayer);
  });

  const bounds = L.latLngBounds([
    ...primaryCoords,
    ...alternativeCoords,
    origin,
    destination
  ]);

  map.fitBounds(bounds, { padding: [30, 30] });
}

async function checkRoute() {
  btn.disabled = true;
  message.textContent = "Calculating route safety...";

  try {
    const body = {
      origin: getLocation("originLat", "originLng"),
      destination: getLocation("destLat", "destLng")
    };

    const response = await fetch(`${API_URL}/api/route`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      throw new Error("Backend returned an error.");
    }

    const data = await response.json();

    document.getElementById("results").classList.remove("hidden");

    document.getElementById("primaryScore").textContent =
      `${data.primary_route.risk_score}/100`;

    document.getElementById("primaryStatus").textContent =
      data.primary_route.status;

    document.getElementById("primaryStatus").className =
      statusClass(data.primary_route.status);

    document.getElementById("alternativeScore").textContent =
      `${data.alternative_route.risk_score}/100`;

    document.getElementById("alternativeStatus").textContent =
      data.alternative_route.status;

    document.getElementById("alternativeStatus").className =
      statusClass(data.alternative_route.status);

    document.getElementById("recommendation").textContent =
      data.explanation;

    showHazards(
      data.primary_route.hazards,
      data.alternative_route.hazards
    );

    drawMap(data);

    message.textContent = "Route analysis completed.";
  } catch (error) {
    console.error(error);
    message.textContent =
      "Could not connect to backend. Make sure FastAPI is running on port 8000.";
  } finally {
    btn.disabled = false;
  }
}

btn.addEventListener("click", checkRoute);
