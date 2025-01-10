from configs import app, db
from models import Purchase, User, CartItem, Order
from forms import RegisterForm, LoginForm, BuyForm
import routes

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)