import sqlite3
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, g
from werkzeug.security import check_password_hash, generate_password_hash
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_final_v3' # Change this in a real application

# --- Session Cookie Configuration for Security ---
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

INVENTORY_DB = 'inventory.db'
USERS_DB = 'users.db'
LOG_DB = 'log.db'

# --- Database Helper Functions ---
def get_db(db_name):
    db_attr = f'_database_{db_name.replace(".db", "")}'
    if not hasattr(g, db_attr):
        setattr(g, db_attr, sqlite3.connect(db_name))
        getattr(g, db_attr).row_factory = sqlite3.Row
    return getattr(g, db_attr)

@app.teardown_appcontext
def close_connections(exception):
    for attr in dir(g):
        if attr.startswith('_database_'):
            getattr(g, attr).close()

def init_db(db_name, schema_name):
    with app.app_context():
        db = get_db(db_name)
        with app.open_resource(schema_name, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- Logging Function ---
def log_action(action, details=""):
    log_db = get_db(LOG_DB)
    log_db.execute(
        "INSERT INTO audit_log (user_id, username, action, details) VALUES (?, ?, ?, ?)",
        (session.get('user_id'), session.get('username'), action, details)
    )
    log_db.commit()

# --- Permission Check Functions ---
def is_admin_or_director():
    return session.get('role') in ['admin', 'director']

def is_director():
    return session.get('role') == 'director'

# --- Main Application Routes ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    db = get_db(USERS_DB)
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if user and user['status'] == 'suspended':
        return jsonify({'success': False, 'message': 'Your account is suspended.'}), 403

    if user and check_password_hash(user['password'], password):
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True
        log_action("USER_LOGIN")
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    log_action("USER_LOGOUT")
    session.clear()
    return jsonify({'success': True})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('index.html', user_role=session.get('role'), user_id=session.get('user_id'))

# --- User Management API (Director Only) ---
@app.route('/api/users', methods=['GET'])
def get_users():
    if not is_director():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db(USERS_DB)
    users = db.execute("SELECT id, username, role, status FROM users ORDER BY username").fetchall()
    return jsonify([dict(user) for user in users])

@app.route('/api/users', methods=['POST'])
def create_user():
    if not is_director():
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not all([username, password, role]):
        return jsonify({"error": "Missing data"}), 400
    if role not in ['director', 'admin', 'viewer']:
        return jsonify({"error": "Invalid role"}), 400

    hashed_password = generate_password_hash(password)
    db = get_db(USERS_DB)
    try:
        cur = db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                         (username, hashed_password, role))
        db.commit()
        new_user_id = cur.lastrowid
        log_action("USER_CREATED", f"Created user '{username}' with role '{role}'.")
        new_user = db.execute("SELECT id, username, role, status FROM users WHERE id = ?", (new_user_id,)).fetchone()
        return jsonify(dict(new_user)), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if not is_director():
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password') # Optional
    role = data.get('role')
    
    db = get_db(USERS_DB)
    user_to_edit = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user_to_edit:
        return jsonify({"error": "User not found"}), 404

    if user_to_edit['role'] == 'director' and user_id == session.get('user_id') and role != 'director':
        return jsonify({"error": "You cannot change your own role from director."}), 403

    update_fields = []
    params = []
    log_details = f"Updated user '{user_to_edit['username']}' (ID: {user_id}):"

    if username and username != user_to_edit['username']:
        update_fields.append("username = ?")
        params.append(username)
        log_details += f" username changed to '{username}',"

    if password:
        update_fields.append("password = ?")
        params.append(generate_password_hash(password))
        log_details += " password changed,"

    if role and role != user_to_edit['role']:
        update_fields.append("role = ?")
        params.append(role)
        log_details += f" role changed to '{role}',"

    if not update_fields:
        return jsonify({"error": "No changes provided"}), 400

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    
    try:
        db.execute(query, tuple(params))
        db.commit()
        log_action("USER_UPDATED", log_details.strip(','))
        updated_user = db.execute("SELECT id, username, role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        return jsonify(dict(updated_user))
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409

@app.route('/api/users/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    if not is_director():
        return jsonify({"error": "Forbidden"}), 403
    if user_id == session.get('user_id'):
        return jsonify({"error": "You cannot change your own status."}), 403
        
    data = request.get_json()
    status = data.get('status')
    if status not in ['active', 'suspended']:
        return jsonify({"error": "Invalid status"}), 400

    db = get_db(USERS_DB)
    db.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
    db.commit()
    log_action("USER_STATUS_CHANGED", f"Set status for user ID {user_id} to '{status}'.")
    return jsonify({"success": True})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not is_director():
        return jsonify({"error": "Forbidden"}), 403
    if user_id == session.get('user_id'):
        return jsonify({"error": "You cannot delete your own account."}), 403

    db = get_db(USERS_DB)
    user_to_delete = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_to_delete:
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        log_action("USER_DELETED", f"Deleted user '{user_to_delete['username']}' (ID: {user_id}).")
    return jsonify({"success": True})

# --- Inventory Management API ---
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db(INVENTORY_DB)
    
    base_query = 'SELECT id, item, color, grade, batch_no, sqm FROM inventory'
    conditions = []
    params = []
    
    search_fields = ['item', 'color', 'grade', 'batch_no']
    for field in search_fields:
        value = request.args.get(field)
        if value:
            conditions.append(f"{field} LIKE ?")
            params.append(f'%{value}%')
            
    if conditions:
        query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY id"
    else:
        query = f"{base_query} ORDER BY id"

    items_from_db = db.execute(query, tuple(params)).fetchall()
    
    sequenced_items = []
    for i, item in enumerate(items_from_db):
        item_dict = dict(item)
        item_dict['sr_no'] = i + 1
        sequenced_items.append(item_dict)
        
    return jsonify(sequenced_items)

@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    if not is_admin_or_director():
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    db = get_db(INVENTORY_DB)
    cur = db.execute('INSERT INTO inventory (item, color, grade, batch_no, sqm) VALUES (?, ?, ?, ?, ?)',
                     [data['item'], data['color'], data['grade'], data['batch_no'], float(data['sqm'])])
    db.commit()
    new_id = cur.lastrowid
    log_action("INVENTORY_ADD", f"Added new item (ID: {new_id}) with details: {data}.")
    new_item = db.execute('SELECT * FROM inventory WHERE id = ?', [new_id]).fetchone()
    return jsonify(dict(new_item)), 201

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    if not is_admin_or_director():
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    db = get_db(INVENTORY_DB)
    
    old_item = db.execute('SELECT * FROM inventory WHERE id = ?', [item_id]).fetchone()
    if not old_item:
        return jsonify({"error": "Item not found"}), 404

    db.execute('UPDATE inventory SET item = ?, color = ?, grade = ?, batch_no = ?, sqm = ? WHERE id = ?',
               [data['item'], data['color'], data['grade'], data['batch_no'], float(data['sqm']), item_id])
    db.commit()
    log_action("INVENTORY_UPDATE", f"Updated item ID {item_id}. Old: {dict(old_item)}, New: {data}")
    updated_item = db.execute('SELECT * FROM inventory WHERE id = ?', [item_id]).fetchone()
    return jsonify(dict(updated_item))

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    if not is_admin_or_director():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db(INVENTORY_DB)
    item_to_delete = db.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()
    if item_to_delete:
        db.execute('DELETE FROM inventory WHERE id = ?', [item_id])
        db.commit()
        log_action("INVENTORY_DELETE", f"Deleted item: {dict(item_to_delete)}")
    return jsonify({"success": True})

@app.route('/api/inventory/reset', methods=['POST'])
def reset_inventory():
    if not is_admin_or_director():
        return jsonify({"error": "Forbidden"}), 403
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file"}), 400
    
    db = get_db(INVENTORY_DB)
    try:
        db.execute('BEGIN TRANSACTION')
        db.execute('DELETE FROM inventory')
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        next(csv_reader, None) # Skip header
        
        new_items = [(row[0], row[1], row[2], row[3], float(row[4])) for row in csv_reader if len(row) == 5]
        
        db.executemany('INSERT INTO inventory (item, color, grade, batch_no, sqm) VALUES (?, ?, ?, ?, ?)', new_items)
        db.commit()
        log_action("INVENTORY_RESET", f"Reset inventory with {len(new_items)} items from file '{file.filename}'.")
        return jsonify({"success": True, "message": f"Inventory reset with {len(new_items)} items."})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# --- Audit Log API ---
@app.route('/api/logs', methods=['GET'])
def get_logs():
    if not is_director():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db(LOG_DB)
    logs = db.execute("SELECT timestamp, username, action, details FROM audit_log ORDER BY timestamp DESC").fetchall()
    return jsonify([dict(log) for log in logs])

if __name__ == '__main__':
    if not os.path.exists(INVENTORY_DB):
        init_db(INVENTORY_DB, 'schema/schema_inventory.sql')
    if not os.path.exists(USERS_DB):
        init_db(USERS_DB, 'schema/schema_users.sql')
    if not os.path.exists(LOG_DB):
        init_db(LOG_DB, 'schema/schema_log.sql')
    app.run(debug=True)