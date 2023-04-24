import logging
from aiogram import Bot, Dispatcher, executor, types
import sqlite3
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()


# Define your Telegram bot token
API_TOKEN = "1713631989:AAHMS-Rb6JS9itJizXJYVem3iGZ6BleppGU"

# Define the payment token for your payment gateway service
PAYMENTS_PROVIDER_TOKEN = "284685063:TEST:MDI4NWUwNDM2YjA3"

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('donation.db')
cursor = conn.cursor()
# Create a table with the specified fields
conn.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY,
             username TEXT,
             cash REAL,
             UNIQUE(id))''')

# Close the connection
#conn.close()

# Define a state to handle withdrawal requests
class WithdrawalState(StatesGroup):
    amount = State()

def get_balance(user: types.User):
    cursor.execute("SELECT cash FROM users WHERE id=?", (user.id,))
    result = cursor.fetchone()
    if result is not None:
        return result[0]
    else:
        return None


x = None
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global x
    print(message)
    x = message.text[7:]
    if message.text.startswith('/start') and len(message.text)<7:
        await message.reply("Welcome to the Donation Bot! To donate, use / commands. If you want to create your account for donation, use /create")
    else:
        cursor.execute("SELECT id FROM users WHERE id=?", (x,))
        result = cursor.fetchone()
        print(result)
        await message.reply(f"Welcome to the Donation Bot! To donate, use /donate_{x}")
        donation_amount = 1000  # Amount in your currency's minimal unit (e.g., cents for USD)
        donation_label = 'Donation'
        donation_description = 'Donate to support my YouTube channel'
        print(x)


####################################################### DONATE #######################################################################

@dp.message_handler(lambda message: message.text.startswith('/donate_') and str(message.chat.id))
async def donate(message: types.Message):
    donation_amount = 100  # Amount in your currency's minimal unit (e.g., cents for USD)
    donation_label = 'Donation'
    donation_description = 'Donate to support my YouTube channel'

    await bot.send_invoice(
        chat_id=message.chat.id,
        title=donation_label,
        description=donation_description,
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency='USD',  # Replace with your currency code
        photo_url='https://lh3.googleusercontent.com/8YpNHJqmFHapv9u4Cf0uVAs2tBt5Jn7F4DGr9WnUcui39yrKRCNOrmfUeIuOJdtYmwSHnjK7JfFkVHq72FZKj2jvmv2vUnw5deNRGv8NSG8fcX5C3zVNUEFvug2sbuoLTRraDsqr1bsLMP3olZhZggASXY9NVhJGVY2v1DRraL_LRHglDTvI7S3oH_PkKiNqEbjKvyW5m00jz3DCGPtsCM4MDcNn-oCf29ZXrRlUwsHByx3-oAAGKfUKa7Xl15yJOB4vSroDDAyHM3plhBETCAOqs4J-32SxHFZqn-xQYnuyjGPiGcGny4UyCLS2pGAzKhascrPHSvY0zOMJ9STVh7N45SiZ3G-GrQUUsg4IRhHKAG_iJernydJtIdpSECEiHnh0VOM4ZcHZbk_IEJ1Z73CbeZAPu4kDINgQtzf6vqWAUt8KUuQPZh1k6LSvaeiilYc8FS2owFerhfm4SJFV9WOMTVQuaV8pacUxwEIx8G_2Aog16Ft8V6skTgcRkfgW-NMVjsFjNHT9j3GYbZgUSBhWAVh4gT5OuUo30UciJmYnIianX0kGbYF0coCsSSnne9kfSNfxW2iCDDtK9gh-FzECjwE0nkc9LOLms8_X8ywT81xPwNUK7j5mKdw2PYJsuiIEhXpLJ2xz_lfQlK9O9mj2UTqHtGh9e8h84orfJmJ8rs0Iwm3TA_5Yz8Qny_QyntSlMd4_Luif1w5Igmlm-nfzVmvi3_EiR4WPkO_rgQRwx_tJuDRXKAYGAFTDENEPcho-vS0KRBzpEdUqV8472PbSIlN73q6HGsAYNObaHCzBB04F2WBdN74vnhIR9st3QCFCltdT4FxyUUH99lRj1F0S18lkRfDQYBD-nOoJ7agiofD_Eu3tjjH6xutukmkHf_1jUZvURHAWBHmrqLYe3Gm4Q856YguCfELN0YLxJn4TNsqY=w640-h640-s-no?authuser=0',  # Replace with your photo URL
        photo_height=512,  # Optional
        photo_width=512,  # Optional
        photo_size=512,  # Optional
        prices=[types.LabeledPrice(amount=donation_amount, label=donation_label)],
        payload='donation'
    )


@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=['successful_payment'])
async def successful_payment(message: types.Message):
    balance = get_balance(message.from_user)
    user_id = message.from_user.id
    donation_amount = message.successful_payment.total_amount  # Get the donation amount from the payment message
    await message.reply('Thank you for your donation! Your support is much appreciated.')


    cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (donation_amount/100, user_id))
    conn.commit()

###################################################### CREATE ###########################################################################


@dp.message_handler(commands=['create'])
async def save(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    try:
        conn.execute("INSERT INTO users (id, username, cash) VALUES (?, ?, ?)", (user_id, username,  0.00))
        conn.commit()
    except sqlite3.IntegrityError:
        # If the user ID already exists in the table, update the existing row instead
        conn.execute("UPDATE users SET username=? WHERE id=?", (username, user_id))
        conn.commit()
    
    await bot.send_message(user_id, f"This is your own link that subscribers will enter with it and will donate you t.me/automatic_use_bot?start={user_id}")
    await bot.send_message(user_id, "1. Check your balance /balance\n2. Withdraw the cash /withdraw\n")
######################################################## Check the Balance ##############################################################

@dp.message_handler(Command('balance'))
async def balance(message: types.Message):
    # Get the user's account balance
    balance = get_balance(message.from_user)

    if balance is not None:
        # Send a message to the user with their account balance
        message_text = f"Your current balance is {balance:.2f}."
    else:
        # Send a message to the user indicating that they don't have an account
        message_text = "You don't have an account yet. Use /start to create one."

    await message.reply(message_text)

######################################################## WITHDRAW #######################################################################
async def withdraw(user: types.User, amount: float, state: FSMContext):
    cursor.execute("UPDATE users SET cash=cash-? WHERE id=?", (amount, user.id))
    conn.commit()


@dp.message_handler(Command('withdraw'))
async def withdrawal(message: types.Message):
    # Ask the user how much they want to withdraw
    await WithdrawalState.amount.set()
    await message.reply("How much do you want to withdraw?")


@dp.message_handler(state=WithdrawalState.amount)
async def process_withdrawal(message: types.Message, state: FSMContext):
    # Get the withdrawal amount from the user's message
    amount = float(message.text.strip())

    # Check that the user has enough funds in their account
    balance = get_balance(message.from_user)
    if balance is None or amount > balance:
        await message.reply("You don't have enough funds in your account.")
        await state.finish()
        return

    # Withdraw the requested amount from the user's account
    await withdraw(message.from_user, amount, state)

# Close the database connection when finished



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)