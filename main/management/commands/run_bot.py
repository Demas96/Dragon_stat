import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import autoreload

from main.telegram_bot import bot
from telebot.async_telebot import asyncio_filters


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Запускаем бота"

    def handle(self, *args, **options):
        try:
            bot.add_custom_filter(asyncio_filters.StateFilter(bot))
            autoreload.run_with_reloader(asyncio.run(bot.infinity_polling(logger_level=settings.LOG_LEVEL)))
        except Exception as exc:
            logger.error(f'Ошибка {exc}')

