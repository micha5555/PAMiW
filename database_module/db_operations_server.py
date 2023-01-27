import sqlite3

from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

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

def get_user(login):
    db = sqlite3.connect("app_database.db")
    sql = db.cursor()
    sql.execute(f"SELECT login, password FROM users WHERE login IN(?)", (login,))
    row = sql.fetchone()
    db.close()
    return row

def register_user(login, password):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (login, password) VALUES (?, ?)", (login, password))
    db.commit()
    db.close()

def check_if_user_exists(login):
    db = sqlite3.connect(db_name)
    sql = db.cursor()
    sql.execute(f"SELECT login FROM users WHERE login IN(?)", (login,))
    row = sql.fetchone()
    db.close()
    if row != None and len(row) > 0:
        return True
    else:
        return False

def create_cart(login):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("INSERT INTO carts (owner, totalPrice) VALUES (?, ?)", (login, 0))
    db.commit()
    db.close()

# [0]-id; [1]-totalPrice
def get_client_cart(login):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT id, totalPrice FROM carts WHERE owner = (?)", (login,))
    cart = cursor.fetchone()
    db.close()
    return cart

def get_clients_products_in_cart(clientCartId):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT products.name, products.price, products.seller, carttoproduct.quantity, carttoproduct.price, products.id FROM carttoproduct INNER JOIN products ON carttoproduct.productId = products.id WHERE cartId = (?)", (clientCartId,))
    products = cursor.fetchall()
    db.close()
    return products

def get_cart_to_product_with_cartId_and_productId(clientCartId, productId):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM carttoproduct WHERE cartId = (?) AND productId = (?)", (clientCartId, productId))
    carttoproduct = cursor.fetchone()
    db.close()
    return carttoproduct

def create_cart_to_product(clientCartId, productId, quantity, productPrice):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("INSERT INTO carttoproduct (cartId, productId, quantity, price) VALUES (?, ?, ?, ?)", (clientCartId, productId, quantity, productPrice))
    db.commit()
    db.close()
    increment_price_in_cart(clientCartId, productPrice)

def empty_cart_from_db(login):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT id FROM carts WHERE owner = (?)", (login,))
    cartId = cursor.fetchone()[0]
    cursor.execute("DELETE FROM carttoproduct WHERE cartId = (?)", (cartId,))
    db.commit()
    cursor.execute("UPDATE carts SET totalPrice = (?) WHERE id = (?)", (0, cartId))
    db.commit()
    db.close()

def increment_price_in_cart(clientCartId, productPrice):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT totalPrice FROM carts WHERE id = (?)", (clientCartId,))
    actualPrice=cursor.fetchone()[0]
    cursor.execute("UPDATE carts SET totalPrice=(?) WHERE id = (?)", (actualPrice+productPrice, clientCartId))
    db.commit()
    db.close()

def make_order(productsFromCart, owner, totalPrice):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("INSERT INTO orders (owner, totalPrice) VALUES (?, ?)", (owner, totalPrice))
    db.commit()
    cursor.execute("SELECT max(id) FROM orders")
    orderId = cursor.fetchone()
    for product in productsFromCart:
        cursor.execute("INSERT INTO ordertoproduct (orderId, productId, quantity, price) VALUES (?, ?, ?, ?)", (orderId[0], product[5], product[3], product[4]))
        db.commit()
    db.close()
    empty_cart_from_db(owner)

def get_client_orders(owner):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT id FROM orders WHERE owner = (?)", (owner,))
    ordersIds = cursor.fetchall()
    # print(ordersIds)
    dict = {}
    for orderId in ordersIds:
        # print(orderId)
        cursor.execute("SELECT products.name, ordertoproduct.quantity, ordertoproduct.price FROM ordertoproduct INNER JOIN products ON ordertoproduct.productId=products.id WHERE orderId = (?)", (orderId[0],))
        products = cursor.fetchall()
        dict[orderId[0]] = products
    db.close()
    return dict

def increment_quantity_in_carttoproduct(clientCartId, productId):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM carttoproduct WHERE cartId = (?) AND productId = (?)", (clientCartId, productId))
    carttoproduct = cursor.fetchone()
    cursor.execute("SELECT price FROM products WHERE id = (?)", (productId))
    productPrice = cursor.fetchone()[0]
    cursor.execute("UPDATE carttoproduct SET quantity = (?), price = (?) WHERE cartId = (?) AND productId = (?)",(carttoproduct[2]+1, carttoproduct[3]+productPrice, clientCartId, productId))
    db.commit()
    db.close()
    increment_price_in_cart(clientCartId, productPrice)

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

def get_order(id):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT id, owner, totalPrice FROM orders WHERE id = (?)", (id,))
    order = cursor.fetchone()
    db.close()
    return order

@Request.application
def application(request):
    dispatcher["create_tables"] = create_tables
    dispatcher["get_user"] = get_user #login
    dispatcher["register_user"] = register_user #login, password
    dispatcher["check_if_user_exists"] = check_if_user_exists #login
    dispatcher["create_cart"] = create_cart #login
    dispatcher["get_client_cart"] = get_client_cart #login
    dispatcher["get_clients_products_in_cart"] = get_clients_products_in_cart #clientCartId
    dispatcher["get_cart_to_product_with_cartId_and_productId"] = get_cart_to_product_with_cartId_and_productId #(clientCartId, productId)
    dispatcher["create_cart_to_product"] = create_cart_to_product #(clientCartId, productId, quantity, productPrice):
    dispatcher["empty_cart_from_db"] = empty_cart_from_db #(login)
    dispatcher["increment_price_in_cart"] = increment_price_in_cart #(clientCartId, productPrice)
    dispatcher["make_order"] = make_order #(productsFromCart, owner, totalPrice)
    dispatcher["get_client_orders"] = get_client_orders #(owner)
    dispatcher["increment_quantity_in_carttoproduct"] = increment_quantity_in_carttoproduct #(clientCartId, productId)
    dispatcher["add_product"] = add_product #(name, price, seller, quantity)
    dispatcher["get_all_products"] = get_all_products
    dispatcher["get_products_where_name_has_pattern"] = get_products_where_name_has_pattern #(pattern)
    dispatcher["get_user_products"] = get_user_products #(user)
    dispatcher["get_order"] = get_order #(id)
    
    response = JSONRPCResponseManager.handle(
        request.get_data(cache=False, as_text=True), dispatcher)
    return Response(response.json, mimetype='application/json')

if __name__ == '__main__':
    run_simple('localhost', 4000, application)