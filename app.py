from flask import Flask, render_template, request, redirect, url_for, session
import csv, os
from ai_manager import AIManager

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # change before deploying
ADMIN_PASSWORD = "admin123"
CSV_FILE = 'products.csv'

# ---- Utility functions ----
def read_products():
    products = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['price'] = float(row['price'])
                row['stock'] = int(row['stock'])
                products.append(row)
    return products

def write_products(products):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'name', 'price', 'stock', 'category']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

# ---- Routes ----

@app.route('/')
def home():
    if 'role' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        if role == 'admin':
            password = request.form['password']
            if password == ADMIN_PASSWORD:
                session['role'] = 'admin'
                return redirect(url_for('admin_panel'))
            else:
                return render_template('login.html', error="Invalid admin password")
        else:
            session['role'] = 'customer'
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---- Customer area ----
@app.route('/products')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))
    products = read_products()

    # --- Searching ---
    query = request.args.get('search', '').lower()
    if query:
        products = [p for p in products if query in p['name'].lower() or query in p['category'].lower()]

    # --- Sorting ---
    sort_by = request.args.get('sort')
    if sort_by == 'price_low':
        products.sort(key=lambda x: x['price'])
    elif sort_by == 'price_high':
        products.sort(key=lambda x: x['price'], reverse=True)
    elif sort_by == 'stock':
        products.sort(key=lambda x: x['stock'], reverse=True)

    return render_template('index.html', products=products, role=session['role'])

# ---- Cart ----
@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    products = read_products()
    for p in products:
        if p['id'] == product_id:
            cart.append(p)
            break
    session['cart'] = cart
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/clear_cart')
def clear_cart():
    session['cart'] = []
    return redirect(url_for('cart'))

# ---- Admin area ----
@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    products = read_products()
    return render_template('admin.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    products = read_products()
    new_product = {
        'id': str(len(products) + 1),
        'name': request.form['name'],
        'price': float(request.form['price']),
        'stock': int(request.form['stock']),
        'category': request.form['category']
    }
    products.append(new_product)
    write_products(products)
    return redirect(url_for('admin_panel'))

@app.route('/update_prices')
def update_prices():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    ai = AIManager()
    products = read_products()
    updated = ai.dynamic_pricing(products)
    write_products(updated)
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
