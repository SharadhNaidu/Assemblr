from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profile_photo = db.Column(db.String(255))
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    profession = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Student specific fields
    college = db.Column(db.String(100))
    university = db.Column(db.String(100))
    degree = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)
    semester = db.Column(db.Integer)
    linkedin = db.Column(db.String(255))
    github = db.Column(db.String(255))
    college_address = db.Column(db.String(255))
    languages = db.Column(db.String(255))

    # Employee specific fields
    company = db.Column(db.String(100))
    education = db.Column(db.String(255))

    # Other profession fields
    other_profession = db.Column(db.String(100))

    def __repr__(self):
        return f'<User {self.username}>'

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.String(100), nullable=False)
    org_type = db.Column(db.String(50), nullable=False)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=False)
    website = db.Column(db.String(255), nullable=True)
    org_email = db.Column(db.String(120), unique=True, nullable=False)
    email_domain = db.Column(db.String(100), nullable=False)
    admin_name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    work_email = db.Column(db.String(120), unique=True, nullable=False)
    contact_number = db.Column(db.String(15), unique=True, nullable=False)
    logo = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    linkedin = db.Column(db.String(255), nullable=True)
    event_categories = db.Column(db.String(500), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Organization {self.org_name}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255))  # Added tags field for event categorization
    visibility = db.Column(db.String(20))  # Public, Private
    registration_deadline = db.Column(db.DateTime)  # Deadline for registration
    banner_image = db.Column(db.String(255))  # Path to banner image
    participation_fee = db.Column(db.Float)  # Fee for participation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Hackathon specific fields
    num_rounds = db.Column(db.Integer)
    max_participants = db.Column(db.Integer)
    min_team_size = db.Column(db.Integer)
    max_team_size = db.Column(db.Integer)
    event_mode = db.Column(db.String(20))  # online, offline, hybrid
    city = db.Column(db.String(100))
    location = db.Column(db.String(255))
    participation_mode = db.Column(db.String(20))  # approval, everyone, pay
    payment_qr = db.Column(db.String(255))  # Path to QR code image
    event_details = db.Column(db.Text)
    
    # Relationships
    rounds = db.relationship('EventRound', backref='event', lazy=True, cascade='all, delete-orphan')
    organizers = db.relationship('EventOrganizer', backref='event', lazy=True, cascade='all, delete-orphan')
    prizes = db.relationship('EventPrize', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.name}>'

class EventRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    result_date = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<Round {self.round_number} of Event {self.event_id}>'

class EventOrganizer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    def __repr__(self):
        return f'<Organizer {self.name} for Event {self.event_id}>'

class EventPrize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    position = db.Column(db.String(50), nullable=False)  # 1st, 2nd, 3rd, etc.
    reward_type = db.Column(db.String(20), nullable=False)  # money, gift
    reward_details = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<Prize {self.position} for Event {self.event_id}>'

class EventParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_name = db.Column(db.String(100))
    team_members = db.Column(db.String(500))  # JSON string of team member user IDs
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, verified
    payment_qr = db.Column(db.String(255))  # Path to payment QR image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref='participants')
    user = db.relationship('User', backref='event_participations')
    
    def __repr__(self):
        return f'<EventParticipant {self.id} for Event {self.event_id}>'

class EventSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('event_participant.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    submission_url = db.Column(db.String(255))
    submission_file = db.Column(db.String(255))  # Path to uploaded file
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, accepted, rejected
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref='submissions')
    participant = db.relationship('EventParticipant', backref='submissions')
    
    def __repr__(self):
        return f'<EventSubmission {self.id} for Round {self.round_number}>'

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists, if not create one
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin_password'),
                first_name='Admin',
                last_name='User',
                phone='1234567890',
                gender='other',
                address='Admin Address',
                dob=datetime.strptime('2000-01-01', '%Y-%m-%d'),
                age=23,
                profession='other',
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")

        # Add dummy events if none exist
        if Event.query.count() == 0:
            print("Adding dummy events...")
            org = Organization.query.first() # Use the first available org, or create one if needed
            if not org:
                # Create a dummy org if none exists (adjust details as needed)
                org = Organization(
                    org_name='Dummy Org',
                    org_type='Community',
                    registration_number='DUMMY123',
                    address='123 Dummy St',
                    org_email='dummy@org.com',
                    email_domain='org.com',
                    admin_name='Dummy Admin',
                    designation='Manager',
                    work_email='admin@dummy.com',
                    contact_number='9876543210',
                    description='A dummy organization for testing.',
                    event_categories='Tech, Fun',
                    password=generate_password_hash('dummy_password'), # Use a secure hash
                    is_verified=True, # Assume verified for simplicity
                    is_email_verified=True
                )
                db.session.add(org)
                db.session.commit()
                print("Dummy organization created.")
                org = Organization.query.first() # Re-fetch the org with its ID

            event1 = Event(
                name='Annual Hackathon 2024',
                event_type='Hackathon',
                organization_id=org.id, 
                description='Join us for 24 hours of coding!',
                tags='coding, tech, innovation',
                visibility='Public',
                registration_deadline=datetime(2024, 8, 15, 23, 59),
                participation_fee=0.0,
                num_rounds=3,
                max_participants=100,
                min_team_size=2,
                max_team_size=4,
                event_mode='online',
                participation_mode='everyone'
            )
            event2 = Event(
                name='Tech Workshop Series',
                event_type='Workshop',
                organization_id=org.id, 
                description='Learn the latest in web development.',
                tags='webdev, workshop, learning',
                visibility='Public',
                registration_deadline=datetime(2024, 9, 1, 18, 00),
                participation_fee=10.0,
                event_mode='hybrid',
                city='Tech City',
                location='Online and Main Hall',
                participation_mode='pay',
                payment_qr='path/to/dummy_qr.png' # Placeholder
            )
            event3 = Event(
                name='Community Meetup',
                event_type='Meetup',
                organization_id=org.id, 
                description='Network with local tech enthusiasts.',
                tags='networking, community',
                visibility='Public',
                participation_fee=0.0,
                event_mode='offline',
                city='Local Town',
                location='Community Center',
                participation_mode='approval'
            )
            db.session.add_all([event1, event2, event3])
            db.session.commit()
            print("Dummy events added successfully.")