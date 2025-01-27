from flask import Flask, request, jsonify
from extensions import db
from models import User
from models import UserSpending
from sqlalchemy import func
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import requests

TELEGRAM_BOT_TOKEN = "7591135062:AAFWDpn4xyfZXAEPbK04O93JRYOAKr3FaUI"
TELEGRAM_CHAT_IDS = ["7922756245",]

uri = "mongodb+srv://ilievskikalin:e7Om0sTLHhARbioY@cluster0.npmal.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))

mongo_db = client['users_vouchers']
collection = mongo_db['user_spending']

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


@app.route('/send_average_spending', methods=['POST'])
def send_average_spending():

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
            "average_spending": avg_spending
        })

    message = "Average Spending by Age Ranges:\n\n"
    for result in results:
        message += f"Age Range {result['age_range']}: ${result['average_spending']}\n"

    for chat_id in TELEGRAM_CHAT_IDS:
        send_telegram_message(chat_id, message)

    return jsonify({"status": "success", "message": "Statistics sent to Telegram!"})


def send_telegram_message(chat_id, message):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")


@app.route('/write_to_mongodb', methods=['POST'])
def write_to_mongodb():
    try:
        # Calculate total spending for all users
        total_spending = db.session.query(
            UserSpending.user_id, func.sum(UserSpending.money_spent).label('total_spent')
        ).group_by(UserSpending.user_id).all()

        high_spenders = []

        for user_id, total_spent in total_spending:
            if total_spent > 1000:
                # Prepare data in the required format
                user_data = {
                    'user_id': user_id,
                    'total_spending': round(total_spent, 2)
                }
                high_spenders.append(user_data)

        # Save high spenders to MongoDB
        mongo_high_spenders = mongo_db['user_spending1']
        if high_spenders:
            mongo_high_spenders.insert_many(high_spenders)

        return jsonify({
            'message': 'High spenders calculated and saved successfully.',
            'high_spenders': high_spenders
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to calculate high spenders.',
            'details': str(e)
        }), 500




if __name__ == '__main__':
    app.run(debug=True)