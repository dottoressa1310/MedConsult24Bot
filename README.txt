
MedConsult24Bot — Telegram-бот (RU) для онлайн-консультаций и оплаты
====================================================================

Функции:
- Меню услуг (5 позиций) и кнопки оплаты: PayPal / YooMoney / LavaTop
- Кнопка перехода в WhatsApp после оплаты
- Уведомление в админ-чат и лог заявок в orders.csv

Структура:
- main.py            — код бота (aiogram 3)
- requirements.txt   — зависимости
- .env.example       — пример переменных окружения
- orders.csv         — создастся автоматически на сервере

Быстрый запуск локально
-----------------------
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export BOT_TOKEN=...            # на Windows: set BOT_TOKEN=...
export ADMIN_CHAT_ID=...        # ID вашего чата/канала
python main.py

Деплой на Render (24/7)
-----------------------
1) Залейте файлы в GitHub-репозиторий (main.py, requirements.txt, .env.example).
2) На render.com: New + -> Web Service -> Connect GitHub -> выберите репозиторий.
3) Настройки:
   - Runtime: Python 3.11
   - Build Command: pip install -r requirements.txt
   - Start Command: python main.py
4) Вкладка Environment: добавьте переменные из .env.example:
   BOT_TOKEN, ADMIN_CHAT_ID, PRICE_*, PAYPAL_BASE, YOOMONEY_TO_URL, LAVATOP_URL, WHATSAPP_URL
5) Create Web Service -> подождите пока статус станет Live.
6) Откройте бота в Telegram, введите /start.

Примечания
----------
- PayPal-ссылки формируются как PAYPAL_BASE/СУММА (например, .../50).
- YooMoney «to» ведёт на страницу перевода; при желании замените на quickpay со встроенной суммой.
- LavaTop — используйте продуктовую ссылку; сумму настраивайте в кабинете LavaTop.
- Для уведомлений в админ-чат укажите ADMIN_CHAT_ID (ID личного чата, группы или канала).
