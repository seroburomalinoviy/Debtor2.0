from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from app.logic.orm import User, Room
from app.utils.room import room_buttons

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

    await message.answer(f"""Введите название комнаты\n🚪 "..." """, reply_markup=keyboard)
    await Registartation.wait_room_name.set()


async def get_room_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if len(message.text) > 30:
        # продолжаем ожидать ввода пароля, не переводим в автомат в след сост
        keyboard.add('Отмена')
        await message.answer("[Некорректный ввод]", reply_markup=keyboard)
    else:
        room = Room(name=message.text)
        if room.exist_room():
            await state.update_data(room=room)
            await Registartation.next() # переводим автомат в следующее состояние - ожидание ввода пароля
            keyboard.add('Отмена')
            await message.answer("Введите пароль\n🚪 ...", reply_markup=keyboard)
        else:
            keyboard.add("/create_room")
            keyboard.add("/login")
            keyboard.add('Отмена')
            await message.answer("Такой комнаты не существует, попробуйте создать комнату или повторить попытку",
                                 reply_markup=keyboard)
            await state.finish()


# в диспетчере задано, что когда автомат в состоянии ожидания логина, то всегда вызывается функция get_room_pass
async def get_room_pass(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

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
            keyboard.add(*room_buttons)
            await message.answer(f"🔆 \n Вы вошли в комнату \n🚪 {room.name}", reply_markup=keyboard)
            await state.finish()
        else:
            keyboard.add('Отмена')
            await message.answer(f"Вы не зарегистрированы. Введите ваше имя", reply_markup=keyboard)
            await Registartation.wait_user_name.set()
    else:
        keyboard.add('Отмена')
        await message.answer(f"💢 \n Неверный пароль. \n Попробуйте ввести пароль еще раз",
                             reply_markup=keyboard)
        await Registartation.wait_room_password.set()


async def get_user_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    room_data = await state.get_data()
    room = room_data['room']

    if len(message.text) > 30:
        keyboard.add('Отмена')
        await message.answer(f"💢 \n Некорректны ввод. \n Попробуйте ввести пароль еще раз",
                             reply_markup=keyboard)
        await Registartation.wait_user_name.set()
    else:
        user = User(str(message.from_user.id))
        user.name = message.text
        user.current_room = room.name
        user.create()
        room.new_member = user.tg_id
        room.add_user()
        logger.info(f"User {user.tg_id} created")
        logger.info(f"User {user.tg_id} added in room {room.name}")

        keyboard.add(*room_buttons)
        await message.answer(f"Вы успешно зарегистрированы, {user.name}!")
        await message.answer(f"🔆 \n Вы вошли в комнату \n🚪 {room.name}", reply_markup=keyboard)
        await state.finish()


def register_handler_login_room(dp: Dispatcher):
    dp.register_message_handler(login_start, Text(equals='Войти в комнату'), state="*")
    dp.register_message_handler(get_user_name, state=Registartation.wait_user_name)
    dp.register_message_handler(get_room_name,  state=Registartation.wait_room_name)
    dp.register_message_handler(get_room_pass, state=Registartation.wait_room_password)

