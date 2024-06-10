# import telebot
# from pybit.unified_trading import HTTP
# from telebot import types
#
# api_key = 'a3ShoNA9rAEuNWmVDI'
# api_secret = 'O8pwP6L7kpjsoTkbvnSruRDkNcalfDVmfaDR'
# BOT_TOKEN = '7430233466:AAEzooJEC_jFbLrxxaOxr5Omx2XALd8LC_Q'
#
# bot = telebot.TeleBot(BOT_TOKEN)
# session = HTTP(
#     testnet=False,
#     api_key=api_key,
#     api_secret=api_secret,
# )
#
#
# @bot.message_handler(commands=['start'])
# def start(message):
#
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     btn1 = types.KeyboardButton('Узнать баланс')
#     markup.add(btn1)
#     bot.send_message(message.from_user.id, "👋 Привет! Я твой бот-помошник!", reply_markup=markup)
#
#
# @bot.message_handler(content_types=['text'])
# def get_text_messages(message):
#     if message.text == 'Узнать баланс':
#         r = session.get_wallet_balance(
#                 accountType='UNIFIED',
#                 coin='USDT',
#             )
#         pnl = round(float(r['result']['list'][0]['coin'][0]['cumRealisedPnl']), 2)
#         totalEquity = round(float(r['result']['list'][0]['totalEquity']), 2)
#         text = f'Баланс: {totalEquity} USDT, Суммарный P&L: {pnl}, Суммарный P&L%: {round(pnl / totalEquity * 100, 2)}%'
#         bot.send_message(message.from_user.id, text, parse_mode='Markdown')
import telebot
from asgiref.sync import sync_to_async

from django.conf import settings
from django.contrib.auth.models import User

from pybit.unified_trading import HTTP

from telebot.async_telebot import AsyncTeleBot
from telebot.async_telebot import types
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
import json

from main.models import Account
from main.models import APIkeys

bot = AsyncTeleBot(settings.BOT_TOKEN, state_storage=StateMemoryStorage())

telebot.logger.setLevel(settings.LOG_LEVEL)


class RegisterStates(StatesGroup):
    api_key = State()
    api_secret = State()
    done = State()


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    # markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    msg = 'Привет, я твой Бот помощник для Bybit. Давай зарегистрируемся.'
    btn1 = types.KeyboardButton('Зарегистрироваться')
    # markup.add(btn1)
    await bot.send_message(message.from_user.id, msg)


@sync_to_async()
def get_user(message):
    user = User.objects.get_or_create(id=message.from_user.id, username=message.from_user.username)
    return user[0]


@sync_to_async()
def get_account(user):
    return Account.objects.get_or_create(user=user)


@sync_to_async()
def create_api_keys(message, key):
    if key == 'api_key':
        return APIkeys.objects.get_or_create(user_id=message.from_user.id, api_key=message.text)
    elif key == 'api_secret':
        return APIkeys.objects.update(user_id=message.from_user.id, api_secret=message.text)


@sync_to_async()
def get_api_keys(id):
    return APIkeys.objects.get(user_id=id)


@bot.message_handler(commands=['reg'])
async def get_text_messages(message):
    # if message.text == 'Зарегистрироваться':
    user = await get_user(message)
    account = await get_account(user)
    msg = 'Введите api_key:'
    await bot.send_message(message.from_user.id, msg)
    await bot.set_state(message.from_user.id, RegisterStates.api_key)


# @bot.message_handler(state='*')
# async def check_reg(message):
#     print(await get_api_keys(message.from_user.id))
#     if await get_api_keys(message.from_user.id):
#         await bot.set_state(message.from_user.id, RegisterStates.done)
#         print(await bot.get_state(message.from_user.id))


@bot.message_handler(state=RegisterStates.api_key)
async def api_key_step(message):
    api_keys = await create_api_keys(message, 'api_key')
    msg = 'Введите api_secret:'
    await bot.send_message(message.from_user.id, msg)
    await bot.set_state(message.from_user.id, RegisterStates.api_secret)


@bot.message_handler(state=RegisterStates.api_secret)
async def api_secret_step(message):
    await create_api_keys(message, 'api_secret')
    msg = 'Всё готово'
    await bot.send_message(message.from_user.id, msg)
    await bot.set_state(message.from_user.id, RegisterStates.done)


@bot.message_handler(commands=['check_balance'])
async def check_balance(message):
    user_keys = await get_api_keys(message.from_user.id)
    session = HTTP(
        testnet=False,
        api_key=user_keys.api_key,
        api_secret=user_keys.api_secret,
    )
    r = session.get_wallet_balance(
        accountType='UNIFIED',
        coin='USDT',
    )
    pnl = round(float(r['result']['list'][0]['coin'][0]['cumRealisedPnl']), 2)
    totalEquity = round(float(r['result']['list'][0]['totalEquity']), 2)
    msg = f'Баланс: {totalEquity} USDT, Суммарный P&L: {pnl}, Суммарный P&L%: {round(pnl / totalEquity * 100, 2)}%'
    await bot.send_message(message.from_user.id, msg)


@bot.message_handler(commands=['get_ordrers'])
async def get_orders(message):
    user_keys = await get_api_keys(message.from_user.id)
    session = HTTP(
        testnet=False,
        api_key=user_keys.api_key,
        api_secret=user_keys.api_secret,
    )
    r = session.get_order_history(
        category="linear",
        limit=1,
    )

    msg = json.dumps(r)
    await bot.send_message(message.from_user.id, msg)

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
# @bot.message_handler(func=lambda message: True)
# async def echo_message(message):
#     await bot.reply_to(message, f'{message.from_user.username} {message.from_user.id}')
