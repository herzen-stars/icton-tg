import pymongo
import telebot
import user_tags
from current_lesson import *
import teachers_parser
from faq_feature import *

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
    f"mongodb+srv://icton_bot:{credentials['mongodb_password']}@cluster0.yieez.mongodb.net/Icton?retryWrites=true&w"
    f"=majority")
db = cluster['Icton']


class NoAdminRights(BaseException):
    msg = "Ошибка: у пользователя нет прав администратора"


# проверить пользователя на права администратора
def check_user_for_admin_right(user, chat):
    flag = False
    for _user in bot.get_chat_administrators(chat.id):
        if user.id == _user.user.id:
            flag = True
    if not flag:
        raise NoAdminRights


# получить текст сообщения из БД по его ID
def msg(db_msg_id, mongo_db=db):
    messages = mongo_db['messages']
    return messages.find_one({'_id': db_msg_id})['msg']


# прикрепить тэг к пользователю
@bot.message_handler(commands=['add_tags'])
def handle_tag_adding_start(tg_message):
    try:
        check_user_for_admin_right(tg_message.from_user, tg_message.chat)

        response_msg = bot.send_message(tg_message.chat.id, "Укажи студента и тэг")
        bot.register_next_step_handler(response_msg, handle_tag_adding_end, response_msg)
    except NoAdminRights as e:
        bot.send_message(tg_message.chat.id, e.msg)


def handle_tag_adding_end(tg_message, info_msg):
    try:
        username, tags = tg_message.text.split(' ', 1)

        if username == "" or tags == "":
            bot.send_message(tg_message.chat.id, "Упс, недостаточно аргументов")
            return

        username = username[1:]
        tags = tags.split(" ")

        user_tags.add_tags_to_user(username, tags, db)

        bot.send_message(tg_message.chat.id,
                         "Тэги " + " ".join(tags) + " успешно прикреплены к пользователю " + username)
    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)
    except Exception:
        bot.send_message(tg_message.chat.id, "Упс, что-то пошло не так")


# уведомить пользователей с хотя бы одним из указанных тэгов
@bot.message_handler(commands=['tag'])
def handle_tag__start(tg_message):
    handle_tag_middle(tg_message, "")


# уведомить пользователей со всеми указанными тэгов
@bot.message_handler(commands=['tag_all'])
def handle_tag_all_start(tg_message):
    handle_tag_middle(tg_message, "all")


def handle_tag_middle(tg_message, _type):
    try:
        check_user_for_admin_right(tg_message.from_user, tg_message.chat)
        if tg_message.reply_to_message is None:
            bot.send_message(tg_message.chat.id,
                             "Ответь этой командой на сообщение, под которым будут отмечены пользователи")
            return

        # удалить сообщение с командой, оно нам больше не нужно
        bot.delete_message(tg_message.chat.id, tg_message.message_id)

        # отправить подсказку и перенаправить ответ
        response_msg = bot.send_message(tg_message.chat.id, "Укажи тэги")
        bot.register_next_step_handler(response_msg, handle_tag_end, tg_message.reply_to_message, response_msg, _type)

    except NoAdminRights as e:
        bot.send_message(tg_message.chat.id, e.msg)


# главный обработчик уведомления пользователей по тэгам
def handle_tag_end(tg_message, original_message, info_message, _type):
    try:
        # удалить сообщение "Укажи тэги"
        bot.delete_message(info_message.chat.id, info_message.message_id)

        # распарсить тэги
        tags = tg_message.text.split(" ")

        # получить пользователей по тэгам
        users = user_tags.get_users_with_tags(tags, _type, tg_message.chat, bot, db)

        # отформатировать строку с упоминаниями
        users_msg = ""
        for user in users:
            user_msg = "@"
            user_msg += str(user.username) + " "
            users_msg += user_msg

        # имя отправителя
        sender_message = original_message.from_user.username + " говорит:\n\n"

        # итоговое сообщение
        final_msg = sender_message + original_message.text + "\n\n" + users_msg

        # удалить изначальное сообщение
        bot.delete_message(original_message.chat.id, original_message.message_id)

        # отправить наше отформатированное сообщение с отметками в конце
        bot.send_message(tg_message.chat.id, final_msg)

        # удалить сообщение с указанными тэгами
        bot.delete_message(tg_message.chat.id, tg_message.message_id)

    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# создать тэг в бд
@bot.message_handler(commands=['create_tag'])
def handle_tag_add_start(tg_message):
    try:
        check_user_for_admin_right(tg_message.from_user, tg_message.chat)

        response_msg = bot.send_message(tg_message.chat.id, "Укажи название и описание тэга")
        bot.register_next_step_handler(response_msg, handle_tag_add_end)

    except NoAdminRights as e:
        bot.send_message(tg_message.chat.id, e.msg)


def handle_tag_add_end(tg_message):
    try:
        index = tg_message.text.find(" ")
        if index != -1:
            tag_name, tag_description = tg_message.text[:index], tg_message.text[index:]
        else:
            tag_name = tg_message.text
            tag_description = ""

        user_tags.add_tag(tag_name, tag_description, db)

        bot.send_message(tg_message.chat.id, "Тэг " + tag_name + " успешно создан")

    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# получить названия и описания всех тэгов
@bot.message_handler(commands=['tags'])
def handle_get_all_tags(tg_message):
    try:
        tags = user_tags.get_all_tags(db)

        message = ""

        for i, tag in enumerate(tags, 1):
            message += '{}. [{}] - {}\n'.format(i, tag['tag_name'], tag['tag_description'])

        bot.send_message(tg_message.chat.id, message)

    except user_tags.UserTagsException as e:
        bot.send_message(tg_message.chat.id, e.msg)


# регистрация
@bot.message_handler(commands=['register_me'])
def handle(tg_message):
    bot.delete_message(tg_message.chat.id, tg_message.message_id)

    try:
        user_tags.register_user(tg_message.from_user, db)
        bot.send_message(tg_message.chat.id,
                         "Пользователь " + tg_message.from_user.first_name + " успешно зарегестрирован.")
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


# вывести расписание на сегодня
@bot.message_handler(commands=['today'])
def send_message(message):
    text = schedule_for_today()
    bot.send_message(message.chat.id, text, parse_mode="html")


# вывести FAQ
@bot.message_handler(commands=['faq'])
def send_message(message):
    text = retrieve_faq(db)
    bot.send_message(message.chat.id, text, parse_mode="html")


# добавить пункт в FAQ
@bot.message_handler(commands=['faq_add'])
def send_message(tg_message):
    try:
        check_user_for_admin_right(tg_message.from_user, tg_message.chat)
        text = 'В ответе на это сообщение пришлите текст нового пункта'
        response_msg = bot.send_message(tg_message.chat.id, text, parse_mode="html")

        def _add_to_faq(new_text):
            add_to_faq(db, new_text.text)
            text = 'FAQ обновлен'
            bot.send_message(tg_message.chat.id, text, parse_mode="html")

        bot.register_next_step_handler(response_msg, _add_to_faq)
    except NoAdminRights as e:
        bot.send_message(tg_message.chat.id, e.msg)


# удалить пункт из FAQ
@bot.message_handler(commands=['faq_remove'])
def send_message(tg_message):
    try:
        check_user_for_admin_right(tg_message.from_user, tg_message.chat)
        text = 'В ответе на это сообщение пришлите номер удаляемого пункта'
        response_msg = bot.send_message(tg_message.chat.id, text, parse_mode="html")

        def _remove_from_faq(new_text):

            try:
                remove_from_faq(db, int(new_text.text))
                text = 'FAQ обновлен'
            except ValueError:
                text = 'Ошибка: ожидалось число. FAQ оставлен без изменений.'
            bot.send_message(tg_message.chat.id, text, parse_mode="html")

        bot.register_next_step_handler(response_msg, _remove_from_faq)
    except NoAdminRights as e:
        bot.send_message(tg_message.chat.id, e.msg)


# очистить FAQ
@bot.message_handler(commands=['faq_flush'])
def send_message(tg_message):
    try:
        check_user_for_admin_right(tg_message.from_user, tg_message.chat)
        flush_faq(db)
        text = 'FAQ очищен'
        bot.send_message(tg_message.chat.id, text, parse_mode="html")
    except NoAdminRights as e:
        bot.send_message(tg_message.chat.id, e.msg)


# получить информацию о преподавателях
@bot.message_handler(commands=['teacher'])
def get_teacher_info_prepare(message):
    _msg = bot.send_message(
        message.chat.id, 'Отправьте имя преподавателя.', parse_mode="html"
    )
    bot.register_next_step_handler(_msg, get_teacher_info)


def get_teacher_info(message):
    if message.text.lower() in ['bruh']:
        result = '''Страница 1 из 1

<b>Имя:</b> <code>Bruhский Bruh Bruhович</code>
<b>Телефон: </b><code>22505</code>
<b>E-mail: </b><code>herzen_bruhs@hello.world</code>'''
    else:
        result = teachers_parser.parse_teacher(message.text)
    bot.send_message(message.chat.id, result, parse_mode="html")


# handle new chat members
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(tg_message):
    if tg_message.new_chat_members is not None:
        for newUser in tg_message.new_chat_members:
            try:
                user_tags.register_user(newUser, db)
                bot.send_message(tg_message.chat.id, "Добро пожаловать, " + newUser.first_name + "!")
            except user_tags.UserTagsException as e:
                if e.msg == "Error: user already exists":
                    bot.send_message(tg_message.chat.id, "Добро пожаловать обратно, " + newUser.first_name + "!")
                else:
                    bot.send_message(tg_message.chat.id, e.msg)


# handle chat member left
@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(tg_message):
    if tg_message.left_chat_member is not None:
        bot.send_message(tg_message.chat.id, "Мы будем скучать, " + tg_message.left_chat_member.first_name + "!")


# прислать подсказку с доступными командами
@bot.message_handler(commands=['help'])
def send_message(message):
    _commands = ['<b>Доступные команды</b>\n',
                 '<b>Расписание</b>',
                 '/now - текущая пара',
                 '/next - следующая пара',
                 '/today - расписание на сегодня',
                 '/tomorrow - расписание на завтра',
                 '\n<b>Получение сведений</b>',
                 '/faq - вывести FAQ',
                 '/faq_flush - очистить FAQ - <b><u>адм.</u></b>',
                 '/faq_add - добавить пункт в FAQ - <b><u>адм.</u></b>',
                 '/faq_remove - удалить пункт из FAQ - <b><u>адм.</u></b>',
                 '/teacher - получить информацию о преподавателе',
                 '\n<b>Роли и тэги</b>',
                 '/register_me - регистрация в чате',
                 '/create_tag - создать новый тэг - <b><u>адм.</u></b>',
                 '/tags - получить список тэгов',
                 '/add_tags - прикрепить к пользователю тэг - <b><u>адм.</u></b>',
                 '/tag - уведомить всех пользователей с указанными тэгами - <b><u>адм.</u></b>',
                 '/tag_all - уведомить только пользователей, имеющих все указанные теги - <b><u>адм.</u></b>',
                 '\n<b>Прочее</b>',
                 '/help - помощь'
                 ]
    text = '\n'.join(_commands)
    bot.send_message(message.chat.id, text, parse_mode="html")


# запустить работу бота в бесконечном цикле
if __name__ == '__main__':
    bot.infinity_polling()
