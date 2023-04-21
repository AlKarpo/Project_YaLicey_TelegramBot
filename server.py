import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import wikipediaapi
from ImageParser import YandexImage
import json
from data import db_session
from data.results import User

parser = YandexImage()

"""Переменные для работы 3 основных функций бота"""

quest = False
place = False
test = False
i = 0
id_check = []
result_check = []

"""Клавиатуры для бота"""

mark = {"0": 'крайне скудные', "1": 'крайне скудные', "2": 'недостаточные', "3": 'недостаточные', "5": 'неплохие',
        "4": 'удовлетворительные', "6": 'неплохие', "7": 'хорошие', "8": 'хорошие', "9": 'отличные', "10": 'отличные'}

with open('questions.json', 'r', encoding='utf-8') as cat_file:
    data = json.load(cat_file)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

"""Клавиатуры для бота"""

markup = ReplyKeyboardMarkup([['❓ Поиск информации', '🌄 Найди фото'],
                              ['📕 Викторина']], resize_keyboard=True, one_time_keyboard=True)

reply_search_back = ReplyKeyboardMarkup([['📎 Сохранить', '🔙 Вернуться назад']], resize_keyboard=True)

reply_photos = ReplyKeyboardMarkup([['💾 Ещё фото', '🔙 Вернуться назад']], resize_keyboard=True)

reply_categori_photos = ReplyKeyboardMarkup([['🎖 Историческая личность', '💂🏿 Место'],
                                             ['📜 Карта', '❌ Без категории']], resize_keyboard=True,
                                            one_time_keyboard=True)

reply_tests = ReplyKeyboardMarkup([['🖊 Перейти к тестам', '📊 Статистика'],
                                   ['🔙 Вернуться назад']], resize_keyboard=True, one_time_keyboard=True)

reply_categories = ReplyKeyboardMarkup([['⚔ Война 1812г.', '⚓ Эпоха Петра I'],
                                        ['🗞 СССР 1960-1980х гг', '🔙 Вернуться назад']], resize_keyboard=True,
                                       one_time_keyboard=True)

reply_answer = ReplyKeyboardMarkup([['1', '2', '3']], resize_keyboard=True,
                                   one_time_keyboard=True)


async def start(update, context):
    """Стартовая функция"""
    await update.message.reply_text(
        "Привет. Это ваш путеводитель в мире истории."
        " Я расскажу о прошлом человечества, только попросите.\n"
        " \n"
        "Для получения информации о работе с ботом воспользуйтесь командой /help")
    await update.message.reply_text(
        "Для продолжения выберите нужную кнопку на клавиатуре:", reply_markup=markup)


async def search_answer(question):
    """Функция делает поиск на Вики по запросу"""
    wiki_wiki = wikipediaapi.Wikipedia('ru')
    page_py = wiki_wiki.page(question)


async def ask_question(update, context):
    """Функция, обрабатывающая главную клавиатуру"""
    global quest, place, test, key
    if update.message.text == "❓ Поиск информации":
        chat_id = update.message.chat_id
        await context.bot.send_message(chat_id, text=f'Введите ваш запрос')
        quest, place, test = True, False, False
    elif update.message.text == "🌄 Найди фото":
        await update.message.reply_text("Что бы вы хотели увидеть?", reply_markup=reply_categori_photos)
        quest, place, test = False, True, False
    elif update.message.text == "📕 Викторина":
        quest, place, test = False, False, True
        await update.message.reply_text("Приветствуем в меню викторины!", reply_markup=reply_tests)


async def comands(update, context):
    """Один из главных обработчиков бота
    Здесь через условного оператора выполняются основные куски кода каждой функии бота
    """
    global page_py, b, list_of_photos
    if quest:
        search = update.message.text
        wiki_wiki = wikipediaapi.Wikipedia('ru')
        page_py = wiki_wiki.page(search)
        if page_py.exists():
            await update.message.reply_text(page_py.title, reply_markup=reply_search_back)
            await update.message.reply_text(page_py.summary, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text=f'Читать подробнее - {page_py.title}', url=page_py.fullurl)]]))
        else:
            await update.message.reply_text('Ваш запрос некорректен или такой страницы не существует.'
                                            ' Попробуйте ввести полное название события/имя личности.'
                                            ' Имена собственные пишите с большой буквы,'
                                            ' а нарицательные - с маленькой',
                                            reply_markup=reply_search_back)
    if place and update.message.text != '💾 Ещё фото':
        search = update.message.text
        list_of_photos = []
        chat_id = update.message.chat_id
        counter = 0
        for item in parser.search(search + key):
            if counter < 10:
                b = item.preview.url
                list_of_photos.append(b)
                counter += 1
            else:
                break
        await context.bot.send_photo(chat_id, list_of_photos[0], reply_markup=reply_photos)

    if test:
        chat_id = update.message.chat_id
        await context.bot.send_message(chat_id, text=f'Выберите тест', reply_markup=reply_categories)

    if update.message.text == '📊 Статистика':
        await find_leader(update, context)


async def printing(update, context):
    """Дополнительная функция для бота-поисковика, сохраняющая текст с википедии в txt файле"""
    if update.message.text == '📎 Сохранить':
        with open(f'{page_py.title}.txt', 'w', encoding='utf-8') as f:
            f.write(page_py.title + '\n')
            f.write(page_py.summary)
            try:
                f = open(f'{page_py.title}.txt')
                f.close()
                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, text=f'Файл успешно сохранён!')
            except FileNotFoundError:
                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, text=f'При сохранении файла возникла ошибка!')
    elif update.message.text == '🔙 Вернуться назад':
        await update.message.reply_text("Для продолжения выберите нужную кнопку на клавиатуре:", reply_markup=markup)


async def act_photos(update, context):
    """Функция, которая запрашивает 10 дополнительных фото по данному запросу и отправляет их по необходимости"""
    global i
    try:
        if update.message.text == '💾 Ещё фото':
            chat_id = update.message.chat_id
            await context.bot.send_photo(chat_id, list_of_photos[i], reply_markup=reply_photos)
            i += 1
        elif update.message.text == '🔙 Вернуться назад':
            await update.message.reply_text("Для продолжения выберите нужную кнопку на клавиатуре:",
                                            reply_markup=markup)
    except IndexError:
        i = 1
        await update.message.reply_text("Фотогорафии кончились", reply_markup=markup)
        await update.message.reply_text("Для продолжения выберите нужную кнопку на клавиатуре:",
                                        reply_markup=markup)


async def choosing(update, context):
    """Вспомогательная функция, которая выбирает категорию поиска для фото"""
    global key
    key = ''
    if update.message.text == '🎖 Историческая личность':
        key = ' Портерт'
    elif update.message.text == '💂🏿 Место':
        key = ' Фото'
    elif update.message.text == '📜 Карта':
        key = ' Карта'
    elif update.message.text == '❌ Без категории':
        key = ''
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id, text=f'Введите ваш запрос')


async def print_answer(update, context, i):
    """Функция для отправки вопроса и вариантов ответы в викторине"""
    if i < 10:
        await update.message.reply_text(f'{data["name"][name_event]["id"][str(i + 1)]["question"]}')
        await update.message.reply_text(f'Варианты ответа:\n'
                                        f'1) {data["name"][name_event]["id"][str(i + 1)]["1"]}\n'
                                        f'2) {data["name"][name_event]["id"][str(i + 1)]["2"]}\n'
                                        f'3) {data["name"][name_event]["id"][str(i + 1)]["3"]}\n',
                                        reply_markup=reply_answer)


async def test_choose(update, context):
    global i
    await print_answer(update, context, i)
    i += 1


async def start_dialog(update, context):
    """Функция-обработчик темы викторины"""
    global answer, key, name_event
    answer = []
    key = update.message.text
    if update.message.text == "⚔ Война 1812г.":
        name_event = "napoleonic_war"
        await test_choose(update, context)
    if update.message.text == "⚓ Эпоха Петра I":
        name_event = "petr"
        await test_choose(update, context)
    if update.message.text == "🗞 СССР 1960-1980х гг":
        name_event = "ussr"
        await test_choose(update, context)
    return 1


async def responser(update, context):
    """Функция, записывающая правильные ответы и в заносящая результаты в БД в конце викторины"""
    global i
    otvet = update.message.text
    if otvet == data["name"][name_event]["id"][str(i)]["answer"]:
        answer.append('Верно')
    await test_choose(update, context)
    if i < 11:
        return i
    else:
        await update.message.reply_text('Тест завершён!')
        db_session.global_init("db/results.db")
        db_sess = db_session.create_session()
        for user in db_sess.query(User).all():
            id_check.append(user.id)
            result_check.append(user.result)
        user_telegram = update.message.from_user
        user = User()
        if len(id_check) > 0:
            user.id = id_check[-1] + 1
            user.result = id_check[-1] + 1
        else:
            user.id = 1
            user.result = 1
        user.name = user_telegram.first_name
        user.test = key
        user.result = (len(answer))
        user.result = (len(answer))
        db_sess.add(user)
        db_sess.commit()
        i = 0
        await update.message.reply_text(
            f'Ваш результат {len(answer)}/10. Ваши познания в этой теме {mark[str(len(answer))]}',
            reply_markup=markup)
        return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Остановка теста")
    return ConversationHandler.END


async def help(update, context):
    await update.message.reply_text("/start - запустить бота, остальное с помощью кнопок :)",
                                    reply_markup=markup)


async def compare(update, context, user, maxi, name):
    """Определение лидера по очкам"""
    if user.result > maxi:
        maxi = user.result
        name = user.name
    return maxi, name


async def find_leader(update, context):
    """Функция записывает лидеров в БД"""
    maxi_nap, maxi_us, maxi_petr = {'name': '', 'points': 0}, {'name': '', 'points': 0}, {'name': '', 'points': 0}
    db_session.global_init("db/results.db")
    db_sess = db_session.create_session()
    for user in db_sess.query(User).all():
        if user.test == '⚔ Война 1812г.':
            maxi_nap['points'], maxi_nap['name'] = await compare(update, context, user, maxi_nap['points'],
                                                                 maxi_nap['name'])
        if user.test == '⚓ Эпоха Петра I':
            maxi_petr['points'], maxi_petr['name'] = await compare(update, context, user, maxi_petr['points'],
                                                                   maxi_petr['name'])
        if user.test == '🗞 СССР 1960-1980х гг':
            maxi_us['points'], maxi_us['name'] = await compare(update, context, user, maxi_us['points'],
                                                               maxi_us['name'])
    await update.message.reply_text(f'🏆 Список лидеров:\n'
                                    f'------------------------\n'
                                    f'⚔ Война 1812г.: {maxi_nap["name"]} - {maxi_nap["points"]} балла\n'
                                    f'⚓ Эпоха Петра I: {maxi_petr["name"]} - {maxi_petr["points"]} балла\n'
                                    f'🗞 СССР 1960-1980х гг: {maxi_us["name"]} - {maxi_us["points"]} балла\n')


def main():
    application = Application.builder().token('6152762952:AAGcTbTTdmnfzeJS4KcVhvQmonqr44BaEcQ').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(
        MessageHandler(filters.Regex("^(❓ Поиск информации|🌄 Найди фото|📕 Викторина)$"),
                       ask_question, block=True))
    application.add_handler(
        MessageHandler(filters.Regex("^(💾 Ещё фото|🔙 Вернуться назад)$"),
                       act_photos, block=True))
    application.add_handler(
        MessageHandler(filters.Regex("^(📎 Сохранить|🔙 Вернуться назад)$"),
                       printing, block=True))
    application.add_handler(
        MessageHandler(filters.Regex("^(🎖 Историческая личность|💂🏿 Место|📜 Карта|❌ Без категории)$"),
                       choosing, block=True))
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^(⚔ Война 1812г.|⚓ Эпоха Петра I|🗞 СССР 1960-1980х гг|🔙 Вернуться назад)$"),
                           start_dialog, block=True)],
        states={
            1: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            2: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            3: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            4: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            5: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            6: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            7: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            8: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            9: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)],
            10: [MessageHandler(filters.Regex("^(1|2|3)$"), responser, block=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT, comands))
    application.run_polling()


if __name__ == '__main__':
    main()
