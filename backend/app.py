"""
Nordic Frame — FastAPI Backend
Provides modular house calculation, BOM generation, PDF estimate export, and engineer geolocation visit handling.
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import math
import json
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
from backend.pdf_generator import generate_estimate_pdf

app = FastAPI(title="Nordic Frame Modular Architecture API", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Moscow Hub coordinates for distance calculation
HUB_LAT = 55.7558
HUB_LON = 37.6173

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

def compute_house_config(base_slug: str, addon_slugs: List[str]) -> Dict[str, Any]:
    base = database.get_base_by_slug(base_slug)
    # Dependency validation: if base missing, default to studio_35
    if not base:
        base = database.get_base_by_slug("studio_35")

    all_addons = database.get_all_addons()
    selected_addons = [a for a in all_addons if a["slug"] in addon_slugs]
    
    addons_total_price = sum(a["price_rub"] for a in selected_addons)
    addons_total_area = sum(a["area_sqm"] for a in selected_addons)
    
    total_price = base["base_price_rub"] + addons_total_price
    total_area = base["area_sqm"] + addons_total_area

    # 45% Materials, 15% Glazing, 20% Engineering, 20% Assembly
    materials = round(total_price * 0.45)
    glazing = round(total_price * 0.15)
    engineering = round(total_price * 0.20)
    assembly = total_price - (materials + glazing + engineering)

    bom = {
        "materials_rub": materials,
        "glazing_rub": glazing,
        "engineering_rub": engineering,
        "assembly_rub": assembly
    }

    return {
        "base": base,
        "addons": selected_addons,
        "total_area_sqm": total_area,
        "total_price_rub": total_price,
        "bom": bom
    }

class ConfigRequest(BaseModel):
    base_slug: str = "studio_35"
    addon_slugs: List[str] = []

class EstimateSubmitRequest(BaseModel):
    client_name: str
    phone: str
    base_slug: str = "studio_35"
    addon_slugs: List[str] = []

class EngineerVisitRequest(BaseModel):
    client_name: str
    phone: str
    latitude: float
    longitude: float
    preferred_date: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Nordic Frame Modular Architecture Backend</h1>")

@app.get("/api/catalog")
async def api_get_catalog():
    bases = database.get_all_bases()
    addons = database.get_all_addons()
    return {"status": "ok", "bases": bases, "addons": addons}

@app.post("/api/calculate")
async def api_calculate(req: ConfigRequest):
    config = compute_house_config(req.base_slug, req.addon_slugs)
    return {"status": "ok", "config": config}

@app.post("/api/estimate")
async def api_submit_estimate(req: EstimateSubmitRequest):
    if not req.client_name.strip() or not req.phone.strip():
        raise HTTPException(status_code=422, detail="Укажите имя и контактный телефон")
        
    config = compute_house_config(req.base_slug, req.addon_slugs)
    
    estimate_data = {
        "client_name": req.client_name,
        "phone": req.phone,
        "base_slug": req.base_slug,
        "selected_addons_json": json.dumps(req.addon_slugs),
        "total_area_sqm": config["total_area_sqm"],
        "materials_rub": config["bom"]["materials_rub"],
        "glazing_rub": config["bom"]["glazing_rub"],
        "engineering_rub": config["bom"]["engineering_rub"],
        "assembly_rub": config["bom"]["assembly_rub"],
        "total_price_rub": config["total_price_rub"]
    }
    est_number = database.save_estimate(estimate_data)
    
    lead_payload = {
        "project_name": "NordicFrame",
        "lead_type": "modular_house_estimate",
        "client_data": {
            "name": req.client_name,
            "phone": req.phone,
            "estimate_number": est_number,
            "model": config["base"]["name"],
            "area": f"{config['total_area_sqm']} м²",
            "addons_count": len(config["addons"]),
            "price_rub": config["total_price_rub"]
        },
        "target_recipient": "@Idrisov_prod"
    }

    return {
        "status": "ok",
        "estimate_number": est_number,
        "config": config,
        "lead_payload": lead_payload,
        "message": f"Смета #{est_number} сформирована! Архитектор бюро подготовил расчет."
    }

@app.post("/api/estimate/pdf")
async def api_download_estimate_pdf(req: EstimateSubmitRequest):
    config = compute_house_config(req.base_slug, req.addon_slugs)
    pdf_payload = {
        "estimate_number": "NF-PROSPECT",
        "client_name": req.client_name or "Заказчик",
        "phone": req.phone or "+7 (999) 000-00-00",
        "base": config["base"],
        "addons": config["addons"],
        "bom": config["bom"],
        "total_price_rub": config["total_price_rub"]
    }
    pdf_bytes = generate_estimate_pdf(pdf_payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=NordicFrame_Estimate.pdf"}
    )

@app.post("/api/engineer-visit")
async def api_engineer_visit(req: EngineerVisitRequest):
    if not req.client_name.strip() or not req.phone.strip():
        raise HTTPException(status_code=422, detail="Укажите имя и телефон")

    distance_km = haversine_distance_km(HUB_LAT, HUB_LON, req.latitude, req.longitude)
    
    if distance_km <= 150:
        zone = "Standard Hub Zone (МСК и МО)"
        fee = 5000
    elif distance_km <= 500:
        zone = "Extended Regional Zone"
        fee = round(5000 + (distance_km - 150) * 35)
    else:
        zone = "Individual Logistics Calculation"
        fee = 25000

    visit_data = {
        "client_name": req.client_name,
        "phone": req.phone,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "distance_km": distance_km,
        "service_zone": zone,
        "visit_fee_rub": fee,
        "preferred_date": req.preferred_date
    }
    visit_id = database.save_engineer_visit(visit_data)

    lead_payload = {
        "project_name": "NordicFrame",
        "lead_type": "engineer_onsite_visit",
        "client_data": {
            "name": req.client_name,
            "phone": req.phone,
            "geo": f"{req.latitude}, {req.longitude}",
            "distance_km": distance_km,
            "fee_rub": fee,
            "zone": zone
        },
        "target_recipient": "@Idrisov_prod",
        "visit_id": visit_id
    }

    return {
        "status": "ok",
        "visit_id": visit_id,
        "distance_km": distance_km,
        "service_zone": zone,
        "visit_fee_rub": fee,
        "lead_payload": lead_payload,
        "message": f"Вызов инженера зарегистрирован. Расстояние: {distance_km} км. Стоимость выезда: {fee:,} ₽".replace(",", " ")
    }
