import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Token Telegram Anda
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# State untuk percakapan
CHOOSING, GET_EMAIL, GET_PASSWORD, BATCH = range(4)

# Cookies yang akan digunakan (sesuaikan dengan cookies Anda)
COOKIES = 'your_cookies_string_here'

# Fungsi start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya bot pendaftaran Netflix.\n"
        "Ketik /register untuk mendaftar satu akun.\n"
        "Ketik /batch untuk pendaftaran batch."
    )

# Fungsi untuk memilih mode
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Apakah Anda ingin mendaftar satu akun atau batch? (balas dengan 'satu' atau 'batch')")
    return CHOOSING

# Mengatur pilihan pengguna
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip().lower()
    if choice == 'satu':
        await update.message.reply_text("Silakan kirim email Anda.")
        return GET_EMAIL
    elif choice == 'batch':
        await update.message.reply_text("Kirim data batch Anda, misalnya dalam format email dan password per baris, pisahkan dengan newline.")
        return BATCH
    else:
        await update.message.reply_text("Pilihan tidak dikenali. Silakan ketik /register atau /batch lagi.")
        return ConversationHandler.END

# Mendapatkan email
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text.strip()
    await update.message.reply_text("Sekarang kirimkan password.")
    return GET_PASSWORD

# Mendapatkan password
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text.strip()
    email = context.user_data['email']
    password = context.user_data['password']
    await update.message.reply_text("Sedang proses pendaftaran...")
    # Panggil fungsi pendaftaran
    success = await register_account(email, password)
    if success:
        await update.message.reply_text("Pendaftaran berhasil!")
    else:
        await update.message.reply_text("Pendaftaran gagal.")
    return ConversationHandler.END

# Mendapatkan batch data
async def handle_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    batch_data = update.message.text.strip().splitlines()
    # Asumsikan format: email,password per baris
    results = []
    count = 0
    max_accounts = 5
    for line in batch_data:
        if count >= max_accounts:
            break
        parts = line.split(',')
        if len(parts) != 2:
            continue
        email, password = parts[0].strip(), parts[1].strip()
        success = await register_account(email, password)
        results.append((email, success))
        count +=1
    msg = "Hasil pendaftaran:\n"
    for email, success in results:
        status = "Berhasil" if success else "Gagal"
        msg += f"{email}: {status}\n"
    await update.message.reply_text(msg)
    return ConversationHandler.END

# Fungsi utama melakukan pendaftaran
async def register_account(email, password):
    url = 'https://www.netflix.com/signup'  # Ganti dengan endpoint yang benar jika berbeda
    headers = {
        'Cookie': COOKIES,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0'
    }
    data = {
        'email': email,
        'password': password
        # Tambahkan data lain sesuai kebutuhan
    }
    try:
        session = requests.Session()
        session.cookies.update({cookie.split('=')[0]: cookie.split('=')[1] for cookie in COOKIES.split(';')})
        response = session.post(url, headers=headers, data=data)
        if response.status_code == 200:
            # Cek respon untuk memastikan pendaftaran berhasil
            # Sesuaikan dengan response dari Netflix
            if "success" in response.text.lower():
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# Fungsi cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Perintah dibatalkan.')
    return ConversationHandler.END

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register_command)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
            GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            GET_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            BATCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)

    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()