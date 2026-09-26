from flask import Flask, request, redirect, send_file, session, url_for, render_template_string, send_from_directory
import sqlite3, os, shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # sessions

# --- Upload folders ---
UPLOAD_FOLDER = 'uploads'
CUSTOMER_UPLOAD_FOLDER = 'customer_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CUSTOMER_UPLOAD_FOLDER, exist_ok=True)

# --- DB Initialization ---
def init_staff_db():
    with sqlite3.connect("bank_staff.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, dob TEXT, gender TEXT, blood_group TEXT, aadhar TEXT,
                pan TEXT, address TEXT, email TEXT, phone TEXT UNIQUE,
                emergency_contact TEXT, employee_id TEXT, department TEXT,
                role TEXT, joining_date TEXT, password TEXT,
                photo TEXT, aadhar_copy TEXT, pan_copy TEXT
            )
        """)
        conn.commit()

def init_customer_db():
    with sqlite3.connect("bank_customers.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT, dob TEXT, gender TEXT, email TEXT, phone TEXT,
                address TEXT, city TEXT, state TEXT, zip TEXT, country TEXT,
                id_type TEXT, id_number TEXT, id_file TEXT,
                username TEXT UNIQUE, password TEXT,
                account_type TEXT, agreed_terms INTEGER, agreed_communication INTEGER, account_number TEXT UNIQUE
            )
        """)
        conn.commit()

init_staff_db()
init_customer_db()

# --- Utility: update customer list ---
def update_customer_list_html():
    conn = sqlite3.connect("bank_customers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    rows = cursor.fetchall()
    conn.close()

    html = """<html><head><title>Customer List</title></head><body>
    <h2>All Registered Customers</h2>
    <table border=1><tr>
    <th>Account Number</th><th>Full Name</th><th>DOB</th><th>Gender</th><th>Email</th>
    <th>Phone</th><th>Address</th><th>City</th><th>ZIP</th><th>Aadhar Number</th>
    <th>PAN Card</th><th>Username</th><th>Password</th><th>Account Type</th>
    </tr>"""
    for r in rows:
        html += f"<tr><td>{r[19]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td>"
        html += f"<td>{r[5]}</td><td>{r[6]}</td><td>{r[7]}</td><td>{r[9]}</td><td>{r[12]}</td>"
        html += f"<td>{r[10]}</td><td>{r[14]}</td><td>{r[15]}</td><td>{r[16]}</td></tr>"
    html += "</table></body></html>"

    with open("customer_list.html", "w", encoding="utf-8") as f:
        f.write(html)

# --- Utility: update staff list ---
def update_staff_list_html():
    with sqlite3.connect("bank_staff.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM staff")
        rows = cursor.fetchall()
    headers = ["ID","Name","DOB","Gender","Blood","Aadhar","PAN","Address","Email","Phone","Emergency","EmpID","Dept","Role","Join Date","Password","Photo","Aadhar Copy","PAN Copy"]
    html = "<html><head><title>Staff List</title></head><body><h2>All Staff</h2><table border=1><tr>"
    html += "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    for row in rows:
        html += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    html += "</table></body></html>"
    with open("staff_list.html", "w", encoding="utf-8") as f:
        f.write(html)

# --- Routes ---

@app.route("/")
def home():
    return send_file("index.html")

# --- Staff Registration ---
@app.route("/staff/register", methods=["GET", "POST"])
def staff_register():
    if request.method=="GET":
        return send_file("register_staff.html")
    form = request.form
    files = request.files

    def save_file(f):
        if f and f.filename:
            filename = f"{int(datetime.now().timestamp())}_{secure_filename(f.filename)}"
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            return filename
        return ""
    photo = save_file(files.get("photo"))
    aadhar_copy = save_file(files.get("aadhar_copy"))
    pan_copy = save_file(files.get("pan_copy"))

    with sqlite3.connect("bank_staff.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM staff")
        count = cursor.fetchone()[0]
        emp_id = f"TRBEMP{str(count+1).zfill(3)}"
        cursor.execute("""
            INSERT INTO staff (name,dob,gender,blood_group,aadhar,pan,address,email,phone,emergency_contact,employee_id,department,role,joining_date,password,photo,aadhar_copy,pan_copy)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            form.get("name"), form.get("dob"), form.get("gender"), form.get("blood_group"),
            form.get("aadhar"), form.get("pan"), form.get("address"), form.get("email"),
            form.get("phone"), form.get("emergency_contact"), emp_id, form.get("department"),
            form.get("role"), form.get("joining_date"), form.get("password"),
            photo, aadhar_copy, pan_copy
        ))
        conn.commit()
    update_staff_list_html()
    return redirect("/success")

# --- Staff Login ---
# --- Staff Login ---
@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    error = ""
    if request.method == "POST":
        emp_id = request.form.get("employee_id").strip()
        password = request.form.get("password").strip()

        conn = sqlite3.connect("bank_staff.db")
        cursor = conn.cursor()
        cursor.execute("SELECT employee_id FROM staff WHERE employee_id=? AND password=?", 
                       (emp_id, password))
        staff = cursor.fetchone()
        conn.close()

        if staff:
            session["staff_id"] = emp_id
            return redirect("/staff/dashboard")
        else:
            error = "❌ Invalid Employee ID or Password"

    return render_template("staff_login.html", error=error)

# --- Staff Dashboard ---
@app.route("/staff/dashboard")
def staff_dashboard():
    if "staff_id" not in session:
        return redirect("/staff/login")

    emp_id = session["staff_id"]

    conn = sqlite3.connect("bank_staff.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT id, full_name, dob, gender, blood_group, aadhar_number, pan_number,
                             address, email, phone, emergency_contact,
                             employee_id, department, role, joining_date, password
                      FROM staff WHERE employee_id=?""", (emp_id,))
    details = cursor.fetchone()
    conn.close()

    if not details:
        return "Staff not found"

    # staff uploads folder (photo only)
    staff_folder = os.path.join("staff_uploads", emp_id)
    photo_url = "https://via.placeholder.com/200"
    if os.path.exists(staff_folder):
        for f in os.listdir(staff_folder):
            if "photo" in f.lower():
                photo_url = f"/staff_uploads/{emp_id}/{f}"

    dashboard_html = """<!DOCTYPE html>
<html>
<head><title>Staff Dashboard</title></head>
<body>
<h2>Welcome, {{ details[1] }}</h2>
<div style="display:flex; gap:20px; margin-top:20px;">
<div>
  <h3>Photo</h3>
  <img src="{{ photo_url }}" width="200" height="200" alt="Photo">
</div>
<div>
  <p><b>Database ID:</b> {{ details[0] }}</p>
  <p><b>Employee ID:</b> {{ details[11] }}</p>
  <p><b>Full Name:</b> {{ details[1] }}</p>
  <p><b>DOB:</b> {{ details[2] }}</p>
  <p><b>Gender:</b> {{ details[3] }}</p>
  <p><b>Blood Group:</b> {{ details[4] }}</p>
  <p><b>Aadhar Number:</b> {{ details[5] }}</p>
  <p><b>PAN Number:</b> {{ details[6] }}</p>
  <p><b>Address:</b> {{ details[7] }}</p>
  <p><b>Email:</b> {{ details[8] }}</p>
  <p><b>Phone:</b> {{ details[9] }}</p>
  <p><b>Emergency Contact:</b> {{ details[10] }}</p>
  <p><b>Department:</b> {{ details[12] }}</p>
  <p><b>Role:</b> {{ details[13] }}</p>
  <p><b>Joining Date:</b> {{ details[14] }}</p>
</div>
</div>
<form method="post" action="/logout">
  <button type="submit">Logout</button>
</form>
</body></html>"""

    return render_template_string(dashboard_html,
                                  details=details,
                                  photo_url=photo_url)


# --- Customer Registration ---
@app.route("/customer/register", methods=["GET"])
def show_customer_register():
    return send_file("register_customer.html")

@app.route("/customer/register", methods=["POST"])
def register_customer():
    form = request.form
    files = request.files
    full_name = f"{form.get('first_name')} {form.get('last_name')}"
    pincode = form.get("pincode", "")
    last_three = pincode[-3:] if len(pincode)>=3 else "000"
    with sqlite3.connect("bank_customers.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers WHERE account_number LIKE ?", (f"TRB{last_three}%",))
        count = cursor.fetchone()[0]
        account_number = f"TRB{last_three}{str(count+1).zfill(3)}"
    account_folder = os.path.join(CUSTOMER_UPLOAD_FOLDER, account_number)
    os.makedirs(account_folder, exist_ok=True)
    uploaded_filenames = {}
    for key,file in files.items():
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(account_folder, filename)
            file.save(file_path)
            uploaded_filenames[key] = filename
    username = full_name.lower().replace(" ","") + str(uuid.uuid4())[:4]
    with sqlite3.connect("bank_customers.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (full_name,dob,gender,email,phone,address,city,state,zip,country,
                                   id_type,id_number,id_file,username,password,account_type,agreed_terms,agreed_communication,account_number)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            full_name, form.get("dob"), form.get("gender"), form.get("email"), form.get("phone"),
            form.get("address"), form.get("city"), 'N/A', form.get("pincode"), 'N/A',
            'Aadhar/PAN', form.get("aadhar_number"), uploaded_filenames.get("aadhar_doc",""),
            username, form.get("password"), form.get("accountType"),1,1, account_number
        ))
        conn.commit()
    update_customer_list_html()
    session['last_account_number'] = account_number
    return redirect("/success")

# --- Customer Login ---
@app.route("/customer/login", methods=["GET","POST"])
def customer_login():
    if request.method=="GET":
        return send_file("customer_login.html")
    login_id = request.form.get("login_id")
    password = request.form.get("password")
    conn = sqlite3.connect("bank_customers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT account_number FROM customers WHERE (account_number=? OR username=?) AND password=?", (login_id,login_id,password))
    customer = cursor.fetchone()
    conn.close()
    if customer:
        session["customer_account"] = customer[0]
        return redirect("/customer/dashboard")  # go directly to dashboard
    else:
        return "❌ Incorrect Account Number or Password"

# --- Customer Dashboard ---
@app.route("/customer/dashboard")
def customer_dashboard():
    if "customer_account" not in session:
        return redirect("/customer/login")
    account = session["customer_account"]
    conn = sqlite3.connect("bank_customers.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT account_number, full_name, dob, gender, email, phone, address, city, zip,
                             '', '', username, password, account_type
                      FROM customers WHERE account_number=?""", (account,))
    details = cursor.fetchone()
    conn.close()
    if not details:
        return "Customer not found"

    account_folder = os.path.join(CUSTOMER_UPLOAD_FOLDER, account)
    photo_url = aadhar_url = pan_url = "https://via.placeholder.com/200"
    if os.path.exists(account_folder):
        for f in os.listdir(account_folder):
            if "photo" in f.lower():
                photo_url = f"/customer_uploads/{account}/{f}"
            elif "aadhar" in f.lower():
                aadhar_url = f"/customer_uploads/{account}/{f}"
            elif "pan" in f.lower():
                pan_url = f"/customer_uploads/{account}/{f}"

    dashboard_html = """<!DOCTYPE html>
<html>
<head><title>Customer Dashboard</title></head>
<body>
<h2>Welcome, {{ details[1] }}</h2>
<div style="display:flex; gap:20px; margin-top:20px;">
<div><h3>Photo</h3><img src="{{ photo_url }}" width="200" height="200" alt="Photo"></div>
<div>
<p><b>Account Number:</b> {{ details[0] }}</p>
<p><b>Full Name:</b> {{ details[1] }}</p>
<p><b>DOB:</b> {{ details[2] }}</p>
<p><b>Gender:</b> {{ details[3] }}</p>
<p><b>Email:</b> {{ details[4] }}</p>
<p><b>Phone:</b> {{ details[5] }}</p>
<p><b>Address:</b> {{ details[6] }}</p>
<p><b>City:</b> {{ details[7] }}</p>
<p><b>ZIP:</b> {{ details[8] }}</p>
<p><b>Account Type:</b> {{ details[13] }}</p>
</div></div>
<h3>Documents</h3>
<ul>
<li><a href="{{ aadhar_url }}" target="_blank">View Aadhar</a></li>
<li><a href="{{ pan_url }}" target="_blank">View PAN</a></li>
</ul>
<form method="post" action="/logout"><button type="submit">Logout</button></form>
</body></html>"""

    return render_template_string(dashboard_html, details=details,
                                  photo_url=photo_url,
                                  aadhar_url=aadhar_url,
                                  pan_url=pan_url)

# --- Serve Uploaded Files ---
@app.route("/customer_uploads/<account>/<filename>")
def customer_file(account, filename):
    folder_path = os.path.join(CUSTOMER_UPLOAD_FOLDER, account)
    return send_from_directory(folder_path, filename)

# --- Logout ---
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")

# --- Success page ---
@app.route("/success")
def success_page():
    return "<h2>✅ Registration Successful!</h2><a href='/'>Go Home</a>"

# --- Run ---
if __name__=="__main__":
    app.run(debug=True, port=5000)
