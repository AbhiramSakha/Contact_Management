
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('app.secret_key')  # Keep this strong and secret

USERS_FILE = 'users.json'
CONTACTS_FILE = 'contacts.json'

def load_data(file):
    """Loads data from a JSON file."""
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                content = f.read()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            print(f"Warning: {file} is empty or contains invalid JSON. Initializing with empty data.")
            return {}
    return {}

def save_data(file, data):
    """Saves data to a JSON file."""
    try:
        with open(file, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving data to {file}: {e}")
        flash('An error occurred while saving data.', 'error')

@app.route('/')
def home():
    """Redirects to the login page."""
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration without phone verification."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        users = load_data(USERS_FILE)

        if username in users:
            flash('Username already exists! Please choose a different one.', 'error')
            return render_template('register.html')
        else:
            hashed_password = generate_password_hash(password)
            users[username] = {
                'password': hashed_password,
            }
            save_data(USERS_FILE, users)
            flash('Registered successfully! Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login without phone verification."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_data(USERS_FILE)

        user_data = users.get(username)

        if user_data and 'password' in user_data and check_password_hash(user_data['password'], password):
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Displays the user's dashboard with contacts."""
    if 'user' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))

    username = session['user']
    
    all_contacts = load_data(CONTACTS_FILE)
    user_contacts = all_contacts.get(username, {})

    # Corrected: Pass user_contacts directly as it's already a dictionary
    return render_template('dashboard.html', username=username, contacts=user_contacts)

@app.route('/add', methods=['POST'])
def add_contact():
    """Adds a new contact for the logged-in user."""
    if 'user' not in session:
        flash('Please log in to add contacts.', 'error')
        return redirect(url_for('login'))

    username = session['user']
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    email = request.form['email'].strip()
    address = request.form['address'].strip()

    if not name or not phone or not email:
        flash('Name, Phone, and Email are required fields.', 'error')
        return redirect(url_for('dashboard'))

    all_contacts = load_data(CONTACTS_FILE)
    user_contacts = all_contacts.get(username, {})

    if name in user_contacts:
        flash(f'Contact with the name "{name}" already exists. Please use a unique name or edit the existing contact.', 'error')
    else:
        user_contacts[name] = {
            'phone': phone,
            'email': email,
            'address': address
        }
        all_contacts[username] = user_contacts
        save_data(CONTACTS_FILE, all_contacts)
        flash('Contact added successfully!', 'success')

    return redirect(url_for('dashboard'))

@app.route('/delete/<string:name>', methods=['POST'])
def delete_contact(name):
    """Deletes a contact for the logged-in user."""
    if 'user' not in session:
        flash('Please log in to delete contacts.', 'error')
        return redirect(url_for('login'))

    username = session['user']
    all_contacts = load_data(CONTACTS_FILE)
    user_contacts = all_contacts.get(username, {})

    if name in user_contacts:
        del user_contacts[name]
        all_contacts[username] = user_contacts
        save_data(CONTACTS_FILE, all_contacts)
        flash(f'Contact "{name}" deleted.', 'success')
    else:
        flash(f'Contact "{name}" not found.', 'error')

    return redirect(url_for('dashboard'))

@app.route('/delete_my_account', methods=['POST'])
def delete_my_account():
    """Deletes the logged-in user's account and all associated data."""
    if 'user' not in session:
        flash('Please log in to delete your account.', 'error')
        return redirect(url_for('login'))

    username = session['user']
    users = load_data(USERS_FILE)
    all_contacts = load_data(CONTACTS_FILE)

    if username in users:
        del users[username]
        save_data(USERS_FILE, users)
        
        if username in all_contacts:
            del all_contacts[username]
            save_data(CONTACTS_FILE, all_contacts)
        
        session.clear()
        flash('Your account and all associated contacts have been successfully deleted.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Account not found.', 'error')
        session.clear() # Clear session even if not found to prevent stale state
        return redirect(url_for('login'))

@app.route('/logout', methods=['POST'])
def logout():
    """Logs out the current user."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
