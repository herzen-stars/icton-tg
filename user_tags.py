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


def add_tags_to_user(username, _tags, db):
    print("@" + __name__ + ": adding tags to user " + username)
    users = db["users"]
    tags = db["tags"]
    db_user = users.find_one({'tg_user_name': username})

    if db_user is None:
        raise UserTagsException("user with given username is not found")

    for tag_name in _tags:
        db_tag = tags.find_one({'tag_name': tag_name})

        if db_tag is None:
            raise UserTagsException("no such tag")

        db_user = users.find_one({'tg_user_name': username})
        db_user_tags = db_user['tags']
        if tag_name in db_user_tags:
            raise UserTagsException("user already has this tag")
        db_user_tags.append(tag_name)
        users.find_one_and_update({'tg_user_name': username}, {'$set': {'tags': db_user['tags']}})


def get_users_with_all_tags(tags, chat, bot, db):
    users = db["users"]
    db_users = users.find({'tags': {'$all': tags}})

    tg_users = list()

    for user in db_users:
        tg_users.append(bot.get_chat_member(chat.id, user['tg_user_id']).user)

    if len(tg_users) == 0:
        raise UserTagsException("no users with this tag found")

    return tg_users


def get_users_with_tags(tags, chat, bot, db):
    users = db["users"]
    db_users = users.find({'tags': {'$in': tags}})

    tg_users = list()

    for user in db_users:
        tg_users.append(bot.get_chat_member(chat.id, user['tg_user_id']).user)

    if len(tg_users) == 0:
        raise UserTagsException("no users with this tag found")

    return tg_users


def add_tag(tag_name, tag_description, db):
    print("@" + __name__ + ": creating tag " + tag_name)
    tags = db["tags"]
    db_tag = tags.find_one({'tag_name': tag_name})
    if db_tag is not None:
        raise UserTagsException("this tag already exists")

    tags.insert_one({
        'tag_name': tag_name,
        'tag_description': tag_description
    })


def get_all_tags(db):
    _tags = db["tags"]

    db_tags = _tags.find()

    tags = list()

    for tag in db_tags:
        print(tag)
        tags.append({
            'tag_name': tag['tag_name'],
            'tag_description': tag['tag_description']
        })

    if len(tags) == 0:
        raise UserTagsException("no tags found, try registering one!")

    return tags
