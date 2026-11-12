# АРХИТЕКТУРА И СПЕЦИФИКАЦИЯ ПРОЕКТА: NORDIC FRAME

> **Проект:** Nordic Frame — Архитектурное бюро модульных и префаб домов  
> **Клиент / Заказчик:** Nordic Frame Architectural Bureau (Хельсинки / Санкт-Петербург / Москва)  
> **Чек проекта:** 380,000 ₽ | **Срок:** 14 дней (Дедлайн: 2026-11-25)  
> **Дедлайн MVP (80%):** 2026-11-22  
> **Тип договора:** Договор СМЗ с ИП (Чек «Мой Налог»)

---

## 🛠 Технологический стек
- **Frontend / UI:** HTML5 / CSS3 / JavaScript (Scandinavian Minimalist Configurator), Dynamic SVG Blueprint Schematics, Live Bill of Materials (BOM)
- **Backend & Logic:** Python 3.12, FastAPI, Uvicorn, SQLite3, ReportLab (PDF Generation), Pydantic v2
- **Telegram Bot:** Aiogram 3.x (Asyncio, Prefab Catalog, Dynamic PDF Estimate Dispatch, GPS Geolocation Visit Request)
- **Уведомления и лиды:** Автоматическая отправка проектных смет и заявок инженеру в @Idrisov_prod

---

## 🏛 Архитектурная схема
```
[ Клиент (Web Конфигуратор) ] ──► [ Смета / SVG Blueprint ] ──► [ REST API /api/estimate ] ──┐
                                                                                            ▼
[ Клиент (Telegram) ] ──► [ Nordic Frame Bot (PDF Смета / GPS Геолокация) ] ──────► [ SQLite DB ]
                                                                                            │
                                                                                            ▼
                                                                             [ Инженер & @Idrisov_prod ]
```

---

## 🔐 Переменные окружения (.env.example)
```env
BOT_TOKEN=8217851677:AAHN34TMuC1P4e6SppuazFN8BIiLHa_RyIc
TELEGRAM_OWNER_ID=1387913438
TELEGRAM_OWNER_USERNAME=@Idrisov_prod
PORT=3015
API_PORT=8015
PROXY_URL=socks5://dsZwtR:PTJNnz@72.57.96.136:8000
DATABASE_PATH=nordicframe.db
```

---

## 🔗 Ресурсы и ссылки
- **Порт Web UI / API:** `http://localhost:3015` / `http://localhost:8015`
- **Telegram Bot:** `@NordicFrameBot`
- **Канал заявок:** `@Idrisov_prod`
