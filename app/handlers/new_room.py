from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.logic.orm import User, Room
from app.utils.room import room_buttons

import logging

logger = logging.getLogger(__name__)


class Registration(StatesGroup):
    wait_room_name = State()
    wait_room_pass = State()
    wait_user_name = State()


async def start_creating(message: types.Message, state: FSMContext):
    await state.finish() # перед логином, сбрасываем все возможные состояния
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    await message.answer(f"Введите название комнаты🚪", reply_markup=keyboard)
    await Registration.wait_room_name.set()


async def get_room_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    if len(message.text) < 30:
        # Создаем комнату
        room = Room(name=message.text)

        if not room.exist_room():
            await state.update_data(room=room) # сохраняем информацию о комнате в виде значения словаря
            await Registration.next()
            await message.answer(f"Создайте пароль для комнаты🚪")
        else:
            await message.answer(f"Это название уже существует, попробуй еще раз")
    else:
        await message.answer(f"Слишком длинное название, попробуй еще раз")


async def get_room_pass(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    keyboard_room = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = room_buttons
    keyboard_room.add(*buttons)
    keyboard_room.add('Отмена')

    # выгружаем данные о комнате
    room_data = await state.get_data()
    room = room_data['room']
    room.password = message.text

    # Запрашиваем пользователя из бд, если его нет, то начинаем регистрацию
    user = User(str(message.from_user.id))
    user_exists = user.get_user()

    if not user_exists:
        del user
        await state.update_data(room=room)
        await Registration.next()
        await message.answer(f"Вы не зарегистрированы. Введите свое имя", reply_markup=keyboard)
    else:
        # пользователь уже зарегистрирован, добавим новую запись в бд с данным пользователем и новой комнатой
        # Имя комнаты уже проверено на уникальность
        room.owner = str(message.from_user.id)
        room.create()  # сохраняем записанные данные в бд
        room.add_user()  # добавим в комнату юзера
        user.current_room = room.name
        user.update() # обновоили текущую комнату пользователя



        logger.info(f"User {user.name} authorized and added in room {user.current_room}")
        await message.answer(f"Вы вошли в комнату 🚪 {user.current_room}!",
                             reply_markup=keyboard_room)
        await state.finish()


async def get_user_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = room_buttons
    keyboard.add(*buttons)
    keyboard.add('Отмена')

    # выгружаем данные о комнате
    room_data = await state.get_data()
    room = room_data['room']
    room.create() # сохраняем записанные данные в бд

    # создаем пользователя и привязываем его к комнате
    user = User(tg_id=str(message.from_user.id), name=message.text, is_owner=True, current_room=room.name)
    user.create()
    logger.info(f"User {user.tg_id} created and added in room {user.current_room}")
    await message.answer(f"Вы успешно зарегистрировались и вошли в комнату 🚪 {room.name}!", reply_markup=keyboard)
    await state.finish()


def register_handler_create_room(dp: Dispatcher):
    dp.register_message_handler(start_creating, commands="create_room", state="*")
    dp.register_message_handler(get_room_name, state=Registration.wait_room_name)
    dp.register_message_handler(get_room_pass, state=Registration.wait_room_pass)
    dp.register_message_handler(get_user_name, state=Registration.wait_user_name)
