from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.logic.orm import User, Package
from app.utils.room import room_buttons

import logging
import datetime

logger = logging.getLogger(__name__)


class Registration(StatesGroup):
    wait_cost = State()
    wait_description = State()
    wait_date = State()


async def take_package(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    user = User(str(message.from_user.id))
    user.get_user()
    product = Package(str(message.from_user.id))
    await state.update_data(product=product)
    await state.update_data(cur_user=user)
    await message.answer(f"Мы добавляем покупку в комнату 🚪 {user.current_room}")
    await message.answer(f"Достаю ручку и записываю... \nВведите стоимость покупки:", reply_markup=keyboard)
    await Registration.wait_cost.set()


async def get_cost(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product = data['product']
    user = data['cur_user']
    logger.info(f"user id: {user.tg_id}")
    logger.info(f"product payer: {product.payer}")
    try:
        product.cost = int(message.text)
        await state.update_data(product=product)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(f"Оплатил(а) {user.name}")
        keyboard.add("Продукты")
        keyboard.add("Интернет")
        keyboard.add("Для дома")
        keyboard.add('Отмена')

        await message.answer(f"Напишите название/описание покупки, например,что покупку оплатили Вы \nИли "
                             f"воспользуйтесь кнопками ниже",
                             reply_markup=keyboard)
        await Registration.next()

    except ValueError:
        await message.answer(f"Используйте цифры")


async def get_description(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Сегодня')
    keyboard.add('Отмена')

    data = await state.get_data()
    product = data['product']

    product.description = message.text
    await state.update_data(product=product)

    await message.answer(f"Вбейте дату (в формате: 01012001) \n Или воспользуйтесь кнопками ниже",
                         reply_markup=keyboard)
    await Registration.next()


async def get_date(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    data = await state.get_data()
    product = data['product']
    user = data['cur_user']

    if message.text == 'Сегодня':
        logger.info(f"product: {product.cost}")
        keyboard.add(*room_buttons)
        await message.answer(f"Описание: {product.description}\nСтоимость: {product.cost}р\nДата:"
                             f" {product.date}\nОплатили: Вы\nПокупка будет разделена в комнате 🚪 {user.current_room}")
        await message.answer(f"Записал!", reply_markup=keyboard)
        await state.finish()

    else:
        if datetime.datetime.strptime(message.text, "%d%m%Y") <= datetime.datetime.today():
            product.date = datetime.datetime.strptime(message.text, "%d%m%Y").strftime("%d.%m.%y")
            keyboard.add(*room_buttons)
            await message.answer(f"Описание: {product.description}\nСтоимость: {product.cost}р\nДата:"
                                 f" {product.date}\nОплатили: Вы")
            await message.answer(f"Записал!", reply_markup=keyboard)
            await state.finish()
        else:
            keyboard.add('Отмена')
            await message.answer(f"Назад в будущее?")
            await message.answer(f"Попробуй еще раз", reply_markup=keyboard)
            await Registration.wait_date.set()


def register_handlers_add_product(dp: Dispatcher):
    dp.register_message_handler(take_package, Text(equals="Добавить покупку", ignore_case=False), state="*")
    dp.register_message_handler(get_cost,  state=Registration.wait_cost)
    dp.register_message_handler(get_description, state=Registration.wait_description)
    dp.register_message_handler(get_date,  state=Registration.wait_date)


