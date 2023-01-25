import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram import Bot

from app.logic.orm import User, Package
from app.utils.room import general_buttons, myoperations_buttons, myoperations_reference, myoperations_keyboard

import logging
import random

logger = logging.getLogger(__name__)


async def start_get_debts(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(myoperations_reference, reply_markup=myoperations_keyboard)


async def package_products(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    inline_keyboard = types.InlineKeyboardMarkup()

    user = User(str(message.from_user.id))
    user.get_user()
    package = Package(user.tg_id, user.current_room, paid=False)
    list_of_products = package.get_products_list()
    emoji = ['🔴','🟠','🟡','🟢','🔵','🟣','⚫️','⚪️','🟤', '🟥', '🟧','🟨','⬛️','🟪','⬜️','🔷','🟦','🔶','🟩']

    if not list_of_products:
        await message.answer(f"Долгов нет, можно идти за покупками! 🔆")
        await message.answer(f"🛒")
    else:
        for id, debt, cost, date, paid, room, user_name, payer_name, product_name in list_of_products:

            current_emoji = random.choice(emoji)
            if product_name is None:
                product_name='Empty'

            inl_but = types.InlineKeyboardButton(text='Отметить', callback_data=f"check_{id}_{current_emoji}")
            inline_keyboard.add(inl_but)

            await message.answer(f"Покупка {current_emoji} "
                             f"в комнате {room}\nОписание: {product_name}\nДата покупки: {date}\nВы должны: "
                             f"{round(debt, 2)} руб\nОбщая "
                             f"стоимость: "
                             f"{cost} руб\nПлатил: {payer_name}",
                                 reply_markup=inline_keyboard)

            inline_keyboard['inline_keyboard'][-1].pop()


async def check_product(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete_reply_markup()
    transaction_id = call.data.split("_")[1]
    emoji = call.data.split("_")[2]
    answer_succses = call.message.text + f"\nВы успешно отметили покупку {emoji} ✔️"
    answer_repeat = call.message.text + f"\nВы уже отметили эту покупку ✔️"

    product = Package(transaction_id=transaction_id)
    product_params = product.get_product()
    paid = product_params[6]
    if paid:
        await call.message.edit_text(answer_repeat)
    else:
        product.check_debt()
        await call.message.edit_text(answer_succses)

        await asyncio.sleep(2)
        try:
            await send_accept_message(call.message.bot, transaction_id)
        except Exception as e:
            logger.error("Ошибка при отправлении сообщения на подтверждение отмеченной покупки", exc_info=e)


async def send_accept_message(bot: Bot, transaction_id):
    product = Package(transaction_id=transaction_id)
    product.check_debt()
    product_params = product.get_product()

    date = product_params[0]
    description = product_params[1]
    debt = product_params[2]
    payer_tg_id = product_params[3]
    debtor_name = product_params[4]

    if product_params[1] is None:
        description = 'Empty'

    inline_keyboard = types.InlineKeyboardMarkup()
    inl_but = types.InlineKeyboardButton(text='Подтвердить', callback_data=f"accept_{transaction_id}")
    inline_keyboard.add(inl_but)

    await bot.send_message(chat_id=payer_tg_id, text=f"{debtor_name} отправил вам платеж в размере {round(debt,2)} за покупку "
                                        f"{description} сделанную {date}.\nПодтвердить получение платежа?", reply_markup=inline_keyboard)


async def payer_accepted_payment(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete_reply_markup()
    transaction_id = call.data.split("_")[1]

    product = Package(transaction_id=transaction_id)
    product.accept_payment()

    answer = call.message.text.replace('Подтвердить получение платежа?','Вы подтвердили полученный платеж ☑️')

    await call.message.edit_text(answer)

    await asyncio.sleep(1)

    product_params = product.get_product()

    date = product_params[0]
    description = product_params[1]
    debt = product_params[2]
    debtor_tg_id = product_params[5]

    await call.message.bot.send_message(chat_id=debtor_tg_id, text=f"Оплата покупки {description} от {date} в размере"
                                                                   f" {round(debt,2)} "
                                                                   f"подтверждена! 🎉")


def register_handlers_get_debts(dp: Dispatcher):
    dp.register_message_handler(start_get_debts, Text(equals=general_buttons[0], ignore_case=False), state='*')
    dp.register_message_handler(package_products, Text(equals=myoperations_buttons[0], ignore_case=False), state='*')
    dp.register_callback_query_handler(check_product, Text(startswith='check_'), state="*")
    dp.register_callback_query_handler(payer_accepted_payment, Text(startswith='accept_'),state="*")
