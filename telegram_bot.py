import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import random
import time
from telegram.error import NetworkError

def init_db():
    try:
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            print("LOG: Initializing bot database...")
            c.execute('''CREATE TABLE IF NOT EXISTS otp_verifications (
                phone_number TEXT PRIMARY KEY,
                otp TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()
            print("LOG: otp_verifications table created or already exists")
    except Exception as e:
        print(f"LOG: Bot database initialization error: {str(e)}")

def generate_otp():
    otp = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    print(f"LOG: Generated OTP: {otp}")
    return otp

def start(update, context):
    print("LOG: Received /start command")
    update.message.reply_text('Please send your 10-digit mobile number.')

def handle_message(update, context):
    phone_number = update.message.text
    print(f"LOG: Received message: {phone_number}")
    if phone_number.isdigit() and len(phone_number) == 10:
        otp = generate_otp()
        try:
            with sqlite3.connect('data.db') as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO otp_verifications (phone_number, otp) VALUES (?, ?)",
                          (phone_number, otp))
                conn.commit()
                print(f"LOG: OTP {otp} stored for {phone_number}")
                update.message.reply_text(f'Your OTP is: {otp}')
        except Exception as e:
            print(f"LOG: Error storing OTP: {str(e)}")
            update.message.reply_text('Error generating OTP. Please try again.')
    else:
        print(f"LOG: Invalid phone number: {phone_number}")
        update.message.reply_text('Please send a valid 10-digit mobile number.')

def main():
    print("LOG: Starting Telegram bot...")
    init_db()
    try:
        updater = Updater("7605058417:AAGg9jgR6KY5MPqfs5mSLRkDy7gL0ft-K9k", use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        max_retries = 5
        retry_delay = 10
        for attempt in range(max_retries):
            try:
                print("LOG: Bot starting polling...")
                updater.start_polling()
                updater.idle()
                break
            except NetworkError as e:
                print(f"LOG: Network error: {e}. Retrying in {retry_delay} seconds... ({attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    print("LOG: Max retries reached. Exiting...")
            except Exception as e:
                print(f"LOG: Bot error: {str(e)}")
                break
            finally:
                updater.stop()
                print("LOG: Bot stopped")
    except Exception as e:
        print(f"LOG: Updater initialization error: {str(e)}")

if __name__ == '__main__':
    main()
