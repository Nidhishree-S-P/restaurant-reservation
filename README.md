# 🍽️ Restaurant Reservation Management System

A full-stack web application for managing restaurant reservations, table bookings, and customer reviews.  
Built with **Flask (Python)**, **MySQL**, and a **HTML/CSS/JS frontend**.

---

## 📌 Features

### 👤 Customer
- Browse available time slots (displayed as cards).
- Filter/search by:
  - Date & Time
  - Party Size
  - Table Area (Indoor, Outdoor, Private)
  - Price Range
  - Special Features
- Book a table with real-time availability updates.
- View reservation history.
- Modify or cancel bookings (restrictions apply).
- Leave reviews (rating + comment + optional photo).

### 🛠️ Staff
- Add new available time slots with:
  - Date & Time
  - Capacity
  - Location
  - Price per person
  - Features/Notes
- View all reservations.
- Manage walk-in customers.
- Update/cancel bookings.
- Generate daily/weekly booking reports.

### 🔒 Authentication & Authorization
- User registration & login.
- Role-based access (Customer / Staff).
- Secure password hashing.
- Display logged-in username.
- Logout functionality.

---

## 🗂️ Tech Stack

| Layer          | Technology |
|----------------|------------|
| **Backend**    | Flask (Python) |
| **Frontend**   | HTML, CSS, JavaScript |
| **Database**   | MySQL (SQLAlchemy ORM) |
| **Auth**       | Werkzeug Security (Password Hashing) |
| **Styling**    | Tailwind CSS + custom palette |
| **Extras**     | Responsive Design, Animations |

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Nidhishree-S-P/restaurant-reservation.git
cd restaurant-reservation
````

### 2️⃣ Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

### 3️⃣ Configure Database

1. Make sure MySQL is running.
2. Create a database:

```sql
CREATE DATABASE restaurant;
```

3. Update `app.py` with your DB credentials:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/restaurant'
```

4. Initialize tables:

```bash
python
>>> from app import db, app
>>> with app.app_context():
...     db.create_all()
```

---

## ▶️ Running the App

```bash
cd backend
venv\Scripts\activate
python app.py
```

* The app will start at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**
* Frontend HTML pages are served directly from Flask.

---

## 🗄️ Database Schema Overview

### `user`

* `id`, `username`, `password_hash` (TEXT), `role`

### `table_slot`

* `id`, `date_time`, `capacity`, `area`, `price_per_person`, `features`, `is_booked`

### `reservation`

* `id`, `user_id`, `slot_id`, `party_size`, `status`, `special_requests`, `created_at`

### `review`

* `id`, `user_id`, `rating`, `comment`, `image_url`, `created_at`

---

## 🧪 Quick Test Data

Run this SQL in MySQL to create sample data:

```sql
-- Create a staff account (password: admin123)
INSERT INTO user (username, password_hash, role) 
VALUES ('admin', '<hashed_password>', 'staff');

-- Create a customer account (password: user123)
INSERT INTO user (username, password_hash, role) 
VALUES ('customer', '<hashed_password>', 'customer');

-- Add sample table slots
INSERT INTO table_slot (date_time, capacity, area, price_per_person, features, is_booked)
VALUES 
('2025-08-14 19:00:00', 4, 'Indoor', 500, 'Window View', 0),
('2025-08-14 20:00:00', 2, 'Outdoor', 400, 'Quiet Area', 0);
```

To generate `<hashed_password>`, run in Python:

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash("yourpassword"))
```

---

## 📸 Screenshots



