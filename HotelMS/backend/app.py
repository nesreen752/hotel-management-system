
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_db
from datetime import datetime
import random

app = Flask(__name__, template_folder="../frontend/templates", static_folder='../frontend/static')
app.secret_key = "secret123"   # Needed for login sessions

def generate_staff_id():
    return str(random.randint(10000000, 99999999))

def generate_booking_id():
    """Generate a random booking ID like HLS-123456"""
    return f"HLS-{random.randint(100000, 999999)}"

# ------------------- HOME & ROOMS -------------------
# @app.route("/")
# def home():
#     return render_template("Home.html")

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

# ------------------- ADD ROOM TYPE -------------------
@app.route("/room-type/add", methods=["GET", "POST"])
def add_room_type():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()

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

        cursor.execute("""
            INSERT INTO RoomType (TypeName, Beds, AC, TV, WiFi, AirportShuttle, Concierge, Pool, Spa, MeetingCorner)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (type_name, beds, ac, tv, wifi, airport_shuttle, concierge, pool, spa, meeting_corner))
        db.commit()

        return redirect("/room-types")

    return render_template("add_room_type.html")

# ------------------- ADD ROOM -------------------
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

# ------------------- BOOKING ROOMS LIST -------------------
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
    bookings_rooms = []

    for row in raw_bookings:
        formatted = row.copy()
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
            formatted['PaymentDate'] = None
        bookings_rooms.append(formatted)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    return render_template("booking_rooms_list.html", bookings_rooms=bookings_rooms, current_time=current_time)

# ------------------- STAFF -------------------
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

        session['staff_id'] = staff['StaffID']
        session['name'] = staff['FirstName']
        session['role'] = staff['Role']

        flash(f'Welcome back, {staff["FirstName"]}!', 'success')
        user_role = staff['Role'].lower()
        if user_role == "manager":
            return redirect('/manager')
        elif user_role == "receptionist":
            return redirect('/reception')
        elif user_role == "roomservice":
            return redirect('/roomservice')

    return render_template("login.html")

# ------------------- ROLE PAGES -------------------
@app.route("/manager")
def manager_page():
    return render_template("Home.html")

@app.route("/reception")
def reception_page():
    return render_template("booking_rooms_list.html")

@app.route("/roomservice")
def roomservice_page():
    return render_template("dashboard.html")

# ------------------- LOGOUT -------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')

# ------------------- BOOKING -------------------
@app.route("/booking", methods=["GET", "POST"])
def booking():
    return render_template("booking.html")

from flask import flash, redirect, url_for

from flask import Flask, request, render_template, flash, redirect, url_for
import random
from datetime import datetime

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









@app.route("/leave_review")
def leave_review():
    return render_template("leave_review.html")


@app.route("/submit_review", methods=["POST"])
def submit_review():
    fname = request.form.get("f_name").strip()
    lname = request.form.get("l_name").strip()
    guest_code = request.form.get("bookingid").strip()  # هنا احنا بناخد GuestCode
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
        # إدخال الريفيو
        cursor.execute("""
            INSERT INTO Review (GuestID, Rating) VALUES (%s, %s)
        """, (guest_id, rating))
        db.commit()
        flash("Review submitted successfully!", "success")
    else:
        flash("Guest not found or name/code mismatch.", "danger")

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

# ------------------- MAIN -------------------
if __name__ == "__main__":
    app.run(debug=True)
