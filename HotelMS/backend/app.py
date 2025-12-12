from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_db
from datetime import datetime
import random

app = Flask(__name__, template_folder="../frontend/templates", static_folder='../frontend/static')
app.secret_key = "secret123"   # Needed for login sessions

def generate_staff_id():
    return str(random.randint(10000000, 99999999))

# @app.route("/")
# def dashboard():
#     db = get_db()
#     cursor = db.cursor(dictionary=True)

#     cursor.execute("SELECT COUNT(*) AS total_rooms FROM Room")
#     total_rooms = cursor.fetchone()["total_rooms"]

#     cursor.execute("SELECT COUNT(*) AS available_rooms FROM Room WHERE Status='Available'")
#     available_rooms = cursor.fetchone()["available_rooms"]

#     cursor.execute("SELECT COUNT(*) AS total_bookings FROM Booking")
#     total_bookings = cursor.fetchone()["total_bookings"]

#     return render_template("dashboard.html",
#                         total_rooms=total_rooms,
#                         available_rooms=available_rooms,
#                         total_bookings=total_bookings)

@app.route("/")
def home():
    return render_template("Home.html")

@app.route("/rooms")
def rooms_list():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT Room.*, RoomType.TypeName 
        FROM Room 
        JOIN RoomType ON Room.RoomTypeID = RoomType.RoomTypeID
    """)
    rooms = cursor.fetchall()
    return render_template("rooms_list.html", rooms=rooms)


@app.route("/room/<int:number>")
def room_details(number):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT Room.*, RoomType.TypeName, RoomType.PricePerNight
        FROM Room
        JOIN RoomType ON Room.RoomTypeID = RoomType.RoomTypeID
        WHERE Room.RoomNumber = %s
    """, (number,))
    room = cursor.fetchone()
    return render_template("room_details.html", room=room)


@app.route("/room-types")
def room_types():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM RoomType")
    types = cursor.fetchall()
    return render_template("room_types.html", types=types)


# Updated the route to handle both GET and POST methods
@app.route("/room-type/add", methods=["GET", "POST"])
def add_room_type():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()

        # Retrieve form data
        type_name = request.form.get("name")
        beds = request.form.get("beds")
        ac = request.form.get("ac", 0)
        tv = request.form.get("tv", 0)
        wifi = request.form.get("wifi", 0)
        airport_shuttle = request.form.get("airportShuttle", 0)
        concierge = request.form.get("concierge", 0)
        pool = request.form.get("pool", 0)
        spa = request.form.get("spa", 0)
        meeting_corner = request.form.get("meetingCorner", 0)

        # Insert into the RoomType table
        cursor.execute(
            """
            INSERT INTO RoomType (TypeName, Beds, AC, TV, WiFi, AirportShuttle, Concierge, Pool, Spa, MeetingCorner)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (type_name, beds, ac, tv, wifi, airport_shuttle, concierge, pool, spa, meeting_corner)
        )
        db.commit()

        # Redirect to the room types page
        return redirect("/room-types")

    # If GET request, render the add room type form
    return render_template("add_room_type.html")


@app.route("/room/add", methods=["GET", "POST"])
def add_room():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM RoomType")
    types = cursor.fetchall()

    if request.method == "POST":
        number = request.form["number"]
        type_id = request.form["type"]
        status = request.form["status"]
        floor = request.form["floor"]

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO Room (RoomNumber, RoomTypeID, Status, FloorLevel)
            VALUES (%s, %s, %s, %s)
        """, (number, type_id, status, floor))

        db.commit()
        return redirect("/rooms")

    return render_template("add_room.html", types=types)



@app.route("/booking_rooms")
def booking_rooms_list():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            br.BookingID, 
            br.RoomNumber,
            CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
            b.CheckInDate, 
            b.CheckOutDate, 
            r.Status AS RoomStatus,

            p.PaymentID,
            p.Amount AS PaymentAmount,
            p.Method AS PaymentMethod,
            p.Date AS PaymentDate

        FROM Booking_Rooms br
        JOIN Booking b ON br.BookingID = b.BookingID
        JOIN Guest g ON b.GuestID = g.GuestID
        JOIN Room r ON br.RoomNumber = r.RoomNumber
        JOIN Payment p ON b.BookingID = p.BookingID

        ORDER BY br.BookingID, br.RoomNumber;
    """)

    raw_bookings = cursor.fetchall()

    # Format dates safely in Python
    bookings_rooms = []
    for row in raw_bookings:
        formatted = row.copy()  # Don't mutate original

        # Format dates if they exist and are datetime objects
        if row['CheckInDate']:
            formatted['CheckInDate'] = row['CheckInDate'].strftime('%b %d, %Y')
        else:
            formatted['CheckInDate'] = '—'

        if row['CheckOutDate']:
            formatted['CheckOutDate'] = row['CheckOutDate'].strftime('%b %d, %Y')
        else:
            formatted['CheckOutDate'] = '—'

        if row['PaymentDate']:
            formatted['PaymentDate'] = row['PaymentDate'].strftime('%b %d, %Y')
        else:
            formatted['PaymentDate'] = None  # Will show as "-"

        bookings_rooms.append(formatted)

    # Format current time in Python
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    return render_template("booking_rooms_list.html", 
                           bookings_rooms=bookings_rooms,
                           current_time=current_time)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname = request.form['firstname'].strip()
        lname = request.form['lastname'].strip()
        role = request.form['role'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip().lower()
        salary = request.form['salary'].strip()

        if not all([fname, lname, role, phone, email,salary]):
            flash('All fields are required!', 'danger')
            return render_template("add_staff.html")

        staff_id = generate_staff_id()

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO Staff (StaffID, FirstName, LastName, Role, Phone, Email, Salary)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (staff_id, fname, lname, role, phone, email, salary))
            db.commit()
            flash(f'Success! Staff registered. Login ID (Password): <strong>{staff_id}</strong>', 'success')
        except Exception as e:
            flash('Email already exists or database error.', 'danger')
            print(e)

        return render_template("Home.html")

    return render_template("add_staff.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    # if 'staff_id' in session:
    #     return redirect(url_for('Home'))

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        staff_id_input = request.form['staff_id'].strip()

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT StaffID, FirstName, Role FROM Staff WHERE LOWER(Email) = %s", (email,))
        staff = cursor.fetchone()

        if not staff:
            flash('Email not found!', 'danger')
            return render_template("login.html")

        if staff['StaffID'] != staff_id_input:
            flash('Incorrect Staff ID!', 'danger')
            return render_template("login.html")

        # Login success
        session['staff_id'] = staff['StaffID']
        session['name'] = staff['FirstName']
        session['role'] = staff['Role']

        flash(f'Welcome back, {staff["FirstName"]}!', 'success')
        # Redirect by role
        # Get role from staff
        user_role = staff['Role'].lower()
        if user_role == "manager":
            return redirect('/manager')
        elif user_role == "receptionist":
            return redirect('/reception')
        elif user_role == "roomservice":
            return redirect('/roomservice')
        # else:
        #     flash("Role not recognized!", "danger")
        #     return redirect('/login')

    return render_template("login.html")

# ----------------------------------------------------------------
# ROLE PAGES
# ----------------------------------------------------------------
@app.route("/manager")
def manager_page():
    return render_template("Home.html")

@app.route("/reception")
def reception_page():
    return render_template("booking_rooms_list.html")

@app.route("/roomservice")
def roomservice_page():
    return render_template("dashboard.html")

# ----------------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)
