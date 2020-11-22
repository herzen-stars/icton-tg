import json

# parse command data
with open("supported_commands.json", "r") as file:
    supported_commands = json.load(file)


# make help message
def help_message(mode=False):
    _message = ['<b>Доступные команды</b>']

    for category, value in supported_commands.items():
        _message.append(f"\n<b>{category}</b>")
        for entry in value:
            if entry['adm_access'] and mode:
                _message.append(f"/{entry['command']} - {entry['description']} <b><u>(админ.)</u></b>")
            elif entry['adm_access']:
                continue
            else:
                _message.append(f"/{entry['command']} - {entry['description']}")

    _message = '\n'.join(_message)
    return _message
