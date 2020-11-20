import pymongo
import telebot
import sys
import user_tags
from current_lesson import current_lesson, next_lesson, schedule_for_tomorrow
import teachers_parser

# получить ключи доступа из окружения
if len(sys.argv) < 3:
    print("""Передайте ключи доступа в аргументы команды:
    python3 main.py пароль_от_mongodb токен_доступа_telegram_api\n""")
    sys.exit()
else:
    credentials = {
        "mongodb_password": sys.argv[1],
        "tg_token": sys.argv[2]
    }

# инициализировать бота
bot = telebot.TeleBot(credentials["tg_token"])

# подключить базу данных
cluster = pymongo.MongoClient(
    f"mongodb+srv://icton_bot:{credentials['mongodb_password']}@cluster0.yieez.mongodb.net/Icton?retryWrites=true&w=majority")
db = cluster['Icton']


# получить текст сообщения из БД по его ID
def msg(db_msg_id, mongo_db=db):
    messages = mongo_db['messages']
    return messages.find_one({'_id': db_msg_id})['msg']


# зарегистрировать пользователя в бд (и другая инициализация)
@bot.message_handler(commands=['start'])
def handle_user_reg(tg_message):
    try:
        user_tags.register_user(tg_message.from_user, db)
    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# прикрепить тэг к пользователю
@bot.message_handler(commands=['add_tag_to_user'])
def handle_tag_adding_start(tg_message):
    response_msg = bot.send_message(tg_message.chat.id, "Укажи студента и тэг")
    bot.register_next_step_handler(response_msg, handle_tag_adding_end)


def handle_tag_adding_end(tg_message):
    try:
        message = tg_message.text
        args = message.split(" ")

        if len(args) < 2:
            bot.send_message(tg_message.chat.id, "Упс, недостаточно аргументов")
            return

        username = args[0]
        username = username[1:]
        tag_name = args[1]

        user_tags.add_tag_to_user(username, tag_name, db)
    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# уведомить пользователей с указанным тэгом
@bot.message_handler(commands=['notify_users_with_tag'])
def handle_users_with_tag_start(tg_message):
    response_msg = bot.send_message(tg_message.chat.id, "Укажи тэг")
    bot.register_next_step_handler(response_msg, handle_users_with_tag_end)


def handle_users_with_tag_end(tg_message):
    try:
        tag = tg_message.text

        users = user_tags.get_users_with_tag(tag, tg_message.chat, bot, db)

        users_msg = ""

        for user in users:
            user_msg = "@"
            user_msg += str(user.username) + " "
            users_msg += user_msg
        bot.send_message(tg_message.chat.id, users_msg)

    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# создать тэг в бд
@bot.message_handler(commands=['create_tag'])
def handle_tag_add_start(tg_message):
    response_msg = bot.send_message(tg_message.chat.id, "Укажи название и описание тэга")
    bot.register_next_step_handler(response_msg, handle_tag_add_end)


def handle_tag_add_end(tg_message):
    try:
        index = tg_message.text.find(" ")

        tag_name, tag_description = tg_message.text[:index], tg_message.text[index:]

        user_tags.add_tag(tag_name, tag_description, db)

    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# получить названия и описания всех тэгов
@bot.message_handler(commands=['get_all_tags'])
def handle_get_all_tags(tg_message):
    try:
        tags = user_tags.get_all_tags(db)

        message = ""

        it = 1

        for tag in tags:
            message += str(it) + ". [" + tag['tag_name'] + "] - " + tag['tag_description'] + "\n"
            it += 1

        bot.send_message(tg_message.chat.id, message)

    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# прислать текущие уроки
@bot.message_handler(commands=['now'])
def send_message(message):
    text = current_lesson()
    bot.send_message(message.chat.id, text, parse_mode="html")


# прислать следующие уроки
@bot.message_handler(commands=['next'])
def send_message(message):
    text = next_lesson()
    bot.send_message(message.chat.id, text, parse_mode="html")


# вывести расписание на завтра
@bot.message_handler(commands=['tomorrow'])
def send_message(message):
    text = schedule_for_tomorrow()
    bot.send_message(message.chat.id, text, parse_mode="html")


# получить информацию о преподавателях
@bot.message_handler(commands=['get_teacher_info'])
def get_teacher_info_prepare(message):
    msg = bot.send_message(
        message.chat.id, 'Отправьте имя преподавателя.', parse_mode="html"
        )
    bot.register_next_step_handler(msg, get_teacher_info)


def get_teacher_info(message):
    if message.text.lower() in ['bruh']:
        result = '''Страница 1 из 1

<b>Имя:</b> <code>Bruhский Bruh Bruhович</code>
<b>Телефон: </b><code>22505</code>
<b>E-mail: </b><code>herzen_bruhs@hello.world</code>'''
    else:
        result = teachers_parser.parse_teacher(message.text)
    bot.send_message(message.chat.id, result, parse_mode="html")


# прислать подсказку с доступными командами
@bot.message_handler(commands=['help'])
def send_message(message):
    _commands = ['<b>Доступные команды</b>\n',
                 '/now - текущие занятия',
                 '/next - следующие занятия',
                 '/tomorrow - расписание на завтра',
                 '/help - помощь',
                 '/create_tag - создать новый тэг',
                 '/get_all_tags - получить список тэгов',
                 '/add_tag_to_user - прикрепить к пользователю тэг',
                 '/notify_users_with_tag - уведомить пользователей с указанным тэгом',
                 '/get_teacher_info - получить информацию о преподавателе'
                 ]
    text = '\n'.join(_commands)
    bot.send_message(message.chat.id, text, parse_mode="html")


# запустить работу бота в бесконечном цикле
if __name__ == '__main__':
    bot.infinity_polling()
