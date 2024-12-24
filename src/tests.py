import os
import csv
import unittest
from app import app, init_csv, users_file, hash_password

class FlaskAppTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run once before all tests."""
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        """Run before each test."""
        # Ensure the users file is fresh for each test
        if os.path.exists(users_file):
            os.remove(users_file)
        init_csv()

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(users_file):
            os.remove(users_file)

    def test_signup(self):
        """Test user signup functionality."""
        response = self.client.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'User signed up successfully')

        # Verify user data in the file
        with open(users_file, 'r') as file:
            reader = csv.DictReader(file)
            users = list(reader)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['username'], 'testuser')
        self.assertEqual(users[0]['email'], 'test@example.com')
        self.assertEqual(users[0]['password'], hash_password('password123'))

    def test_signup_existing_user(self):
        """Test signing up with an existing username."""
        self.client.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })

        response = self.client.post('/signup', json={
            'email': 'test2@example.com',
            'username': 'testuser',
            'password': 'password456'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['message'], 'Username already exists')

    def test_login(self):
        """Test user login functionality."""
        self.client.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })

        response = self.client.post('/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Login successful')

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        self.client.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })

        response = self.client.post('/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['message'], 'Invalid username or password')

    def test_delete_account(self):
        """Test account deletion."""
        self.client.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })

        response = self.client.delete('/delete_account', json={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Account deleted successfully')

        # Verify the account is removed from the file
        with open(users_file, 'r') as file:
            reader = csv.DictReader(file)
            users = list(reader)
        self.assertEqual(len(users), 0)

    def test_delete_account_invalid_credentials(self):
        """Test account deletion with invalid credentials."""
        self.client.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })

        response = self.client.delete('/delete_account', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['message'], 'Invalid username or password')

if __name__ == '__main__':
    unittest.main()
