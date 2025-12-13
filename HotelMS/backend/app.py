from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_db
from datetime import datetime
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

# @app.route("/")
# def home():
#     return render_template("Home.html")

@app.route("/rooms")
def rooms_list():
    if 'staff_id' not in session:     
        return redirect(url_for('login'))
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
        staff_id_input = request.form['password'].strip()

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
        session['role'] = staff['Role'].lower()

        flash(f'Welcome back, {staff["FirstName"]}!', 'success')
        # Redirect by role
        # Get role from staff
        user_role = staff['Role'].lower()
        if user_role == "manager":
            return redirect('/dashboard')
        elif user_role == "receptionist":
            return redirect('/dashboard')
        elif user_role == "roomservice":
            return redirect('/dashboard')
        else:
            flash("Role not recognized!", "danger")
            return redirect('/login')

    return render_template("login.html")

# ----------------------------------------------------------------
# ROLE PAGES
# ----------------------------------------------------------------
# @app.route("/manager")
# def manager_page():
#     return render_template("main_dashboard.html")

# @app.route("/reception")
# def reception_page():
#     return render_template("main_dashboard.html")

# @app.route("/roomservice")
# def roomservice_page():
#     return render_template("main_dashboard.html")

# ----------------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect('/login')


# ================================
# DASHBOARD — dynamic by role
# ================================
@app.route("/dashboard")
def dashboard():
    # If user not logged in → redirect
    if "role" not in session:
        return redirect("/login")

    role = session["role"].lower()
    name = session["name"]

    # choose navbar
    if role == "manager":
        navbar = "navbar_manager.html"
    elif role == "receptionist":
        navbar = "navbar_reception.html"
    else:
        navbar = "navbar_roomservice.html"

    # Render unified dashboard with correct navbar
    return render_template(
        "main_dashboard.html",
        name=name,
        role=role,
        navbar=navbar
    )

@app.route("/staff/add", methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
    
        fname = request.form.get('firstname', '').strip()
        lname = request.form.get('lastname', '').strip()
        role = request.form.get('role', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        salary = request.form.get('salary', '').strip()

    
        if not all([fname, lname, role, phone, email, salary]):
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
            flash(f'Staff member added successfully! Staff ID: {staff_id}', 'success')
            return redirect(url_for('rooms_list'))

        except Exception as e:
            print(e)
            flash('Error adding staff member. Email might already exist.', 'danger')
            return render_template("add_staff.html")

    
    return render_template("add_staff.html")

@app.route("/staff")
def staff_list():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Staff ORDER BY FirstName, LastName")
    staff_members = cursor.fetchall()
    
    return render_template("staff_list.html", staff_members=staff_members)

from datetime import datetime

@app.route("/transactions")
def transactions():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            b.BookingID,
            br.RoomNumber,
            CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
            rt.TypeName AS RoomType,
            DATEDIFF(b.CheckOutDate, b.CheckInDate) AS Nights,
            b.CheckInDate,
            b.CheckOutDate,
            p.Amount AS PaymentAmount,
            p.Method AS PaymentMethod,
            p.Date AS PaymentDate
        FROM Booking b
        JOIN Booking_Rooms br ON b.BookingID = br.BookingID
        JOIN Guest g ON b.GuestID = g.GuestID
        JOIN Room r ON br.RoomNumber = r.RoomNumber
        JOIN RoomType rt ON r.RoomTypeID = rt.RoomTypeID
        LEFT JOIN Payment p ON b.BookingID = p.BookingID
        ORDER BY b.BookingID DESC
    """)
    
    transactions_data = cursor.fetchall()

    # Format dates and add PaymentStatus dynamically
    for t in transactions_data:
        t['CheckInDate'] = t['CheckInDate'].strftime('%Y-%m-%d') if t['CheckInDate'] else '-'
        t['CheckOutDate'] = t['CheckOutDate'].strftime('%Y-%m-%d') if t['CheckOutDate'] else '-'
        t['PaymentDate'] = t['PaymentDate'].strftime('%Y-%m-%d') if t.get('PaymentDate') else '-'
        # Determine status: if PaymentAmount exists → Completed, else Processing
        t['PaymentStatus'] = 'Completed' if t.get('PaymentAmount') else 'Processing'
    
    return render_template("transactions.html", transactions=transactions_data)

@app.route("/my_tasks")
def my_tasks():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    staff_id = session.get('staff_id')

    # جلب المهام الخاصة بالموظف الحالي
    cursor.execute("""
        SELECT ra.AssignmentID, ra.RoomNumber, ra.DateAssigned, ra.DateCompleted
        FROM RoomAssignment ra
        JOIN RoomAssignment_Staff ras ON ra.AssignmentID = ras.AssignmentID
        WHERE ras.StaffID = %s
    """, (staff_id,))
    raw_tasks = cursor.fetchall()

    tasks = []
    for row in raw_tasks:
        task = row.copy()
        # تحويل string to datetime إذا مش None
        if task['DateAssigned'] and isinstance(task['DateAssigned'], str):
            task['DateAssigned'] = datetime.strptime(task['DateAssigned'], "%Y-%m-%d %H:%M:%S")
        if task['DateCompleted'] and isinstance(task['DateCompleted'], str):
            task['DateCompleted'] = datetime.strptime(task['DateCompleted'], "%Y-%m-%d %H:%M:%S")
        tasks.append(task)
    
    return render_template("my_tasks.html", tasks=tasks)


@app.route("/room-assign/add", methods=["GET", "POST"])
def add_room_assignment():
    if "staff_id" not in session:
        return redirect("/login")

    staff_id = session["staff_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("SELECT RoomNumber FROM Room WHERE Status = 'Available'")
    rooms = cursor.fetchall()

    if request.method == "POST":
        room_number = request.form.get("room_number")
        date_assigned = request.form.get("date_assigned")

        # Insert into RoomAssignment
        cursor.execute("""
            INSERT INTO RoomAssignment (RoomNumber, DateAssigned)
            VALUES (%s, %s)
        """, (room_number, date_assigned))
        assignment_id = cursor.lastrowid

        # Link the assignment to the logged-in staff
        cursor.execute("""
            INSERT INTO RoomAssignment_Staff (AssignmentID, StaffID)
            VALUES (%s, %s)
        """, (assignment_id, staff_id))

        db.commit()
        return redirect("/booking_rooms")

    return render_template("add_room_assignment.html", rooms=rooms)







# nory
# ------------------- BOOKING -------------------
@app.route("/booking", methods=["GET", "POST"])
def booking():
    return render_template("booking.html")


from flask import Flask, request, render_template, flash, redirect, url_for


@app.route("/process_booking", methods=["POST"])
def process_booking():
    from datetime import datetime
    import random

    # جلب بيانات الفورم
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    phone = request.form.get("phone")
    email = request.form.get("email")
    city = request.form.get("city")
    state = request.form.get("state")
    country = request.form.get("country")
    room_type_name = request.form.get("room_type")
    checkin = request.form.get("checkin")
    checkout = request.form.get("checkout")
    payment_method = request.form.get("payment_method")

    db = get_db()
    cursor = db.cursor(buffered=True)

    # توليد GuestCode عشوائي
    guest_code = str(random.randint(10000000, 99999999))

    # إدخال بيانات الضيف
    cursor.execute("""
        INSERT INTO Guest (FirstName, LastName, PhoneNumber, Email, City, State, Country, GuestCode)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (fname, lname, phone, email, city, state, country, guest_code))
    guest_id = cursor.lastrowid

    # توليد BookingID عشوائي
    booking_id = str(random.randint(10000000, 99999999))

    # إنشاء الحجز
    cursor.execute("""
        INSERT INTO Booking (BookingID, GuestID, CheckInDate, CheckOutDate)
        VALUES (%s, %s, %s, %s)
    """, (booking_id, guest_id, checkin, checkout))

    # جلب بيانات نوع الغرفة
    cursor.execute("""
        SELECT RoomTypeID, TypeName, BedCount, HasAC, HasTV, HasWiFi, 
               HasAirportShuttle, HasConcierge, HasPool, HasSpa, 
               HasMeetingCorner, PricePerNight
        FROM RoomType
        WHERE TypeName = %s
    """, (room_type_name,))
    room = cursor.fetchone()

    if not room:
        flash("Selected room type not found.", "danger")
        return redirect(url_for("booking"))

    room_type_info = {
        "id": room[0],
        "name": room[1],
        "beds": room[2],
        "ac": room[3],
        "tv": room[4],
        "wifi": room[5],
        "shuttle": room[6],
        "concierge": room[7],
        "pool": room[8],
        "spa": room[9],
        "meeting": room[10],
        "price": float(room[11])
    }

    # حجز غرفة متاحة
    cursor.execute("""
        SELECT RoomNumber FROM Room
        WHERE RoomTypeID = %s AND Status = 'Available'
        LIMIT 1
    """, (room_type_info["id"],))
    booked_room = cursor.fetchone()
    if not booked_room:
        flash("No available room for the selected type.", "danger")
        return redirect(url_for("booking"))

    booked_room_number = booked_room[0]

    # تحديث حالة الغرفة
    cursor.execute("UPDATE Room SET Status = 'Occupied' WHERE RoomNumber = %s", (booked_room_number,))

    # إضافة رقم الغرفة للـ dictionary
    room_type_info["number"] = booked_room_number

    # حساب السعر
    nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days
    subtotal = nights * room_type_info["price"]
    tax_percent = 14
    taxes = round(subtotal * tax_percent / 100, 2)
    total_amount = round(subtotal + taxes, 2)

    # إدخال الدفع
    cursor.execute("""
        INSERT INTO Payment (BookingID, Amount, Date, Method)
        VALUES (%s, %s, NOW(), %s)
    """, (booking_id, total_amount, payment_method))

    # ربط الحجز بالغرفة
    cursor.execute("INSERT INTO Booking_Rooms (BookingID, RoomNumber) VALUES (%s, %s)", (booking_id, booked_room_number))

    db.commit()

    # عرض صفحة التأكيد
    return render_template("booking_done.html",
                           booking_id=booking_id,
                           guest_code=guest_code,
                           guest_name=f"{fname} {lname}",
                           guest_email=email,
                           guest_phone=phone,
                           checkin=checkin,
                           checkout=checkout,
                           nights=nights,
                           room_type=room_type_info,
                           room_number=booked_room_number,
                           subtotal=subtotal,
                           taxes=taxes,
                           tax_percent=tax_percent,
                           total=total_amount)









# @app.route("/leave_review")
# def leave_review():
#     return render_template("leave_review.html")


# @app.route("/submit_review", methods=["POST"])
# def submit_review():
#     fname = request.form.get("f_name").strip()
#     lname = request.form.get("l_name").strip()
#     guest_code = request.form.get("bookingid").strip()  # هنا احنا بناخد GuestCode
#     rating = request.form.get("rating")

#     db = get_db()
#     cursor = db.cursor()

#     # جلب GuestID بناءً على GuestCode و الاسم
#     cursor.execute("""
#         SELECT GuestID 
#         FROM Guest
#         WHERE GuestCode = %s AND FirstName = %s AND LastName = %s
#     """, (guest_code, fname, lname))
    
#     guest = cursor.fetchone()

#     if guest:
#         guest_id = guest[0]
#         # إدخال الريفيو
#         cursor.execute("""
#             INSERT INTO Review (GuestID, Rating) VALUES (%s, %s)
#         """, (guest_id, rating))
#         db.commit()
#         flash("Review submitted successfully!", "success")
#     else:
#         flash("Guest not found or name/code mismatch.", "danger")

#     return redirect(url_for("home_reviews"))



# @app.route("/home")  # غيرنا ال route عشان ما يتعارضش مع /
# def home_reviews():   # غيرنا اسم الدالة
#     db = get_db()
#     cursor = db.cursor(dictionary=True)
    
#     # جلب آخر الـ Reviews
#     cursor.execute("""
#         SELECT g.FirstName, g.LastName, r.Rating 
#         FROM Review r
#         JOIN Guest g ON r.GuestID = g.GuestID
#         ORDER BY r.ReviewID DESC
#     """)
#     reviews = cursor.fetchall()
    
#     return render_template("home.html", reviews=reviews)



@app.route("/leave_review")
def leave_review():
    return render_template("leave_review.html")


@app.route("/submit_review", methods=["POST"])
def submit_review():
    fname = request.form.get("f_name").strip()
    lname = request.form.get("l_name").strip()
    guest_code = request.form.get("bookingid").strip()
    rating = request.form.get("rating")

    db = get_db()
    cursor = db.cursor()

    # جلب GuestID بناءً على GuestCode و الاسم
    cursor.execute("""
        SELECT GuestID 
        FROM Guest
        WHERE GuestCode = %s AND FirstName = %s AND LastName = %s
    """, (guest_code, fname, lname))
    
    guest = cursor.fetchone()

    if guest:
        guest_id = guest[0]
        cursor.execute("INSERT INTO Review (GuestID, Rating) VALUES (%s, %s)", (guest_id, rating))
        db.commit()
        flash("Review submitted successfully!", "success")
    else:
        flash("Guest not found or name/code mismatch.", "danger")

    # ارجع على الهوم اللي بيعرض الريفيوز
    return redirect(url_for("home"))


@app.route("/")
def home():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # جلب آخر الـ Reviews
    cursor.execute("""
        SELECT g.FirstName, g.LastName, r.Rating 
        FROM Review r
        JOIN Guest g ON r.GuestID = g.GuestID
        ORDER BY r.ReviewID DESC
    """)
    reviews = cursor.fetchall()
    
    return render_template("home.html", reviews=reviews)




if __name__ == "__main__":
    app.run(debug=True)
