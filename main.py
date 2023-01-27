from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from validator import validate_login_and_password
from flask import Flask, request, render_template, redirect, flash
from argon2 import PasswordHasher
import requests
import json
from requests import Request, post
# OAuth
import random, string
from flask_dance.contrib.github import github

# to fill
CLIENT_ID = ''
CLIENT_SECRET = ''

app = Flask(__name__) 
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = "854658yuthjtureyu89tjh89trj8h548h754y7854hty8er8ygw875g6854yt88"

def generate_state(length=30):
  char = string.ascii_letters + string.digits
  rand = random.SystemRandom()
  return ''.join(rand.choice(char) for _ in range(length))

@app.route("/callback")
def callback():
  args = request.args
  cookies = request.cookies

  if args.get("state") != cookies.get("state"):
    return "State does not match. Possible authorization_code injection attempt", 400

  params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": args.get("code")
  }
  
  access_token = post("https://github.com/login/oauth/access_token",
                      params=params)
  part_of_the_access_token = access_token.text[:24]
  print(part_of_the_access_token, end="...\n")

#   headers = {"Authorization": f"Token {access_token}"}
#   user_info = requests.get("https://api.github.com/user", headers=headers).json()
#   print(user_info)

  return "Authorized in GitHub OAuth Server", 200

@app.route("/oauth")
def authorize_with_github():
  random_state = generate_state()
  params = {
    "client_id": CLIENT_ID,
    "redirect_uri": "http://127.0.0.1:5050/callback",
    "scope": "repo user",
    "state": random_state
  }

  authorize = Request("GET", "https://github.com/login/oauth/authorize",
                      params=params).prepare()

  response = redirect(authorize.url)
  response.set_cookie("state", random_state)
  return response



# json-rpc
url = "http://localhost:4000/jsonrpc"
headers = {'content-type': 'application/json'}
def send_request(method_name, args):
    payload = {
        "method": method_name,
        "params": args,
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(
    url, data=json.dumps(payload), headers=headers).json()
    return response['result']

send_request("create_tables", [])

ph = PasswordHasher()
class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username is None:
        return None
    row = send_request("get_user", [username])
    try:
        username, password = row
    except:
        return None

    user = User()
    user.id = username
    user.password = password
    return user

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route('/signin', methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = user_loader(username)
        if user is None:
            flash("Nieprawidłowy login lub hasło")
            return redirect("/signin")

        try:
            ph.verify(user.password, password)
            login_user(user)
            return redirect('/mainpanel')
        except:
            flash("Nieprawidłowy login lub hasło")
            return redirect("/signin")

@app.route('/login', methods=["POST"])
def login():
    if 'login' in request.form.keys():
        return redirect('/')
    
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("registerpanel.html")
    username = request.form.get("username")
    password = request.form.get("password")
    repeated_password = request.form.get("repeated_password")
    userExists = send_request("check_if_user_exists", [username])
    print(userExists)
    if userExists:
        flash("Użytkownik " + username + " już istnieje")
        return redirect("/signin")
    if password != repeated_password:
        flash("Niepoprawne dane")
        return render_template("registerpanel.html")
    if(validate_login_and_password(username, password)):
        passwd = ph.hash(request.form.get("password"))
        print(username)
        print(passwd)
        send_request("register_user", [username, passwd])
        send_request("create_cart", [username])
        flash("Zarejestrowano pomyślnie")
        return redirect("/signin")
    else:
        if "submit" in request.form :
            flash("Niepoprawne dane")
        return render_template("registerpanel.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")
    
@app.route('/mainpanel')
@login_required
def main_panel():
    if not check_if_logged():
        return render_template("notlogged.html")
    return render_template("mainpanel.html", name=current_user.id)

# walidacja czy poprawnie chłop wpisał dane
@app.route('/products', methods=["GET", "POST"])
@login_required
def products():
    rows = ''
    if request.method == 'POST' and 'prod_name' in request.form:
        prod_name = request.form.get('prod_name')
        price = float(request.form.get('price'))
        quantity = int(request.form.get('quantity'))
        added = send_request("add_product", [prod_name, price, current_user.id, quantity])
        if not added:
            flash("Nie udało się dodać produktu. Upewnij się, że nazwa jest poprawna, cena oraz ilość większa od zera")
            redirect("/products")
    if request.method == 'POST' and 'search_field' in request.form and len(request.form.get('search_field')) > 0:
        rows = send_request("get_products_where_name_has_pattern", [request.form.get('search_field')])
    else:
        rows = send_request("get_all_products", [])
    return render_template("products.html", products_table=rows)

@app.route('/myproducts', methods=["GET", "POST"])
@login_required
def myproducts():
    user_products = send_request("get_user_products", [current_user.id])
    return render_template("myproducts.html", products_table=user_products)

@app.route('/myorders', methods=["GET", "POST"])
@login_required
def myorders():
    orders = send_request("get_client_orders", [current_user.id])
    keys = orders.keys()
    ordersValue = []
    for key in keys:
        ordersValue.append(orders[key])
    print(ordersValue)
    print(ordersValue[0])
    return render_template("myorders.html", orders=ordersValue)

@app.route('/cart', methods=["GET", "POST"])
@login_required
def cart():
    clientCart = send_request("get_client_cart", [current_user.id])
    productsFromCart = None
    try:
        productsFromCart = send_request("get_clients_products_in_cart",[clientCart[0]])
    except:
        pass
    return render_template("cart.html", productsFromCart=productsFromCart, totalPrice=clientCart[1])

@app.route('/createorder', methods=["POST"])
@login_required
def make_order():
    clientCart = send_request("get_client_cart", [current_user.id])
    productsFromCart = None
    try:
        productsFromCart = send_request("get_clients_products_in_cart",[clientCart[0]])
        # print(productsFromCart[0]) 
        # print(len(productsFromCart))2
        # print(len(productsFromCart[0]))5
        send_request("make_order", [productsFromCart, current_user.id, clientCart[1]])
    except:
        flash("Brak produktów w koszyku")
    return redirect('/cart')

@app.route('/addtocart', methods=["POST"])
@login_required
def add_to_cart():
    productId = request.form.get("productid")
    productPrice = request.form.get("productprice")
    clientCart = send_request("get_client_cart", [current_user.id])
    cartToProduct = send_request("get_cart_to_product_with_cartId_and_productId", [clientCart[0], productId])
    if cartToProduct == None:
        send_request("create_cart_to_product", [clientCart[0], productId, 1, float(productPrice)])
        return redirect('/products')
    send_request("increment_quantity_in_carttoproduct", [clientCart[0], productId])
    return redirect('/products')

@app.route('/emptycart', methods=["POST", "GET"])
@login_required
def empty_cart():
    send_request("empty_cart_from_db", [current_user.id])
    return redirect('/cart')

def check_if_logged():
    return len(current_user.id) > 0

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)
