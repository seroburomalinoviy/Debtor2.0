from aiogram import types
general_buttons = ['Мои операции⚙️', 'Добавить покупки🛍', 'Осмотреться в комнате👥']
first_in_buttons = ['Войти в комнату🔑', 'Создать комнату🚪']
cancel_buttons = ["отмена", 'Вернуться', 'назад🔙']
myoperations_buttons = ['Покупками🛍', 'Участнику👤','Отметить суммой💰','Назад🔙']
myoperations_reference = """В этом меню ты можешь выбрать, в каком виде ты хочешь получить выписку по долгам📝.\n 
Задолженность  покупками🛍 - отправит тебе список всех неотмеченных покупок с подробностями о каждой покупке, 
ты сможешь отметить покупки по одной. Эта выписка также позволяет зачесть долги.\n
Задолженность участнику👤 - предоставит список всех участников комнаты и долги каждому из них, а также возможность отметить все задолженность одному участнику.\n
Отметить суммой💰 - меню для оплаты долгов на определенную сумму, которую ты вводишь сам\n"""

first_in_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
first_in_keyboard.add(first_in_buttons[0])
first_in_keyboard.add(first_in_buttons[1])

myoperations_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
myoperations_keyboard.add(myoperations_buttons[0], myoperations_buttons[1])
myoperations_keyboard.add(myoperations_buttons[2])
myoperations_keyboard.add(myoperations_buttons[3])

general_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
general_keyboard.add(general_buttons[0], general_buttons[1])
general_keyboard.add(general_buttons[2])

cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')