from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from PIL import Image
import io
import pymysql
import random
import string
from sqlalchemy.exc import IntegrityError
from database import db, User, init_db, Organization, Event, EventRound, EventOrganizer, EventPrize, EventParticipant
from routes.event_admin import event_admin
from config import Config

pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Load configuration from Config class
app.config.from_object(Config)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'assemblrnoreply@gmail.com'
app.config['MAIL_PASSWORD'] = 'dthy pxit cqkh cvee'

# Initialize mail
mail = Mail(app)

# Register blueprints
app.register_blueprint(event_admin)

# Initialize database and migrations
try:
    init_db(app)
    migrate = Migrate(app, db)
    print("Database initialized successfully!")
except Exception as e:
    print(f"Error initializing database: {str(e)}")
    print("Please make sure:")
    print("1. MySQL server is running")
    print("2. The database 'assemblr_db' exists")
    print("3. The MySQL root password is correct")
    print("4. The user has necessary permissions")
    exit(1)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    msg = Message('Your OTP for Assemblr Registration',
                  sender='your-email@gmail.com',
                  recipients=[email])
    msg.body = f'Your OTP for registration is: {otp}'
    mail.send(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        age = int(request.form['age'])
        profession = request.form['profession']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate age
        if age < 18:
            flash('You must be at least 18 years old to register.')
            return redirect(url_for('register'))

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        # Check if username, email, or phone already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect(url_for('register'))
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already registered!')
            return redirect(url_for('register'))

        # Handle profile photo
        profile_photo = None
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file:
                # Save and process the image
                img = Image.open(file)
                # Add image processing logic here
                filename = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = os.path.join('static', 'profile_photos', filename)
                img.save(filepath)
                profile_photo = filename

        # Generate OTP
        otp = generate_otp()
        session['registration_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'phone': phone,
            'email': email,
            'address': address,
            'dob': dob,
            'age': age,
            'profession': profession,
            'password': generate_password_hash(password),
            'profile_photo': profile_photo,
            'gender': request.form['gender']
        }
        session['otp'] = otp

        # Send OTP via email
        send_otp_email(email, otp)

        return redirect(url_for('verify_otp'))

    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'registration_data' not in session:
        return redirect(url_for('register'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session['otp']:
            # Create new user
            user_data = session['registration_data']
            # Add default values for required fields
            user_data.update({
                'is_verified': True,  # Set to True since OTP is verified
                'is_admin': False,
                'created_at': datetime.utcnow(),
                'last_login': None,
                'college': None,
                'university': None,
                'degree': None,
                'graduation_year': None,
                'semester': None,
                'linkedin': None,
                'github': None,
                'college_address': None,
                'languages': None,
                'company': None,
                'education': None,
                'other_profession': None
            })
            
            # Ensure gender is not None
            if 'gender' not in user_data or user_data['gender'] is None:
                flash('Please select a gender!')
                return redirect(url_for('register'))
                
            new_user = User(**user_data)
            db.session.add(new_user)
            db.session.commit()

            # Clear session data
            session.pop('registration_data', None)
            session.pop('otp', None)

            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP! Please try again.')
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Try to find user by username, email, or phone
        user = User.query.filter(
            (User.username == username) |
            (User.email == username) |
            (User.phone == username)
        ).first()

        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Please verify your email first!')
                return redirect(url_for('login'))

            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials!')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            otp = generate_otp()
            session['reset_email'] = email
            session['reset_otp'] = otp
            send_otp_email(email, otp)
            return redirect(url_for('reset_password'))
        else:
            flash('Email not found!')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'verify_otp' in request.form:
            if request.form['otp'] == session['reset_otp']:
                return render_template('reset_password.html', show_password_form=True)
            else:
                flash('Invalid OTP!')
                return redirect(url_for('reset_password'))
        
        if 'new_password' in request.form:
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if new_password != confirm_password:
                flash('Passwords do not match!')
                return redirect(url_for('reset_password'))
            
            user = User.query.filter_by(email=session['reset_email']).first()
            user.password = generate_password_hash(new_password)
            db.session.commit()
            
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            
            flash('Password reset successful! Please login.')
            return redirect(url_for('login'))

    return render_template('reset_password.html', show_password_form=False)

@app.route('/user-dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Fetch public events
    events = Event.query.filter_by(visibility='Public').order_by(Event.created_at.desc()).all()
    
    return render_template('user_dashboard.html', events=events)


@app.route('/participate/<int:event_id>', methods=['POST'])
@login_required
def participate_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is already participating
    existing_participation = EventParticipant.query.filter_by(
        event_id=event_id, 
        user_id=current_user.id
    ).first()

    if existing_participation:
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('user_dashboard'))

    # Determine initial status based on participation mode
    initial_status = 'pending'
    if event.participation_mode == 'everyone':
        initial_status = 'approved'
    elif event.participation_mode == 'pay' and event.participation_fee == 0:
        # If it's pay but fee is 0, approve directly
        initial_status = 'approved'
        
    # Create new participation record
    new_participant = EventParticipant(
        event_id=event_id,
        user_id=current_user.id,
        status=initial_status,
        payment_status='pending' # Default payment status
    )
    
    try:
        db.session.add(new_participant)
        db.session.commit()
        if initial_status == 'approved':
             flash('Successfully registered for the event!', 'success')
        else:
             flash('Participation request submitted. Waiting for approval or payment.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('An error occurred while registering. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred: {str(e)}', 'danger')

    return redirect(url_for('user_dashboard'))

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    # Get pending organizations (email verified but not admin verified)
    pending_organizations = Organization.query.filter_by(
        is_email_verified=True,
        is_verified=False
    ).order_by(Organization.created_at.desc()).all()
    
    # Get verified organizations
    verified_organizations = Organization.query.filter_by(
        is_verified=True
    ).order_by(Organization.verified_at.desc()).all()
    
    return render_template('admin_dashboard.html',
                         pending_organizations=pending_organizations,
                         verified_organizations=verified_organizations)

@app.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin user!')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action!')
        return redirect(url_for('user_dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot change your own admin status!')
        return redirect(url_for('admin_dashboard'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Admin status {"removed from" if not user.is_admin else "granted to"} {user.username}!')
    return redirect(url_for('admin_dashboard'))

# Organization routes
@app.route('/organization/register', methods=['GET', 'POST'])
def organization_register():
    if request.method == 'POST':
        # Get form data
        org_data = {
            'org_name': request.form['org_name'],
            'org_type': request.form['org_type'],
            'registration_number': request.form['registration_number'],
            'address': request.form['address'],
            'website': request.form['website'],
            'org_email': request.form['org_email'],
            'email_domain': request.form['org_email'].split('@')[1],
            'admin_name': request.form['admin_name'],
            'designation': request.form['designation'],
            'work_email': request.form['work_email'],
            'contact_number': request.form['contact_number'],
            'description': request.form['description'],
            'linkedin': request.form['linkedin'],
            'event_categories': ','.join(request.form.getlist('event_categories')),
            'password': generate_password_hash(request.form['password']),
            'logo': None  # Initialize logo as None
        }

        # Check if organization already exists
        if Organization.query.filter_by(org_email=org_data['org_email']).first():
            flash('Organization email already registered!')
            return redirect(url_for('organization_register'))
        if Organization.query.filter_by(registration_number=org_data['registration_number']).first():
            flash('Organization with this registration number already exists!')
            return redirect(url_for('organization_register'))

        # Handle logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                filename = secure_filename(f"{org_data['org_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'org_logos', filename)
                file.save(logo_path)
                org_data['logo'] = filename

        # Generate and send OTP
        otp = generate_otp()
        session['org_registration_data'] = org_data
        session['org_otp'] = otp

        # Send OTP via email
        msg = Message('Verify your organization email',
                     sender=app.config['MAIL_USERNAME'],
                     recipients=[org_data['org_email']])
        msg.body = f'Your OTP for organization registration is: {otp}'
        mail.send(msg)

        return redirect(url_for('organization_verify_otp'))

    return render_template('organization_register.html')

@app.route('/organization/verify-otp', methods=['GET', 'POST'])
def organization_verify_otp():
    if 'org_registration_data' not in session:
        flash('Please complete the registration form first.')
        return redirect(url_for('organization_register'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session['org_otp']:
            try:
                # Create new organization
                org_data = session['org_registration_data']
                org_data['is_email_verified'] = True
                new_org = Organization(**org_data)
                db.session.add(new_org)
                db.session.commit()

                # Clear session data
                session.pop('org_registration_data', None)
                session.pop('org_otp', None)

                flash('Email verification successful! Please wait for admin verification.')
                return redirect(url_for('organization_waiting'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.')
                print(f"Error during organization registration: {str(e)}")
                return redirect(url_for('organization_register'))
        else:
            flash('Invalid OTP! Please try again.')
            return redirect(url_for('organization_verify_otp'))

    return render_template('verify_otp.html')

@app.route('/organization/waiting')
def organization_waiting():
    return render_template('organization_waiting.html')

@app.route('/organization/login', methods=['GET', 'POST'])
def organization_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        org = Organization.query.filter_by(org_email=email).first()

        if org and check_password_hash(org.password, password):
            if not org.is_email_verified:
                flash('Please verify your email first!')
                return redirect(url_for('organization_login'))
            
            if not org.is_verified:
                return redirect(url_for('organization_waiting'))
            
            session['org_id'] = org.id
            return redirect(url_for('organization_dashboard'))
        else:
            flash('Invalid credentials!')
            return redirect(url_for('organization_login'))

    return render_template('organization_login.html')

@app.route('/organization/dashboard')
def organization_dashboard():
    if 'org_id' not in session:
        return redirect(url_for('organization_login'))
    
    org = Organization.query.get(session['org_id'])
    if not org.is_verified:
        return render_template('organization_pending.html', organization=org)
    
    # Get all events for this organization
    events = Event.query.filter_by(organization_id=org.id).order_by(Event.created_at.desc()).all()
    
    return render_template('organization_dashboard.html', organization=org, events=events)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'org_id' not in session:
        flash('Please log in as an organization first.', 'warning')
        return redirect(url_for('organization_login'))

    org = Organization.query.get(session['org_id'])
    if not org:
        flash('Organization not found.', 'error')
        session.pop('org_id', None)
        return redirect(url_for('organization_login'))

    if not org.is_verified:
        flash('Your organization must be verified to create events!', 'warning')
        return redirect(url_for('organization_dashboard'))

    if request.method == 'GET':
        return render_template('create_event.html', organization=org)

    # POST request - process form data
    try:
        event_type = request.form.get('event_type')
        if not event_type:
            flash('Event Type is required.', 'error')
            return render_template('create_event.html', organization=org, **request.form)

        # Basic Event Details (Common to all types)
        event_name = request.form.get('event_name')
        description = request.form.get('event_details')
        tags = request.form.get('event_tags') # Assuming tags are comma-separated string for now
        visibility = request.form.get('event_visibility')
        registration_deadline_str = request.form.get('registration_deadline')

        if not all([event_name, description, visibility, registration_deadline_str]):
             flash('Please fill in all required basic event fields.', 'error')
             return render_template('create_event.html', organization=org, **request.form)

        registration_deadline = datetime.strptime(registration_deadline_str, '%Y-%m-%dT%H:%M')

        event = Event(
            name=event_name,
            event_type=event_type,
            organization_id=org.id,
            description=description,
            tags=tags,
            visibility=visibility,
            registration_deadline=registration_deadline,
            # --- Hackathon Specific Fields (Set defaults or get from form if type is HACKATHON) ---
            num_rounds=None,
            max_participants=None,
            min_team_size=None,
            max_team_size=None,
            event_mode=None,
            participation_mode=None,
            city=None,
            location=None,
            payment_qr=None,
            participation_fee=None
        )

        # Handle Event Banner
        if 'event_banner' in request.files:
            banner_file = request.files['event_banner']
            if banner_file and banner_file.filename:
                banner_filename = secure_filename(f"banner_{org.id}_{int(datetime.utcnow().timestamp())}_{banner_file.filename}")
                banner_path = os.path.join(app.config['UPLOAD_FOLDER'], 'event_images', banner_filename)
                banner_file.save(banner_path)
                event.banner_image = banner_filename

        # --- Process Hackathon Specific Fields --- 
        if event_type == 'HACKATHON':
            # Validate required hackathon fields
            required_hackathon_fields = [
                request.form.get('num_rounds'), request.form.get('max_participants'),
                request.form.get('min_team_size'), request.form.get('max_team_size'),
                request.form.get('event_mode'), request.form.get('participation_mode')
            ]
            if not all(required_hackathon_fields):
                flash('Please fill all required Hackathon configuration fields.', 'error')
                return render_template('create_event.html', organization=org, **request.form)

            event.num_rounds = int(request.form['num_rounds'])
            event.max_participants = int(request.form['max_participants'])
            event.min_team_size = int(request.form['min_team_size'])
            event.max_team_size = int(request.form['max_team_size'])
            event.event_mode = request.form['event_mode']
            event.participation_mode = request.form['participation_mode']

            # Location fields (if offline/hybrid)
            if event.event_mode in ['offline', 'hybrid']:
                event.city = request.form.get('city')
                event.location = request.form.get('location')
                if not event.city or not event.location:
                    flash('City and Venue Address are required for Offline/Hybrid events.', 'error')
                    return render_template('create_event.html', organization=org, **request.form)

            # Payment fields (if pay mode)
            if event.participation_mode == 'pay':
                event.participation_fee = request.form.get('participation_fee')
                if event.participation_fee:
                    try:
                        event.participation_fee = float(event.participation_fee)
                    except ValueError:
                        flash('Invalid participation fee.', 'error')
                        return render_template('create_event.html', organization=org, **request.form)

                if 'payment_qr' in request.files:
                    qr_file = request.files['payment_qr']
                    if qr_file and qr_file.filename:
                        qr_filename = secure_filename(f"qr_{org.id}_{int(datetime.utcnow().timestamp())}_{qr_file.filename}")
                        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], 'event_qrs', qr_filename)
                        qr_file.save(qr_path)
                        event.payment_qr = qr_filename
                    elif not event.payment_qr: # Require QR if payment mode is selected
                        flash('Payment QR Code is required for paid events.', 'error')
                        return render_template('create_event.html', organization=org, **request.form)
                elif not event.payment_qr: # Check if QR already exists if file not uploaded again
                     flash('Payment QR Code is required for paid events.', 'error')
                     return render_template('create_event.html', organization=org, **request.form)

        # --- Save Event and Related Data --- 
        db.session.add(event)
        db.session.flush()  # Get the event ID before adding related items

        # Add Rounds (Only if Hackathon)
        if event_type == 'HACKATHON' and event.num_rounds:
            round_starts = request.form.getlist('round_start_time[]')
            round_ends = request.form.getlist('round_end_time[]')
            round_results = request.form.getlist('round_results_date[]')

            if len(round_starts) == event.num_rounds and len(round_ends) == event.num_rounds and len(round_results) == event.num_rounds:
                for i in range(event.num_rounds):
                    try:
                        start_time = datetime.strptime(round_starts[i], '%Y-%m-%dT%H:%M')
                        end_time = datetime.strptime(round_ends[i], '%Y-%m-%dT%H:%M')
                        result_date = datetime.strptime(round_results[i], '%Y-%m-%dT%H:%M')

                        round_entry = EventRound(
                            event_id=event.id,
                            round_number=i + 1,
                            start_time=start_time,
                            end_time=end_time,
                            result_date=result_date
                        )
                        db.session.add(round_entry)
                    except ValueError:
                        db.session.rollback()
                        flash(f'Invalid date format for round {i+1}. Please use YYYY-MM-DDTHH:MM.', 'error')
                        return render_template('create_event.html', organization=org, **request.form)
            else:
                db.session.rollback()
                flash('Mismatch between number of rounds specified and round details provided.', 'error')
                return render_template('create_event.html', organization=org, **request.form)

        # Add Organizers (Only if Hackathon)
        if event_type == 'HACKATHON':
            organizer_names = request.form.getlist('organizer_name[]')
            organizer_designations = request.form.getlist('organizer_designation[]')
            organizer_phones = request.form.getlist('organizer_phone[]')
            organizer_emails = request.form.getlist('organizer_email[]')

            # Basic validation: check if all lists have the same length and are not empty if provided
            if len(organizer_names) > 0 and len(organizer_names) == len(organizer_designations) == len(organizer_phones) == len(organizer_emails):
                for i in range(len(organizer_names)):
                    # Add more specific validation if needed (e.g., non-empty strings)
                    if organizer_names[i] and organizer_designations[i] and organizer_phones[i] and organizer_emails[i]:
                        organizer = EventOrganizer(
                            event_id=event.id,
                            name=organizer_names[i],
                            designation=organizer_designations[i],
                            phone=organizer_phones[i],
                            email=organizer_emails[i]
                        )
                        db.session.add(organizer)
                    else:
                        db.session.rollback()
                        flash(f'Incomplete details for organizer #{i+1}. All fields are required.', 'error')
                        return render_template('create_event.html', organization=org, **request.form)
            elif len(organizer_names) > 0: # If names list is not empty, but lengths mismatch
                db.session.rollback()
                flash('Mismatch in organizer details provided.', 'error')
                return render_template('create_event.html', organization=org, **request.form)
            # else: No organizers provided, which might be acceptable

        # Add Prizes (Only if Hackathon)
        if event_type == 'HACKATHON':
            prize_positions = request.form.getlist('prize_position[]')
            prize_types = request.form.getlist('prize_type[]')
            prize_descriptions = request.form.getlist('prize_description[]') # Changed from prize_details

            if len(prize_positions) > 0 and len(prize_positions) == len(prize_types) == len(prize_descriptions):
                for i in range(len(prize_positions)):
                    if prize_positions[i] and prize_types[i] and prize_descriptions[i]:
                        prize = EventPrize(
                            event_id=event.id,
                            position=prize_positions[i],
                            reward_type=prize_types[i],
                            reward_details=prize_descriptions[i] # Changed from reward_details
                        )
                        db.session.add(prize)
                    else:
                        db.session.rollback()
                        flash(f'Incomplete details for prize #{i+1}. All fields are required.', 'error')
                        return render_template('create_event.html', organization=org, **request.form)
            elif len(prize_positions) > 0:
                db.session.rollback()
                flash('Mismatch in prize details provided.', 'error')
                return render_template('create_event.html', organization=org, **request.form)
            # else: No prizes provided, which might be acceptable

        # --- Final Commit --- 
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('organization_dashboard'))

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Database Integrity Error creating event: {e}")
        flash('Database error. Could there be a duplicate entry?', 'error')
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f"Value Error creating event: {e}")
        flash(f'Invalid input value: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating event: {e}", exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'error')

    # If any error occurred, render the form again with submitted data
    return render_template('create_event.html', organization=org, **request.form)

# Admin organization management routes
@app.route('/verify-organization/<int:org_id>', methods=['POST'])
@login_required
def verify_organization(org_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action!')
        return redirect(url_for('user_dashboard'))
    
    org = Organization.query.get_or_404(org_id)
    org.is_verified = True
    org.verified_at = datetime.utcnow()
    org.verified_by = current_user.id
    db.session.commit()

    # Send verification email
    msg = Message('Organization Verification Successful',
                 sender=app.config['MAIL_USERNAME'],
                 recipients=[org.org_email])
    msg.body = f'Congratulations! Your organization {org.org_name} has been verified. You can now login and start hosting events.'
    mail.send(msg)
    
    flash(f'Organization {org.org_name} has been verified!')
    return redirect(url_for('admin_dashboard'))

@app.route('/revoke-organization/<int:org_id>', methods=['POST'])
@login_required
def revoke_organization(org_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action!')
        return redirect(url_for('user_dashboard'))
    
    org = Organization.query.get_or_404(org_id)
    org.is_verified = False
    org.verified_at = None
    org.verified_by = None
    db.session.commit()

    # Send revocation email
    msg = Message('Organization Verification Revoked',
                 sender=app.config['MAIL_USERNAME'],
                 recipients=[org.org_email])
    msg.body = f'Your organization {org.org_name} verification has been revoked. Please contact support for more information.'
    mail.send(msg)
    
    flash(f'Organization {org.org_name} verification has been revoked!')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete-organization/<int:org_id>', methods=['POST'])
@login_required
def delete_organization(org_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action!')
        return redirect(url_for('user_dashboard'))
    
    org = Organization.query.get_or_404(org_id)
    
    # Delete logo file if exists
    if org.logo:
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'org_logos', org.logo)
        if os.path.exists(logo_path):
            os.remove(logo_path)
    
    db.session.delete(org)
    db.session.commit()
    
    flash(f'Organization {org.org_name} has been deleted!')
    return redirect(url_for('admin_dashboard'))

# Create upload directories
def create_upload_directories():
    # Create main uploads directory
    uploads_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Create subdirectories
    subdirs = ['org_logos', 'profile_photos', 'event_images', 'event_qrs']
    for subdir in subdirs:
        subdir_path = os.path.join(uploads_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)

# Create upload directories
create_upload_directories()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)