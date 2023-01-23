from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from app.logic.orm import User, Room
from app.utils.room import first_in_keyboard, general_keyboard, first_in_buttons, cancel_keyboard

import logging


logger = logging.getLogger(__name__)


# Объявляем состояния Конечного автомата - то есть тут хранятся все шаги/этапы, по
# которым мы ведем пользователя
class Registartation(StatesGroup):
    wait_room_name = State()
    wait_room_password = State()
    wait_user_name = State()


async def login_start(message: types.Message, state: FSMContext):
    # перед логином, сбрасываем все возможные состояния
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    await message.answer(f"""Введите название комнаты \n "..." """, reply_markup=keyboard)
    await Registartation.wait_room_name.set()


async def get_room_name(message: types.Message, state: FSMContext):

    if len(message.text) > 30:
        # продолжаем ожидать ввода пароля, не переводим в автомат в след сост
        await message.answer("Некорректный ввод 💢\nПовторите ввод названия", reply_markup=cancel_keyboard)
    else:
        room = Room(name=message.text)
        if room.exist_room():
            await state.update_data(room=room)
            await Registartation.next() # переводим автомат в следующее состояние - ожидание ввода пароля
            await message.answer("Введите пароль ...",reply_markup=cancel_keyboard)
        else:
            await message.answer("Такой комнаты не существует, попробуйте создать комнату или повторить попытку.",
                                 reply_markup=first_in_keyboard)
            await state.finish()


# в диспетчере задано, что когда автомат в состоянии ожидания логина, то всегда вызывается функция get_room_pass
async def get_room_pass(message: types.Message, state: FSMContext):
    keyboard = general_keyboard

    room_data = await state.get_data()
    room = room_data['room']
    room.password = message.text

    if room.auth():
        user = User(str(message.from_user.id))
        if user.get_user():
            user_list = room.get_userlist()
            if user.tg_id in user_list:
                user.current_room = room.name
                user.update()
            else:
                room.new_member = user.tg_id
                room.add_user()
                logger.info(f"User {user.tg_id} added in room {room.name}")
            await message.answer(f"Вы вошли в комнату 🔑\n«{room.name}»🚪", reply_markup=keyboard)
            await state.finish()
        else:
            await message.answer(f"Вы не зарегистрированы. Введите ваше имя", reply_markup=cancel_keyboard)
            await Registartation.wait_user_name.set()
    else:
        await message.answer(f"Неверный пароль 💢\nПопробуйте ввести пароль еще раз",
                             reply_markup=cancel_keyboard)
        await Registartation.wait_room_password.set()


async def get_user_name(message: types.Message, state: FSMContext):
    keyboard = general_keyboard

    room_data = await state.get_data()
    room = room_data['room']

    if len(message.text) > 30:
        await message.answer(f"Некорректны ввод 💢\nПопробуйте ввести пароль еще раз.",
                             reply_markup=cancel_keyboard)
        await Registartation.wait_user_name.set()
    else:
        user = User(str(message.from_user.id))
        user.name = message.text
        user.current_room = room.name
        user.tg_name = str(message.from_user.username)
        user.create()
        room.new_member = user.tg_id
        room.add_user()

        logger.info(f"User {user.tg_id} created")
        logger.info(f"User {user.tg_id} added in room {room.name}")

        await message.answer(f"{user.name}, вы успешно зарегистрировались и вошли в комнату 🔑\n"
                             f"«{user.current_room}»🚪",
                             reply_markup=keyboard)
        await state.finish()


def register_handler_login_room(dp: Dispatcher):
    dp.register_message_handler(login_start, Text(equals=first_in_buttons[0]), state="*")
    dp.register_message_handler(get_user_name, state=Registartation.wait_user_name)
    dp.register_message_handler(get_room_name,  state=Registartation.wait_room_name)
    dp.register_message_handler(get_room_pass, state=Registartation.wait_room_password)

