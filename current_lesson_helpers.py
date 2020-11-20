from datetime import datetime, timedelta


# returns current time in XXXX format (no delimiter, int)
def current_time():
    _current_time = str(datetime.now().time())[:5]
    _current_time = int(_current_time.replace(":", ""))
    return _current_time


# returns current time in XX:XX format
def log_time():
    _current_time = str(datetime.now().time())[:5]
    return _current_time


# calculate schedule's expiration date
def expiration_date():
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday())
    nearest_saturday = last_monday + timedelta(days=5)
    timestamp = nearest_saturday.replace(hour=23, minute=59)
    return str(timestamp)[:-10]


# returns a true or false if the datetime has passed already
def expired(timestamp_):
    timestamp_ = datetime.strptime(timestamp_, "%Y-%m-%d %H:%M")
    if timestamp_ <= datetime.now():
        return True
    else:
        return False