from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from app.logic.orm import User
from app.utils.room import general_buttons, cancel_buttons, first_in_keyboard


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user = User(str(message.from_user.id))

    if user.get_user():
        first_in_keyboard.add('Вернуться')
        mes = f"""
        Ты в Прихожей🔑\n\nСтоишь у комнаты\n«{user.current_room}»🚪\n
[Выбери действие]
                """
    else:
        mes = f"""
Привет, вы попали в Прихожею! 🔑\n
Для того чтобы войти в комнату, вам будет предложено ввести уникальное название комнаты и пароль.\n
Также вы можете создать свою комнату 🚪\n
        """
    await message.answer(mes, reply_markup=first_in_keyboard)


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    user = User(str(message.from_user.id))
    if user.get_user():
        keyboard.add(general_buttons[0], general_buttons[1])
        keyboard.add(general_buttons[2])
        await message.answer(f"Вы в комнате\n«{user.current_room}»🚪", reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardRemove()
        await message.answer("[Отменяю]", reply_markup=keyboard)


def register_handlers_start_bot(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel, Text(equals=cancel_buttons, ignore_case=True), state="*")
