def validate_register_data_corectness(login, password, repeated_password):
    if(login is not None and password is not None and repeated_password is not None):
        if(len(login) > 0 and len(password) > 0):
            if(password != repeated_password):
                return False
            
        return len(login) > 0 and len(password) > 0 
    return False

# def validate_login_data_corectness(login, password):
#     if(login is not None and password is not None):
#         return(len(login) > 0 and len(password) > 0)
#     return False