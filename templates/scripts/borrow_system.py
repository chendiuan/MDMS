from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


# 初始化 SQLite 資料庫
def init_db():
    conn = sqlite3.connect("borrow.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS borrow_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    status TEXT DEFAULT 'Borrowed')''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    conn = sqlite3.connect("borrow.db")
    c = conn.cursor()
    c.execute("SELECT * FROM borrow_requests")
    items = c.fetchall()
    conn.close()
    return render_template("index.html", items=items)


@app.route('/borrow', methods=['POST'])
def borrow():
    name = request.form['name']
    quantity = request.form['quantity']
    duration = request.form['duration']

    conn = sqlite3.connect("borrow.db")
    c = conn.cursor()
    c.execute("INSERT INTO borrow_requests (name, quantity, duration) VALUES (?, ?, ?)",
              (name, quantity, duration))
    conn.commit()
    conn.close()

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
