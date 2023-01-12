from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram import Bot

from app.logic.orm import User, Package

import logging
import random

logger = logging.getLogger(__name__)

class Registration(StatesGroup):
    wait_package_products = State()
    wait_payer_accept = State()
    wait_smart_list = State()


async def start_get_debts(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Покупками')
    keyboard.add('Плательщиками')
    keyboard.add('Назад')

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

    if not list_of_products:
        await message.answer(f"Поздравляю, у вас нет долгов 🔆")
    else:
        for id, debt, cost, date, paid, room, user_name, payer_name, product_name, payment_accept in list_of_products:
            status1 = 'Оплачено' if paid else 'Не отмечено'
            status2 = 'Подтверждено' if payment_accept else 'Не подтверждено'

            current_emoji = random.choice(emoji)
            if product_name is None:
                product_name='Empty'

            inl_but = types.InlineKeyboardButton(text='Отметить', callback_data=f"check_{id}_{current_emoji}")
            inline_keyboard.add(inl_but)

            await message.answer(f"Покупка {current_emoji} "
                             f"в комнате {room}\nОписание: {product_name}\nДата покупки: {date}\nВы должны: "
                             f"{round(debt, 2)} руб\nОбщая "
                             f"стоимость: "
                             f"{cost} руб\nПлатил: {payer_name}\nСтатус: {status1}. {status2}.",
                                 reply_markup=inline_keyboard)

            inline_keyboard['inline_keyboard'][-1].pop()


async def check_product(call: types.CallbackQuery, state: FSMContext):
    # for current user
    await call.message.delete_reply_markup()
    transaction_id = call.data.split("_")[1]
    emoji = call.data.split("_")[2]

    product = Package(transaction_id=transaction_id)
    product.check_debt()
    product_params = product.get_product()

    date = product_params[0]
    description = product_params[1]
    debt = product_params[2]
    payer_tg_id = product_params[3]
    debtor = product_params[4]

    if product_params[1] is None:
        description = 'Empty'

    await call.message.answer(f"Вы успешно отметили покупку {emoji}\n{description} "
                              f"{date}\nСтатус: Оплачен. Не подтвержден.")




    # for payer
    inline_keyboard = types.InlineKeyboardMarkup()
    inl_but = types.InlineKeyboardButton(text='Подтвердить', callback_data=f"accept_{transaction_id}")
    inline_keyboard.add(inl_but)

    await call.message.bot.send_message(chat_id=payer_tg_id,
                                   text=f"{debtor} отправил вам платеж в размере {round(debt,2)} за покупку "
                                        f"{description} сделанную {date}.\nПодтвердить получение платежа?",
                                       reply_markup=inline_keyboard)


async def payer_accepted_payment(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete_reply_markup()
    transaction_id = call.data.split("_")[1]

    product = Package(transaction_id=transaction_id)
    product.accept_payment()

    answer = call.message.text.replace('Подтвердить получение платежа?','Вы подтвердили полученный платеж ☑️')

    await call.message.edit_text(answer)
    await state.finish()


def register_handlers_get_debts(dp: Dispatcher):
    dp.register_message_handler(start_get_debts, Text(equals='Мои долги', ignore_case=False), state='*')
    dp.register_message_handler(package_products, Text(equals='Покупками', ignore_case=False), state='*')
    dp.register_callback_query_handler(check_product, Text(startswith='check_'), state=Registration.wait_package_products)
    dp.register_callback_query_handler(payer_accepted_payment, Text(startswith='accept_'),
                                       state=Registration.wait_package_products)
