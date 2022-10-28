from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.logic.orm import User, Room

import logging

logger = logging.getLogger(__name__)


# Объявляем состояния Конечного автомата - то есть тут хранятся все шаги/этапы, по
# которым мы ведем пользователя
class Registartation(StatesGroup):
    wait_user_name = State()
    wait_room_name = State()
    wait_room_password = State()


async def login_start(message: types.Message, state: FSMContext):
    # перед логином, сбрасываем все возможные состояния
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    user = User(str(message.from_user.id))
    user_exists = user.get_user()
    if not user_exists:
        await message.answer(f"Вы не зарегистрированы. Введите своё имя.", reply_markup=keyboard)
        await Registartation.wait_user_name.set()
    else:
        await message.answer(f"[Введите название комнаты🚪]", reply_markup=keyboard)
        await Registartation.wait_room_name.set()


async def get_user_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    user = User(str(message.from_user.id))
    user.name = message.text
    user.create()

    logger.info(f"User {user.name} created")
    await message.answer(f"Вы успешно зарегистрированы")
    await message.answer(f"[Введите название комнаты🚪]", reply_markup=keyboard)
    await Registartation.wait_room_name.set()


# в диспетчере задано, что когда автомат в состоянии ожидания логина, то всегда вызывается функция get_room_num
async def get_room_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    if len(message.text) < 30:
        room = Room(name=message.text)
        await state.update_data(room=room)
        await Registartation.next() # переводим автомат в следующее состояние - ожидание ввода пароля
        await message.answer("[Введите пароль]", reply_markup=keyboard)
    else:
        # продолжаем ожидать ввода пароля, не переводим в автомат в след сост
        await message.answer("[Некорректный ввод]", reply_markup=keyboard)


# в диспетчере задано, что когда автомат в состоянии ожидания логина, то всегда вызывается функция get_room_pass
async def get_room_pass(message: types.Message, state: FSMContext):
    keyboard_room = types.ReplyKeyboardMarkup(resize_keyboard=True)
    room_buttons = ['Мои долги', 'Добавить покупку', 'Осмотреться в комнате']
    keyboard_room.add(*room_buttons)
    keyboard_room.add('Отмена')

    room_data = await state.get_data()
    room = room_data['room']
    room.password = message.text

    if room.auth():
        user = User(str(message.from_user.id))
        user.get_user()
        user.room_name = room.name
        user.is_owner = False
        user.update()

        await message.answer(f"🔆 \n Вы вошли в комнату 🚪 {room.name}", reply_markup=keyboard_room)
        await state.finish()
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("/login")
        keyboard.add('Отмена')
        await message.answer(f"💢 \n Название или пароль введены неверно. \n Попробуйте еще раз.",
                             reply_markup=keyboard)
        await state.finish()


def register_handler_login_room(dp: Dispatcher):
    dp.register_message_handler(login_start, commands="login", state="*")
    dp.register_message_handler(get_user_name, state=Registartation.wait_user_name)
    dp.register_message_handler(get_room_name,  state=Registartation.wait_room_name)
    dp.register_message_handler(get_room_pass, state=Registartation.wait_room_password)

