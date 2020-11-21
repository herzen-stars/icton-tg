faq_title = '<b>Часто задаваемые вопросы</b>\n\n'


# получить faq из бд
def retrieve_faq(db):
    _message = [faq_title]
    messages = db['messages']
    _message.append(messages.find_one({'_id': 'faq'})['msg'])
    _return = ''.join(_message)
    return _return


# перезаписать faq
def override_faq(db, faq):
    messages = db['messages']
    messages.update_one({'_id': 'faq'}, {'$set': {'msg': faq}})
    return 0


# сбросить faq
def flush_faq(db):
    faq = 'FAQ пока что пуст. Запишите его командой: /faq_change'
    messages = db['messages']
    messages.update_one({'_id': 'faq'}, {'$set': {'msg': faq}})
    return 0
