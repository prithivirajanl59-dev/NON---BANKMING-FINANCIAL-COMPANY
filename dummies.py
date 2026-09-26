from flask import Flask, request, redirect, send_file, session, url_for, render_template_string, send_from_directory
import sqlite3, os
from datetime import datetime
from werkzeug.utils import secure_filename


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = os.urandom(24)


# --- Upload folders ---
CUSTOMER_UPLOAD_FOLDER = 'customer_uploads'
STAFF_UPLOAD_FOLDER = 'staff_uploads'
os.makedirs(CUSTOMER_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STAFF_UPLOAD_FOLDER, exist_ok=True)

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
        # DO NOT DROP TABLE! Keep existing customers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT, dob TEXT, gender TEXT, email TEXT, phone TEXT,
                address TEXT, city TEXT, state TEXT, zip TEXT, country TEXT,
                aadhar_number TEXT, pan_number TEXT,
                photo TEXT, aadhar_copy TEXT, pan_copy TEXT,
                username TEXT UNIQUE, password TEXT,
                account_type TEXT, agreed_terms INTEGER, agreed_communication INTEGER,
                account_number TEXT UNIQUE
            )
        """)
        conn.commit()
        
DB_FILE = "bank.db"  # your SQLite file


def init_loan_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS loan_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_number TEXT UNIQUE,
        account_number TEXT,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        aadhar TEXT,
        pan TEXT,
        dob TEXT,
        address TEXT,
        loan_type TEXT,
        amount REAL,
        tenure INTEGER,
        purpose TEXT,
        gold_weight REAL,
        gold_type TEXT,
        loan_amount REAL,
        vehicle_type TEXT,
        vehicle_cost REAL,
        down_payment REAL,
        course_name TEXT,
        institution TEXT,
        course_fee REAL,
        documents TEXT,
        application_date TEXT
    )
    """)
    conn.commit()
    conn.close()


# --- Utility ---
def save_file(f, folder):
    if f and f.filename:
        filename = f"{int(datetime.now().timestamp())}_{secure_filename(f.filename)}"
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, filename)
        f.save(file_path)
        return filename
    return ""

def format_dob(dob):
    """Convert YYYY-MM-DD to '01 February 2003' format."""
    try:
        return datetime.strptime(dob, "%Y-%m-%d").strftime("%d %B %Y")
    except:
        return dob

def update_staff_list_html():
    with sqlite3.connect("bank_staff.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM staff")
        rows = cursor.fetchall()

    headers = ["ID","Name","DOB","Gender","Blood","Aadhar","PAN","Address","Email","Phone",
               "Emergency","EmpID","Dept","Role","Join Date","Password","Photo","Aadhar Copy","PAN Copy"]
    html = "<html><head><title>Staff List</title></head><body><h2>All Staff</h2><table border=1><tr>"
    html += "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    for row in rows:
        row = list(row)
        row[2] = format_dob(row[2]) if row[2] else ""  # format DOB
        html += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    html += "</table></body></html>"
    with open("staff_list.html", "w", encoding="utf-8") as f:
        f.write(html)

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
    <th>PAN Number</th><th>Username</th><th>Password</th><th>Account Type</th>
    </tr>"""
    for r in rows:
        dob_display = format_dob(r[2]) if r[2] else ""
        html += f"<tr><td>{r[21]}</td><td>{r[1]}</td><td>{dob_display}</td><td>{r[3]}</td><td>{r[4]}</td>"
        html += f"<td>{r[5]}</td><td>{r[6]}</td><td>{r[7]}</td><td>{r[9]}</td><td>{r[11]}</td>"
        html += f"<td>{r[12]}</td><td>{r[17]}</td><td>{r[18]}</td><td>{r[19]}</td></tr>"
    html += "</table></body></html>"
    with open("customer_list.html", "w", encoding="utf-8") as f:
        f.write(html)




# --- Routes ---
@app.route("/")
def home():
    return send_file("index.html")

# --- Staff Registration ---
@app.route("/staff/register", methods=["GET","POST"])
def staff_register():
    if request.method == "GET":
        return send_file("register_staff.html")

    form = request.form
    files = request.files

    with sqlite3.connect("bank_staff.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM staff")
        count = cursor.fetchone()[0]
        emp_id = f"TRBEMP{str(count+1).zfill(3)}"

        emp_folder = os.path.join(STAFF_UPLOAD_FOLDER, emp_id)
        os.makedirs(emp_folder, exist_ok=True)

        photo = save_file(files.get("photo"), emp_folder)
        aadhar_copy = save_file(files.get("aadhar_copy"), emp_folder)
        pan_copy = save_file(files.get("pan_copy"), emp_folder)

        cursor.execute("""
            INSERT INTO staff (name,dob,gender,blood_group,aadhar,pan,address,email,phone,emergency_contact,
                               employee_id,department,role,joining_date,password,photo,aadhar_copy,pan_copy)
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
    session['last_employee_id'] = emp_id
    return redirect("/success")

# --- Staff Login ---
@app.route("/staff/login", methods=["GET","POST"])
def staff_login():
    if request.method == "GET":
        return send_file("staff_login.html")
    emp_id = request.form.get("employee_id").strip()
    password = request.form.get("password").strip()
    conn = sqlite3.connect("bank_staff.db")
    cursor = conn.cursor()
    cursor.execute("SELECT employee_id FROM staff WHERE employee_id=? AND password=?", (emp_id,password))
    staff = cursor.fetchone()
    conn.close()
    if staff:
        session["staff_id"] = emp_id
        return redirect("/staff/dashboard")
    return "❌ Invalid Employee ID or Password"

@app.route("/staff/dashboard")
def staff_dashboard():
    if "staff_id" not in session:
        return redirect("/staff/login")
    emp_id = session["staff_id"]
    conn = sqlite3.connect("bank_staff.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT name,dob,gender,blood_group,aadhar,pan,address,email,phone,
                             emergency_contact,employee_id,department,role,joining_date,password
                      FROM staff WHERE employee_id=?""", (emp_id,))
    details = list(cursor.fetchone())
    conn.close()
    details[1] = format_dob(details[1])

    emp_folder = os.path.join(STAFF_UPLOAD_FOLDER, emp_id)
    photo_url = "https://via.placeholder.com/200"
    if os.path.exists(emp_folder):
        for f in os.listdir(emp_folder):
            if "photo" in f.lower():
                photo_url = url_for('staff_file', emp_id=emp_id, filename=f)

    dashboard_html = """<!DOCTYPE html>
<html><head><title>Staff Dashboard</title></head>
<body>
<h2>{{ details[11] }} - {{ details[12] }}</h2>
<div style="display:flex; gap:20px; margin-top:20px;">
  <div><img src="{{ photo_url }}" width="200" height="200"></div>
  <div>
    <p>Employee ID: {{ details[10] }}</p>
    <p>Name: {{ details[0] }}</p>
    <p>DOB: {{ details[1] }}</p>
    <p>Gender: {{ details[2] }}</p>
    <p>Blood Group: {{ details[3] }}</p>
    <p>Aadhar: {{ details[4] }}</p>
    <p>PAN: {{ details[5] }}</p>
    <p>Address: {{ details[6] }}</p>
    <p>Email: {{ details[7] }}</p>
    <p>Phone: {{ details[8] }}</p>
    <p>Emergency Contact: {{ details[9] }}</p>
    <p>Joining Date: {{ details[13] }}</p>
  </div>
</div>
</body></html>"""
    return render_template_string(dashboard_html, details=details, photo_url=photo_url)

@app.route("/staff_uploads/<emp_id>/<filename>")
def staff_file(emp_id, filename):
    folder_path = os.path.join(STAFF_UPLOAD_FOLDER, emp_id)
    return send_from_directory(folder_path, filename)

# --- Customer Registration ---
@app.route("/customer/register", methods=["GET","POST"])
def customer_register():
    if request.method == "GET":
        return send_file("register_customer.html")

    form = request.form
    files = request.files

    zip_last3 = form.get("zip")[-3:] if form.get("zip") else "000"

    conn = sqlite3.connect("bank_customers.db")
    cursor = conn.cursor()

    # Check existing account numbers with the same ZIP
    cursor.execute("SELECT account_number FROM customers WHERE account_number LIKE ?", (f"TRB{zip_last3}%",))
    existing = cursor.fetchall()
    if existing:
        seq_numbers = [int(acc[0][-5:]) for acc in existing]
        next_seq = max(seq_numbers) + 1
    else:
        next_seq = 1

    acc_num = f"TRB{zip_last3}{str(next_seq).zfill(5)}"

    # Create folder for uploads
    cust_folder = os.path.join(CUSTOMER_UPLOAD_FOLDER, acc_num)
    os.makedirs(cust_folder, exist_ok=True)

    # Save files
    photo_file = save_file(files.get("photo"), cust_folder)
    aadhar_file = save_file(files.get("aadhar_copy"), cust_folder)
    pan_file = save_file(files.get("pan_copy"), cust_folder)

    # Insert customer into DB
    cursor.execute("""
        INSERT INTO customers (full_name,dob,gender,email,phone,address,city,state,zip,country,
                               aadhar_number,pan_number,photo,aadhar_copy,pan_copy,
                               username,password,account_type,
                               agreed_terms,agreed_communication,account_number)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        form.get("full_name"), form.get("dob"), form.get("gender"), form.get("email"), form.get("phone"),
        form.get("address"), form.get("city"), form.get("state"), form.get("zip"), form.get("country"),
        form.get("aadhar_number"), form.get("pan_number"),
        photo_file, aadhar_file, pan_file,
        form.get("username"), form.get("password"), form.get("account_type"),
        int(form.get("agree_terms","0")), int(form.get("agree_communication","0")),
        acc_num
    ))
    conn.commit()
    conn.close()

    # Update the customer list HTML
    update_customer_list_html()
    session['last_account_number'] = acc_num
    return redirect("/success")


# --- Customer Login & Dashboard ---
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
        return redirect("/customer/dashboard")
    return "❌ Incorrect Account Number or Password"





@app.route("/customer/dashboard")
def customer_dashboard():
    if "customer_account" not in session:
        return redirect("/customer/login")
    
    # Serve your saved HTML
    return send_file("customer_dashboard.html")


# Route to show full profile
@app.route("/customer/profile")
def customer_profile():
    if "customer_account" not in session:
        return redirect("/customer/login")
    account = session["customer_account"]

    # Fetch full customer details
    conn = sqlite3.connect("bank_customers.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT full_name,account_number,dob,gender,email,phone,address,city,zip,
                             aadhar_number,pan_number,account_type
                      FROM customers WHERE account_number=?""", (account,))
    details = cursor.fetchone()
    conn.close()

    # Dynamic file URLs
    account_folder = os.path.join(CUSTOMER_UPLOAD_FOLDER, account)
    photo_url = aadhar_url = pan_url = "https://via.placeholder.com/200"
    if os.path.exists(account_folder):
        for f in os.listdir(account_folder):
            f_lower = f.lower()
            if "photo" in f_lower:
                photo_url = f"/customer_uploads/{account}/{f}"
            elif "aadhar" in f_lower:
                aadhar_url = f"/customer_uploads/{account}/{f}"
            elif "pan" in f_lower:
                pan_url = f"/customer_uploads/{account}/{f}"

    # Profile page
    profile_html = f"""<!DOCTYPE html>
<html>
<head><title>Profile</title></head>
<body>
<h2>{details[0]}'s Profile</h2>
<div style="display:flex; gap:20px;">
  <div><img src="{photo_url}" width="200" height="200"></div>
  <div>
    <p><b>Name:</b> {details[0]}</p>
    <p><b>Account Number:</b> {details[1]}</p>
    <p><b>DOB:</b> {details[2]}</p>
    <p><b>Gender:</b> {details[3]}</p>
    <p><b>Email:</b> {details[4]}</p>
    <p><b>Phone:</b> {details[5]}</p>
    <p><b>Address:</b> {details[6]}, {details[7]}, ZIP: {details[8]}</p>
    <p><b>Aadhar:</b> {details[9]}</p>
    <p><b>PAN:</b> {details[10]}</p>
    <p><b>Account Type:</b> {details[11]}</p>
  </div>
</div>
<h3>Documents</h3>
<ul>
<li><a href="{aadhar_url}" target="_blank">View Aadhar</a></li>
<li><a href="{pan_url}" target="_blank">View PAN</a></li>
</ul>
<button onclick="window.location.href='/customer/dashboard'">Back</button>
</body>
</html>
"""
    return profile_html


@app.route("/customer/apply_loan", methods=["POST"])
def apply_loan():
    # Ensure user is logged in
    account_number = session.get("customer_account")
    if not account_number:
        return redirect("/customer/login")

    # Get form data (loan-specific and personal info if needed)
    full_name = request.form.get("full_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    aadhar = request.form.get("aadhar")
    pan = request.form.get("pan")
    dob = request.form.get("dob")
    address = request.form.get("address")
    loan_type = request.form.get("loan_type")
    
    # Loan specific fields
    amount = request.form.get("amount")
    tenure = request.form.get("tenure")
    purpose = request.form.get("purpose")
    
    gold_weight = request.form.get("gold_weight")
    gold_type = request.form.get("gold_type")
    loan_amount = request.form.get("loan_amount")
    
    vehicle_type = request.form.get("vehicle_type")
    vehicle_cost = request.form.get("vehicle_cost")
    down_payment = request.form.get("down_payment")
    
    course_name = request.form.get("course_name")
    institution = request.form.get("institution")
    course_fee = request.form.get("course_fee")
    
    # Handle uploaded documents
    documents = request.files.getlist("documents")
    upload_folder = os.path.join(os.getcwd(), "loan_uploads", account_number)
    os.makedirs(upload_folder, exist_ok=True)
    documents_str = ""
    for doc in documents:
        if doc and doc.filename:
            filename = f"{int(datetime.now().timestamp())}_{secure_filename(doc.filename)}"
            doc.save(os.path.join(upload_folder, filename))
            documents_str += filename + ","
    documents_str = documents_str.rstrip(",")

    application_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Connect to DB and generate unique loan number
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    acc_last3 = account_number[-3:]  # last 3 digits of account number
    c.execute("SELECT loan_number FROM loan_applications WHERE loan_number LIKE ?", (f"TRBLN{acc_last3}%",))
    existing = c.fetchall()
    if existing:
        seq_numbers = [int(l[0][-5:]) for l in existing if l[0]]
        next_seq = max(seq_numbers) + 1
    else:
        next_seq = 1

    loan_number = f"TRBLN{acc_last3}{str(next_seq).zfill(5)}"

    # Insert into loan table
    c.execute("""INSERT INTO loan_applications
    (account_number, full_name, email, phone, aadhar, pan, dob, address, loan_type,
     amount, tenure, purpose, gold_weight, gold_type, loan_amount,
     vehicle_type, vehicle_cost, down_payment, course_name, institution, course_fee,
     documents, application_date, loan_number)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (account_number, full_name, email, phone, aadhar, pan, dob, address, loan_type,
     amount, tenure, purpose, gold_weight, gold_type, loan_amount,
     vehicle_type, vehicle_cost, down_payment, course_name, institution, course_fee,
     documents_str, application_date, loan_number)
    )

    conn.commit()
    conn.close()

    session["last_loan_number"] = loan_number
    return redirect("/customer/loan_confirmation")



@app.route("/customer_uploads/<account>/<path:filename>")
def serve_customer_file(account, filename):
    folder_path = os.path.join(CUSTOMER_UPLOAD_FOLDER, account)
    return send_from_directory(folder_path, filename)


@app.route("/loan/personal/apply")
def personal_loan_apply():
    if 'customer_account' not in session:
        return redirect("/customer/login")

    account = session['customer_account']

    conn = sqlite3.connect("bank_customers.db")
    c = conn.cursor()
    c.execute("""
        SELECT full_name, dob, gender, email, phone, address, aadhar_number, pan_number, account_number 
        FROM customers 
        WHERE account_number=?
    """, (account,))
    customer = c.fetchone()
    conn.close()

    if not customer:
        return "Customer data not found."

    # Prepare pre-filled data
    customer_data = {
        "full_name": customer[0],
        "dob": customer[1],
        "gender": customer[2],
        "email": customer[3],
        "phone": customer[4],
        "address": customer[5],
        "aadhar": customer[6],
        "pan": customer[7],
        "account_number": customer[8]
    }

    # Load loan_application.html and replace placeholders
    html_file = os.path.join(ROOT_DIR, "loan_application.html")
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    for key, value in customer_data.items():
        html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

    return html_content


@app.route("/customer_uploads/<account>/<filename>")
def customer_file(account, filename):
    folder_path = os.path.join(CUSTOMER_UPLOAD_FOLDER, account)
    return send_from_directory(folder_path, filename)

@app.route('/loan_application')
def loan_application():
    account_number = session.get('account_number')
    if not account_number:
        return "Please login first", 403

    conn = sqlite3.connect('bank_customers.db')
    c = conn.cursor()
    c.execute("SELECT full_name, dob, gender, email, phone, address, account_number, aadhar, pan FROM customers WHERE account_number=?", (account_number,))
    row = c.fetchone()
    conn.close()

    if row:
        customer_data = {
            'full_name': row[0],
            'dob': row[1],
            'gender': row[2],
            'email': row[3],
            'phone': row[4],
            'address': row[5],
            'account_number': row[6],
            'aadhar': row[7],
            'pan': row[8]
        }
        return render_template('loan_application.html', **customer_data)
    else:
        return "Customer not found", 404



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")  # redirects to index.html

@app.route("/success")
def success():
    emp_id = session.get('last_employee_id', '')
    acc_num = session.get('last_account_number', '')
    msg = "<h2>✅ Registration Successful!</h2>"
    if emp_id: msg += f"<p>Employee ID: {emp_id}</p>"
    if acc_num: msg += f"<p>Account Number: {acc_num}</p>"
    msg += "<a href='/'>Go Home</a>"
    return msg

@app.route("/uploads/<filename>")
def serve_uploads(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route("/services/<filename>")
def serve_services(filename):
    return send_file(f"services/{filename}")
@app.route("/customer/loan_confirmation")
def loan_confirmation():
    if "last_loan_number" not in session:
        return redirect("/customer/dashboard")

    loan_number = session["last_loan_number"]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT loan_number, loan_type, COALESCE(amount, loan_amount, course_fee, vehicle_cost, 0),
               application_date
        FROM loan_applications WHERE loan_number=?
    """, (loan_number,))
    loan = c.fetchone()
    conn.close()

    if not loan:
        return "<h3>Loan not found.</h3><a href='/customer/dashboard'>Back</a>"

    # Optional: you can set default status as “Pending Verification”
    status = "Pending Verification"

    html = f"""
    <html>
    <head>
        <title>Loan Confirmation - Global Trust Bank</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background-color: #f8f9fa;
                color: #333;
                text-align: center;
                padding-top: 60px;
            }}
            .card {{
                background: white;
                width: 450px;
                margin: auto;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }}
            h2 {{ color: #0056b3; }}
            p {{ font-size: 16px; margin: 10px 0; }}
            .status {{
                background: #ffc107;
                padding: 6px 12px;
                border-radius: 5px;
                color: black;
                display: inline-block;
                font-weight: bold;
            }}
            a {{
                display: inline-block;
                margin-top: 20px;
                background: #0056b3;
                color: white;
                text-decoration: none;
                padding: 10px 18px;
                border-radius: 6px;
            }}
            a:hover {{ background: #003d80; }}
            .print-btn {{
                margin-top: 10px;
                background: #28a745;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Loan Application Submitted Successfully ✅</h2>
            <p><strong>Loan Number:</strong> {loan[0]}</p>
            <p><strong>Loan Type:</strong> {loan[1].capitalize()}</p>
            <p><strong>Loan Amount:</strong> ₹{loan[2]}</p>
            <p><strong>Status:</strong> <span class='status'>{status}</span></p>
            <p><strong>Applied On:</strong> {loan[3]}</p>
            <button onclick="window.print()" class="print-btn">🖨️ Print</button><br>
            <a href='/customer/dashboard'>Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

    # Clear the last loan number after showing
    session.pop("last_loan_number", None)

    return html

@app.route("/submit-loan", methods=["POST"])
def submit_loan():
    if 'customer_account' not in session:
        return redirect("/customer/login")

    account = session['customer_account']
    form = request.form
    files = request.files

    # Create folder for uploaded loan documents
    cust_folder = os.path.join(CUSTOMER_UPLOAD_FOLDER, account, "loan_docs")
    os.makedirs(cust_folder, exist_ok=True)

    # Save uploaded files
    saved_files = {}
    for field in ["identity_proof", "address_proof", "income_proof", "bank_statements", "business_proof"]:
        f = files.get(field)
        if f:
            filename = f"{int(datetime.now().timestamp())}_{secure_filename(f.filename)}"
            f.save(os.path.join(cust_folder, filename))
            saved_files[field] = filename

    # Save loan application in DB
    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO loan_applications (account_number, loan_type, amount, applied_on)
        VALUES (?, ?, ?, ?)
    """, (
        account,
        form.get("loan_type"),
        form.get("amount") or 0,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    return redirect("/loan/confirmation")


@app.route("/customer/my_loans")
def my_loans():
    if "customer_account" not in session:
        return redirect("/customer/login")

    account_number = session["customer_account"]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    SELECT loan_number, loan_type, amount, tenure, purpose, application_date, status
    FROM loan_applications
    WHERE account_number = ?
    ORDER BY application_date DESC
""", (account_number,))
    loans = c.fetchall()
    conn.close()

    if not loans:
        return "<h3 style='text-align:center;'>You have not applied for any loan yet.</h3>"

    table_rows = ""
    for loan in loans:
        table_rows += f"""
        <tr>
            <td>{loan[0]}</td>
            <td>{loan[1]}</td>
            <td>{loan[2]}</td>
            <td>{loan[3]}</td>
            <td>{loan[4]}</td>
            <td>{loan[5]}</td>
            <td>{loan[6]}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <title>My Loans</title>
        <style>
            table {{ border-collapse: collapse; width: 80%; margin: 20px auto; }}
            th, td {{ border: 1px solid #333; padding: 10px; text-align: center; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            h2 {{ text-align: center; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h2>My Loan Applications</h2>
        <table>
            <tr>
                <th>Loan Number</th>
                <th>Loan Type</th>
                <th>Amount</th>
                <th>Tenure</th>
                <th>Purpose</th>
                <th>Applied On</th>
                <th>Loan status</th>
            </tr>
            {table_rows}
        </table>
        <div style="text-align:center; margin-top:20px;">
            <button onclick="location.href='/customer/dashboard'">Back to Dashboard</button>
        </div>
    </body>
    </html>
    """
    return html



if __name__ == "__main__":
    app.run(debug=True, port=5000)
