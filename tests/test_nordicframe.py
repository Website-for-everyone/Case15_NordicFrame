"""
Unit and Smoke Tests for Case 15: Nordic Frame
Verifies modular house calculations, dependency resolution, ReportLab PDF byte streams, API routes, and bot registration.
"""

import pytest
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from backend.app import app, compute_house_config, haversine_distance_km
from backend.pdf_generator import generate_estimate_pdf
import database
from bot.bot import router, create_bot_and_dispatcher
from fastapi.testclient import TestClient

client = TestClient(app)

def test_database_bases_and_addons():
    bases = database.get_all_bases()
    assert len(bases) == 3
    slugs = [b["slug"] for b in bases]
    assert "studio_35" in slugs
    assert "family_65" in slugs
    assert "villa_110" in slugs

    addons = database.get_all_addons()
    assert len(addons) >= 4

def test_house_config_calculation():
    # Studio 35 + Terrace (+25m2, 480k) + Sauna (+15m2, 750k)
    config = compute_house_config("studio_35", ["terrace", "sauna"])
    assert config["base"]["slug"] == "studio_35"
    assert config["total_area_sqm"] == 35 + 25 + 15 # 75 sqm
    expected_total = 2450000 + 480000 + 750000 # 3680000
    assert config["total_price_rub"] == expected_total

    bom = config["bom"]
    bom_sum = bom["materials_rub"] + bom["glazing_rub"] + bom["engineering_rub"] + bom["assembly_rub"]
    assert bom_sum == expected_total

def test_missing_base_dependency_fallback():
    # If base is unknown or empty, system automatically falls back to studio_35
    config = compute_house_config("unknown_model", ["terrace"])
    assert config["base"]["slug"] == "studio_35"
    assert config["total_price_rub"] == 2450000 + 480000

def test_haversine_distance_and_zones():
    # Moscow center to nearby Khimki (55.88, 37.44) ~18 km
    dist_near = haversine_distance_km(55.7558, 37.6173, 55.88, 37.44)
    assert 10 <= dist_near <= 30

    # Moscow to Saint Petersburg (59.9343, 30.3351) ~630 km
    dist_spb = haversine_distance_km(55.7558, 37.6173, 59.9343, 30.3351)
    assert 600 <= dist_spb <= 700

def test_pdf_generation_bytes():
    config = compute_house_config("family_65", ["terrace", "glazing", "smart_light"])
    pdf_data = {
        "estimate_number": "NF-TEST-99",
        "client_name": "Test Client",
        "phone": "+79990001122",
        "base": config["base"],
        "addons": config["addons"],
        "bom": config["bom"],
        "total_price_rub": config["total_price_rub"]
    }
    pdf_bytes = generate_estimate_pdf(pdf_data)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    # PDF magic header
    assert pdf_bytes.startswith(b"%PDF-")

def test_api_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "NORDIC FRAME" in response.text

def test_api_catalog_endpoint():
    response = client.get("/api/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["bases"]) == 3
    assert len(data["addons"]) >= 4

def test_api_calculate_endpoint():
    payload = {"base_slug": "villa_110", "addon_slugs": ["solar", "floor_heating"]}
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["config"]["base"]["name"] == "Villa 110"

def test_api_estimate_submission():
    payload = {
        "client_name": "Dmitry",
        "phone": "+79998889900",
        "base_slug": "studio_35",
        "addon_slugs": ["terrace"]
    }
    response = client.post("/api/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["estimate_number"].startswith("NF-")

def test_api_pdf_download_endpoint():
    payload = {
        "client_name": "Anna",
        "phone": "+79997776655",
        "base_slug": "family_65",
        "addon_slugs": ["sauna"]
    }
    response = client.post("/api/estimate/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")

def test_api_engineer_visit_endpoint():
    payload = {
        "client_name": "Sergey",
        "phone": "+79994443322",
        "latitude": 55.85,
        "longitude": 37.55
    }
    response = client.post("/api/engineer-visit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["distance_km"] > 0
    assert data["visit_fee_rub"] >= 5000

def test_bot_registration():
    bot, dp = create_bot_and_dispatcher()
    assert bot is not None
    assert dp is not None
    assert len(router.message.handlers) >= 1
    assert len(router.callback_query.handlers) >= 4
