from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from math import radians, sin, cos, sqrt, atan2
from typing import List

app = FastAPI(title="SafeRoute AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class RouteRequest(BaseModel):
    origin: Location
    destination: Location

# Demo hazard data.
# Later this can be replaced by IMD / APSDMA / SACHET / verified feeds.
HAZARDS = [
    {
        "id": 1,
        "type": "Flood",
        "lat": 16.5062,
        "lng": 80.6480,
        "severity": "high",
        "weight": 45,
        "description": "Flood-prone road segment"
    },
    {
        "id": 2,
        "type": "Heavy Rain",
        "lat": 16.5100,
        "lng": 80.6400,
        "severity": "medium",
        "weight": 25,
        "description": "Heavy rainfall reported"
    },
    {
        "id": 3,
        "type": "Road Closure",
        "lat": 16.5150,
        "lng": 80.6550,
        "severity": "high",
        "weight": 40,
        "description": "Road closure / obstruction"
    },
    {
        "id": 4,
        "type": "Damaged Infrastructure",
        "lat": 16.5000,
        "lng": 80.6600,
        "severity": "medium",
        "weight": 20,
        "description": "Infrastructure hazard reported"
    },
]

def distance_km(a, b):
    """Haversine distance between two lat/lng points."""
    R = 6371.0
    lat1, lon1 = radians(a["lat"]), radians(a["lng"])
    lat2, lon2 = radians(b["lat"]), radians(b["lng"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(h), sqrt(1 - h))

def point_to_segment_distance_km(point, start, end):
    """
    Approximate distance from a geographic point to a route segment.
    For this MVP we use a local lat/lng projection, which is sufficient
    for short demo routes.
    """
    lat_scale = 111.0
    lon_scale = 111.0 * cos(radians((start["lat"] + end["lat"]) / 2))

    px = (point["lng"] - start["lng"]) * lon_scale
    py = (point["lat"] - start["lat"]) * lat_scale
    ex = (end["lng"] - start["lng"]) * lon_scale
    ey = (end["lat"] - start["lat"]) * lat_scale

    length_sq = ex * ex + ey * ey
    if length_sq == 0:
        return distance_km(point, start)

    t = max(0, min(1, (px * ex + py * ey) / length_sq))
    closest = {
        "lat": start["lat"] + t * (end["lat"] - start["lat"]),
        "lng": start["lng"] + t * (end["lng"] - start["lng"]),
    }
    return distance_km(point, closest)

def interpolate(a, b, count=8):
    points = []
    for i in range(count + 1):
        t = i / count
        points.append({
            "lat": a["lat"] + (b["lat"] - a["lat"]) * t,
            "lng": a["lng"] + (b["lng"] - a["lng"]) * t,
        })
    return points

def calculate_route_risk(points):
    risk = 0
    matched_hazards = []

    for hazard in HAZARDS:
        closest = min(
            point_to_segment_distance_km(hazard, points[i], points[i + 1])
            for i in range(len(points) - 1)
        )

        # Hazard affects route if it is within ~2 km.
        if closest <= 2.0:
            risk += hazard["weight"]
            matched_hazards.append({
                **hazard,
                "distance_from_route_km": round(closest, 2)
            })

    # Keep score in 0-100 range.
    risk = min(100, risk)

    if risk >= 70:
        status = "HIGH RISK"
    elif risk >= 35:
        status = "MEDIUM RISK"
    else:
        status = "LOWER RISK"

    return risk, status, matched_hazards

def build_alternative(origin, destination):
    """
    Demo alternative: shifts the midpoint east/west.
    This is NOT a real road-routing algorithm.
    Replace with OSRM/Google Maps/Mapbox routing later.
    """
    mid = {
        "lat": (origin["lat"] + destination["lat"]) / 2,
        "lng": (origin["lng"] + destination["lng"]) / 2 + 0.015,
    }

    first = interpolate(origin, mid, 4)
    second = interpolate(mid, destination, 4)[1:]
    return first + second

@app.get("/")
def root():
    return {"message": "SafeRoute AI backend is running"}

@app.get("/api/hazards")
def get_hazards():
    return {"hazards": HAZARDS}

@app.post("/api/route")
def calculate_route(request: RouteRequest):
    origin = request.origin.model_dump()
    destination = request.destination.model_dump()

    primary_points = interpolate(origin, destination, 10)
    primary_risk, primary_status, primary_hazards = calculate_route_risk(primary_points)

    alternative_points = build_alternative(origin, destination)
    alternative_risk, alternative_status, alternative_hazards = calculate_route_risk(
        alternative_points
    )

    if alternative_risk < primary_risk:
        recommendation = "Use the alternative route because it has lower detected hazard risk."
        recommended = "alternative"
    else:
        recommendation = "The primary route currently has the lower detected hazard risk."
        recommended = "primary"

    return {
        "origin": origin,
        "destination": destination,
        "primary_route": {
            "risk_score": primary_risk,
            "status": primary_status,
            "hazards": primary_hazards,
            "points": primary_points,
        },
        "alternative_route": {
            "risk_score": alternative_risk,
            "status": alternative_status,
            "hazards": alternative_hazards,
            "points": alternative_points,
        },
        "recommended_route": recommended,
        "explanation": recommendation,
        "note": "This MVP uses demo hazard data and geometric demo routes, not live road routing."
    }
