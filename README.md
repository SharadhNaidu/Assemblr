# Assemblr - Event Hosting Platform

A web application for hosting and attending events, built with Flask and MySQL.

## Features

- User registration with OTP verification
- Login with username/email/phone
- Profile management
- Admin dashboard
- Password reset functionality
- Profile photo upload
- Age verification
- Professional information management

## Prerequisites

- Python 3.7+
- MySQL
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd assemblr
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a MySQL database:
```sql
CREATE DATABASE assemblr_db;
```

5. Configure the application:
   - Update the database connection string in `app.py`
   - Set up email configuration in `app.py` for OTP functionality
   - Create necessary directories:
     ```bash
     mkdir -p static/profile_photos
     ```

6. Initialize the database:
```bash
python
>>> from app import db
>>> db.create_all()
>>> exit()
```

7. Create an admin user:
```python
from app import db, User
from werkzeug.security import generate_password_hash

admin = User(
    username='admin',
    email='admin@example.com',
    password=generate_password_hash('admin_password'),
    first_name='Admin',
    last_name='User',
    phone='1234567890',
    address='Admin Address',
    dob='2000-01-01',
    age=23,
    profession='other',
    is_admin=True,
    is_verified=True
)

db.session.add(admin)
db.session.commit()
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Access the application at `http://localhost:5000`

## Usage

### User Registration
1. Click "Register" in the navigation bar
2. Fill in the required information
3. Upload a profile photo (optional)
4. Verify your email with the OTP
5. Complete the registration

### User Login
1. Click "Login" in the navigation bar
2. Enter your username/email/phone and password
3. Access your dashboard upon successful login

### Admin Dashboard
1. Login with admin credentials
2. View all registered users
3. Manage user accounts
4. Monitor user activity

## Security Features

- Password hashing
- OTP verification
- Age verification
- Unique constraints on username, email, and phone
- Admin-only access to sensitive features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 