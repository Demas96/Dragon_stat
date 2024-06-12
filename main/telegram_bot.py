import telebot
from asgiref.sync import sync_to_async

from django.conf import settings
from django.contrib.auth.models import User

from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError

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


@sync_to_async()
def create_user(message):
    username = message.from_user.username if message.from_user.username else 'None'
    user = User.objects.get_or_create(id=message.from_user.id, username=username)
    return user[0]


@sync_to_async()
def get_account(user):
    return Account.objects.get_or_create(user=user)


@sync_to_async()
def create_api_keys(message, key):
    if key == 'api_key':
        query = APIkeys.objects.get_or_create(user_id=message.from_user.id)
        query[0].api_key = message.text
        query[0].save()
        return query[0]
    elif key == 'api_secret':
        return APIkeys.objects.update(user_id=message.from_user.id, api_secret=message.text)


@sync_to_async()
def get_api_keys(user_id):
    try:
        user_keys = APIkeys.objects.get(user_id=user_id)
    except APIkeys.DoesNotExist:
        user_keys = False
    return user_keys


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    msg = 'Привет, я твой Бот помощник для Bybit.'
    print(await bot.get_state(user_id))
    if await bot.get_state(user_id) is None:
        if await get_api_keys(user_id):
            await bot.set_state(user_id, RegisterStates.done)
    if await bot.get_state(user_id) == str(RegisterStates.done):
        print('Проверить баланс')
        btn = types.KeyboardButton('Проверить баланс')
    else:
        print('Зарегистрироваться')
        btn = types.KeyboardButton('Зарегистрироваться')
    markup.add(btn)
    await bot.send_message(user_id, msg, reply_markup=markup)


def check_registration(func):
    async def wrapper(*args, **kwargs):
        user_id = args[0].from_user.id
        if await bot.get_state(user_id) != str(RegisterStates.done):
            if await get_api_keys(user_id):
                await bot.set_state(user_id, RegisterStates.done)
                f = await func(*args, **kwargs)
                return f
            else:
                f = await send_welcome(*args, **kwargs)
                return f
        else:
            f = await func(*args, **kwargs)
            return f
    return wrapper


@bot.message_handler(state=RegisterStates.api_key)
async def api_key_step(message):
    api_keys = await create_api_keys(message, 'api_key')
    msg = 'Введите api_secret:'
    await bot.send_message(message.from_user.id, msg)
    await bot.set_state(message.from_user.id, RegisterStates.api_secret)


@bot.message_handler(state=RegisterStates.api_secret)
async def api_secret_step(message):
    await create_api_keys(message, 'api_secret')
    await check_balance(message)
    msg = 'Всё готово'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('Проверить баланс')
    markup.add(btn)
    await bot.send_message(message.from_user.id, msg, reply_markup=markup)
    await bot.set_state(message.from_user.id, RegisterStates.done)


@check_registration
async def check_balance(message):
    user_keys = await get_api_keys(message.from_user.id)
    session = HTTP(
        testnet=False,
        api_key=user_keys.api_key,
        api_secret=user_keys.api_secret,
    )
    try:
        r = session.get_wallet_balance(
            accountType='UNIFIED',
            coin='USDT',
        )
        pnl = round(float(r['result']['list'][0]['coin'][0]['cumRealisedPnl']), 2)
        totalEquity = round(float(r['result']['list'][0]['totalEquity']), 2)
        msg = f'Баланс: {totalEquity} USDT\nСуммарный P&L: {pnl} USDT\nСуммарный P&L%: {round(pnl / totalEquity * 100, 2)}%'
    except InvalidRequestError as exc:
        msg = f'{exc}'

    await bot.send_message(message.from_user.id, msg)


@bot.message_handler(commands=['get_ordrers'])
@check_registration
async def get_orders(message):
    await check_registration(message)
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


@bot.message_handler(content_types=['text'])
async def get_text_messages(message):
    if message.text == 'Зарегистрироваться':
        msg = '- Для начала создайте api ключ, для этого перейдите по ссылке ' \
              'https://www.bybit.com/app/user/api-management.\n' \
              '- Нажмите "Создать новый ключ".\n' \
              '- "API ключи, созданные системой".\n' \
              '- Название API ключа выберите любое, например "Statistic bot".\n' \
              '- Разрешения API ключа: Только чтение, Доступ к OpenAPI есть только у IP со специальным разрешением: ' \
              'используйте ip 213.171.28.9\n' \
              '- Ниже выберите Единый торговый аккаунт и нажмите Отправить.\n' \
              '- Дальше отправьте в этот чат созданные ключи.'
        await bot.send_message(message.from_user.id, msg, reply_markup=types.ReplyKeyboardRemove())
        user = await create_user(message)
        account = await get_account(user)
        msg = 'Введите api_key:'
        await bot.send_message(message.from_user.id, msg)
        await bot.set_state(message.from_user.id, RegisterStates.api_key)
    if message.text == 'Проверить баланс':
        await check_balance(message)


