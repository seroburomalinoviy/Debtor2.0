import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.utils.config_reader import load_config
from app.handlers.start_bot import register_handlers_start_bot
from app.handlers.login_room import register_handler_login_room
from app.handlers.new_room import register_handler_create_room
from app.handlers.add_product import register_handlers_add_product
from app.handlers.get_debts import register_handlers_get_debts


# Настройка логирования
logger = logging.getLogger(__name__)


# Регистрация команд, отображаемых в интерфейсе Telegram
# async def set_commands(bot: Bot):
#     commands = [
#         BotCommand(command="/start", description="Создай комнату или авторизуйся"),
#         BotCommand(command="/rooms", description="Переключись между своими комнатами"),
#         BotCommand(command="/cancel", description="Отменить текущее действие")
#     ]
#     await bot.set_my_commands(commands)


async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting bot")

    # Парсинг конфига
    config = load_config('config/bot.ini')

    # Создание бота, диспетчера и хранилища состояний
    bot = Bot(token=config.tg_bot.token)

    # Включить на продакшине Redis
    # storage = RedisStorage2('localhost', 6379, db=0)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Регистрация хендлеров
    register_handlers_start_bot(dp)
    register_handler_login_room(dp)
    register_handler_create_room(dp)
    register_handlers_add_product(dp)
    register_handlers_get_debts(dp)

    print(config.tg_bot.admin_ids)

    # Установка команд бота
    # await set_commands(bot)

    # Запуск поллинга
    await dp.skip_updates()
    await dp.start_polling()

    # Закрытие хранилища
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())