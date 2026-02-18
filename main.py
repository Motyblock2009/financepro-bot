import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔴 ВСТАВЬ СЮДА СВОЙ ТОКЕН
import os
TOKEN = os.getenv("7833296103:AAGwEszlBcZpGZKB9xtCQeK66yAuMpRjAO8")


# ---------- БАЗА ----------
conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    income INTEGER DEFAULT 0,
    expense INTEGER DEFAULT 0
)
""")

conn.commit()

# ---------- МЕНЮ ----------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Доход", callback_data="income"),
         InlineKeyboardButton("➖ Расход", callback_data="expense")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧮 Калькулятор", callback_data="calc")],
        [InlineKeyboardButton("📚 Урок", callback_data="lesson")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    await update.message.reply_text(
        "💰 FinancePro работает 🚀",
        reply_markup=main_menu()
    )

# ---------- КНОПКИ ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "income":
        context.user_data["state"] = "income"
        await query.message.reply_text("Введите сумму дохода:")

    elif query.data == "expense":
        context.user_data["state"] = "expense"
        await query.message.reply_text("Введите сумму расхода:")

    elif query.data == "stats":
        cursor.execute("SELECT income, expense FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        if row:
            income, expense = row
        else:
            income, expense = 0, 0

        balance = income - expense

        await query.edit_message_text(
            f"📊 Статистика\n\n"
            f"Доход: {income} ₽\n"
            f"Расход: {expense} ₽\n"
            f"Баланс: {balance} ₽",
            reply_markup=main_menu()
        )

    elif query.data == "calc":
        context.user_data["state"] = "calc"
        await query.message.reply_text(
            "Введите: сумма процент годы\nПример: 100000 10 5"
        )

    elif query.data == "lesson":
        await query.edit_message_text(
            "📚 Урок: Правило 50/30/20\n\n"
            "50% — обязательные расходы\n"
            "30% — желания\n"
            "20% — накопления",
            reply_markup=main_menu()
        )

# ---------- ОБРАБОТКА ВВОДА ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = context.user_data.get("state")

    if not state:
        return

    try:
        if state == "income":
            amount = int(update.message.text)

            cursor.execute(
                "UPDATE users SET income = income + ? WHERE user_id=?",
                (amount, user_id),
            )
            conn.commit()

            await update.message.reply_text("✅ Доход добавлен")
            context.user_data["state"] = None

        elif state == "expense":
            amount = int(update.message.text)

            cursor.execute(
                "UPDATE users SET expense = expense + ? WHERE user_id=?",
                (amount, user_id),
            )
            conn.commit()

            await update.message.reply_text("❌ Расход добавлен")
            context.user_data["state"] = None

        elif state == "calc":
            s, p, y = map(int, update.message.text.split())
            result = s * ((1 + p / 100) ** y)

            await update.message.reply_text(f"📈 Итог: {int(result)} ₽")
            context.user_data["state"] = None

    except:
        await update.message.reply_text("Ошибка ввода. Попробуйте ещё раз.")

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 Бот запущен")
    app.run_polling()
