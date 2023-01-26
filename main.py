from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from validator import validate_register_data_corectness
from flask import Flask, request, make_response, render_template, redirect, flash
from db_operations import *
import sqlite3
from argon2 import PasswordHasher

app = Flask(__name__) 
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = "854658yuthjtureyu89tjh89trj8h548h754y7854hty8er8ygw875g6854yt88"
create_tables()
DATABASE = "app_database.db"
ph = PasswordHasher()
class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username is None:
        return None

    db = sqlite3.connect(DATABASE)
    sql = db.cursor()
    sql.execute(f"SELECT login, password FROM users WHERE login IN(?)", (username,))
    row = sql.fetchone()
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
        # time.sleep(3)
        user = user_loader(username)
        if user is None:
            # invalidLoginsCounter = invalidLoginsCounter + 1
            flash("Nieprawidłowy login lub hasło")
            # if invalidLoginsCounter == 5:
            #     flash("Nastąpiło zbyt wiele nieudanych prób logowania, musiałeś chwilę zaczekać")
            #     mustWait = 1
            #     invalidLoginsCounter = 0
            return redirect("/signin")

        try:
            ph.verify(user.password, password)
            login_user(user)
            # invalidLoginsCounter = 0
            return redirect('/mainpanel')
        except:
            # invalidLoginsCounter = invalidLoginsCounter + 1
            flash("Nieprawidłowy login lub hasło")
            # if invalidLoginsCounter == 5:
            #     flash("Nastąpiło zbyt wiele nieudanych prób logowania, musiałeś chwilę zaczekać")
            #     mustWait = 1
            #     invalidLoginsCounter = 0
            return redirect("/signin")

    # if request.method == 'POST':
    #     username = request.form.get("username", "nothing")
    #     password = request.form.get("password", "nothing")
    #     # if validate_login_data_corectness(login, password) and check_credentials(username, password):
    #     if check_credentials(username, password):
    #         global actual_user
    #         actual_user = username
    #         return redirect('/mainpanel')
    #     flash("Niepoprawny login lub hasło")
    # return render_template("signin.html")

@app.route('/login', methods=["POST"])
def login():
    # print(request.forSm.keys())
    # if 'register' in request.form.keys():
    #     return render_registrationpanel()
    if 'login' in request.form.keys():
        return redirect('/')
    
@app.route("/register", methods=['POST'])
def register():
    if(validate_register_data_corectness(request.form.get("username"), request.form.get("password"), request.form.get("repeated_password"))):
        passwd = ph.hash(request.form.get("password"))
        register_user(request.form.get("username"), passwd)
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
    # print("actual user ", actual_user)
    # if request.method == "POST":
    #     actual_user = ""
    #     return redirect('/login')
    # if actual_user == "":
    #     return redirect('/')
    return render_template("mainpanel.html", name=current_user.id)

@app.route('/products', methods=["GET", "POST"])
@login_required
def products():
    rows = ''
    if request.method == 'POST' and 'prod_name' in request.form:
        added = add_product(request.form.get('prod_name'), float(request.form.get('price')), current_user.id, int(request.form.get('quantity')))
        if not added:
            flash("Nie udało się dodać produktu. Upewnij się, że nazwa jest poprawna, cena oraz ilość większa od zera")
            redirect("/products")
    if request.method == 'POST' and 'search_field' in request.form and len(request.form.get('search_field')) > 0:
        rows = get_products_where_name_has_pattern(request.form.get('search_field'))
    else:
        rows = get_all_products()
    return render_template("products.html", products_table=rows)

@app.route('/myproducts', methods=["GET", "POST"])
@login_required
def myproducts():
    # if request.method == 'GET':
    user_products = get_user_products(current_user.id)
    return render_template("myproducts.html", products_table=user_products)

@app.route('/myorders', methods=["GET", "POST"])
@login_required
def myorders():
    # if request.method == 'GET':
    return render_template("myorders.html")

@app.route('/cart', methods=["GET", "POST"])
@login_required
def cart():
    # if request.method == 'GET':
    return render_template("cart.html")

@app.route('/addtocart', methods=["POST"])
@login_required
def add_to_cart():
    print(request.form.get("1"))
    print(request.form.get("2"))
    print(request.form.get("3"))
    print("nnnn")
    return redirect('/products')

def check_if_logged():
    return len(current_user.id) > 0
# def register():
#     username = request.form.get("login", "")
#     password = request.form.get("password", "")
#     repeated_password = request.form.get("repeated_password", "")
# @app.route('/with-url/<argument>', methods=["GET"])
# def with_url(argument):
#     return "Got argument [" + argument + "]", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)
