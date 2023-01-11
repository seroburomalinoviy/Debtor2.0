from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from app.logic.orm import User, Package

import logging
import random

logger = logging.getLogger(__name__)

class Registration(StatesGroup):
    wait_package_products = State()
    wait_smart_list = State()


async def start_get_debts(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Списком покупок')
    keyboard.add('Списком плательщиков')
    keyboard.add('Отмена')

    await message.answer(f"Выберете представление списка долгов", reply_markup=keyboard)

async def package_products(message: types.Message, state: FSMContext):
    await Registration.wait_package_products.set()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    inline_keyboard = types.InlineKeyboardMarkup()

    user = User(str(message.from_user.id))
    user.get_user()
    package = Package(user.tg_id, user.current_room)
    list_of_products = package.get_products_list()
    emoji = ['🔴','🟠','🟡','🟢','🔵','🟣','⚫️','⚪️','🟤']

    for id, debt, cost, date, paid, room, user_name, payer_name in list_of_products:
        if not paid:
            inl_but = types.InlineKeyboardButton(text='Отметить', callback_data=f'check_product_{id}')
            inline_keyboard.add(inl_but)
            await message.answer(f"Покупка {random.choice(emoji)} "
                             f"в комнате {room}\nДата покупки: {date}\nВы должны: "
                             f"{round(debt, 2)} руб\nОбщая "
                             f"стоимость: "
                             f"{cost} руб\nПлатил: {payer_name}\n", reply_markup=inline_keyboard)
            print(inline_keyboard['inline_keyboard'][-1].pop())
            #inline_keyboard['inline_keyboard'][-1].pop()

async def check_product(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    transaction_id = call.data.split("_")[2]
    print(transaction_id)




def register_handlers_get_debts(dp: Dispatcher):
    dp.register_message_handler(start_get_debts, Text(equals='Мои долги', ignore_case=False), state='*')
    dp.register_message_handler(package_products, Text(equals='Списком покупок', ignore_case=False), state='*')
    dp.register_callback_query_handler(check_product, Text(startswith='check_product_'), state=Registration.wait_package_products)
