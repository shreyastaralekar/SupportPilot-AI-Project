import functools, re, time
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func, insert, select, update
from werkzeug.security import check_password_hash, generate_password_hash
import config, db, ml

DEPTS = ["IT", "HR", "Finance", "Sales", "Operations", "Marketing"]
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NAME = re.compile(r"[^\W\d_](?:[^\W\d_]|[ .'-])+")
FAILS = {}

app = Flask(__name__)
app.config.update(SECRET_KEY=config.SECRET_KEY, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)
iso = lambda d: d.isoformat() + "Z" if d else None
strong = lambda p: len(p) >= 8 and all(re.search(x, p) for x in (r"[a-z]", r"[A-Z]", r"\d", r"[^\w\s]"))

with db.engine.begin() as c:   # seed the admin account once
    if not c.execute(select(db.users.c.id).where(db.users.c.role == "admin")).first():
        c.execute(insert(db.users).values(role="admin", login_id=config.ADMIN_ID, name="System Admin", email="admin@supportpilot.local",
                                          department="IT", password_hash=generate_password_hash(config.ADMIN_PASSWORD), created_at=now()))


def guard(role=None):
    def deco(f):
        @functools.wraps(f)
        def wrap(*a, **k):
            api = request.path.startswith("/api/")
            if "uid" not in session:
                return (jsonify(error="Please sign in."), 401) if api else redirect(url_for("login_page"))
            if role and session["role"] != role:
                return (jsonify(error="You do not have access to this."), 403) if api else redirect(url_for("home"))
            return f(*a, **k)
        return wrap
    return deco


@app.after_request
def no_cache(r):
    if not request.path.startswith("/static"):
        r.headers["Cache-Control"] = "no-store"
    return r


@app.get("/")
def home():
    return redirect(url_for("dashboard" if "uid" in session else "login_page"))


@app.get("/login")
def login_page():
    return redirect(url_for("dashboard")) if "uid" in session else render_template("auth.html", depts=DEPTS)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.get("/dashboard")
@guard()
def dashboard():
    return render_template("dashboard.html", role=session["role"], name=session["name"], dept=session["dept"], email=session["email"])


@app.post("/api/signup")
def signup():
    d = request.get_json(silent=True) or {}
    name, email, dept = (str(d.get(k, "")).strip() for k in ("name", "email", "department"))
    pw, confirm = str(d.get("password", "")), str(d.get("confirm", ""))
    e = {}
    if len(name) > 60 or not NAME.fullmatch(name): e["name"] = "Enter your full name (letters only)."
    if not EMAIL.match(email): e["email"] = "Enter a valid work email."
    if dept not in DEPTS: e["department"] = "Choose your department."
    if not strong(pw): e["password"] = "Use 8+ characters with upper and lower case, a number and a symbol."
    if pw != confirm: e["confirm"] = "Passwords do not match."
    if e:
        return jsonify(error="Please fix the highlighted fields.", fields=e), 400
    with db.engine.begin() as c:
        if c.execute(select(db.users.c.id).where(db.users.c.login_id == email.lower())).first():
            return jsonify(error="An account with this email already exists.", fields={"email": "Already registered. Sign in instead."}), 409
        c.execute(insert(db.users).values(role="employee", login_id=email.lower(), name=name, email=email.lower(), department=dept,
                                          password_hash=generate_password_hash(pw), created_at=now()))
    return jsonify(ok=True), 201


@app.post("/api/login")
def login():
    d = request.get_json(silent=True) or {}
    role, lid, pw = d.get("role"), str(d.get("login_id", "")).strip().lower(), str(d.get("password", ""))
    key = f"{role}:{lid}"
    n, t = FAILS.get(key, (0, 0))
    if n and time.time() - t > 300:
        FAILS.pop(key, None); n = 0
    if n >= 5:
        return jsonify(error="Too many failed attempts. Try again in 5 minutes."), 429
    u = None
    if role in ("admin", "employee") and lid:
        with db.engine.connect() as c:
            u = c.execute(select(db.users).where(func.lower(db.users.c.login_id) == lid, db.users.c.role == role)).first()
    if not u or not check_password_hash(u.password_hash, pw):
        FAILS[key] = (n + 1, time.time())
        return jsonify(error="Incorrect ID or password."), 401
    FAILS.pop(key, None)
    session.clear()
    session.permanent = True
    session.update(uid=u.id, role=u.role, name=u.name, dept=u.department, email=u.email)
    return jsonify(ok=True)


@app.post("/api/tickets")
@guard("employee")
def create_ticket():
    d = request.get_json(silent=True) or {}
    title, desc = str(d.get("title", "")).strip(), str(d.get("description", "")).strip()
    e = {}
    if not 5 <= len(title) <= 120: e["title"] = "Title must be 5 to 120 characters."
    if not 20 <= len(desc) <= 2000: e["description"] = "Describe the issue in 20 to 2000 characters."
    if e:
        return jsonify(error="Please fix the highlighted fields.", fields=e), 400
    cat, sub, sub_conf, sev, sev_conf = ml.classify(f"{title}. {desc}")
    prio, hours = ml.priority_for(sev, f"{title} {desc}")
    t = now()
    with db.engine.begin() as c:
        pk = c.execute(insert(db.tickets).values(
            user_id=session["uid"], title=title, description=desc, category=cat, sub_category=sub, severity=sev, confidence=sev_conf,
            ai_status="Classified" if sub_conf >= 0.45 else "Needs review", priority=prio, sla_hours=hours, status="Open",
            created_at=t, due_at=t + timedelta(hours=hours))).inserted_primary_key[0]
        tid = f"T-{t.year}-{pk:04d}"
        c.execute(update(db.tickets).where(db.tickets.c.id == pk).values(ticket_id=tid))
    return jsonify(ticket_id=tid, title=title, priority=prio, sla_hours=hours, created_at=iso(t), due_at=iso(t + timedelta(hours=hours))), 201


@app.get("/api/tickets")
@guard()
def list_tickets():
    admin = session["role"] == "admin"
    q = select(db.tickets, db.users.c.name, db.users.c.email, db.users.c.department).join(
        db.users, db.users.c.id == db.tickets.c.user_id).order_by(db.tickets.c.id.desc())
    if not admin:
        q = q.where(db.tickets.c.user_id == session["uid"])
    with db.engine.connect() as c:
        rows = c.execute(q).all()
    out = []
    for t in rows:
        r = dict(ticket_id=t.ticket_id, title=t.title, priority=t.priority, sla_hours=t.sla_hours, status=t.status,
                 created_at=iso(t.created_at), due_at=iso(t.due_at), closed_at=iso(t.closed_at))
        if admin:   # classification details are admin-only
            r.update(description=t.description, category=t.category, sub_category=t.sub_category, severity=t.severity,
                     confidence=round((t.confidence or 0) * 100), ai_status=t.ai_status, requester=t.name, email=t.email, department=t.department)
        out.append(r)
    return jsonify(tickets=out, accuracy=ml.ACCURACY if admin else None)


@app.post("/api/tickets/<tid>/status")
@guard("admin")
def set_status(tid):
    to = (request.get_json(silent=True) or {}).get("status")
    if to not in ("Open", "Closed"):
        return jsonify(error="Invalid status."), 400
    with db.engine.begin() as c:
        n = c.execute(update(db.tickets).where(db.tickets.c.ticket_id == tid).values(status=to, closed_at=now() if to == "Closed" else None)).rowcount
    return (jsonify(ok=True) if n else (jsonify(error="Ticket not found."), 404))


if __name__ == "__main__":
    app.run(debug=True)
