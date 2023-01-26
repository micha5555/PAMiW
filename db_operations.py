import sqlite3

db_name = "app_database.db"

def create_tables():
    db = sqlite3.connect(db_name)
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            login string NOT NULL PRIMARY KEY,
            password string NOT NULL)
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id integer PRIMARY KEY AUTOINCREMENT,
            name string,
            price double,
            seller string,
            quantity integer,
            FOREIGN KEY (seller)
                REFERENCES users(login))
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id integer PRIMARY KEY AUTOINCREMENT,
            owner string,
            totalPrice double,
            FOREIGN KEY (owner)
                REFERENCES users(login))
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordertoproduct (
        orderId integer,
        productId integer,
        quantity integer,
        price double,
        FOREIGN KEY (orderId)
            REFERENCES orders(id),
        FOREIGN KEY (productId)
            REFERENCES products(id))
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id integer PRIMARY KEY AUTOINCREMENT,
            owner string,
            totalPrice double,
            FOREIGN KEY (owner)
                REFERENCES users(login))
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carttoproduct (
        cartId integer,
        productId integer,
        quantity integer,
        price double,
        FOREIGN KEY (cartId)
            REFERENCES carts(id),
        FOREIGN KEY (productId)
            REFERENCES products(id))
    ''')
    db.commit()
    db.close()

# to do zmiany fest
def check_credentials(login, password):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute('''
            SELECT * FROM users
    ''')
    rows = cursor.fetchall()
    print(rows)
    db.close()
    for row in rows:
        if row[1] == login and row[2] == password:
            print('true')
            return True
    # if login in login_credentials.keys():
    #     if password == login_credentials[login]:
    #         return True
    print('false')
    return False

def check_corectness(login, password):
    if(login is not None and password is not None):
        print('in if')
        print(len(login))
        print(len(password))
        return len(login) > 0 and len(password) > 0 
    return False

def register_user(login, password):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (login, password) VALUES (?, ?)", (login, password))
    db.commit()
    db.close()

def add_product(name, price, seller, quantity):
    if len(name) > 0 and price > 0 and quantity > 0:
        db = sqlite3.connect(db_name)
        cursor = db.cursor()
        cursor.execute("INSERT INTO products (name, price, seller, quantity) VALUES (?, ?, ?, ?)", (name, price, seller, quantity))
        db.commit()
        db.close()
        return True
    else:
        return False


def get_all_products():
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    db.close()
    return rows

# poprawić bo będzie sql injection
def get_products_where_name_has_pattern(pattern):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    query = "SELECT * FROM products WHERE name LIKE \"%" + pattern +"%\""
    # print(query)
    cursor.execute(query)
    rows = cursor.fetchall()
    db.close()
    return rows

def get_user_products(user):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT name, price, quantity FROM products WHERE seller = (?)", (user,))
    rows = cursor.fetchall()
    db.close()
    return rows