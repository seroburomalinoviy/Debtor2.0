from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from app.logic.orm import User
from app.utils.room import room_buttons


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    user = User(str(message.from_user.id))
    if user.get_user():
        buttons = room_buttons
        keyboard.add(*buttons)
    else:
        keyboard = types.ReplyKeyboardRemove()
    await message.answer(
        f"""
Привет, ты попал в Прихожею! \n
Для того чтобы авторизоваться, тебе будет предложено ввести номер комнаты и уникальный пароль для входа.\n
Также ты можешь создать свою комнату.\n
        [Войти в комнату] - /login \n 
        [Создать комнату] - /create_room \n
Для отмены какого либо действия напиши 'отмена' или (/cancel).
        """,
        reply_markup=keyboard
    )


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("[Отменяю]", reply_markup=types.ReplyKeyboardRemove())


def register_handlers_start_bot(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel, Text(equals="отмена", ignore_case=True), state="*")
