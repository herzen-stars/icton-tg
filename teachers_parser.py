import requests
import re
from bs4 import BeautifulSoup

def parse_teacher(name, page=1):
    '''
    Parses a teacher with given name.

    :param name: name to be found
    :type name: str
    :param page: page number to find on
    :type page: int

    Returns a Telegram-prepared string with teachers' info.
    '''
    print('running from {}'.format(__name__))

    ROOT = 'https://atlas.herzen.spb.ru'
    ENDPOINT = '{}/prof.php'.format(ROOT)
    payload = {'FND': 0, 'FIO': name, 'PAGE': page}
    resp = requests.get(ENDPOINT, params=payload)
    result = []

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content)
        pages_qty = len(soup.find_all('a', {'class': 'rd'}))
        pages_qty = pages_qty // 2 + 1  # filter duplicate values
        table = soup.find('table', {'class': 'table_good'})
        teacher_lst = table.find_all('tr')
        teacher_info = [t.find_all(
            'td', {'class': 't1'}
            ) for t in table.find_all('tr')][1:] # find all teachers
        teacher_links = [
            it.find('a') for tchr in teacher_info for it in tchr
            ]  # get all "a" tags
        teacher_links = [it for it in teacher_links if it]  # remove empty vals
        teacher_names = [it.get_text() for it in teacher_links]
        teacher_links = [
            '{}/{}'.format(ROOT, it.get('href')) for it in teacher_links
            ]  # get hyperlinks and make them full
    else:
        return '<b>Не удалось получить список преподавателей!</b>'

    for idx, link in enumerate(teacher_links):
        resp = requests.get(link)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content)
            phone = soup.find('h3', string=re.compile('Контактный телефон'))
            if phone:
                phone = phone.next_sibling.get_text()  # dive down the tree
            else:
                phone = 'не найден'
            email = soup.find('h3', string=re.compile('E-mail'))
            if email:
                email = email.next_sibling.get_text()
            else:
                email = 'не найден'

            # let's sum up what we've got
            result_name = '<b>Имя:</b> <code>{}</code>'.format(
                teacher_names[idx]
                )
            result_phone = '<b>Телефон:</b> <code>{}</code>'.format(phone)
            result_email = '<b>E-mail:</b> <code>{}</code>'.format(email)

            result_args = (result_name, result_phone, result_email)
            result.append('\n'.join(result_args))

    return 'Страница {} из {}\n\n{}'.format(
        page, pages_qty, '\n\n'.join(result)
        )

