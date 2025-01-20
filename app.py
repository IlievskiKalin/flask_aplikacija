from flask import Flask, request, jsonify
from extensions import db
from models import User
from models import UserSpending
from sqlalchemy import func


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

@app.route('/total/<int:user_id>', methods=['GET'])
def get_total_spent(user_id):
    total_spent = db.session.query(func.sum(UserSpending.money_spent)).filter_by(user_id=user_id).scalar()

    if total_spent is None:
        return jsonify({"error": f"No spending records found for user_id {user_id}"}), 404

    total_spent = round(total_spent, 2)
    return jsonify({"user_id": user_id, "total_spent": total_spent})


@app.route('/average_spending_by_age', methods=['GET'])
def average_spending_by_age():

    age_ranges = [
        (18, 25),
        (26, 35),
        (36, 45),
        (46, 55),
        (56, 65),
        (66, 100)
    ]
    results = []


    for age_min, age_max in age_ranges:
        avg_spending = db.session.query(func.avg(UserSpending.money_spent)) \
            .join(User, User.user_id == UserSpending.user_id) \
            .filter(User.age.between(age_min, age_max)) \
            .scalar()


        avg_spending = round(avg_spending, 2) if avg_spending else 0.0
        results.append({
            "age_range": f"{age_min}-{age_max}",
            "average_spending": avg_spending,
        })

    return jsonify(results)