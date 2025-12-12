from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import random

app = Flask(__name__)
app.secret_key = "secret123"   # Needed for login sessions

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hotel_db'

mysql = MySQL(app)

# ----------------------------------------------------------------
# Generate random 8-digit Staff ID
# ----------------------------------------------------------------
def generate_staff_id():
    return str(random.randint(10000000, 99999999))

# ----------------------------------------------------------------
# REGISTRATION
# ----------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        staff_id = generate_staff_id()   # random ID generated in python
        
        fname = request.form['firstname']
        lname = request.form['lastname']
        role  = request.form['role']
        phone = request.form['phone']
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO Staff (StaffID, FirstName, LastName, Role, Phone, Email, Salary)
            VALUES (%s, %s, %s, %s, %s, %s, 0)
        """, (staff_id, fname, lname, role, phone, email))
        
        mysql.connection.commit()
        cur.close()

        return f"Staff Registered Successfully! StaffID (password) = {staff_id}"

    return render_template("register.html")

# ----------------------------------------------------------------
# LOGIN (Email + StaffID)
# ----------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        email = request.form['email']
        entered_id = request.form['staff_id']

        cur = mysql.connection.cursor()
        cur.execute("SELECT StaffID, Role FROM Staff WHERE Email = %s", (email,))
        staff = cur.fetchone()
        cur.close()

        if staff is None:
            return "Email not found!"

        real_id = staff[0]
        role = staff[1]

        # StaffID acts as password
        if entered_id != real_id:
            return "Incorrect Staff ID!"

        # Save session
        session['staff_id'] = real_id
        session['role'] = role

        # Redirect by role
        role = role.lower()
        if role == "manager":
            return redirect('/manager')
        elif role == "receptionist":
            return redirect('/reception')
        elif role == "roomservice":
            return redirect('/roomservice')
        else:
            return "Unknown role!"

    return render_template("login.html")

# ----------------------------------------------------------------
# ROLE PAGES
# ----------------------------------------------------------------
@app.route("/manager")
def manager_page():
    return render_template("manager.html")

@app.route("/reception")
def reception_page():
    return render_template("reception.html")

@app.route("/roomservice")
def roomservice_page():
    return render_template("roomservice.html")

# ----------------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')

# ----------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
