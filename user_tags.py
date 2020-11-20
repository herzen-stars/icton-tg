class UserTagsException(BaseException):
    msg = "Error: "

    def __init__(self, _msg=""):
        self.msg += _msg


def register_user(user, db):
    print("@" + __name__ + ": registering user " + str(user.id))
    users = db["users"]
    db_user = users.find_one({'tg_user_id': user.id})
    if db_user is not None:
        raise UserTagsException("user already exists")
    users.insert_one({
        'tg_user_id': user.id,
        'tg_user_name': user.username,
        'tg_user_first_name': user.first_name,
        'tg_user_last_name': user.last_name,
        'tags': []
    })


def add_tag_to_user(username, tag, db):
    print("@" + __name__ + ": adding tag " + tag + " to user " + username)
    users = db["users"]
    db_user = users.find_one({'tg_user_name': username})

    if db_user is None:
        raise UserTagsException("user with given username is not found")

    db_user = users.find_one({'tg_user_name': username})
    db_user_tags = db_user['tags']
    if tag in db_user_tags:
        raise UserTagsException("user already has this tag")
    db_user_tags.append(tag)
    users.find_one_and_update({'tg_user_name': username}, {'$set': {'tags': db_user['tags']}})


def get_users_with_tag(tag, chat, bot, db):
    users = db["users"]
    db_users = users.find({'tags': tag})

    tg_users = list()

    for user in db_users:
        tg_users.append(bot.get_chat_member(chat.id, user['tg_user_id']).user)

    if len(tg_users) == 0:
        raise UserTagsException("no users with this tag found")

    return tg_users
