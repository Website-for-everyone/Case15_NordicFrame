"""
Nordic Frame — SQLite Database Engine
Stores modular prefab house options, add-on components, project estimates, and on-site engineer requests.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "nordicframe.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # House bases table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS house_bases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        area_sqm INTEGER NOT NULL,
        bedrooms INTEGER NOT NULL,
        bathrooms INTEGER NOT NULL,
        base_price_rub INTEGER NOT NULL,
        dimensions TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """)
    
    # Add-on modules table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS addons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        price_rub INTEGER NOT NULL,
        area_sqm INTEGER DEFAULT 0,
        description TEXT NOT NULL
    )
    """)
    
    # Project Estimates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estimates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estimate_number TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        base_slug TEXT NOT NULL,
        selected_addons_json TEXT NOT NULL,
        total_area_sqm INTEGER NOT NULL,
        materials_rub INTEGER NOT NULL,
        glazing_rub INTEGER NOT NULL,
        engineering_rub INTEGER NOT NULL,
        assembly_rub INTEGER NOT NULL,
        total_price_rub INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # On-site Engineer Visit Requests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS engineer_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        distance_km REAL NOT NULL,
        service_zone TEXT NOT NULL,
        visit_fee_rub INTEGER NOT NULL,
        preferred_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )
    """)
    
    # Seed default bases if empty
    cursor.execute("SELECT COUNT(*) FROM house_bases")
    if cursor.fetchone()[0] == 0:
        default_bases = [
            ("Studio 35", "studio_35", 35, 1, 1, 2450000, "7.0 x 5.0 м", "Компактный энергоэффективный дом-студия для круглогодичного отдыха с панорамным фасадом."),
            ("Family 65", "family_65", 65, 2, 1, 4200000, "10.0 x 6.5 м", "Оптимальный загородный дом для семьи с двумя изолированными спальнями и просторной кухней-гостиной."),
            ("Villa 110", "villa_110", 110, 3, 2, 6900000, "13.5 x 8.2 м", "Флагманская скандинавская вилла с мастер-спальней, вторым светом, гардеробной и двумя санузлами.")
        ]
        cursor.executemany("""
        INSERT INTO house_bases 
        (name, slug, area_sqm, bedrooms, bathrooms, base_price_rub, dimensions, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_bases)

    # Seed default add-ons if empty
    cursor.execute("SELECT COUNT(*) FROM addons")
    if cursor.fetchone()[0] == 0:
        default_addons = [
            ("Панорамная терраса из лиственницы", "terrace", "exterior", 480000, 25, "Открытая терраса из сибирской лиственницы высшего сорта Вельвет с матовым защитным маслом."),
            ("Финская сауна из канадского кедра", "sauna", "spa", 750000, 15, "Встроенный банный модуль с электрокаменкой Harvia Cilindro и панорамным закаленным стеклом."),
            ("Панорамное остекление в пол Reynaers", "glazing", "facade", 390000, 0, "Теплый алюминиевый профиль Reynaers MasterLine 8 с энергоэффективными двухкамерными стеклопакетами."),
            ("Архитектурная подсветка и умный дом", "smart_light", "engineering", 240000, 0, "Скрытые LED-профили теплого спектра 2700K и сценарии освещения через Apple HomeKit / Zigbee."),
            ("Солнечная электростанция с АКБ", "solar", "eco", 620000, 0, "Монокристаллические панели 5 кВт на кровле + литий-железо-фосфатный аккумуляторный блок 10 кВт*ч."),
            ("Скандинавский водяной теплый пол", "floor_heating", "climate", 180000, 0, "Низкотемпературная система напольного отопления с позонными термостатами Danfoss.")
        ]
        cursor.executemany("""
        INSERT INTO addons (name, slug, category, price_rub, area_sqm, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, default_addons)
        
    conn.commit()
    conn.close()

def get_all_bases() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM house_bases ORDER BY base_price_rub ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_base_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM house_bases WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_addons() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM addons ORDER BY price_rub ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_estimate(data: Dict[str, Any]) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    
    import random
    est_num = f"NF-{random.randint(10000, 99999)}"
    
    cursor.execute("""
    INSERT INTO estimates 
    (estimate_number, client_name, phone, base_slug, selected_addons_json, total_area_sqm, materials_rub, glazing_rub, engineering_rub, assembly_rub, total_price_rub)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        est_num,
        data.get("client_name", "Anonymous"),
        data.get("phone", "N/A"),
        data.get("base_slug", "studio_35"),
        data.get("selected_addons_json", "[]"),
        data.get("total_area_sqm", 35),
        data.get("materials_rub", 0),
        data.get("glazing_rub", 0),
        data.get("engineering_rub", 0),
        data.get("assembly_rub", 0),
        data.get("total_price_rub", 0)
    ))
    conn.commit()
    conn.close()
    return est_num

def save_engineer_visit(data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO engineer_visits 
    (client_name, phone, latitude, longitude, distance_km, service_zone, visit_fee_rub, preferred_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("client_name", "Anonymous"),
        data.get("phone", "N/A"),
        data.get("latitude", 0.0),
        data.get("longitude", 0.0),
        data.get("distance_km", 0.0),
        data.get("service_zone", "Standard"),
        data.get("visit_fee_rub", 5000),
        data.get("preferred_date", None)
    ))
    visit_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return visit_id

# Initialize upon module import
init_db()
