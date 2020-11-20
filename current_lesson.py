import json
import requests
import sys
from current_lesson_helpers import *
from pathlib import Path
from datetime import datetime

# getting directory's absolute path in case it does not match CWD
path = Path(__file__).parent.absolute()

# Parsing config data, performing the initial checks
c_path = path / "current_lesson.json"
if not c_path.is_file():
    print(f"{__name__}: current_lesson.json not found, exiting")
    sys.exit()
else:
    with open(c_path, "r") as open_file:
        config_file = json.load(open_file)

# for config in config_file:
# parsing schedule for today
s_path = path / "schedule.json"

if (not s_path.is_file()) or "schedule_expiration_date" not in config_file or expired(config_file["schedule_expiration_date"]):
    print("schedule.json not found or expired, attempting download")

    schedule = []
    for config in config_file["groups"]:
        try:
            if int(config["subgroup"]) == 0:
                response = requests.get(url=f"{config['schedule_provider_url']}?groupID={config['group_id']}")
            elif int(config["subgroup"]) > 0:
                response = requests.get(
                    url=f"{config['schedule_provider_url']}?groupID={config['group_id']}&subgroup={int(config['subgroup']) - 1}"
                                        )
            else:
                print("Subgroup parameter in config is invalid")
                raise ValueError

            schedule.append(response.json())

            try:
                if schedule["status"] == 500:
                    print(f"Provider returned error: {schedule['message']}. Wrong group id?")
                    raise ValueError
            except ValueError:
                sys.exit()
            except TypeError:
                pass

            print("Success!")

        except ValueError:
            sys.exit()

        except:
            print(f"Error. Response status code: {response.status_code}. \
            Provider's website might be down, try again in a few minutes.")
            sys.exit()

        with open(s_path, "w") as file:
            json.dump(schedule, file, indent=4)

        config_file["schedule_expiration_date"] = expiration_date()
        with open(c_path, "w") as file:
            json.dump(config_file, file, indent=4)

else:
    with open(s_path, "r") as file:
        schedule = json.load(file)


def current_lesson_for_group(_schedule):
    dow = datetime.now().weekday()
    if dow == 6:
        return None

    today = _schedule[dow]
    for i in range(len(today)):
        lesson = today[i]
        if int(lesson["start_time"]) <= current_time() <= int(lesson["end_time"]):
            return lesson
        elif not i + 1 == len(today):
            if int(lesson["end_time"]) <= current_time() <= int(today[i + 1]["start_time"]):  # problem
                return_ = {
                    "name": "break",
                    "start_time": lesson["end_time"],
                    "end_time": today[i + 1]["start_time"]
                }
                return return_
        else:
            continue

    return None

def current_lesson():
    raw_return = {}
    config = config_file['groups']
    for i in range(len(schedule)):
        group = f'{config[i]["group_id"]}_{config[i]["subgroup"]}'
        raw_return[group] = current_lesson_for_group(schedule[i])

    message = []
    message.append('<b>Занятия сейчас:</b>')

    for group in raw_return:
        group_ = group.split('_')

        if raw_return[group] == None:
            lesson = 'занятий нет'
        elif raw_return[group]['name'] == 'break':
            lesson = 'перерыв'
        else:
            lesson = raw_return[group]['name']
            link = raw_return[group]['course_link']
            lesson = f'<a href="{link}">{lesson}</a>'

        if group_[1] != '0':
            msg = f"Гр. {group_[0]}, пг. {group_[1]}: {lesson}."
        else:
            msg = f"Гр. {group_[0]}: {lesson}."
        message.append(msg)

    message = '\n'.join(message)

    return message

def next_lesson_for_group(_schedule):
    dow = datetime.now().weekday()
    if dow == 6:
        return None

    today = _schedule[dow]
    for i in range(len(today)):
        lesson = today[i]
        if not i == len(today) and int(lesson["start_time"]) <= current_time() <= int(lesson["end_time"]):
            return today[i + 1]
        elif not i + 1 == len(today):
            if int(lesson["end_time"]) <= current_time() <= int(today[i + 1]["start_time"]):
                return today[i + 1]
        else:
            continue

    return None

def next_lesson():
    raw_return = {}
    config = config_file['groups']
    for i in range(len(schedule)):
        group = f'{config[i]["group_id"]}_{config[i]["subgroup"]}'
        raw_return[group] = next_lesson_for_group(schedule[i])

    message = []
    message.append('<b>Следующее занятие:</b>')

    for group in raw_return:
        group_ = group.split('_')

        if raw_return[group] == None:
            lesson = 'занятия на сегодня окончены'
        else:
            lesson = raw_return[group]['name']
            link = raw_return[group]['course_link']
            lesson = f'<a href="{link}">{lesson}</a>'

        if group_[1] != '0':
            msg = f"Гр. {group_[0]}, пг. {group_[1]}: {lesson}."
        else:
            msg = f"Гр. {group_[0]}: {lesson}."
        message.append(msg)

    message = '\n'.join(message)

    return message

def schedule_for_tomorrow():
    dow = datetime.now().weekday() + 1
    if dow == 7:
        return 'На завтра занятия не запланированы'
    elif dow == 8:
        dow = 1
        schedules = []
        for _group in schedule:
            schedules.append(_group[dow - 1])
    else:
        schedules = []
        for _group in schedule:
            schedules.append(_group[dow - 1])

    _return = []
    counter = 0
    group_ids = []

    # get froup ids
    for _group in config_file["groups"]:
        entry = f"{_group['group_id']}-{_group['subgroup']}"
        group_ids.append(entry)

    for _schedule in schedules:
        _return.append(f'\n<b>Расписание на завтра (гр. {group_ids[counter]}):</b>\n')
        counter += 1
        for lesson in _schedule:
            start = lesson['start_time']
            start = f'{start[0:2]}:{start[2:4]}'
            end = lesson['end_time']
            end = f'{end[0:2]}:{end[2:4]}'
            name = lesson['name']
            _return.append(f'{start} - {end}: {name}')
        if 'завтра' in _return[-1]:
            _return.append('Занятий не запланировано')

    _return = '\n'.join(_return)
    return _return
