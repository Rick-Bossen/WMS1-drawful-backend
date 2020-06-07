import re


# Validate correct email formatting
def validate_mail(mail):
    return bool(re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$)", mail))


# Validate username only containing letters/numbers and length between 4 and 32 characters
def validate_username(username):
    return bool(re.match("(^[a-zA-Z0-9]{4,32}$)", username))
