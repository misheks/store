from flask import render_template, redirect, request, session, url_for, flash, g
from configs import app, db
from models import User, CartItem, Purchase
from forms import RegisterForm, LoginForm, BuyForm

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

@app.route('/')
def home():
    return render_template('index.html')

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

@app.route("/products")
def product_list():
    return render_template("products.html", products=products)

@app.route("/products/<int:product_id>", methods=['GET', 'POST'])
def product_detail(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('product_list'))
    if request.method == 'POST' and 'user_id' in session:
        user_id = session['user_id']
        cart_item = CartItem(user_id=user_id, product_name=product['name'], price=product['price'])
        db.session.add(cart_item)
        db.session.commit()
        flash('Added to cart!', 'success')
        return redirect(url_for('cart'))
    return render_template("product_details.html", product=product)

@app.route("/pcparts")
def pcpart_list():
    return render_template("pcparts.html", pcparts=pcparts)

@app.route("/pcparts/<int:part_id>", methods=['GET', 'POST'])
def pcpart_detail(part_id):
    pc_part = next((p for p in pcparts if p["id"] == part_id), None)
    if not pc_part:
        flash('PC Part not found.', 'danger')
        return redirect(url_for('pcpart_list'))
    if request.method == 'POST' and 'user_id' in session:
        user_id = session['user_id']
        cart_item = CartItem(user_id=user_id, product_name=pc_part['name'], price=pc_part['price'])
        db.session.add(cart_item)
        db.session.commit()
        flash('Added to cart!', 'success')
        return redirect(url_for('cart'))
    return render_template("pcpart_details.html", pc_part=pc_part)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        flash('You need to log in to view your cart.', 'info')
        return redirect('/login')
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if request.method == 'POST':
        db.session.query(CartItem).filter_by(user_id=user_id).delete()
        db.session.commit()
        flash('Cart cleared!', 'success')
        return redirect('/')
    return render_template('cart.html', cart_items=cart_items)

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if 'user_id' not in session:
        flash('You need to log in to make a purchase.', 'info')
        return redirect('/login')
    form = BuyForm()
    if form.validate_on_submit():
        new_purchase = Purchase(
            user_id=session.get('user_id'),
            id_number=form.id_number.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data
        )
        db.session.add(new_purchase)
        db.session.commit()
        db.session.query(CartItem).filter_by(user_id=session.get('user_id')).delete()
        db.session.commit()
        flash('Purchase successful!', 'success')
        return render_template('purchase_confirmation.html')  # Direct rendering
    return render_template('buy.html', form=form)


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