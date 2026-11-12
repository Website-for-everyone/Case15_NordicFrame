"""
Nordic Frame — Aiogram 3.x Telegram Bot Companion
Prefab catalog, dynamic PDF estimate streaming, and engineer on-site GPS visit requests.
"""

import asyncio
import os
import sys
import json
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
from backend.app import compute_house_config, haversine_distance_km, HUB_LAT, HUB_LON
from backend.pdf_generator import generate_estimate_pdf

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8217851677:AAHN34TMuC1P4e6SppuazFN8BIiLHa_RyIc")
OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", "1387913438"))
OWNER_USERNAME = os.environ.get("TELEGRAM_OWNER_USERNAME", "@Idrisov_prod")

router = Router()

class EngineerVisitState(StatesGroup):
    waiting_for_location = State()
    waiting_for_contact = State()

def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏡 Каталог типовых домов", callback_data="catalog_bases")],
        [InlineKeyboardButton(text="📥 Получить смету в PDF", callback_data="pdf_wizard")],
        [InlineKeyboardButton(text="🧭 Вызов инженера на участок (GPS)", callback_data="start_visit")],
        [InlineKeyboardButton(text="💬 Главный архитектор", url=f"https://t.me/{OWNER_USERNAME.lstrip('@')}")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🌲 <b>Архитектурное бюро Nordic Frame</b>\n\n"
        "Мы проектируем и возводим современные модульные дома в лаконичной скандинавской эстетике.\n\n"
        "• Каркас из австрийского CLT-бруса\n"
        "• Энергоэффективность класса А++\n"
        "• Заводская сборка за 45 дней, монтаж на участке за 3–5 дней\n"
        "• Гарантия 25 лет на конструктив\n\n"
        "Выберите интересующий раздел:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🌲 <b>Главное меню Nordic Frame:</b>", parse_mode="HTML", reply_markup=get_main_menu())
    await call.answer()

# --- House Bases Catalog ---
@router.callback_query(F.data == "catalog_bases")
async def cb_catalog_bases(call: CallbackQuery):
    bases = database.get_all_bases()
    kb = []
    for b in bases:
        kb.append([InlineKeyboardButton(text=f"{b['name']} ({b['area_sqm']} м²) — {b['base_price_rub']:,} ₽".replace(",", " "), callback_data=f"base_detail_{b['slug']}")])
    kb.append([InlineKeyboardButton(text="⬅️ В главное меню", callback_data="main_menu")])
    
    await call.message.edit_text(
        "🏡 <b>Модельный ряд модульных домов Nordic Frame:</b>\nВыберите проект для ознакомления со спецификацией:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()

@router.callback_query(F.data.startswith("base_detail_"))
async def cb_base_detail(call: CallbackQuery):
    slug = call.data.replace("base_detail_", "")
    base = database.get_base_by_slug(slug)
    if not base:
        await call.answer("Проект не найден", show_alert=True)
        return
        
    text = (
        f"🏡 <b>Nordic Frame {base['name']}</b>\n\n"
        f"📐 <b>Площадь:</b> {base['area_sqm']} м² ({base['dimensions']})\n"
        f"🛏 <b>Спальни:</b> {base['bedrooms']} | 🚿 <b>Санузлы:</b> {base['bathrooms']}\n"
        f"📝 {base['description']}\n\n"
        f"💰 <b>Стоимость теплого контура:</b> {base['base_price_rub']:,} ₽\n"
    ).replace(",", " ")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать PDF-смету проекта", callback_data=f"get_pdf_{base['slug']}")],
        [InlineKeyboardButton(text="⬅️ К каталогу", callback_data="catalog_bases")]
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

# --- PDF Estimate Stream Generator ---
@router.callback_query(F.data == "pdf_wizard" | F.data.startswith("get_pdf_"))
async def cb_send_pdf_estimate(call: CallbackQuery):
    slug = "studio_35"
    if call.data.startswith("get_pdf_"):
        slug = call.data.replace("get_pdf_", "")
        
    user = call.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"
    
    config = compute_house_config(slug, ["terrace", "glazing", "sauna"])
    
    pdf_payload = {
        "estimate_number": f"NF-{call.from_user.id % 100000}",
        "client_name": user.full_name,
        "phone": username,
        "base": config["base"],
        "addons": config["addons"],
        "bom": config["bom"],
        "total_price_rub": config["total_price_rub"]
    }
    
    await call.answer("⏳ Генерируем архитектурную PDF-смету...")
    pdf_bytes = generate_estimate_pdf(pdf_payload)
    
    input_file = BufferedInputFile(pdf_bytes, filename=f"NordicFrame_Estimate_{slug.upper()}.pdf")
    
    caption = (
        f"📄 <b>Официальная смета Nordic Frame готова</b>\n\n"
        f"Модель: <b>{config['base']['name']}</b>\n"
        f"Площадь: <b>{config['total_area_sqm']} м²</b>\n"
        f"Итоговая смета под ключ: <b>{config['total_price_rub']:,} ₽</b>\n\n"
        f"В смету включены: панорамная терраса, остекление Reynaers и финская сауна из кедра.".replace(",", " ")
    )
    
    await call.message.answer_document(
        document=input_file,
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧭 Вызвать инженера на участок", callback_data="start_visit")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ])
    )

# --- Engineer On-Site Visit & Geolocation Request ---
@router.callback_query(F.data == "start_visit")
async def cb_visit_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EngineerVisitState.waiting_for_location)
    text = (
        "🧭 <b>Вызов главного инженера на земельный участок</b>\n\n"
        "Инженер приедет с геодезическим оборудованием для:\n"
        "• Анализа перепада высот и уклона грунта\n"
        "• Определения типа фундамента (сваи / плита УШП)\n"
        "• Привязки дома к сторонам света и инсоляции\n"
        "• Замера подъездных путей для монтажного крана\n\n"
        "👇 <b>Отправьте геометку вашего участка</b> (через скрепку 📎 -> Геопозиция):"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="main_menu")]
        ])
    )
    await call.answer()

@router.message(EngineerVisitState.waiting_for_location, F.location)
async def process_visit_location(message: Message, state: FSMContext):
    loc = message.location
    lat, lon = loc.latitude, loc.longitude
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"

    distance_km = haversine_distance_km(HUB_LAT, HUB_LON, lat, lon)
    
    if distance_km <= 150:
        zone = "Стандартная зона выезда (МСК и МО)"
        fee = 5000
    elif distance_km <= 500:
        zone = "Расширенная региональная зона"
        fee = round(5000 + (distance_km - 150) * 35)
    else:
        zone = "Индивидуальный расчет логистики (удаленный регион)"
        fee = 25000

    visit_data = {
        "client_name": user.full_name,
        "phone": username,
        "latitude": lat,
        "longitude": lon,
        "distance_km": distance_km,
        "service_zone": zone,
        "visit_fee_rub": fee
    }
    visit_id = database.save_engineer_visit(visit_data)
    await state.clear()

    reply_text = (
        f"✅ <b>Геометка участка получена! Заявка #{visit_id}</b>\n\n"
        f"📍 <b>Координаты:</b> <code>{lat:.4f}, {lon:.4f}</code>\n"
        f"🚗 <b>Расстояние от бюро:</b> {distance_km} км\n"
        f"🌍 <b>Зона обслуживания:</b> {zone}\n"
        f"💰 <b>Стоимость выезда инженера:</b> {fee:,} ₽ (зачитывается в стоимость договора)\n\n"
        f"Ведущий инженер свяжется с вами для согласования даты и времени прибытия!".replace(",", " ")
    )

    await message.answer(
        reply_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ])
    )

@router.message(EngineerVisitState.waiting_for_location, ~F.location)
async def process_visit_no_location(message: Message):
    await message.answer("⚠️ Пожалуйста, прикрепите геометку участка через кнопку скрепки (Вложение -> Геолокация).")

def create_bot_and_dispatcher():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return bot, dp

async def main():
    bot, dp = create_bot_and_dispatcher()
    print("Starting Nordic Frame Telegram Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
