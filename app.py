from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                     (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('profile', username=username))
        except sqlite3.IntegrityError:
            flash('Username already exists!')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get user info
    c.execute('SELECT id, username FROM users WHERE username = ?', (username,))
    user = c.execute('SELECT id, username FROM users WHERE username = ?', (username,)).fetchone()
    
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file selected')
            return redirect(request.url)
            
        file = request.files['photo']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            c.execute('INSERT INTO photos (user_id, filename) VALUES (?, ?)',
                     (user[0], filename))
            conn.commit()
            flash('Photo uploaded successfully!')
            
    # Get user's photos
    c.execute('SELECT filename FROM photos WHERE user_id = ?', (user[0],))
    photos = c.execute('SELECT filename FROM photos WHERE user_id = ?', (user[0],)).fetchall()
    conn.close()
    
    return render_template('profile.html', username=username, photos=photos)

if __name__ == '__main__':
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True) 