from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import os
import json
from datetime import datetime, date
import secrets

# Base directory is the project root (one level up from api/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, 'static'),
            static_url_path='/static')

# IMPORTANT: set a real SECRET_KEY as a Vercel env var. Flask sessions are
# signed client-side cookies (no server-side session store), so this key
# must stay constant across deploys/cold-starts or logged-in users get
# booted out every time you redeploy.
app.secret_key = os.environ.get('SECRET_KEY', 'electropaas-dev-secret-2024')

# In production set ALLOWED_ORIGIN to your real Vercel URL, e.g.
# https://your-project.vercel.app  — "*" cannot be combined with
# supports_credentials=True in real browsers, so we default to same-origin.
_allowed_origin = os.environ.get('ALLOWED_ORIGIN', '*')
CORS(app, supports_credentials=True, origins=[_allowed_origin] if _allowed_origin != '*' else '*')

DB_PATH = os.path.join(BASE_DIR, 'electropaas.db')

# ── DATABASE BACKEND ──────────────────────────────────────────────────────
# Locally (no env vars set): falls back to the same electropaas.db file as
# before, so local dev is unchanged.
#
# In production (Vercel): set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN as
# env vars. Vercel's filesystem is read-only/ephemeral, so a local sqlite
# file cannot be used there — this app talks to a hosted Turso database
# instead, using a library that mimics the built-in sqlite3 API.
TURSO_URL = os.environ.get('TURSO_DATABASE_URL')
TURSO_TOKEN = os.environ.get('TURSO_AUTH_TOKEN')
USE_TURSO = bool(TURSO_URL)

if USE_TURSO:
    import libsql_experimental as libsql


def get_db():
    if USE_TURSO:
        return libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
    conn = sqlite3.connect(DB_PATH)
    return conn


def _row_dict(cursor, row):
    """Convert a single fetched row (tuple) into a dict using cursor.description.
    Works the same whether the row came from sqlite3 or libsql."""
    if row is None:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def _rows_dict(cursor, rows):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


# ── FRONTEND ROUTES ───────────────────────────────────────────────────────────
# Note: on Vercel these are normally intercepted by vercel.json's static
# routes before ever reaching Flask (faster, no cold start). They're kept
# here so `python api/app.py` still works for local dev.

@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'user'), 'storefront.html')

@app.route('/login')
def login_page():
    return send_from_directory(os.path.join(BASE_DIR, 'frontend'), 'index.html')

@app.route('/admin')
@app.route('/admin/')
def admin_page():
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'admin'), 'index.html')

@app.route('/seller')
@app.route('/seller/')
def seller_page():
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'seller'), 'index.html')

@app.route('/storefront')
@app.route('/storefront/')
def storefront_page():
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'user'), 'storefront.html')


# ── DB SETUP (local dev only) ────────────────────────────────────────────
# This only runs against the local sqlite file. When USE_TURSO is true we
# skip it entirely — your Turso database is created and seeded once via
# the `turso db shell` import step in DEPLOYMENT.md, not on every cold
# start. Running CREATE TABLE / seed-product inserts on every serverless
# invocation would be slow and risk re-adding sample rows you deleted.

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    if USE_TURSO:
        return
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sellers (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        store_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        price REAL NOT NULL,
        bulk_price REAL,
        quantity INTEGER DEFAULT 0,
        image_url TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS seller_orders (
        id INTEGER PRIMARY KEY,
        seller_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        total_amount REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        delivered_at TEXT,
        FOREIGN KEY(seller_id) REFERENCES sellers(id)
    );

    CREATE TABLE IF NOT EXISTS seller_order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES seller_orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS user_orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        total_amount REAL DEFAULT 0,
        shipping_address TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS user_order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES user_orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS billbook (
        id INTEGER PRIMARY KEY,
        seller_id INTEGER NOT NULL,
        order_id INTEGER,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        payment_date TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(seller_id) REFERENCES sellers(id),
        FOREIGN KEY(order_id) REFERENCES seller_orders(id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        from_seller_id INTEGER,
        order_id INTEGER,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(from_seller_id) REFERENCES sellers(id)
    );
    """)

    admin_pass = hash_password('admin123')
    c.execute("INSERT OR IGNORE INTO admins (username, password_hash) VALUES (?, ?)", ('admin', admin_pass))

    sample_products = [
        ('Samsung 65" 4K OLED TV', 'Stunning 4K OLED display with smart features', 'Television', 89999, 75000, 15, ''),
        ('Sony WH-1000XM5 Headphones', 'Industry-leading noise cancelling wireless headphones', 'Audio', 29999, 24000, 30, ''),
        ('iPhone 15 Pro Max', 'Latest Apple flagship with titanium design', 'Smartphones', 159900, 145000, 20, ''),
        ('LG 1.5T Split AC', '5-star rated inverter air conditioner', 'Air Conditioners', 45000, 38000, 10, ''),
        ('Bosch Washing Machine 8kg', 'Fully automatic front-loading with i-Dos', 'Appliances', 55000, 46000, 8, ''),
        ('Dell XPS 15 Laptop', 'OLED display, Intel i9, 32GB RAM', 'Laptops', 189000, 172000, 12, ''),
        ('Canon EOS R6 Mark II', 'Full-frame mirrorless camera 40fps', 'Cameras', 229000, 210000, 5, ''),
        ('PS5 Console', 'PlayStation 5 with DualSense controller', 'Gaming', 54990, 49000, 25, ''),
    ]
    for p in sample_products:
        c.execute("INSERT OR IGNORE INTO products (name, description, category, price, bulk_price, quantity) SELECT ?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM products WHERE name=?)",
                  (p[0], p[1], p[2], p[3], p[4], p[5], p[0]))

    conn.commit()
    conn.close()

# ── AUTH HELPERS ─────────────────────────────────────────────────────────────

def get_current_user():
    return session.get('user')

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        u = get_current_user()
        if not u or u['role'] != 'admin':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def require_seller(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        u = get_current_user()
        if not u or u['role'] != 'seller':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def require_user(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        u = get_current_user()
        if not u or u['role'] != 'user':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    role = data.get('role')
    password_hash = hash_password(data.get('password', ''))
    conn = get_db()
    c = conn.cursor()

    if role == 'admin':
        cur = c.execute("SELECT * FROM admins WHERE username=? AND password_hash=?", (data['username'], password_hash))
        row = _row_dict(cur, cur.fetchone())
        if row:
            session['user'] = {'id': row['id'], 'role': 'admin', 'username': row['username']}
            conn.close()
            return jsonify({'success': True, 'role': 'admin', 'username': row['username']})

    elif role == 'seller':
        cur = c.execute("SELECT * FROM sellers WHERE username=? AND password_hash=? AND is_active=1", (data['username'], password_hash))
        row = _row_dict(cur, cur.fetchone())
        if row:
            session['user'] = {'id': row['id'], 'role': 'seller', 'username': row['username'], 'store_name': row['store_name']}
            conn.close()
            return jsonify({'success': True, 'role': 'seller', 'username': row['username'], 'store_name': row['store_name']})

    elif role == 'user':
        cur = c.execute("SELECT * FROM users WHERE email=? AND password_hash=?", (data['email'], password_hash))
        row = _row_dict(cur, cur.fetchone())
        if row:
            session['user'] = {'id': row['id'], 'role': 'user', 'email': row['email'], 'name': row['name']}
            conn.close()
            return jsonify({'success': True, 'role': 'user', 'name': row['name'], 'email': row['email']})

    conn.close()
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password_hash, name, phone) VALUES (?,?,?,?)",
                  (data['email'], hash_password(data['password']), data['name'], data.get('phone', '')))
        conn.commit()
        user_id = c.lastrowid
        session['user'] = {'id': user_id, 'role': 'user', 'email': data['email'], 'name': data['name']}
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 400
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'Email already registered'}), 400
        raise
    finally:
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
def me():
    u = get_current_user()
    if u:
        return jsonify(u)
    return jsonify({'error': 'Not logged in'}), 401

# ── PRODUCTS ─────────────────────────────────────────────────────────────────

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    c = conn.cursor()
    category = request.args.get('category')
    search = request.args.get('search')
    query = "SELECT * FROM products WHERE is_active=1"
    params = []
    if category:
        query += " AND category=?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    cur = c.execute(query, params)
    result = _rows_dict(cur, cur.fetchall())
    conn.close()
    return jsonify(result)

@app.route('/api/products/<int:pid>', methods=['GET'])
def get_product(pid):
    conn = get_db()
    cur = conn.execute("SELECT * FROM products WHERE id=?", (pid,))
    row = _row_dict(cur, cur.fetchone())
    conn.close()
    return jsonify(row) if row else ('', 404)

@app.route('/api/admin/products', methods=['POST'])
@require_admin
def add_product():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO products (name, description, category, price, bulk_price, quantity, image_url) VALUES (?,?,?,?,?,?,?)",
              (data['name'], data.get('description'), data.get('category'), data['price'], data.get('bulk_price'), data.get('quantity', 0), data.get('image_url', '')))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': pid})

@app.route('/api/admin/products/<int:pid>', methods=['PUT'])
@require_admin
def update_product(pid):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE products SET name=?, description=?, category=?, price=?, bulk_price=?, quantity=?, image_url=? WHERE id=?",
                 (data['name'], data.get('description'), data.get('category'), data['price'], data.get('bulk_price'), data.get('quantity', 0), data.get('image_url', ''), pid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/products/<int:pid>', methods=['DELETE'])
@require_admin
def delete_product(pid):
    conn = get_db()
    conn.execute("UPDATE products SET is_active=0 WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── ADMIN: SELLERS ────────────────────────────────────────────────────────────

@app.route('/api/admin/sellers', methods=['GET'])
@require_admin
def get_sellers():
    conn = get_db()
    cur = conn.execute("SELECT id, username, store_name, phone, email, created_at, is_active FROM sellers")
    result = _rows_dict(cur, cur.fetchall())
    conn.close()
    return jsonify(result)

@app.route('/api/admin/sellers', methods=['POST'])
@require_admin
def add_seller():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO sellers (username, password_hash, store_name, phone, email) VALUES (?,?,?,?,?)",
                  (data['username'], hash_password(data['password']), data['store_name'], data.get('phone', ''), data.get('email', '')))
        conn.commit()
        return jsonify({'success': True, 'id': c.lastrowid})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'Username already exists'}), 400
        raise
    finally:
        conn.close()

@app.route('/api/admin/sellers/<int:sid>', methods=['PUT'])
@require_admin
def update_seller(sid):
    data = request.json
    conn = get_db()
    if data.get('password'):
        conn.execute("UPDATE sellers SET store_name=?, phone=?, email=?, password_hash=?, is_active=? WHERE id=?",
                     (data['store_name'], data.get('phone'), data.get('email'), hash_password(data['password']), data.get('is_active', 1), sid))
    else:
        conn.execute("UPDATE sellers SET store_name=?, phone=?, email=?, is_active=? WHERE id=?",
                     (data['store_name'], data.get('phone'), data.get('email'), data.get('is_active', 1), sid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/sellers/<int:sid>', methods=['DELETE'])
@require_admin
def remove_seller(sid):
    conn = get_db()
    conn.execute("UPDATE sellers SET is_active=0 WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── ADMIN: ORDERS & NOTIFICATIONS ────────────────────────────────────────────

@app.route('/api/admin/seller-orders', methods=['GET'])
@require_admin
def admin_seller_orders():
    conn = get_db()
    cur = conn.execute("""
        SELECT so.*, s.store_name, s.username
        FROM seller_orders so
        JOIN sellers s ON s.id = so.seller_id
        ORDER BY so.created_at DESC
    """)
    orders = _rows_dict(cur, cur.fetchall())
    result = []
    for order in orders:
        icur = conn.execute("""
            SELECT soi.*, p.name as product_name FROM seller_order_items soi
            JOIN products p ON p.id = soi.product_id
            WHERE soi.order_id=?
        """, (order['id'],))
        order['items'] = _rows_dict(icur, icur.fetchall())
        result.append(order)
    conn.close()
    return jsonify(result)

@app.route('/api/admin/seller-orders/<int:oid>/deliver', methods=['POST'])
@require_admin
def mark_delivered(oid):
    conn = get_db()
    conn.execute("UPDATE seller_orders SET status='delivered', delivered_at=datetime('now') WHERE id=?", (oid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/notifications', methods=['GET'])
@require_admin
def get_notifications():
    conn = get_db()
    cur = conn.execute("""
        SELECT n.*, s.store_name FROM notifications n
        LEFT JOIN sellers s ON s.id = n.from_seller_id
        ORDER BY n.created_at DESC
    """)
    result = _rows_dict(cur, cur.fetchall())
    conn.close()
    return jsonify(result)

@app.route('/api/admin/notifications/<int:nid>/read', methods=['POST'])
@require_admin
def mark_notification_read(nid):
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=?", (nid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── ADMIN: BILLBOOK ───────────────────────────────────────────────────────────

@app.route('/api/admin/billbook', methods=['GET'])
@require_admin
def admin_billbook():
    conn = get_db()
    cur = conn.execute("""
        SELECT b.*, s.store_name, s.username FROM billbook b
        JOIN sellers s ON s.id = b.seller_id
        ORDER BY b.created_at DESC
    """)
    result = _rows_dict(cur, cur.fetchall())
    conn.close()
    return jsonify(result)

@app.route('/api/admin/billbook', methods=['POST'])
@require_admin
def add_billbook_entry():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO billbook (seller_id, order_id, amount, type, description, payment_date) VALUES (?,?,?,?,?,?)",
              (data['seller_id'], data.get('order_id'), data['amount'], data['type'], data.get('description'), data.get('payment_date')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/billbook/summary', methods=['GET'])
@require_admin
def billbook_summary():
    conn = get_db()
    cur = conn.execute("""
        SELECT s.id, s.store_name, s.username,
            SUM(CASE WHEN b.type='due' THEN b.amount ELSE 0 END) as total_due,
            SUM(CASE WHEN b.type='paid' THEN b.amount ELSE 0 END) as total_paid
        FROM sellers s
        LEFT JOIN billbook b ON b.seller_id = s.id
        WHERE s.is_active=1
        GROUP BY s.id
    """)
    rows = _rows_dict(cur, cur.fetchall())
    conn.close()
    for r in rows:
        r['total_due'] = r['total_due'] or 0
        r['total_paid'] = r['total_paid'] or 0
    return jsonify(rows)

# ── SELLER ROUTES ─────────────────────────────────────────────────────────────

@app.route('/api/seller/cart/submit', methods=['POST'])
@require_seller
def seller_submit_order():
    data = request.json
    seller_id = get_current_user()['id']
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'Cart is empty'}), 400

    conn = get_db()
    c = conn.cursor()

    total = 0
    for item in items:
        cur = conn.execute("SELECT * FROM products WHERE id=?", (item['product_id'],))
        p = _row_dict(cur, cur.fetchone())
        if p:
            price = p['bulk_price'] or p['price']
            total += price * item['quantity']

    c.execute("INSERT INTO seller_orders (seller_id, total_amount, notes) VALUES (?,?,?)",
              (seller_id, total, data.get('notes', '')))
    order_id = c.lastrowid

    for item in items:
        cur = conn.execute("SELECT * FROM products WHERE id=?", (item['product_id'],))
        p = _row_dict(cur, cur.fetchone())
        if p:
            price = p['bulk_price'] or p['price']
            c.execute("INSERT INTO seller_order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
                      (order_id, item['product_id'], item['quantity'], price))

    c.execute("INSERT INTO billbook (seller_id, order_id, amount, type, description) VALUES (?,?,?,?,?)",
              (seller_id, order_id, total, 'due', f'Order #{order_id}'))

    scur = conn.execute("SELECT store_name FROM sellers WHERE id=?", (seller_id,))
    seller = _row_dict(scur, scur.fetchone())
    c.execute("INSERT INTO notifications (from_seller_id, order_id, message) VALUES (?,?,?)",
              (seller_id, order_id, f"New order from {seller['store_name']} — ₹{total:,.0f}"))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/seller/orders', methods=['GET'])
@require_seller
def seller_orders():
    seller_id = get_current_user()['id']
    conn = get_db()
    cur = conn.execute("SELECT * FROM seller_orders WHERE seller_id=? ORDER BY created_at DESC", (seller_id,))
    orders = _rows_dict(cur, cur.fetchall())
    result = []
    for order in orders:
        icur = conn.execute("""
            SELECT soi.*, p.name as product_name FROM seller_order_items soi
            JOIN products p ON p.id = soi.product_id WHERE soi.order_id=?
        """, (order['id'],))
        order['items'] = _rows_dict(icur, icur.fetchall())
        result.append(order)
    conn.close()
    return jsonify(result)

@app.route('/api/seller/billbook', methods=['GET'])
@require_seller
def seller_billbook():
    seller_id = get_current_user()['id']
    conn = get_db()
    cur = conn.execute("SELECT * FROM billbook WHERE seller_id=? ORDER BY created_at DESC", (seller_id,))
    entries = _rows_dict(cur, cur.fetchall())
    d_cur = conn.execute("SELECT COALESCE(SUM(amount),0) as t FROM billbook WHERE seller_id=? AND type='due'", (seller_id,))
    total_due = _row_dict(d_cur, d_cur.fetchone())['t']
    p_cur = conn.execute("SELECT COALESCE(SUM(amount),0) as t FROM billbook WHERE seller_id=? AND type='paid'", (seller_id,))
    total_paid = _row_dict(p_cur, p_cur.fetchone())['t']
    conn.close()
    return jsonify({'entries': entries, 'total_due': total_due, 'total_paid': total_paid, 'balance': total_due - total_paid})

# ── USER ROUTES ───────────────────────────────────────────────────────────────

@app.route('/api/user/orders', methods=['GET'])
@require_user
def user_orders():
    user_id = get_current_user()['id']
    conn = get_db()
    cur = conn.execute("SELECT * FROM user_orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    orders = _rows_dict(cur, cur.fetchall())
    result = []
    for order in orders:
        icur = conn.execute("""
            SELECT uoi.*, p.name as product_name FROM user_order_items uoi
            JOIN products p ON p.id = uoi.product_id WHERE uoi.order_id=?
        """, (order['id'],))
        order['items'] = _rows_dict(icur, icur.fetchall())
        result.append(order)
    conn.close()
    return jsonify(result)

@app.route('/api/user/orders', methods=['POST'])
@require_user
def place_user_order():
    data = request.json
    user_id = get_current_user()['id']
    items = data.get('items', [])
    conn = get_db()
    c = conn.cursor()
    total = 0
    for item in items:
        cur = conn.execute("SELECT * FROM products WHERE id=?", (item['product_id'],))
        p = _row_dict(cur, cur.fetchone())
        if p:
            total += p['price'] * item['quantity']
    c.execute("INSERT INTO user_orders (user_id, total_amount, shipping_address) VALUES (?,?,?)",
              (user_id, total, data.get('address', '')))
    order_id = c.lastrowid
    for item in items:
        cur = conn.execute("SELECT * FROM products WHERE id=?", (item['product_id'],))
        p = _row_dict(cur, cur.fetchone())
        if p:
            c.execute("INSERT INTO user_order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
                      (order_id, item['product_id'], item['quantity'], p['price']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'order_id': order_id})

# ── CATEGORIES ────────────────────────────────────────────────────────────────

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cur = conn.execute("SELECT DISTINCT category FROM products WHERE is_active=1 AND category IS NOT NULL")
    rows = _rows_dict(cur, cur.fetchall())
    conn.close()
    return jsonify([r['category'] for r in rows])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
