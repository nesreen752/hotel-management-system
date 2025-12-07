from flask import Flask, render_template, request, redirect
from db import get_db

app = Flask(__name__, template_folder="../frontend/templates")


@app.route("/")
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_rooms FROM Room")
    total_rooms = cursor.fetchone()["total_rooms"]

    cursor.execute("SELECT COUNT(*) AS available_rooms FROM Room WHERE Status='Available'")
    available_rooms = cursor.fetchone()["available_rooms"]

    cursor.execute("SELECT COUNT(*) AS total_bookings FROM Booking")
    total_bookings = cursor.fetchone()["total_bookings"]

    return render_template("dashboard.html",
                        total_rooms=total_rooms,
                        available_rooms=available_rooms,
                        total_bookings=total_bookings)


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


if __name__ == "__main__":
    app.run(debug=True)
