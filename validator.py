import re
from flask import flash
# string that contains only letters and numbers
login_pattern = "^[a-zA-Z0-9]+$"
# at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character
password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"

def validate_login_and_password(login, password):
    if re.match(login_pattern, login) and re.match(password_pattern, password):
        return True
    else:
        return False