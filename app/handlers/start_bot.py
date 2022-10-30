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
        mes = f"""
        Ты в Прихожей. Стоишь у комнаты \n🚪 {user.current_room.split(' ')[0]} \n
                [Войти в другую комнату] - /login \n 
                [Создать комнату] - /create_room \n
        Для отмены какого либо действия напиши 'отмена' или (/cancel).
                """
    else:
        keyboard = types.ReplyKeyboardRemove()
        mes = f"""
Привет, вы попали в Прихожею! \n
Для того чтобы войти в комнату, вам будет предложено ввести уникальное название комнаты и пароль для входа.\n
Также вы можете создать свою комнату.\n
        [Войти в комнату] - /login \n 
        [Создать комнату] - /create_room \n
Для отмены какого либо действия напишите 'отмена' или (/cancel).
        """
    await message.answer(mes,
        reply_markup=keyboard
    )


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    user = User(str(message.from_user.id))
    if user.get_user():
        buttons = room_buttons
        keyboard.add(*buttons)
        await message.answer("[Отменяю]")
        await message.answer(f"Вы в комнате\n🚪 {user.current_room.split(' ')[0]}", reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardRemove()
        await message.answer("[Отменяю]", reply_markup=keyboard)


def register_handlers_start_bot(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel, Text(equals="отмена", ignore_case=True), state="*")
