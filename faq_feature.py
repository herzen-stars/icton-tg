faq_title = '<b>Часто задаваемые вопросы</b>'


# получить faq из бд
def retrieve_faq(db):
    _message = [faq_title]
    messages = db['messages']
    faq_entries = messages.find_one({'_id': 'faq'})['msg']

    counter = 1
    for entry in faq_entries:
        _message.append(f'{counter}. {entry}')
        counter += 1

    _return = '\n\n'.join(_message)
    return _return


# добавить элемент в faq
def add_to_faq(db, entry):
    messages = db['messages']
    old_faq = messages.find_one({'_id': 'faq'})['msg']
    if '/faq_add' in old_faq[0]:
        old_faq.pop(0)
    new_faq = old_faq
    new_faq.append(entry)
    messages.update_one({'_id': 'faq'}, {'$set': {'msg': new_faq}})
    return 0


# удалить элемент из faq
def remove_from_faq(db, entry_no):
    messages = db['messages']
    old_faq = messages.find_one({'_id': 'faq'})['msg']
    new_faq = old_faq
    new_faq.pop(entry_no - 1)
    messages.update_one({'_id': 'faq'}, {'$set': {'msg': new_faq}})
    return 0


# сбросить faq
def flush_faq(db):
    faq = ['FAQ пока что пуст. Запишите в него пункты командой: /faq_add']
    messages = db['messages']
    messages.update_one({'_id': 'faq'}, {'$set': {'msg': faq}})
    return 0
