from flask import Flask, request, jsonify
import csv
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
users_file = 'users.csv'

def init_csv():
    if not os.path.exists(users_file):
        with open(users_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['email', 'username', 'password'])

def user_exists(username):
    with open(users_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                return True
    return False

def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()

import re

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    # Check if email is provided and valid
    if not email or not is_valid_email(email):
        return jsonify({'message': 'Invalid or missing email'}), 400

    # Check if username already exists
    if user_exists(username):
        return jsonify({'message': 'Username already exists'}), 400

    # Hash the password before saving
    hashed_password = hash_password(password)

    # Save the user to the file
    with open(users_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email, username, hashed_password])

    return jsonify({'message': 'User signed up successfully'}), 201

# Helper function to validate email format
def is_valid_email(email):
    # Simple regex to check for a valid email format
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    hashed_password = hash_password(password)

    with open(users_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username and row['password'] == hashed_password:
                # Generate a random token (simple for now, could be a JWT)
                token = secrets.token_urlsafe(16)
                return jsonify({'message': 'Login successful', 'token': token}), 200

    return jsonify({'message': 'Invalid username or password'}), 401


def send_recovery_email(email, username):
    sender_email = "usermanagement.eraz@gmail.com"
    sender_password = "password"
    with open(f'{__file__}/../password.txt', 'r') as file:
        sender_password = file.read()
    subject = "Password Recovery"
    body = f"Hello {username},\n\nPlease use the following link to reset your password: http://example.com/reset_password?username={username}\n\nBest regards,\nEraz User Management Team"
    def generate_reset_token():
        return secrets.token_urlsafe(16)

    reset_tokens = {}

@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    username = data.get('username')
    new_password = data.get('new_password')
    token = data.get('token')

    if username not in reset_tokens or reset_tokens[username] != token:
        return jsonify({'message': 'Invalid or expired token'}), 400

    hashed_password = hash_password(new_password)

    users = []
    user_found = False

    with open(users_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                row['password'] = hashed_password
                user_found = True
            users.append(row)

    if not user_found:
        return jsonify({'message': 'Username not found'}), 404

    with open(users_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['email', 'username', 'password'])
        writer.writeheader()
        writer.writerows(users)

    del reset_tokens[username]

    return jsonify({'message': 'Password reset successfully'}), 200

reset_tokens = {}

def generate_reset_token():
    return secrets.token_urlsafe(16)

def send_recovery_email(email, username, token):
    sender_email = "usermanagement.eraz@gmail.com"
    with open(f'{__file__}/../password.txt', 'r') as file:
        sender_password = file.read()
    subject = "Password Recovery"
    body = f"Hello {username},\n\nPlease use the following link to reset your password: http://81.244.229.34:5000/reset_password?username={username}&token={token}\n\nBest regards,\nEraz User Management Team"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/request_reset', methods=['POST'])
def request_reset():
    data = request.json
    username = data.get('username')
    
    with open(users_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                email = row['email']
                token = generate_reset_token()
                reset_tokens[username] = token
                if send_recovery_email(email, username, token):
                    return jsonify({'message': 'Password reset email sent', 'token': token}), 200
                else:
                    return jsonify({'message': 'Failed to send reset email'}), 500
    
    return jsonify({'message': 'Username not found'}), 404

@app.route('/lost_password', methods=['POST'])
def lost_password():
    data = request.json
    username = data.get('username')

    with open(users_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                email = row['email']
                if send_recovery_email(email, username):
                    return jsonify({'message': 'Password recovery email sent'}), 200
                else:
                    return jsonify({'message': 'Failed to send recovery email'}), 500

    return jsonify({'message': 'Username not found'}), 404

@app.route('/user', methods=['GET'])
def get_user():
    # Assume the username is sent via a query parameter
    username = request.args.get('username')
    
    if not username:
        return jsonify({'message': 'Username is required'}), 400

    # Read the CSV file to find the user
    with open(users_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                # Return email and username if the user is found
                return jsonify({'email': row['email'], 'username': row['username']}), 200
    
    # If the user is not found, return an error
    return jsonify({'message': 'User not found'}), 404


clients = {}

# Route to receive a message from Unity (client)
@app.route('/receive_message', methods=['POST'])
def receive_message():
    data = request.get_json()
    message_type = data.get('type')
    content = data.get('content')

    if message_type == "connect":
        client_name = content
        clients[client_name] = request.remote_addr  # Store client address
        return jsonify({"status": "Client connected", "message": "Connection successful"}), 200
    else:
        return jsonify({"status": "Error", "message": "Invalid message type"}), 400


# Route to send a message to a specific client or broadcast to all clients
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    message_type = data.get('type')
    content = data.get('content')
    target_client = data.get('target_client', 'all')

    # Broadcast message to all clients or specific client
    if target_client == 'all':
        for client in clients:
            # Logic to send the message to all clients (e.g., via another method or message queue)
            print(f"Sending message to {client}: {content}")
        return jsonify({"status": "Message sent to all", "type": message_type, "content": content}), 200
    else:
        if target_client in clients:
            # Logic to send the message to the specific client (e.g., store in DB, notify, etc.)
            print(f"Sending message to {target_client}: {content}")
            return jsonify({"status": "Message sent", "type": message_type, "content": content}), 200
        else:
            return jsonify({"status": "Error", "message": f"Client {target_client} not found"}), 404
        
@app.route('/disconnect', methods=['POST'])
def disconnect():
    data = request.get_json()
    client_name = data.get('client_name')
    
    if client_name in clients:
        del clients[client_name]  # Remove the client from the list
        return jsonify({"status": "Client disconnected", "type": "ACK", "content": f"{client_name} disconnected successfully"})
    else:
        return jsonify({"status": "Error", "type": "ERR", "content": f"Client {client_name} not found"})



if __name__ == '__main__':
    init_csv()
    app.run(host="0.0.0.0", debug=True, port=5000, ssl_context='adhoc')