import re
from flask import flash

def validate_login_and_password(login, password):
    # string that contains only letters and numbers
    login_pattern = "^[a-zA-Z0-9]+$"
    # at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character
    password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
    if re.match(login_pattern, login) and re.match(password_pattern, password):
        return True
    else:
        return False
    
def validate_product(prod_name, price, quantity):
    try:
        float(price)
        int(quantity)
    except:
        return False
    if prod_name != None and len(prod_name) > 0 and float(price) > 0 and int(quantity) > 0:
        return True
    return False