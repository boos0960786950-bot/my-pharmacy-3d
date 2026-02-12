from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pharmacy_ultra_secure_2026"

# --- دالة الاتصال بقاعدة البيانات ---
def get_db_connection():
    conn = sqlite3.connect("pharmacy.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- دالة تحديث وإنشاء الجداول (تلقائية) ---
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # إنشاء جدول الأدوية
    c.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            quantity INTEGER, 
            price REAL
        )
    """)
    # إنشاء جدول المبيعات
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            medicine_id INTEGER, 
            sale_date TIMESTAMP, 
            quantity_sold INTEGER, 
            total_price REAL, 
            payment_method TEXT, 
            cash_amount REAL DEFAULT 0, 
            bank_amount REAL DEFAULT 0, 
            buyer_type TEXT DEFAULT 'عام'
        )
    """)
    
    # التأكد من وجود الأعمدة الجديدة (لتجنب الخطأ الذي ظهر في صورك)
    try:
        columns = [column[1] for column in c.execute("PRAGMA table_info(sales)").fetchall()]
        if 'cash_amount' not in columns:
            c.execute("ALTER TABLE sales ADD COLUMN cash_amount REAL DEFAULT 0")
        if 'bank_amount' not in columns:
            c.execute("ALTER TABLE sales ADD COLUMN bank_amount REAL DEFAULT 0")
        if 'buyer_type' not in columns:
            c.execute("ALTER TABLE sales ADD COLUMN buyer_type TEXT DEFAULT 'عام'")
    except Exception as e:
        print(f"Update Notice: {e}")

    conn.commit()
    conn.close()

init_db()

# --- 1. صفحة تسجيل الدخول (الشخصيات المتحركة) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "123":
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "بيانات خاطئة، الشخصيات تراقبك! 👀"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- 2. الصفحة الرئيسية (لوحة التحكم الزجاجية) ---
@app.route("/")
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    
    if search_query:
        medicines = conn.execute("SELECT * FROM medicines WHERE name LIKE ?", ('%' + search_query + '%',)).fetchall()
    else:
        medicines = conn.execute("SELECT * FROM medicines").fetchall()

    today = datetime.now().strftime('%Y-%m-%d')
    stats_row = conn.execute("""
        SELECT SUM(cash_amount), SUM(bank_amount), SUM(total_price) 
        FROM sales WHERE date(sale_date) = ?
    """, (today,)).fetchone()
    
    stats = {
        'total_cash': stats_row[0] or 0,
        'total_bank': stats_row[1] or 0,
        'total_revenue': stats_row[2] or 0
    }
    
    recent_sales = conn.execute("""
        SELECT m.name, s.* FROM sales s
        JOIN medicines m ON s.medicine_id = m.id 
        WHERE date(s.sale_date) = ? 
        ORDER BY s.id DESC LIMIT 10
    """, (today,)).fetchall()
    
    conn.close()
    return render_template("index.html", medicines=medicines, stats=stats, recent_sales=recent_sales, search_query=search_query)

# --- 3. عملية البيع ---
@app.route("/sell/<int:id>", methods=["POST"])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    med = conn.execute("SELECT * FROM medicines WHERE id=?", (id,)).fetchone()
    
    if med and med['quantity'] > 0:
        method = request.form["payment_method"]
        buyer = request.form.get("buyer_type", "عام")
        total = med['price']
        
        cash = float(request.form.get("cash_amount") or 0) if method == "مختلط" else (total if method == "كاش" else 0)
        bank = float(request.form.get("bank_amount") or 0) if method == "مختلط" else (total if method == "بنكك" else 0)

        conn.execute("UPDATE medicines SET quantity = quantity - 1 WHERE id=?", (id,))
        conn.execute("""
            INSERT INTO sales (medicine_id, sale_date, quantity_sold, total_price, payment_method, cash_amount, bank_amount, buyer_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (id, datetime.now(), 1, total, method, cash, bank, buyer))
        conn.commit()
    
    conn.close()
    return redirect(url_for('index'))

# --- 4. إضافة دواء جديد ---
@app.route("/add", methods=["GET", "POST"])
def add():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute("INSERT INTO medicines (name, quantity, price) VALUES (?, ?, ?)", 
                     (request.form["name"], request.form["quantity"], request.form["price"]))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template("add.html")

# --- 5. حذف دواء ---
@app.route("/delete/<int:id>")
def delete(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM medicines WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))
if __name__ == 'main':
    # أضفنا host و port لكي يتمكن السيرفر من التعرف على الموقع
    app.run(host='0.0.0.0', port=5000)