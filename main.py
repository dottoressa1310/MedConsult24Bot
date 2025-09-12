
import os, csv, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage

# === Environment ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # <-- Вставь в Render (Secrets), НЕ в GitHub
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # ID твоего приватного админ-чата/канала

# Цены, можно менять в Render переменных
PRICE_CONSULT = int(os.getenv("PRICE_CONSULT", "50"))
PRICE_ANALYSIS = int(os.getenv("PRICE_ANALYSIS", "40"))
PRICE_PAGE = int(os.getenv("PRICE_PAGE", "30"))
PRICE_VIDEO = int(os.getenv("PRICE_VIDEO", "100"))
PRICE_URGENT = int(os.getenv("PRICE_URGENT", "100"))

# Платёжные ссылки (базы/полные)
PAYPAL_BASE = os.getenv("PAYPAL_BASE", "https://www.paypal.me/TatianaBocharova24")
YOOMONEY_TO_URL = os.getenv("YOOMONEY_TO_URL", "https://yoomoney.ru/to/4100119284022146")
LAVATOP_URL = os.getenv("LAVATOP_URL", "https://app.lava.top/products/a0bfe32b-ba3b-4c70-b408-ff4a67d81854")

# WhatsApp
WHATSAPP_URL = os.getenv("WHATSAPP_URL", "https://wa.me/393534689415")

# Файл-лог (локально на сервере Render)
ORDERS_CSV = "orders.csv"

# === Bot init ===
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

SERVICES = {
    "Консультация онлайн": PRICE_CONSULT,
    "Разбор анализов (за комплект)": PRICE_ANALYSIS,
    "Перевод мед. документов (1 стр.)": PRICE_PAGE,
    "Видеоконсультация": PRICE_VIDEO,
    "Срочная консультация (WhatsApp, ответ ≤ 30 мин)": PRICE_URGENT,
}

INFO_TEXT = (
    "⚠️ Важно:\n"
    "• Бот не предназначен для экстренных случаев (112/118).\n"
    "• Возрастное ограничение: 16+.\n"
    "• Рекомендации носят информационный характер.\n"
    "• Решение о лечении принимает ваш лечащий врач после очной консультации.\n"
)

def pay_kb(service_name: str, amount: int):
    kb = InlineKeyboardBuilder()
    # PayPal — можно указать сумму в конце
    kb.button(text=f"💳 PayPal — {amount} €", url=f"{PAYPAL_BASE}/{amount}")
    # YooMoney — ссылка «to», клиент сам вводит сумму (или используйте quickpay)
    kb.button(text=f"💳 YooMoney — {amount} €", url=YOOMONEY_TO_URL)
    # LavaTop — продуктовая ссылка (сумма на стороне LavaTop)
    kb.button(text="💳 LavaTop", url=LAVATOP_URL)
    # После оплаты — WhatsApp
    kb.button(text="✅ Я оплатил(а) — перейти в WhatsApp", url=WHATSAPP_URL)
    kb.button(text="↩️ Назад в меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()

def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="💼 Услуги и тарифы", callback_data="services")
    kb.button(text="💬 Связаться в WhatsApp", url=WHATSAPP_URL)
    kb.button(text="ℹ️ Информация", callback_data="info")
    kb.adjust(1)
    return kb.as_markup()

def services_kb():
    kb = InlineKeyboardBuilder()
    for name, price in SERVICES.items():
        kb.button(text=f"{name} — {price} €", callback_data=f"svc:{name}")
    kb.button(text="↩️ Назад в меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()

def save_order(user, service_name: str, amount: int):
    is_new = not os.path.exists(ORDERS_CSV)
    with open(ORDERS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if is_new:
            w.writerow(["datetime", "user_id", "username", "full_name", "service", "amount_eur"])
        w.writerow([
            datetime.datetime.now().isoformat(timespec="seconds"),
            user.id,
            user.username or "",
            f"{user.first_name or ''} {user.last_name or ''}".strip(),
            service_name,
            amount
        ])

async def notify_admin(user, service_name: str, amount: int):
    if not ADMIN_CHAT_ID:
        return
    txt = (
        f"🆕 Новая заявка\n"
        f"Пользователь: @{user.username} (ID {user.id})\n"
        f"Имя: {user.first_name or ''} {user.last_name or ''}\n"
        f"Услуга: {service_name}\n"
        f"Сумма: {amount} €\n"
        f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await bot.send_message(ADMIN_CHAT_ID, txt)

@dp.message(Command("start"))
async def start(m: Message):
    greet = "Здравствуйте! 🌿 Я бот *MedConsult24*.\n\nВыберите действие:"
    await m.answer(greet, reply_markup=main_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "menu")
async def back_to_menu(c: CallbackQuery):
    await c.message.edit_text("Главное меню:", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "info")
async def info(c: CallbackQuery):
    await c.message.answer(INFO_TEXT)

@dp.callback_query(F.data == "services")
async def list_services(c: CallbackQuery):
    text = "💼 *Услуги и тарифы:*\n\n" + "\n".join([f"• {n} — {p} €" for n, p in SERVICES.items()])
    text += "\n\nВыберите услугу:"
    await c.message.answer(text, parse_mode="Markdown", reply_markup=services_kb())

@dp.callback_query(F.data.startswith("svc:"))
async def service_selected(c: CallbackQuery):
    service_name = c.data.split("svc:")[1]
    amount = SERVICES.get(service_name)
    if amount is None:
        await c.answer("Неизвестная услуга", show_alert=True)
        return

    # лог и уведомление
    save_order(c.from_user, service_name, amount)
    await notify_admin(c.from_user, service_name, amount)

    extra = ""
    if "Срочная консультация" in service_name:
        extra = "\n\n⏱ Срочная услуга: ответ в WhatsApp в течение *30 минут* после обращения."
    if "Видеоконсультация" in service_name:
        extra = "\n\n🎥 Видеосвязь: после оплаты согласуем время (Zoom/Meet/WhatsApp call)."

    text = (
        f"*{service_name}* — {amount} €\n\n"
        "1) Оплатите удобным способом ниже.\n"
        "2) Нажмите «✅ Я оплатил(а) — перейти в WhatsApp».\n"
        "3) Напишите мне, укажите ФИО/тему запроса.\n"
        f"{extra}\n\n" + INFO_TEXT
    )
    await c.message.answer(text, parse_mode="Markdown", reply_markup=pay_kb(service_name, amount))
    await c.answer()

@dp.message(Command("prices"))
async def prices(m: Message):
    text = "💼 *Услуги и тарифы:*\n\n" + "\n".join([f"• {n} — {p} €" for n, p in SERVICES.items()])
    await m.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer("Связаться в WhatsApp: " + WHATSAPP_URL)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
