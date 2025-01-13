from flask import Flask, request, jsonify
from extensions import db
from models import User
from models import UserSpending


app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users_vouchers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Create tables at startup
with app.app_context():
    db.create_all()


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])



@app.route('/total/<int:user_id> ', methods=['GET'])
def get_total_spent(id):
    userSpending = UserSpending.query.get_or_404(id)
    return jsonify(userSpending.to_dict())

