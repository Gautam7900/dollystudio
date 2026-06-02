from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "dollystudio123"

def init_db():
    conn = sqlite3.connect('studio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        address TEXT,
        email TEXT
    )''')
    c.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    shoot_type TEXT,
    total_amount REAL,
    date TEXT,
    delivery_date TEXT,
    status TEXT,
    notes TEXT
)
''')

    
    c.execute('''
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    total_amount REAL,
    paid_amount REAL DEFAULT 0,
    remaining_amount REAL,
    payment_status TEXT
)
''')
    c.execute('''
CREATE TABLE IF NOT EXISTS payment_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER,
    amount REAL,
    payment_mode TEXT,
    payment_date TEXT,
    notes TEXT
)
''')
   
    conn.commit()
    conn.close()

init_db()


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Default Credentials
        if username == "admin" and password == "admin123":
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html',
                                   error="Invalid Username or Password")

    return render_template('login.html')


@app.route('/')
def index():

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    # Total Customers
    total_customers = c.execute("""
        SELECT COUNT(*)
        FROM customers
    """).fetchone()[0]

    # Total Orders
    total_orders = c.execute("""
        SELECT COUNT(*)
        FROM orders
    """).fetchone()[0]

    # Pending Orders
    pending_orders = c.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status != 'Delivered'
    """).fetchone()[0]

    # Outstanding Amount
    total_due = c.execute("""
        SELECT COALESCE(SUM(remaining_amount),0)
        FROM payments
    """).fetchone()[0]

    # Recent Orders
    recent_orders = c.execute("""
        SELECT
            o.id,
            c.name,
            o.shoot_type,
            o.date

        FROM orders o

        LEFT JOIN customers c
        ON o.customer_id = c.id

        ORDER BY o.id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        'index.html',
        total_customers=total_customers,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_due=total_due,
        recent_orders=recent_orders
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))





@app.route('/customers')
def customers():

    search_query = request.args.get('search', '')

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    if search_query:

        customers = c.execute(
            """
            SELECT * FROM customers
            WHERE name LIKE ?
            OR phone LIKE ?
            """,
            (
                f'%{search_query}%',
                f'%{search_query}%'
            )
        ).fetchall()

    else:

        customers = c.execute(
            "SELECT * FROM customers"
        ).fetchall()

    conn.close()

    return render_template(
        'customers.html',
        customers=customers,
        search_query=search_query
    )
    
    
    

@app.route('/add_customer', methods=['POST'])
def add_customer():

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO customers
        (name, phone, address, email)
        VALUES (?, ?, ?, ?)
        """,
        (
            request.form['name'],
            request.form['phone'],
            request.form['address'],
            request.form['email']
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for('customers'))


@app.route('/delete_customer/<int:id>')
def delete_customer(id):

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    c.execute(
        "DELETE FROM customers WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('customers'))




@app.route('/orders')
def orders():

    search_query = request.args.get('search', '')

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    customers = c.execute("""
        SELECT id,name,phone
        FROM customers
        ORDER BY name
    """).fetchall()

    if search_query:

        orders = c.execute("""
            SELECT
                o.id,
                c.name,
                o.shoot_type,
                o.total_amount,
                o.date,
                o.delivery_date,
                o.status,
                o.notes

            FROM orders o

            LEFT JOIN customers c
            ON o.customer_id = c.id

            WHERE c.name LIKE ?

            ORDER BY o.id DESC
        """,
        (f'%{search_query}%',)
        ).fetchall()

    else:

        orders = c.execute("""
            SELECT
                o.id,
                c.name,
                o.shoot_type,
                o.total_amount,
                o.date,
                o.delivery_date,
                o.status,
                o.notes

            FROM orders o

            LEFT JOIN customers c
            ON o.customer_id = c.id

            ORDER BY o.id DESC
        """).fetchall()

    conn.close()

    return render_template(
        'orders.html',
        customers=customers,
        orders=orders,
        search_query=search_query
    )

@app.route('/add_order', methods=['POST'])
def add_order():

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO orders
        (
            customer_id,
            shoot_type,
            total_amount,
            date,
            delivery_date,
            status,
            notes
        )
        VALUES (?,?,?,?,?,?,?)
    """,
    (
        request.form['customer_id'],
        request.form['shoot_type'],
        float(request.form['total_amount']),
        request.form['date'],
        request.form['delivery_date'],
        request.form['status'],
        request.form['notes']
    ))

    order_id = c.lastrowid

    total_amount = float(
        request.form['total_amount']
    )

    c.execute("""
        INSERT INTO payments
        (
            order_id,
            total_amount,
            paid_amount,
            remaining_amount,
            payment_status
        )
        VALUES (?,?,?,?,?)
    """,
    (
        order_id,
        total_amount,
        0,
        total_amount,
        'Due'
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('orders'))



@app.route('/order_receipt/<int:order_id>')
def order_receipt(order_id):

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    order = c.execute("""
        SELECT
            o.id,
            c.name,
            c.phone,
            c.address,
            o.shoot_type,
            o.date,
            o.delivery_date,
            o.total_amount,
            p.paid_amount,
            p.remaining_amount,
            p.payment_status,
            o.notes

        FROM orders o

        LEFT JOIN customers c
        ON o.customer_id = c.id

        LEFT JOIN payments p
        ON p.order_id = o.id

        WHERE o.id=?
    """,(order_id,)).fetchone()

    conn.close()

    return render_template(
        'order_receipt.html',
        order=order
    )


@app.route('/delete_order/<int:id>')
def delete_order(id):

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    c.execute(
        "DELETE FROM orders WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('orders'))



@app.route('/payments')
def payments():

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    orders = c.execute("""
        SELECT
            o.id,
            c.name,
            o.shoot_type
        FROM orders o
        LEFT JOIN customers c
        ON o.customer_id = c.id
        ORDER BY o.id DESC
    """).fetchall()

    payments = c.execute("""
        SELECT
            p.id,
            c.name,
            o.shoot_type,
            p.total_amount,
            p.paid_amount,
            p.remaining_amount,
            p.payment_status

        FROM payments p

        LEFT JOIN orders o
        ON p.order_id = o.id

        LEFT JOIN customers c
        ON o.customer_id = c.id

        ORDER BY p.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        'payments.html',
        payments=payments,
        orders=orders
    )


@app.route('/add_transaction/<int:payment_id>', methods=['POST'])
def add_transaction(payment_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    amount = float(request.form['amount'])
    payment_mode = request.form['payment_mode']
    payment_date = request.form['payment_date']
    notes = request.form['notes']

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    # Get Payment Details

    payment = c.execute("""
        SELECT
            order_id,
            total_amount,
            paid_amount
        FROM payments
        WHERE id=?
    """, (payment_id,)).fetchone()

    order_id = payment[0]
    total_amount = float(payment[1])
    old_paid_amount = float(payment[2])

    # Calculate New Amounts

    new_paid_amount = old_paid_amount + amount

    remaining_amount = total_amount - new_paid_amount

    # Auto Update Status

    if remaining_amount <= 0:

        remaining_amount = 0
        payment_status = "Paid"

        # Order Automatically Completed

        c.execute("""
            UPDATE orders
            SET status='Completed'
            WHERE id=?
        """, (order_id,))

    else:

        payment_status = "Partial"

    # Update Payment Summary

    c.execute("""
        UPDATE payments
        SET
            paid_amount=?,
            remaining_amount=?,
            payment_status=?
        WHERE id=?
    """,
    (
        new_paid_amount,
        remaining_amount,
        payment_status,
        payment_id
    ))

    # Save Transaction History

    c.execute("""
        INSERT INTO payment_transactions
        (
            payment_id,
            amount,
            payment_mode,
            payment_date,
            notes
        )
        VALUES (?,?,?,?,?)
    """,
    (
        payment_id,
        amount,
        payment_mode,
        payment_date,
        notes
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('payments'))

@app.route('/payment_transactions/<int:payment_id>')
def payment_transactions(payment_id):

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    transactions = c.execute("""
        SELECT *
        FROM payment_transactions
        WHERE payment_id=?
        ORDER BY id DESC
    """,
    (payment_id,)
    ).fetchall()

    conn.close()

    return render_template(
        'payment_transactions.html',
        transactions=transactions,
        payment_id=payment_id
    )





@app.route('/delete_payment/<int:id>')
def delete_payment(id):

    conn = sqlite3.connect('studio.db')
    c = conn.cursor()

    c.execute(
        "DELETE FROM payments WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('payments'))









if __name__ == '__main__':
    app.run(debug=True)
