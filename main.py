import sys

# получить ключи доступа из окружения
if len(sys.argv) < 3:
    print("""Передайте ключи доступа в аргументы команды:\n
    python3 main.py пароль_от_mongodb токен_доступа_telegram_api\n""")
    sys.exit()
else:
    credentials = {
        "mongodb_password": sys.argv[1],
        "tg_token": sys.argv[2]
    }