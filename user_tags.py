class UserTagsException(BaseException):
    msg = "Ошибка:\n"

    def __init__(self, _msg=""):
        self.msg += _msg


def register_user(user, db):
    print("@" + __name__ + ": registering user " + str(user.id))
    users = db["users"]
    db_user = users.find_one({'tg_user_id': user.id})
    if db_user is not None:
        raise UserTagsException("Такой пользователь уже существует")
    users.insert_one({
        'tg_user_id': user.id,
        'tg_user_name': user.username,
        'tg_user_first_name': user.first_name,
        'tg_user_last_name': user.last_name,
        'tags': []
    })


def add_tags_to_user(username, _tags, db):
    print("@" + __name__ + ": adding tags to user " + username)
    users = db["users"]
    tags = db["tags"]
    db_user = users.find_one({'tg_user_name': username})

    if db_user is None:
        raise UserTagsException("Я не знаю такого пользователя, возможно он не зарегистрировался, пусть попробует "
                                "написать мне /register_me")

    for tag_name in _tags:
        db_tag = tags.find_one({'tag_name': tag_name})

        if db_tag is None:
            raise UserTagsException("Такого тэга не существует")

        db_user = users.find_one({'tg_user_name': username})
        db_user_tags = db_user['tags']
        if tag_name in db_user_tags:
            raise UserTagsException("К пользователю уже прикреплен данный тэг")
        db_user_tags.append(tag_name)
        users.find_one_and_update({'tg_user_name': username}, {'$set': {'tags': db_user['tags']}})


def remove_tags_from_user(username, _tags, db):
    print("@" + __name__ + ": removing tags from user " + username)
    users_collection = db["users"]

    user = users_collection.find_one({'tg_user_name': username})
    user_tags = user["tags"]

    for tag in _tags:
        user_tags.remove(tag)

    users_collection.find_one_and_update({'tg_user_name': username}, {'$set': {'tags': user_tags}})


def get_users_with_tags(tags, _type, chat, bot, db):
    users = db["users"]

    if _type == "all":
        query = '$all'
    else:
        query = '$in'

    db_users = users.find({'tags': {query: tags}})

    tg_users = list()

    for user in db_users:
        tg_users.append(bot.get_chat_member(chat.id, user['tg_user_id']).user)

    if len(tg_users) == 0:
        raise UserTagsException("Нет пользователей с таким тэгом.")

    return tg_users


def create_tag(tag_name, tag_description, db):
    print("@" + __name__ + ": creating tag " + tag_name)
    tags = db["tags"]
    db_tag = tags.find_one({'tag_name': tag_name})
    if db_tag is not None:
        raise UserTagsException("Такой тэг уже существует.")

    tags.insert_one({
        'tag_name': tag_name,
        'tag_description': tag_description
    })


def destroy_tag(tag_name, db):
    print("@" + __name__ + ": destroying tag " + tag_name)
    users_collection = db["users"]
    tag_collection = db["tags"]

    db_tag = tag_collection.find({'tag_name': tag_name})

    if db_tag is None:
        raise UserTagsException("Такого тэга не существует")

    tag_collection.delete_one({'tag_name': tag_name})

    users_with_tag = users_collection.find({'tags': {'$in': [tag_name]}})

    for user in users_with_tag:
        user_tags = user["tags"]
        user_tags.remove(tag_name)
        users_collection.find_one_and_update({'tg_user_name': user['tg_user_name']}, {'$set': {'tags': user_tags}})


def get_tags_for_user(username, db):
    users_collection = db["users"]

    db_user = users_collection.find_one({'tg_user_name': username})

    if db_user is None:
        raise UserTagsException("такого пользователя не существует")

    return db_user["tags"]


def get_all_tags(db):
    _tags = db["tags"]

    db_tags = _tags.find()

    tags = list()

    for tag in db_tags:
        tags.append({
            'tag_name': tag['tag_name'],
            'tag_description': tag['tag_description']
        })

    if len(tags) == 0:
        raise UserTagsException("Вы еще не создали ни одного тэга")

    return tags
