import telebot
from pybit.unified_trading import HTTP
from telebot import types

api_key = 'a3ShoNA9rAEuNWmVDI'
api_secret = 'O8pwP6L7kpjsoTkbvnSruRDkNcalfDVmfaDR'
BOT_TOKEN = '7430233466:AAEzooJEC_jFbLrxxaOxr5Omx2XALd8LC_Q'

bot = telebot.TeleBot(BOT_TOKEN)
session = HTTP(
    testnet=False,
    api_key=api_key,
    api_secret=api_secret,
)


@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Узнать баланс')
    markup.add(btn1)
    bot.send_message(message.from_user.id, "👋 Привет! Я твой бот-помошник!", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == 'Узнать баланс':
        r = session.get_wallet_balance(
                accountType='UNIFIED',
                coin='USDT',
            )
        pnl = round(float(r['result']['list'][0]['coin'][0]['cumRealisedPnl']), 2)
        totalEquity = round(float(r['result']['list'][0]['totalEquity']), 2)
        text = f'Баланс: {totalEquity} USDT, Суммарный P&L: {pnl}, Суммарный P&L%: {round(pnl / totalEquity * 100, 2)}%'
        bot.send_message(message.from_user.id, text, parse_mode='Markdown')




