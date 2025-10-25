import telebot
from telebot import types
import json
import os

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8402099225:AAHjAH4d-a7TIU_pJmCCurpzDsRK_FygLwg")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7903688837))
DATA_FILE = "data.json"
# ----------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------------- HELPERS ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "prices": {
                "100💎": 13000,
                "210💎": 25000,
                "560💎": 62000,
                "1000💎": 110000,
                "2180💎": 210000
            },
            "card": "**** **** **** 5953",
            "orders": [],
            "users": {}
        }
        save_data(data)
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.from_user.id)
    data = load_data()

    if user_id not in data["users"]:
        data["users"][user_id] = {"total_orders": 0}
        save_data(data)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💎 Almaz sotib olish", "🧾 Profil")
    if msg.from_user.id == ADMIN_ID:
        markup.add("👑 Admin panel")
    bot.send_message(msg.chat.id, "👋 Salom! Bu yerda Free Fire almaz sotib olishingiz mumkin!", reply_markup=markup)

# ---------------- USER PART ----------------
@bot.message_handler(func=lambda m: m.text == "💎 Almaz sotib olish")
def buy_almaz(msg):
    data = load_data()
    prices = data["prices"]

    markup = types.InlineKeyboardMarkup()
    for name, price in prices.items():
        markup.add(types.InlineKeyboardButton(text=f"{name} - {price} so'm", callback_data=f"buy_{name}"))
    bot.send_message(msg.chat.id, "💎 Qancha almaz olmoqchisiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def select_id(call):
    almaz = call.data.replace("buy_", "")
    bot.send_message(call.message.chat.id, f"🎮 Free Fire ID raqamingizni kiriting (almaz: {almaz})")
    bot.register_next_step_handler(call.message, lambda msg: ask_payment(msg, almaz))

def ask_payment(msg, almaz):
    ffid = msg.text.strip()
    data = load_data()
    card = data["card"]
    price = data["prices"][almaz]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Click / Payme", callback_data=f"click_{almaz}_{ffid}"))
    markup.add(types.InlineKeyboardButton("🏦 Kartadan to‘lash", callback_data=f"card_{almaz}_{ffid}"))
    bot.send_message(msg.chat.id, f"💰 {almaz} narxi: {price} so‘m\nTo‘lov turini tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("click_", "card_")))
def payment_process(call):
    parts = call.data.split("_")
    pay_type = parts[0]
    almaz = parts[1]
    ffid = parts[2]
    data = load_data()
    price = data["prices"][almaz]
    card = data["card"]

    if pay_type == "card":
        bot.send_message(call.message.chat.id, f"💳 To‘lov uchun karta:\n<code>{card}</code>\n\n💰 {price} so‘m\n\nTo‘lovni amalga oshirib, chek (screenshot)ni shu yerga yuboring.")
    else:
        bot.send_message(call.message.chat.id, f"💸 Click yoki Payme orqali {price} so‘m to‘lang.\nSo‘ngra chekni yuboring.")

    bot.register_next_step_handler(call.message, lambda msg: send_to_admin(msg, almaz, ffid, price, pay_type))

def send_to_admin(msg, almaz, ffid, price, pay_type):
    if not msg.photo:
        bot.send_message(msg.chat.id, "❌ Iltimos, to‘lov cheki rasm holatda yuboring.")
        return
    photo_id = msg.photo[-1].file_id
    data = load_data()
    order = {
        "user_id": msg.from_user.id,
        "almaz": almaz,
        "ffid": ffid,
        "price": price,
        "type": pay_type
    }
    data["orders"].append(order)
    data["users"][str(msg.from_user.id)]["total_orders"] += 1
    save_data(data)
    bot.send_photo(ADMIN_ID, photo_id, caption=f"🆕 Yangi buyurtma!\n👤 @{msg.from_user.username}\n💎 {almaz}\n🎮 FF ID: {ffid}\n💰 {price} so‘m\n💳 {pay_type}")
    bot.send_message(msg.chat.id, "✅ Buyurtmangiz yuborildi, admin tasdiqlaguncha kuting.")

# ---------------- PROFILE ----------------
@bot.message_handler(func=lambda m: m.text == "🧾 Profil")
def profile(msg):
    data = load_data()
    user = data["users"].get(str(msg.from_user.id), {"total_orders": 0})
    bot.send_message(msg.chat.id, f"👤 Profil:\n🛍 Jami buyurtmalar: {user['total_orders']} ta")

# ---------------- ADMIN PANEL ----------------
@bot.message_handler(func=lambda m: m.text == "👑 Admin panel" and m.from_user.id == ADMIN_ID)
def admin_panel(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Narxlarni o‘zgartirish", "💳 Kartani o‘zgartirish")
    markup.add("📦 Buyurtmalar ro‘yxati", "📤 Xabar yuborish", "⬅️ Orqaga")
    bot.send_message(msg.chat.id, "👑 Admin panel", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def back(msg):
    start(msg)

@bot.message_handler(func=lambda m: m.text == "💰 Narxlarni o‘zgartirish" and m.from_user.id == ADMIN_ID)
def change_prices(msg):
    data = load_data()
    text = "💎 Hozirgi narxlar:\n"
    for name, price in data["prices"].items():
        text += f"{name}: {price} so‘m\n"
    text += "\nYangi narxni yozing shu formatda:\n<code>100💎=15000</code>"
    bot.send_message(msg.chat.id, text)
    bot.register_next_step_handler(msg, save_new_price)

def save_new_price(msg):
    if "=" not in msg.text:
        bot.send_message(msg.chat.id, "❌ Noto‘g‘ri format.")
        return
    key, val = msg.text.split("=")
    key = key.strip()
    val = int(val.strip())
    data = load_data()
    data["prices"][key] = val
    save_data(data)
    bot.send_message(msg.chat.id, f"✅ {key} narxi {val} so‘m qilib o‘zgartirildi.")

@bot.message_handler(func=lambda m: m.text == "💳 Kartani o‘zgartirish" and m.from_user.id == ADMIN_ID)
def change_card(msg):
    bot.send_message(msg.chat.id, "💳 Yangi kartani kiriting (masalan: 8600 **** **** 1234):")
    bot.register_next_step_handler(msg, save_new_card)

def save_new_card(msg):
    new_card = msg.text.strip()
    data = load_data()
    data["card"] = new_card
    save_data(data)
    bot.send_message(msg.chat.id, f"✅ Karta yangilandi: {new_card}")

@bot.message_handler(func=lambda m: m.text == "📦 Buyurtmalar ro‘yxati" and m.from_user.id == ADMIN_ID)
def order_list(msg):
    data = load_data()
    if not data["orders"]:
        bot.send_message(msg.chat.id, "📭 Hozircha buyurtmalar yo‘q.")
        return
    text = "📦 Buyurtmalar:\n"
    for o in data["orders"][-10:]:
        text += f"{o['almaz']} | {o['price']} so‘m | FFID: {o['ffid']}\n"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📤 Xabar yuborish" and m.from_user.id == ADMIN_ID)
def broadcast(msg):
    bot.send_message(msg.chat.id, "📢 Yuboriladigan xabarni kiriting:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(msg):
    text = msg.text
    data = load_data()
    users = data["users"].keys()
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, text)
            count += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"✅ Xabar {count} foydalanuvchiga yuborildi.")

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
