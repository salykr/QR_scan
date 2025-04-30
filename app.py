from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import uuid
import pyotp
import json

app = Flask(__name__)
app.secret_key = 'myverysecretkeyforpoc'  # Needed for session management

login_sessions = {}

fake_users = { 
    'saly@example.com': 'saly',
    'user@example.com': 'user'
}

@app.route('/validate-login', methods=['POST'])
def validate_login():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        data = request.form.get('scanned_qr')
        if not data:
            return jsonify({'status': 'error', 'message': 'No QR code data provided'}), 400

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            return jsonify({'status': 'error', 'message': 'Invalid QR code data format'}), 400

        if not isinstance(parsed, dict):
            return jsonify({'status': 'error', 'message': 'Invalid QR code data format'}), 400

        login_id = parsed.get('loginSessionId')
        scanned_totp = parsed.get('totp')

        if not login_id or not scanned_totp:
            return jsonify({'status': 'error', 'message': 'Missing required fields in QR code data'}), 400

        if login_id not in login_sessions:
            return jsonify({'status': 'error', 'message': 'Invalid login session'}), 400

        stored_totp = login_sessions[login_id].get('totp')
        if not stored_totp or stored_totp != scanned_totp:
            return jsonify({'status': 'error', 'message': 'TOTP mismatch'}), 403

        # Store the scanning user's info in the login session
        login_sessions[login_id].update({
            'validated': True,
            'approved_by': session['user'],
            'scanning_user': session['user']  # Store the scanning user's info
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Login approved successfully!'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 400


@app.route('/start-login', methods=['GET'])
def start_login():
    secret = pyotp.random_base32()
    login_session_id = str(uuid.uuid4())
    
    # Generate TOTP using the secret
    totp = pyotp.TOTP(secret)
    current_totp = totp.now()

    login_sessions[login_session_id] = {
        'totp': current_totp,  # Store the TOTP value instead of secret
        'validated': False
    }

    return jsonify({
        'loginSessionId': login_session_id,
        'totp': current_totp  # Send TOTP instead of secret
    })

#login with credentials , just checks the input
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email in fake_users and fake_users[email] == password:
            session['user'] = email
            return redirect(url_for('home'))
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('home.html', user=session['user'])

@app.route('/qr')
def phone_b():
    return render_template('qr.html')

@app.route('/scan')
def scan_qr_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('scan.html')

@app.route('/check-login-status/<login_id>')
def check_login_status(login_id):
    if login_id not in login_sessions:
        return jsonify({'validated': False}), 404
        
    session_data = login_sessions[login_id]
    if session_data['validated']:
        # Set the session for the QR-displaying device with the scanning user's credentials
        session['user'] = session_data['scanning_user']
        return jsonify({
            'validated': True,
            'redirect_url': url_for('home', _external=True)
        })
    
    return jsonify({'validated': False})

# (later: add /login and /home routes here too)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
