from flask import Flask, render_template, request, redirect
import psycopg2
from datetime import datetime

app = Flask(__name__)

# PostgreSQL configuration
DB_NAME = "inventory"
DB_USER = "postgres"
DB_PASSWORD = "nishanth4328"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT product_id, name FROM products")
    products = cur.fetchall()

    cur.execute("SELECT location_id, name FROM locations")
    locations = cur.fetchall()

    cur.execute("""
        SELECT movement_id, timestamp, from_location, to_location, product_id, qty
        FROM product_movements
        ORDER BY timestamp DESC
    """)
    movements = cur.fetchall()

    balance = {}
    for product in products:
        for location in locations:
            balance[(product[0], location[0])] = 0

    for m in movements:
        product_id = m[4]
        from_location = m[2]
        to_location = m[3]
        qty = m[5]

        if from_location:
            balance[(product_id, from_location)] -= qty
        if to_location:
            balance[(product_id, to_location)] += qty

    cur.close()
    conn.close()

    return render_template('index.html', products=products, locations=locations, movements=movements, balance=balance)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['product_name']  # Removed product_id since it's auto-generated
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name) VALUES (%s)", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        name = request.form['product_name']
        cur.execute("UPDATE products SET name = %s WHERE product_id = %s", (name, product_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/')
    else:
        cur.execute("SELECT product_id, name FROM products WHERE product_id = %s", (product_id,))
        product = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('edit_product.html', product=product)

@app.route('/add_location', methods=['POST'])
def add_location():
    name = request.form['location_name']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO locations (name) VALUES (%s)", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/edit_location/<int:location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        name = request.form['location_name']
        cur.execute("UPDATE locations SET name = %s WHERE location_id = %s", (name, location_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/')
    else:
        cur.execute("SELECT location_id, name FROM locations WHERE location_id = %s", (location_id,))
        location = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('edit_location.html', location=location)
    


@app.route('/add_movement', methods=['POST'])
def add_movement():
    from_location = request.form.get('from_location') or None
    to_location = request.form.get('to_location') or None
    product_id = request.form['product_id']
    qty = int(request.form['qty'])

    # Check if locations exist
    if from_location and to_location:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO product_movements (timestamp, from_location, to_location, product_id, qty)
            VALUES (%s, %s, %s, %s, %s)
        """, (datetime.utcnow(), from_location, to_location, product_id, qty))
        conn.commit()
        cur.close()
        conn.close()

    return redirect('/')

@app.route('/edit_movement/<int:movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        qty = int(request.form['quantity'])
        movement_time = request.form['movement_time']
        movement_time = datetime.strptime(movement_time, '%Y-%m-%dT%H:%M') if movement_time else datetime.utcnow()

        cur.execute("""
            UPDATE product_movements
            SET product_id = %s,
                from_location = %s,
                to_location = %s,
                qty = %s,
                timestamp = %s
            WHERE movement_id = %s
        """, (product_id, from_location, to_location, qty, movement_time, movement_id))

        conn.commit()
        cur.close()
        conn.close()
        return redirect('/')
    else:
        cur.execute("""
            SELECT movement_id, product_id, from_location, to_location, qty, timestamp
            FROM product_movements
            WHERE movement_id = %s
        """, (movement_id,))
        movement = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('edit_movement.html', movement=movement)

if __name__ == '__main__':
    app.run(debug=True)
