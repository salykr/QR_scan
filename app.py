from flask import render_template
from flask import Flask, jsonify
import uuid
import pyotp 

app = Flask(__name__)

# In-memory storage for login sessions
login_sessions = {}

@app.route('/start-login', methods=['GET'])
def start_login():
    # 1. Generate a random secret for TOTP
    secret = pyotp.random_base32()  # Generates a random 16-character base32 secret

    # 2. Generate a unique loginSessionId
    login_session_id = str(uuid.uuid4())

    # 3. Save the session details in memory
    login_sessions[login_session_id] = {
        'secret': secret,
        'validated': False
    }

    # 4. Return the secret and session id
    return jsonify({
        'loginSessionId': login_session_id,
        'secret': secret
    })


@app.route('/phone-b')
def phone_b():
    return render_template('phone_b.html')

if __name__ == '__main__':
    app.run(debug=True)
