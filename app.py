"""
Smart Commune DSM - huduma ya arifa (USSD + SMS + website).
Endesha kwa:  python app.py
Bila funguo za Africa's Talking, SMS zitaandikwa kwenye terminal tu (hali ya majaribio).
"""
import os
import re
import sqlite3
import time
from datetime import datetime

from flask import Flask, Response, jsonify, render_template_string, request

app = Flask(__name__)

DB_FILE = "commune.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "badilisha-hii")
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "")
AT_SENDER = os.environ.get("AT_SENDER", "")  # hiari: jina/namba ya mtumaji

# Barabara (ongeza au badilisha hapa). Namba ya kwanza ndiyo inayotumika kwenye USSD.
ROAD_LIST = [
    ("morogoro", "Morogoro Rd"),
    ("bagamoyo", "Bagamoyo Rd"),
    ("nyerere", "Nyerere Rd"),
    ("kilwa", "Kilwa Rd"),
    ("kigamboni", "Kigamboni"),
]
ROADS = dict(ROAD_LIST)
LEVELS = {"safi": "Salama", "wastani": "Wastani", "nzito": "Foleni kubwa"}
KINDS = {"1": "Ajali", "2": "Foleni kubwa", "3": "Mafuriko", "4": "Barabara imefungwa"}


# ---------- Database ----------
def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def init_db():
    with db() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS subscribers(
                phone TEXT, road TEXT, created TEXT, PRIMARY KEY(phone, road));
            CREATE TABLE IF NOT EXISTS status(
                road TEXT PRIMARY KEY, level TEXT, note TEXT, updated TEXT);
            CREATE TABLE IF NOT EXISTS reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT, road TEXT, place TEXT, details TEXT, phone TEXT, created TEXT);
            """
        )
        for key in ROADS:
            c.execute("INSERT OR IGNORE INTO status VALUES(?,?,?,?)",
                      (key, "safi", "Hakuna taarifa mpya", now()))


# ---------- Vifaa vidogo ----------
def clean_phone(raw):
    p = re.sub(r"[^\d+]", "", raw or "")
    if p.startswith("0"):
        p = "+255" + p[1:]
    elif p.startswith("255"):
        p = "+" + p
    return p if re.fullmatch(r"\+255\d{9}", p) else None


def pick_road(number):
    """Namba ya menyu ya USSD (1,2,3...) -> jina fupi la barabara."""
    if number.isdigit() and 1 <= int(number) <= len(ROAD_LIST):
        return ROAD_LIST[int(number) - 1][0]
    return None


def road_menu():
    return "\n".join(f"{i}. {name}" for i, (_, name) in enumerate(ROAD_LIST, 1))


def send_sms(phones, message):
    phones = list(phones)
    if not phones:
        return
    message = message[:300]
    if not AT_API_KEY:
        print("[SMS ya majaribio]", phones, "->", message)
        return
    try:
        import africastalking
        africastalking.initialize(AT_USERNAME, AT_API_KEY)
        africastalking.SMS.send(message, phones, AT_SENDER or None)
    except Exception as err:  # usiache seva ife kwa sababu ya SMS
        print("Hitilafu ya SMS:", err)


def subscribe(phone, road):
    with db() as c:
        c.execute("INSERT OR IGNORE INTO subscribers VALUES(?,?,?)", (phone, road, now()))


def unsubscribe(phone):
    with db() as c:
        c.execute("DELETE FROM subscribers WHERE phone=?", (phone,))


def get_status(road):
    with db() as c:
        return c.execute("SELECT * FROM status WHERE road=?", (road,)).fetchone()


def notify_road(road, message):
    """Tuma SMS kwa wote waliojisajili kwa barabara hii. Inarudisha idadi."""
    with db() as c:
        phones = [r["phone"] for r in c.execute(
            "SELECT phone FROM subscribers WHERE road=?", (road,))]
    send_sms(phones, message)
    return len(phones)


def add_report(kind, road, place, details, phone):
    with db() as c:
        c.execute(
            "INSERT INTO reports(kind,road,place,details,phone,created) VALUES(?,?,?,?,?,?)",
            (kind, road, place, details, phone, now()))
    # Arifa ya haraka. Imeandikwa wazi kuwa haijathibitishwa.
    where = f" {place}" if place else ""
    notify_road(road, f"Taarifa ya wananchi (haijathibitishwa) - {ROADS[road]}: {kind}{where}.")


# ---------- USSD (Africa's Talking inatuma POST hapa) ----------
@app.route("/ussd", methods=["POST"])
def ussd():
    phone = clean_phone(request.form.get("phoneNumber"))
    text = request.form.get("text", "")
    parts = text.split("*") if text else []

    def con(msg):
        return Response("CON " + msg, mimetype="text/plain")

    def end(msg):
        return Response("END " + msg, mimetype="text/plain")

    if not parts:
        return con("Smart Commune DSM\n1. Hali ya barabara\n2. Pata arifa\n"
                   "3. Toa taarifa\n4. Acha arifa")

    top = parts[0]

    if top == "1":
        if len(parts) == 1:
            return con("Chagua barabara:\n" + road_menu())
        road = pick_road(parts[1])
        if road:
            s = get_status(road)
            return end(f"{ROADS[road]}: {LEVELS[s['level']]}. {s['note']} ({s['updated']})")

    elif top == "2":
        if len(parts) == 1:
            return con("Pata arifa za barabara:\n" + road_menu())
        road = pick_road(parts[1])
        if road and phone:
            subscribe(phone, road)
            return end(f"Umejiunga. Utapata arifa za {ROADS[road]} kwa SMS.")

    elif top == "3":
        if len(parts) == 1:
            return con("Nini kimetokea?\n" + "\n".join(f"{k}. {v}" for k, v in KINDS.items()))
        if len(parts) == 2:
            return con("Barabara gani?\n" + road_menu())
        kind, road = KINDS.get(parts[1]), pick_road(parts[2])
        if kind and road:
            add_report(kind, road, "", "kupitia USSD", phone or "")
            return end("Asante. Taarifa yako imetumwa kwa wenzako wa njia hiyo.")

    elif top == "4":
        if phone:
            unsubscribe(phone)
        return end("Umeacha kupokea arifa. Karibu tena.")

    return end("Chaguo si sahihi. Piga tena.")


# ---------- SMS inayoingia (Africa's Talking inatuma POST hapa) ----------
@app.route("/sms", methods=["POST"])
def sms_incoming():
    phone = clean_phone(request.form.get("from"))
    words = request.form.get("text", "").strip().upper().split()
    if not phone or not words:
        return "OK"
    command = words[0]
    road = words[1].lower() if len(words) > 1 and words[1].lower() in ROADS else None

    if command == "JIUNGE" and road:
        subscribe(phone, road)
        send_sms([phone], f"Umejiunga na arifa za {ROADS[road]}. Tuma ONDOA kuacha.")
    elif command == "HALI" and road:
        s = get_status(road)
        send_sms([phone], f"{ROADS[road]}: {LEVELS[s['level']]}. {s['note']}")
    elif command == "ONDOA":
        unsubscribe(phone)
        send_sms([phone], "Umeacha kupokea arifa za Smart Commune DSM.")
    else:
        send_sms([phone], "Tuma: JIUNGE MOROGORO, HALI KILWA au ONDOA. "
                          "Barabara: " + ", ".join(k.upper() for k in ROADS))
    return "OK"


# ---------- Website (JavaScript) inaongea na seva hapa ----------
@app.after_request
def cors(resp):
    # "*" inaruhusu website kutoka popote. Ukiweka mtandaoni, weka anwani yako: ALLOWED_ORIGIN
    resp.headers["Access-Control-Allow-Origin"] = os.environ.get("ALLOWED_ORIGIN", "*")
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    return resp


@app.route("/api/status")
def api_status():
    with db() as c:
        rows = {r["road"]: r for r in c.execute("SELECT * FROM status")}
    roads = [{"id": k, "name": n, "level": rows[k]["level"],
              "note": rows[k]["note"], "updated": rows[k]["updated"]}
             for k, n in ROAD_LIST if k in rows]
    return jsonify(updated=now(), roads=roads)


RATE = {}  # anwani ya mtumaji -> nyakati za taarifa zake


def too_many(ip, limit=5, window=3600):
    """Zuia mtu mmoja kutuma taarifa nyingi (ulinzi dhidi ya barua taka)."""
    t = time.time()
    RATE[ip] = [x for x in RATE.get(ip, []) if t - x < window]
    if len(RATE[ip]) >= limit:
        return True
    RATE[ip].append(t)
    return False


def safe(text, n):
    return re.sub(r"[\x00-\x1f]", " ", text or "").strip()[:n]


@app.route("/report", methods=["POST"])
def report_web():
    if too_many(request.remote_addr or "?"):
        return jsonify(error="Umetuma taarifa nyingi. Jaribu tena baadaye."), 429
    road = request.form.get("road", "")
    kind = safe(request.form.get("kind"), 40)
    if road not in ROADS or not kind:
        return jsonify(error="Chagua barabara na aina ya tatizo."), 400
    add_report(kind, road, safe(request.form.get("place"), 80),
               safe(request.form.get("details"), 300),
               clean_phone(request.form.get("phone")) or "")
    return jsonify(message="Asante! Taarifa yako imetumwa kwa watu wanaotumia njia hiyo.")


# ---------- Usajili kutoka kwenye website ----------
@app.route("/subscribe", methods=["POST"])
def subscribe_web():
    phone = clean_phone(request.form.get("phone"))
    roads = [r for r in request.form.getlist("roads") if r in ROADS]
    wants_json = "application/json" in request.headers.get("Accept", "")
    if not phone or not roads:
        msg = "Namba ya simu au barabara si sahihi."
        return (jsonify(error=msg), 400) if wants_json else (f"<h2>{msg} Rudi nyuma ujaribu tena.</h2>", 400)
    for r in roads:
        subscribe(phone, r)
    names = ", ".join(ROADS[r] for r in roads)
    send_sms([phone], f"Karibu Smart Commune DSM. Utapata arifa za: {names}. Tuma ONDOA kuacha.")
    msg = "Asante! Umejisajili. Utapata SMS ya uthibitisho."
    return jsonify(message=msg) if wants_json else f"<h2>{msg}</h2>"


# ---------- Ukurasa wa msimamizi ----------
ADMIN_HTML = """
<!doctype html><html lang="sw"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Msimamizi - Smart Commune DSM</title>
<body style="font-family:Arial;max-width:640px;margin:24px auto;padding:0 16px">
<h1>Msimamizi</h1>
{% if msg %}<p style="background:#FFF6D6;padding:10px;border-radius:6px">{{ msg }}</p>{% endif %}
<form method="post">
  <p><label>Password<br><input type="password" name="password" required style="width:100%;padding:8px"></label></p>
  <p><label>Barabara<br><select name="road" style="width:100%;padding:8px">
    {% for key, name in roads %}<option value="{{ key }}">{{ name }}</option>{% endfor %}
  </select></label></p>
  <p><label>Hali<br><select name="level" style="width:100%;padding:8px">
    <option value="safi">Salama</option><option value="wastani">Wastani</option>
    <option value="nzito">Foleni kubwa</option></select></label></p>
  <p><label>Maelezo mafupi<br><input name="note" maxlength="120" required style="width:100%;padding:8px"
    placeholder="Mfano: Ajali Ubungo, tumia Mandela Rd"></label></p>
  <button style="padding:12px 20px;font-size:1rem">Sasisha na tuma SMS kwa wote</button>
</form>
<h2>Muhtasari</h2>
<p>Waliojisajili: <b>{{ subs }}</b> | Taarifa za wananchi: <b>{{ reps|length }}</b> (za mwisho 10)</p>
<ul>{% for r in reps %}<li>{{ r.created }} - {{ r.kind }} - {{ r.road }} {{ r.place }}</li>{% endfor %}</ul>
</body></html>
"""


@app.route("/admin", methods=["GET", "POST"])
def admin():
    msg = ""
    if request.method == "POST":
        road = request.form.get("road", "")
        level = request.form.get("level", "")
        note = request.form.get("note", "")[:120]
        if request.form.get("password") != ADMIN_PASSWORD:
            msg = "Password si sahihi."
        elif road in ROADS and level in LEVELS:
            with db() as c:
                c.execute("UPDATE status SET level=?, note=?, updated=? WHERE road=?",
                          (level, note, now(), road))
            sent = notify_road(road, f"{ROADS[road]}: {LEVELS[level]}. {note}")
            msg = f"Imesasishwa. SMS zimetumwa kwa watu {sent}."
    with db() as c:
        subs = c.execute("SELECT COUNT(DISTINCT phone) FROM subscribers").fetchone()[0]
        reps = c.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 10").fetchall()
    return render_template_string(ADMIN_HTML, msg=msg, roads=ROAD_LIST, subs=subs, reps=reps)


@app.route("/")
def home():
    return "Smart Commune DSM inafanya kazi. Msimamizi: /admin"


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
