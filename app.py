from flask import Flask, render_template, redirect, request, session, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError
from models import User, CartItem, Purchase


app = Flask(__name__)
app.config["SECRET_KEY"] = "ddgg"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    id_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.String(50), nullable=False)

class Order(db.Model):  # New database table
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id_number = db.Column(db.String(11), nullable=False)
    phone_number = db.Column(db.String(9), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BuyForm(FlaskForm):  # New form for the /buy page
    id_number = StringField('ID Number', validators=[DataRequired(), Length(max=11)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=9)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Place Order')

products = [
    {"name": "HyperX Cloud Stinger 2", 'img': "/static/stinger2.jpg", "description": "Gaming Headset", "price": "139", "id": 0},
    {"name": "Razer Kraken X", 'img': "/static/razerkrakenxheadset.jpg", "description": "Gaming Headset", "price": "230", "id": 1},
    {"name": "Razer DeathAdder", 'img': "/static/razerdeathaddermouse.jpg", "description": "Gaming Mouse", "price": "40", "id": 2}
]

pcparts = [
    {"name": "Asus TUF GTX 1650 4GB", 'img': "/static/gtx1650.jpg", "description": "Nvidia Graphics Card", "price": "699", "id": 0},
    {"name": "Asus Dual RX6500XT OC", 'img': "/static/rx6500xtoc.jpg", "description": "AMD Graphics Card", "price": "799", "id": 1},
    {"name": "Gigabyte RTX 3050 EAGLE", 'img': "/static/rtx3050.jpg", "description": "Nvidia Graphics Card", "price": "679", "id": 2}
]

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/products")
def product_list():
    return render_template("products.html", products=products)

@app.route("/products/<int:product_id>", methods=['GET', 'POST'])
def product_detail(product_id):
    product = next((p for p in products if p["id"] == product_id))
    if request.method == 'POST' and 'user_id' in session:
        user_id = session['user_id']
        cart_item = CartItem(user_id=user_id, product_name=product['name'], price=product['price'])
        db.session.add(cart_item)
        db.session.commit()
        return redirect(url_for('cart'))
    return render_template("product_details.html", product=product)

@app.route("/pcparts")
def pcpart_list():
    return render_template("pcparts.html", pcparts=pcparts)

@app.route("/pcparts/<int:part_id>", methods=['GET', 'POST'])
def pcpart_detail(part_id):
    pc_part = next((p for p in pcparts if p["id"] == part_id))
    if request.method == 'POST' and 'user_id' in session:
        user_id = session['user_id']
        cart_item = CartItem(user_id=user_id, product_name=pc_part['name'], price=pc_part['price'])
        db.session.add(cart_item)
        db.session.commit()
        return redirect(url_for('cart'))
    return render_template("pcpart_details.html", pc_part=pc_part)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if request.method == 'POST':
        db.session.query(CartItem).filter_by(user_id=user_id).delete()
        db.session.commit()
        return redirect('/')
    return render_template('cart.html', cart_items=cart_items)


@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        id_number = request.form['id_number']
        phone_number = request.form['phone_number']
        email = request.form['email']
        address = request.form['address']

        new_purchase = Purchase(
            user_id=session.get('user_id'),
            id_number=id_number,
            phone_number=phone_number,
            email=email,
            address=address
        )
        db.session.add(new_purchase)
        db.session.commit()

        db.session.query(CartItem).filter_by(user_id=session.get('user_id')).delete()
        db.session.commit()

        return render_template('purchase_confirmation.html')

    return render_template('buy.html')


@app.context_processor
def cart_count():
    user_id = session.get('user_id')
    count = CartItem.query.filter_by(user_id=user_id).count() if user_id else 0
    return {'cart_count': count}

@app.before_request
def load_cart_count():
    if 'user_id' in session:
        g.cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
    else:
        g.cart_count = 0

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
