-- =============================
--  HOTEL MANAGEMENT DATABASE
-- =============================
CREATE DATABASE HOTELDB;
USE HOTELDB;
CREATE USER 'user'@'%' IDENTIFIED BY 'user123';
GRANT ALL PRIVILEGES ON HOTELDB.* TO 'user'@'%';
FLUSH PRIVILEGES;

-- =============================
-- 1) GUEST TABLE
-- =============================
CREATE TABLE Guest (
    GuestID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    PhoneNumber VARCHAR(20) NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50) NOT NULL,
    Country VARCHAR(50) NOT NULL
);

-- =============================
-- 2) ROOMTYPE TABLE
-- =============================
CREATE TABLE RoomType (
    RoomTypeID INT AUTO_INCREMENT PRIMARY KEY,
    TypeName VARCHAR(50) NOT NULL,
    BedCount INT NOT NULL,
    HasAC BOOLEAN NOT NULL,
    HasTV BOOLEAN NOT NULL,
    HasWiFi BOOLEAN NOT NULL,
    HasBar BOOLEAN NOT NULL,
    HasView BOOLEAN NOT NULL,
    HasAirportShuttle BOOLEAN NOT NULL,
    HasConcierge BOOLEAN NOT NULL,
    HasPool BOOLEAN NOT NULL,
    HasSpa BOOLEAN NOT NULL,
    HasMeetingCorner BOOLEAN NOT NULL,
    PricePerNight DECIMAL(10,2) NOT NULL
);

-- =============================
-- 3) ROOM TABLE
-- =============================
CREATE TABLE Room (
    RoomNumber INT AUTO_INCREMENT PRIMARY KEY,
    RoomTypeID INT NOT NULL,
    Status ENUM('Available', 'Occupied', 'Maintenance', 'Cleaning') DEFAULT 'Available',
    FloorLevel INT,
    FOREIGN KEY (RoomTypeID) REFERENCES RoomType(RoomTypeID) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =============================
-- 4) BOOKING TABLE
-- =============================
CREATE TABLE Booking (
    BookingID INT AUTO_INCREMENT PRIMARY KEY,
    GuestID INT NOT NULL,
    CheckInDate DATETIME NOT NULL,
    CheckOutDate DATETIME NOT NULL,
    BookingDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (GuestID) REFERENCES Guest(GuestID) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (CheckOutDate > CheckInDate)
);

-- =============================
-- 5) BOOKING_ROOMS TABLE
-- =============================
CREATE TABLE Booking_Rooms (
    BookingID INT NOT NULL,
    RoomNumber INT NOT NULL,
    PRIMARY KEY (BookingID, RoomNumber),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (RoomNumber) REFERENCES Room(RoomNumber) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =============================
-- 6) PAYMENT TABLE
-- =============================
CREATE TABLE Payment (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    BookingID INT UNIQUE NOT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    Method ENUM('Cash', 'Credit Card', 'Debit Card') NOT NULL,
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =============================
-- 7) STAFF TABLE
-- =============================
CREATE TABLE Staff (
    StaffID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Role VARCHAR(50) NOT NULL,
    Phone VARCHAR(20) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Salary DECIMAL(10,2)
);

-- =============================
-- 8) ROOM ASSIGNMENT TABLE
-- =============================
CREATE TABLE RoomAssignment (
    AssignmentID INT AUTO_INCREMENT PRIMARY KEY,
    RoomNumber INT NOT NULL,
    DateAssigned DATETIME NOT NULL,
    DateCompleted DATETIME,
    FOREIGN KEY (RoomNumber) REFERENCES Room(RoomNumber) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =============================
-- 9) ROOMASSIGNMENT_STAFF TABLE
-- =============================
CREATE TABLE RoomAssignment_Staff (
    AssignmentID INT NOT NULL,
    StaffID INT NOT NULL,
    PRIMARY KEY (AssignmentID, StaffID),
    FOREIGN KEY (AssignmentID) REFERENCES RoomAssignment(AssignmentID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =============================
-- 10) REVIEW TABLE
-- =============================
CREATE TABLE Review (
    ReviewID INT AUTO_INCREMENT PRIMARY KEY,
    GuestID INT NOT NULL,
    Rating INT NOT NULL CHECK (Rating BETWEEN 1 AND 5),
    FOREIGN KEY (GuestID) REFERENCES Guest(GuestID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ===========================================
-- INSERT MOCKING DATA
-- ===========================================

-- ROOM TYPES
INSERT INTO RoomType (TypeName, BedCount, HasAC, HasTV, HasWiFi, HasBar, HasView,
    HasAirportShuttle, HasConcierge, HasPool, HasSpa, HasMeetingCorner, PricePerNight) VALUES
('Classic',1,1,1,1,0,0,0,0,0,0,0,1000),
('Deluxe',1,1,1,1,1,1,0,1,0,0,0,3500),
('Business',1,1,1,1,1,1,0,1,0,0,1,5000),
('Suite',2,1,1,1,1,1,1,1,1,1,0,7000),
('VIP',3,1,1,1,1,1,1,1,1,1,1,10000);

-- GUESTS
INSERT INTO Guest (FirstName, LastName, Email, PhoneNumber, City, State, Country) VALUES
('Ahmed','Mostafa','ahmed@example.com','01000111222','Cairo','Cairo','Egypt'),
('Sara','Mahmoud','sara@example.com','01055667788','Giza','Giza','Egypt'),
('John','Smith','john@example.com','01298765432','Alex','Alexandria','Egypt');

-- ROOMS
INSERT INTO Room (RoomTypeID,Status,FloorLevel) VALUES
(1,'Available',1),
(1,'Occupied',1),
(2,'Available',2),
(3,'Maintenance',2),
(4,'Available',3),
(5,'Available',4);

-- BOOKINGS
INSERT INTO Booking (GuestID, CheckInDate, CheckOutDate) VALUES
(1,'2025-12-10 15:00:00','2025-12-15 15:00:00'),
(2,'2025-12-13 15:00:00','2025-12-18 15:00:00');

-- Booking Rooms
INSERT INTO Booking_Rooms VALUES
(1,3),
(1,2),
(2,1);

-- PAYMENTS
INSERT INTO Payment (BookingID, Amount, Date, Method) VALUES
(1,5000,'2025-12-15 15:00:00','Credit Card'),
(2,7000,'2025-12-18 15:00:00','Cash');

-- STAFF
INSERT INTO Staff (FirstName, LastName, Role, Phone, Email, Salary) VALUES
('Omar','Hassan','Cleaner','01000000001','omar@hotel.com',6000),
('Mona','Ali','Receptionist','01000000002','mona@hotel.com',8000),
('Khaled','Nabil','Manager','01000000003','khaled@hotel.com',15000);

-- ROOM ASSIGNMENTS
INSERT INTO RoomAssignment (RoomNumber, DateAssigned, DateCompleted) VALUES
(5,'2025-12-10 15:00:00','2025-12-10 15:00:00'),
(6,'2025-12-11 15:00:00','2025-12-11 15:00:00');

-- ROOM ASSIGNMENT STAFF
INSERT INTO RoomAssignment_Staff VALUES
(1,1),
(1,2),
(2,1),
(2,3);

-- REVIEWS
INSERT INTO Review (GuestID, Rating) VALUES
(1,5),
(2,4),
(3,3);
