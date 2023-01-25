from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from app.logic.orm import User
from app.utils.room import cancel_buttons, first_in_keyboard, general_keyboard

keyboard = first_in_keyboard.add('Вернуться')


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user = User(str(message.from_user.id))

    if user.get_user():
        mes = f"""
        Ты в Прихожей🔑\n\nСтоишь у комнаты\n«{user.current_room}»🚪\n
Ты можешь войти или создать комнату.
                """
    else:
        mes = f"""
Привет, вы попали в Прихожею! 🔑\n
Для того чтобы войти в комнату, вам будет предложено ввести уникальное название комнаты и пароль.\n
Также вы можете создать свою комнату 🚪\n
        """
    await message.answer(mes, reply_markup=keyboard)


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    user = User(str(message.from_user.id))
    if user.get_user():
        await message.answer(f"Вы в главном меню⚒\nКомната «{user.current_room}»🚪", reply_markup=general_keyboard)
    else:
        await message.answer("[Отменяю]", reply_markup=cancel_buttons)


def register_handlers_start_bot(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel, Text(equals=cancel_buttons, ignore_case=True), state="*")
