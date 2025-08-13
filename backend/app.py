# # backend/app.py
# from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from flask_cors import CORS
# from models import db, User, TableSlot, Reservation, Review

# app = Flask(__name__)
# CORS(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://restaurant_user:strongpassword@localhost/restaurant'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)

# @app.route('/tables', methods=['GET'])
# def get_tables():
#     slots = TableSlot.query.all()
#     return jsonify([{
#         "id": s.id,
#         "date_time": s.date_time,
#         "capacity": s.capacity,
#         "area": s.area,
#         "price_per_person": s.price_per_person,
#         "features": s.features,
#         "is_booked": s.is_booked
#     } for s in slots])

# @app.route('/reserve', methods=['POST'])
# def make_reservation():
#     data = request.json
#     slot = TableSlot.query.get(data['table_slot_id'])
#     if slot.is_booked:
#         return jsonify({"error": "Already booked"}), 400
#     slot.is_booked = True
#     reservation = Reservation(user_id=data['user_id'], table_slot_id=slot.id)
#     db.session.add(reservation)
#     db.session.commit()
#     return jsonify({"message": "Reservation successful"})

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)

# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
from models import db, User, TableSlot, Reservation, Review

app = Flask(__name__)
app.secret_key = "change-me-please"  # TODO: set from env
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://restaurant_user:strongpassword@localhost/restaurant"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# ---------- helpers ----------
def login_required(f):
    @wraps(f)
    def _wrap(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return _wrap

def role_required(role):
    def deco(f):
        @wraps(f)
        def _wrap(*args, **kwargs):
            if session.get("role") != role:
                abort(403)
            return f(*args, **kwargs)
        return _wrap
    return deco

def current_user():
    if not session.get("user_id"): return None
    return User.query.get(session["user_id"])

# ---------- pages ----------
@app.route("/")
def home():
    # initial page; filtering happens via JS fetch to /api/slots
    return render_template("index.html", user=current_user())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(username=request.form["username"]).first()
        if u and check_password_hash(u.password_hash, request.form["password"]):
            session["user_id"] = u.id
            session["role"] = u.role
            session["username"] = u.username
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form.get("role", "customer")
        if not username or not password:
            return render_template("register.html", error="All fields required")
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already taken")
        u = User(username=username, password_hash=generate_password_hash(password), role=role)
        db.session.add(u); db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/me/reservations")
@login_required
def my_reservations_page():
    return render_template("my_reservations.html", user=current_user())

@app.route("/staff/dashboard")
@login_required
@role_required("staff")
def staff_dashboard():
    return render_template("staff_dashboard.html", user=current_user())

# ---------- API: slots (search/filter/list/add) ----------
@app.route("/api/slots", methods=["GET"])
def api_slots():
    # filters: date (YYYY-MM-DD), time (HH:MM), size, area, price_min, price_max, features
    q = TableSlot.query
    # Only show not-booked to customers on the homepage; staff sees all on their page (handled client-side)
    only_available = request.args.get("only_available", "true").lower() == "true"
    if only_available:
        q = q.filter_by(is_booked=False)

    d = request.args.get("date")
    t = request.args.get("time")
    if d:
        day_start = datetime.fromisoformat(d + "T00:00:00")
        day_end = day_start + timedelta(days=1)
        q = q.filter(TableSlot.date_time >= day_start, TableSlot.date_time < day_end)
    if t:
        # match hour+minute on same date range if provided; or generic time-of-day match
        # simplest: match HH:MM string
        try:
            hh, mm = map(int, t.split(":"))
            q = q.filter(db.extract("hour", TableSlot.date_time) == hh,
                         db.extract("minute", TableSlot.date_time) == mm)
        except Exception:
            pass

    size = request.args.get("size", type=int)
    if size:
        q = q.filter(TableSlot.capacity >= size)
    area = request.args.get("area")
    if area:
        q = q.filter(TableSlot.area == area)

    pmin = request.args.get("price_min", type=float)
    pmax = request.args.get("price_max", type=float)
    if pmin is not None: q = q.filter(TableSlot.price_per_person >= pmin)
    if pmax is not None: q = q.filter(TableSlot.price_per_person <= pmax)

    features = request.args.get("features")
    if features:
        # comma separated contains-any
        terms = [f.strip().lower() for f in features.split(",")]
        for term in terms:
            q = q.filter(TableSlot.features.ilike(f"%{term}%"))

    slots = q.order_by(TableSlot.date_time.asc()).all()
    return jsonify([{
        "id": s.id,
        "date_time": s.date_time.isoformat(),
        "capacity": s.capacity,
        "area": s.area,
        "price_per_person": s.price_per_person,
        "features": s.features,
        "is_booked": s.is_booked
    } for s in slots])

@app.route("/api/slots", methods=["POST"])
@login_required
@role_required("staff")
def api_add_slot():
    data = request.json or {}
    try:
        dt = datetime.fromisoformat(data["date_time"])
        slot = TableSlot(
            date_time=dt,
            capacity=int(data["capacity"]),
            area=data.get("area","indoor"),
            price_per_person=float(data.get("price_per_person", 0)),
            features=data.get("features",""),
            is_booked=False
        )
        db.session.add(slot); db.session.commit()
        return jsonify({"ok": True, "id": slot.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

# ---------- API: reservations (book/list/cancel/modify) ----------
@app.route("/api/reservations", methods=["POST"])
@login_required
def api_book():
    data = request.json or {}
    slot_id = int(data.get("table_slot_id", 0))
    party_size = int(data.get("party_size", 1))
    slot = TableSlot.query.get(slot_id)
    if not slot or slot.is_booked or party_size > slot.capacity:
        return jsonify({"ok": False, "error": "Slot not available"}), 400
    slot.is_booked = True
    r = Reservation(user_id=session["user_id"], table_slot_id=slot.id)
    db.session.add(r); db.session.commit()
    return jsonify({"ok": True, "reservation_id": r.id})

@app.route("/api/reservations/me", methods=["GET"])
@login_required
def api_my_reservations():
    rows = (db.session.query(Reservation, TableSlot)
            .join(TableSlot, Reservation.table_slot_id == TableSlot.id)
            .filter(Reservation.user_id == session["user_id"])
            .order_by(Reservation.created_at.desc())
            .all())
    out = []
    for r, s in rows:
        out.append({
            "id": r.id,
            "slot_id": s.id,
            "date_time": s.date_time.isoformat(),
            "capacity": s.capacity,
            "area": s.area,
            "price_per_person": s.price_per_person,
            "features": s.features
        })
    return jsonify(out)

@app.route("/api/reservations/<int:rid>", methods=["DELETE"])
@login_required
def api_cancel_reservation(rid):
    r = Reservation.query.get(rid)
    if not r or r.user_id != session["user_id"]:
        abort(404)
    # simple rule: allow cancel if more than 2 hours before slot time
    slot = TableSlot.query.get(r.table_slot_id)
    if slot and slot.date_time - datetime.utcnow() < timedelta(hours=2):
        return jsonify({"ok": False, "error": "Too late to cancel"}), 400
    if slot:
        slot.is_booked = False
    db.session.delete(r); db.session.commit()
    return jsonify({"ok": True})

# ---------- API: reviews ----------
@app.route("/api/reviews", methods=["GET"])
def api_reviews():
    rows = (db.session.query(Review, User)
            .join(User, Review.user_id == User.id)
            .order_by(Review.created_at.desc())
            .limit(50).all())
    out = []
    for rv, u in rows:
        out.append({
            "id": rv.id, "username": u.username,
            "rating": rv.rating, "comment": rv.comment,
            "created_at": rv.created_at.isoformat()
        })
    return jsonify(out)

@app.route("/api/reviews", methods=["POST"])
@login_required
def api_add_review():
    data = request.json or {}
    rating = int(data.get("rating", 0))
    comment = data.get("comment","").strip()
    if rating < 1 or rating > 5:
        return jsonify({"ok": False, "error":"Rating must be 1-5"}), 400
    rv = Review(user_id=session["user_id"], rating=rating, comment=comment)
    db.session.add(rv); db.session.commit()
    return jsonify({"ok": True, "id": rv.id})

# ---------- simple reports (staff) ----------
@app.route("/api/reports/daily", methods=["GET"])
@login_required
@role_required("staff")
def api_report_daily():
    d = request.args.get("date")
    if d:
        day = date.fromisoformat(d)
    else:
        day = date.today()
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    count = (Reservation.query
             .join(TableSlot, Reservation.table_slot_id == TableSlot.id)
             .filter(TableSlot.date_time >= start, TableSlot.date_time < end)
             .count())
    return jsonify({"date": day.isoformat(), "reservations": count})

@app.route("/api/reports/weekly", methods=["GET"])
@login_required
@role_required("staff")
def api_report_weekly():
    # week starting Monday
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start = datetime.combine(monday, datetime.min.time())
    end = start + timedelta(days=7)
    count = (Reservation.query
             .join(TableSlot, Reservation.table_slot_id == TableSlot.id)
             .filter(TableSlot.date_time >= start, TableSlot.date_time < end)
             .count())
    return jsonify({"week_start": monday.isoformat(), "reservations": count})

# ---------- bootstrap ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



