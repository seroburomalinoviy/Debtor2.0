import logging

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext # продакшн: redis
from aiogram.dispatcher.filters import Text

from app.logic.orm import User, Room
from app.utils.room import general_buttons, general_keyboard

logger = logging.getLogger(__name__)


async def get_members(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = general_keyboard

    user = User(str(message.from_user.id))
    user.get_user()
    room = Room(name=user.current_room)
    room_participants = room.get_userlist()

    answer_title = f"С вами в комнате «{user.current_room}»🚪 находятся:\n\n"
    answer_content = ""
    answer_if_one = f"В комнате «{user.current_room}»🚪 находитесь  только вы."
    for id, info in room_participants.items():
        if user.tg_id != id:
            answer_content += f"{'@'+info[0].split(' ')[0] if info[0] else '👤 '} ({info[1].split(' ')[0]})\n"

    await message.answer(answer_title+answer_content if answer_content else answer_if_one, reply_markup=keyboard)


def register_handlers_look_around(dp: Dispatcher):
    dp.register_message_handler(get_members, Text(equals=general_buttons[2]))

