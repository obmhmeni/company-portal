from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import string
import random
import re
import hashlib
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_123'

def init_db():
    try:
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            print("LOG: Initializing database tables...")
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                full_name TEXT, mother_name TEXT, father_name TEXT, gender TEXT,
                age INTEGER, date_of_birth TEXT, education TEXT, subject TEXT,
                schooling_location TEXT, residential_area TEXT, skills TEXT,
                work_area TEXT, relocate TEXT, role TEXT, other_district TEXT,
                salary TEXT, gov_job TEXT, house_no TEXT, ward_no TEXT,
                police_station TEXT, chowki TEXT, subdistrict TEXT, district TEXT,
                state TEXT, pin TEXT, contact TEXT, rooms TEXT, room_details TEXT,
                disabled_member TEXT, disabled_details TEXT, self_disabled TEXT,
                interest TEXT, payment_status TEXT, recruited_by TEXT,
                worker_id TEXT, worker_password TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS workers (
                username TEXT PRIMARY KEY, password TEXT, is_wkw INTEGER DEFAULT 0
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS otp_verifications (
                phone_number TEXT PRIMARY KEY, otp TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            c.execute("INSERT OR IGNORE INTO workers (username, password) VALUES (?, ?)",
                      ('admin', 'admin123'))
            c.execute("INSERT OR IGNORE INTO workers (username, password) VALUES (?, ?)",
                      ('worker1', 'pass123'))
            conn.commit()
            print("LOG: Database initialized successfully: users, workers, otp_verifications tables created")
    except Exception as e:
        print(f"LOG: Database initialization error: {str(e)}")

def generate_unique_id():
    characters = string.ascii_letters + string.digits + "!@#%^&*"
    while True:
        unique_id = ''.join(random.choice(characters) for _ in range(22))
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#%^&*]).{22}$', unique_id):
            continue
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE id = ?", (unique_id,))
            if not c.fetchone():
                print(f"LOG: Generated unique ID: {unique_id}")
                return unique_id

def generate_worker_credentials(full_name, dob, contact, unique_id):
    base = f"{full_name[:3]}{dob.replace('-', '')}{contact[-4:]}{unique_id[:4]}"
    worker_id = hashlib.md5(base.encode()).hexdigest()[:18]
    password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(password_chars) for _ in range(12))
    print(f"LOG: Generated worker credentials - ID: {worker_id}, Password: {password}")
    return worker_id, password

def check_otp(phone_number, otp):
    try:
        print(f"LOG: Verifying OTP for {phone_number}: {otp}")
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT otp, timestamp FROM otp_verifications WHERE phone_number = ?", (phone_number,))
            result = c.fetchone()
            if result:
                stored_otp, timestamp = result
                print(f"LOG: Found OTP {stored_otp} with timestamp {timestamp} for {phone_number}")
                otp_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
                current_time = datetime.now(pytz.UTC)
                if (current_time - otp_time).total_seconds() > 300:
                    c.execute("DELETE FROM otp_verifications WHERE phone_number = ?", (phone_number,))
                    conn.commit()
                    print(f"LOG: OTP expired for {phone_number}")
                    return False
                if stored_otp == otp:
                    c.execute("DELETE FROM otp_verifications WHERE phone_number = ?", (phone_number,))
                    conn.commit()
                    print(f"LOG: OTP verified successfully for {phone_number}")
                    return True
                else:
                    print(f"LOG: OTP mismatch for {phone_number}. Stored: {stored_otp}, Provided: {otp}")
                    return False
            else:
                print(f"LOG: No OTP found for {phone_number}")
                return False
    except Exception as e:
        print(f"LOG: OTP verification error: {str(e)}")
        return False

@app.route('/')
def home():
    print("LOG: Rendering home page")
    return render_template('home.html', results=[])

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'worker' not in session and 'admin' not in session:
        print("LOG: No worker or admin session, redirecting to worker_login")
        flash('Please log in first', 'error')
        return redirect(url_for('worker_login'))
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        user_otp = request.form.get('otp')
        print(f"LOG: Verifying OTP for {phone_number}: {user_otp}")
        if check_otp(phone_number, user_otp):
            session['otp_verified'] = True
            session['phone_number'] = phone_number
            print("LOG: OTP verification successful, redirecting to register")
            flash('OTP verified successfully.', 'success')
            return redirect(url_for('register'))
        else:
            print("LOG: OTP verification failed, rendering verify_otp.html")
            flash('Invalid or expired OTP.', 'error')
            return render_template('verify_otp.html')
    print("LOG: Rendering verify_otp.html for GET request")
    return render_template('verify_otp.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'worker' not in session and 'admin' not in session:
        print("LOG: No worker or admin session, redirecting to worker_login")
        flash('Please log in first', 'error')
        return redirect(url_for('worker_login'))
    if not session.get('otp_verified'):
        print("LOG: OTP not verified, redirecting to verify_otp")
        flash('Please verify your mobile number with OTP.', 'error')
        return redirect(url_for('verify_otp'))
    if request.method == 'POST':
        print(f"LOG: Received form data: {request.form}")
        required_fields = [
            'full_name', 'mother_name', 'father_name', 'gender', 'age',
            'date_of_birth', 'education', 'schooling_location', 'residential_area',
            'skills', 'work_area', 'relocate', 'role', 'other_district', 'salary',
            'gov_job', 'house_no', 'ward_no', 'police_station', 'subdistrict',
            'district', 'state', 'pin', 'contact', 'rooms', 'disabled_member',
            'self_disabled', 'interest', 'payment_status'
        ]
        for field in required_fields:
            if field not in request.form or not request.form[field]:
                print(f"LOG: Missing or empty required field: {field}")
                flash(f'Missing or empty required field: {field}', 'error')
                return redirect(url_for('register'))
        dob = request.form['date_of_birth']
        try:
            datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            print("LOG: Invalid Date of Birth format")
            flash('Invalid Date of Birth format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('register'))
        if 'worker' in session and request.form.get('payment_status') != 'Paid':
            print("LOG: Worker registration requires payment_status=Paid")
            flash('Payment of ₹20 must be marked as Paid for workers.', 'error')
            return redirect(url_for('register'))
        if request.form['contact'] != session.get('phone_number'):
            print("LOG: Phone number does not match OTP-verified number")
            flash('Phone number does not match OTP-verified number.', 'error')
            return redirect(url_for('register'))
        if request.form['education'] in ['Bachelors', 'PhD'] and not request.form.get('subject'):
            print("LOG: Subject required for Bachelors or PhD")
            flash('Subject is required for Bachelors or PhD.', 'error')
            return redirect(url_for('register'))
        try:
            unique_id = generate_unique_id()
            worker_id, worker_password = ('', '')
            if request.form['interest'] == 'Yes' and request.form.get('payment_status') == 'Paid':
                worker_id, worker_password = generate_worker_credentials(
                    request.form['full_name'], dob, request.form['contact'], unique_id
                )
                with sqlite3.connect('data.db') as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO workers (username, password, is_wkw) VALUES (?, ?, ?)",
                              (worker_id, worker_password, 1))
                    conn.commit()
                    print(f"LOG: New worker added: {worker_id}")
            data = {
                'id': unique_id,
                'full_name': request.form['full_name'],
                'mother_name': request.form['mother_name'],
                'father_name': request.form['father_name'],
                'gender': request.form['gender'],
                'age': request.form['age'],
                'date_of_birth': dob,
                'education': request.form['education'],
                'subject': request.form.get('subject', ''),
                'schooling_location': request.form['schooling_location'],
                'residential_area': request.form['residential_area'],
                'skills': request.form['skills'],
                'work_area': request.form['work_area'],
                'relocate': request.form['relocate'],
                'role': request.form['role'],
                'other_district': request.form['other_district'],
                'salary': request.form['salary'],
                'gov_job': request.form['gov_job'],
                'house_no': request.form['house_no'],
                'ward_no': request.form['ward_no'],
                'police_station': request.form['police_station'],
                'chowki': request.form.get('chowki', ''),
                'subdistrict': request.form['subdistrict'],
                'district': request.form['district'],
                'state': request.form['state'],
                'pin': request.form['pin'],
                'contact': request.form['contact'],
                'rooms': request.form['rooms'],
                'room_details': ','.join([
                    request.form.get('rent', ''),
                    request.form.get('advance', ''),
                    request.form.get('area', '')
                ]) if request.form['rooms'] == 'Yes' else '',
                'disabled_member': request.form['disabled_member'],
                'disabled_details': ','.join([
                    request.form.get('disabled_name', ''),
                    request.form.get('disabled_mother_name', ''),
                    request.form.get('disabled_father_name', ''),
                    request.form.get('disabled_education', ''),
                    request.form.get('disabled_schooling_location', ''),
                    request.form.get('disabled_residential_area', ''),
                    request.form.get('disabled_address', ''),
                    request.form.get('disabled_contact', '')
                ]) if request.form['disabled_member'] == 'Yes' else '',
                'self_disabled': request.form['self_disabled'],
                'interest': request.form['interest'],
                'payment_status': request.form['payment_status'],
                'recruited_by': session.get('worker', session.get('admin', '')),
                'worker_id': worker_id,
                'worker_password': worker_password
            }
            print(f"LOG: Inserting user data: {data}")
            with sqlite3.connect('data.db') as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO users VALUES (
                    :id, :full_name, :mother_name, :father_name, :gender,
                    :age, :date_of_birth, :education, :subject, :schooling_location,
                    :residential_area, :skills, :work_area, :relocate, :role,
                    :other_district, :salary, :gov_job, :house_no, :ward_no,
                    :police_station, :chowki, :subdistrict, :district, :state,
                    :pin, :contact, :rooms, :room_details, :disabled_member,
                    :disabled_details, :self_disabled, :interest, :payment_status,
                    :recruited_by, :worker_id, :worker_password
                )''', data)
                conn.commit()
                print("LOG: User data inserted successfully")
            flash(f'Registration successful! Your Unique ID: {unique_id}' +
                  (f' | Worker ID: {worker_id}, Password: {worker_password}' if worker_id else ''), 'success')
            session.pop('otp_verified', None)
            session.pop('phone_number', None)
            print("LOG: Registration complete, redirecting to home")
            return redirect(url_for('home'))
        except Exception as e:
            print(f"LOG: Registration error: {str(e)}")
            flash(f'Error saving data: {str(e)}', 'error')
            return redirect(url_for('register'))
    print("LOG: Rendering register.html for GET request")
    return render_template('register.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        print(f"LOG: Searching for ID: {search_term}")
        if search_term:
            with sqlite3.connect('data.db') as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE id = ?", (search_term,))
                results = c.fetchall()
                print(f"LOG: Search results: {results}")
            if not results:
                print("LOG: No users found for ID")
                flash('No user found with this ID', 'error')
            else:
                print("LOG: User found, rendering results")
                flash('User found!', 'success')
        else:
            print("LOG: No search term provided")
            flash('Please enter a user ID', 'error')
    print("LOG: Rendering home.html with search results")
    return render_template('home.html', results=results)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"LOG: Admin login attempt: {username}")
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM workers WHERE username = ? AND password = ?",
                      (username, password))
            user = c.fetchone()
            print(f"LOG: Admin login result: {user}")
            if user:
                session['admin'] = username
                print("LOG: Admin login successful, redirecting to admin_dashboard")
                flash('Admin login successful', 'success')
                return redirect(url_for('admin_dashboard'))
            print("LOG: Invalid admin credentials")
            flash('Invalid credentials', 'error')
    print("LOG: Rendering login.html for admin")
    return render_template('login.html', role='Admin')

@app.route('/worker_login', methods=['GET', 'POST'])
def worker_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"LOG: Worker login attempt: {username}, {password}")
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM workers WHERE username = ? AND password = ?",
                      (username, password))
            user = c.fetchone()
            print(f"LOG: Worker found: {user}")
            if user:
                session['worker'] = username
                print("LOG: Worker login successful, redirecting to verify_otp")
                flash('Worker login successful', 'success')
                return redirect(url_for('verify_otp'))
            print("LOG: Invalid worker credentials")
            flash('Invalid credentials', 'error')
    print("LOG: Rendering login.html for worker")
    return render_template('login.html', role='Worker')

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        print("LOG: No admin session, redirecting to admin_login")
        flash('Please log in as admin', 'error')
        return redirect(url_for('admin_login'))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    with sqlite3.connect('data.db') as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        print(f"LOG: Total users: {total_users}")
        c.execute("SELECT * FROM users LIMIT ? OFFSET ?", (per_page, (page-1)*per_page))
        users = c.fetchall()
        print(f"LOG: Users fetched for page {page}: {users}")
        c.execute("SELECT username, is_wkw FROM workers")
        workers = c.fetchall()
        print(f"LOG: Workers fetched: {workers}")
        worker_stats = []
        for worker in workers:
            username, is_wkw = worker
            c.execute("SELECT COUNT(*) FROM users WHERE recruited_by = ?", (username,))
            total_added = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE recruited_by = ? AND payment_status = 'Paid'", (username,))
            paid_added = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE recruited_by = ? AND worker_id != ''", (username,))
            wkw_added = c.fetchone()[0]
            worker_stats.append({
                'username': username,
                'is_wkw': is_wkw,
                'total_added': total_added,
                'paid_added': paid_added,
                'wkw_added': wkw_added
            })
        print(f"LOG: Worker stats: {worker_stats}")
    print(f"LOG: Rendering admin.html for page {page}")
    return render_template('admin.html', users=users, page=page, total=total_users,
                          per_page=per_page, worker_stats=worker_stats)

@app.route('/logout')
def logout():
    print("LOG: Logging out, clearing session")
    session.pop('admin', None)
    session.pop('worker', None)
    session.pop('otp_verified', None)
    session.pop('phone_number', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    print("LOG: Starting Flask app...")
    init_db()
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
