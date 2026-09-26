from flask import Flask, render_template_string, request, redirect, session, url_for, send_from_directory
import pandas as pd
import os

from bs4 import BeautifulSoup
import pandas as pd
import os

html_file = r"C:\Users\Mowli\MyBankProject\customer_list.html"

with open(html_file, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Find the table (or container)
table = soup.find("table")  # if you have a <table>
if table:
    df = pd.read_html(str(table))[0]
else:
    # If your HTML is div-based, you may need to parse manually
    rows = soup.find_all("div", class_="row")  # example, adjust class
    data = []
    for row in rows:
        cols = row.find_all("div")
        data.append([col.text.strip() for col in cols])
    columns = ["Account Number","Full Name","DOB","Gender","Email","Phone","Address","City","ZIP","Aadhar Number","PAN Card Number","Username","Password","Account Type"]
    df = pd.DataFrame(data, columns=columns)

print(df.head())

app = Flask(__name__)
app.secret_key = "supersecretkey"


html_file = r"C:\Users\Mowli\MySampleApp\MyBankProject\customer_list.html"
df_list = pd.read_html(html_file)  # requires html5lib: pip install html5lib
df = df_list[0]  # first table
df.to_csv(r"C:\Users\Mowli\MySampleApp\MyBankProject\customer_list.csv", index=False)

# ------------------ Paths ------------------
BASE_DIR = os.path.abspath("C:/Users/Mowli/MySampleApp/MyBankProject")
CUSTOMER_CSV = os.path.join(BASE_DIR, "customer_list.csv")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "customer_uploads")

# Load customer data from CSV
if not os.path.exists(CUSTOMER_CSV):
    raise FileNotFoundError(f"CSV file not found at {CUSTOMER_CSV}")

df = pd.read_csv(CUSTOMER_CSV)

# ------------------ HTML Templates ------------------

login_html = """
<!DOCTYPE html>
<html>
<head><title>Customer Login</title></head>
<body>
<h2>Customer Login</h2>
<form method="post">
    Account Number: <input type="text" name="account_number" required><br><br>
    Password: <input type="password" name="password" required><br><br>
    <input type="submit" value="Login">
</form>
<p style="color:red;">{{ error }}</p>
</body>
</html>
"""

dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<title>Dashboard</title>
<style>
body { font-family: Arial; }
.container { display: flex; margin-top: 20px; }
.left { flex: 1; text-align: center; }
.right { flex: 2; padding-left: 30px; position: relative; }
.profile-icon { position: absolute; top: 0; right: 0; cursor: pointer; font-size: 24px; }
.profile-details { display: none; border: 1px solid #ccc; padding: 10px; margin-top: 50px; }
</style>
<script>
function toggleDetails() {
    var div = document.getElementById("details");
    if(div.style.display === "none") { div.style.display = "block"; }
    else { div.style.display = "none"; }
}
</script>
</head>
<body>
<h2>Welcome, {{ full_name }}</h2>
<div class="container">
    <div class="left">
        <img src="{{ photo_url }}" width="200" height="200" alt="Photo">
    </div>
    <div class="right">
        <span class="profile-icon" onclick="toggleDetails()">⚙️</span>
        <div id="details" class="profile-details">
            <p><b>Account Number:</b> {{ account_number }}</p>
            <p><b>Full Name:</b> {{ full_name }}</p>
            <p><b>DOB:</b> {{ dob }}</p>
            <p><b>Gender:</b> {{ gender }}</p>
            <p><b>Email:</b> {{ email }}</p>
            <p><b>Phone:</b> {{ phone }}</p>
            <p><b>Address:</b> {{ address }}</p>
            <p><b>City:</b> {{ city }}</p>
            <p><b>ZIP:</b> {{ zip }}</p>
            <p><b>Aadhar Number:</b> {{ aadhar }}</p>
            <p><b>PAN Card Number:</b> {{ pan }}</p>
            <p><b>Account Type:</b> {{ account_type }}</p>
        </div>
    </div>
</div>
<a href="{{ url_for('logout') }}">Logout</a>
</body>
</html>
"""

# ------------------ Routes ------------------

@app.route("/", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        acc = request.form.get("account_number")
        pwd = request.form.get("password")

        # Check login in DataFrame
        user = df[(df["Account Number"]==acc) & (df["Password"]==pwd)]
        if not user.empty:
            session["account_number"] = acc
            return redirect("/dashboard")
        else:
            error = "Invalid account number or password"
    return render_template_string(login_html, error=error)

@app.route("/dashboard")
def dashboard():
    if "account_number" not in session:
        return redirect("/")
    
    acc = session["account_number"]
    user = df[df["Account Number"]==acc].iloc[0]

    # Map columns
    account_number = user["Account Number"]
    full_name = user["Full Name"]
    dob = user["DOB"]
    gender = user["Gender"]
    email = user["Email"]
    phone = user["Phone"]
    address = user["Address"]
    city = user["City"]
    zip_code = user["ZIP"]
    aadhar = user["Aadhar Number"]
    pan = user["PAN Card Number"]
    account_type = user["Account Type"]

    # Photo path
    photo_path = os.path.join(UPLOAD_FOLDER, account_number, "photo.jpg")
    if os.path.exists(photo_path):
        photo_url = "/" + photo_path.replace("\\", "/")
    else:
        photo_url = "https://via.placeholder.com/200"

    return render_template_string(dashboard_html,
        account_number=account_number,
        full_name=full_name,
        dob=dob,
        gender=gender,
        email=email,
        phone=phone,
        address=address,
        city=city,
        zip=zip_code,
        aadhar=aadhar,
        pan=pan,
        account_type=account_type,
        photo_url=photo_url
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route('/customer_uploads/<account>/<filename>')
def uploaded_file(account, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, account), filename)

# ------------------ Run Flask ------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
