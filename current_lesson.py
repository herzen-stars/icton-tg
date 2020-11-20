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
        config = json.load(open_file)


# parsing schedule for today
s_path = path / "schedule.json"

if (not s_path.is_file()) or "schedule_expiration_date" not in config or expired(config["schedule_expiration_date"]):
    print("schedule.json not found or expired, attempting download")

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

        schedule = response.json()

        try:
            if schedule["status"] == 500:
                print(f"Provider returned error: {schedule['message']}. Wrong group id?")
                raise ValueError
        except ValueError:
            sys.exit()
        except TypeError:
            pass

        with open(s_path, "w") as file:
            json.dump(schedule, file, indent=4, ensure_ascii=False)

        config["schedule_expiration_date"] = expiration_date()
        with open(c_path, "w") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)

        print("Success!\n")

    except ValueError:
        sys.exit()

    except:
        print(f"Error. Response status code: {response.status_code}. \
        Provider's website might be down, try again in a few minutes.")
        sys.exit()

else:
    with open(s_path, "r") as file:
        schedule = json.load(file)


def current_lesson():
    dow = datetime.now().weekday()
    if dow == 6:
        return None

    today = schedule[dow]
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