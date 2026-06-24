from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)

app.secret_key = "safeher123"


# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    port=3307,
    user="root",
    password="mysql@t_12",
    database="safeher"
)

cursor = db.cursor()

# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template('index.html')


# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        full_name = request.form['full_name']
        dob = request.form['dob']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match"

        if not phone.isdigit() or len(phone) != 10:
            return "Phone Number must contain exactly 10 digits"

        sql = """
        INSERT INTO users
        (full_name, dob, email, phone, address, password)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            full_name,
            dob,
            email,
            phone,
            address,
            password
        )

        cursor.execute(sql, values)
        db.commit()

        return redirect('/registersuccess')

    return render_template('register.html')

#------------register success
@app.route('/registersuccess')
def registersuccess():

    return render_template(
        'register_success.html'
    )

# ---------------- USER LOGIN ----------------

@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        query = """
        SELECT *
        FROM users
        WHERE email=%s
        AND password=%s
        """

        cursor.execute(query, (email, password))

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['user_name'] = user[1]

            return redirect('/dashboard')

        else:
            return "Invalid Email or Password"

    return render_template('user_login.html')


# ---------------- OFFICER LOGIN ----------------

@app.route('/officerlogin', methods=['GET', 'POST'])
def officerlogin():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = """
        SELECT *
        FROM officers
        WHERE email=%s
        AND password=%s
        """

        cursor.execute(sql, (email, password))

        officer = cursor.fetchone()

        if officer:

            session['officer_id'] = officer[0]
            session['officer_name'] = officer[1]

            return redirect('/officerdashboard')

        else:

            return "Invalid Officer Email or Password"

    return render_template('officer_login.html')

#------officer dashboard
@app.route('/officerdashboard')
def officerdashboard():

    officer_id = session.get('officer_id')
    officer_name = session.get('officer_name')

    cursor.execute("""
    SELECT report_id,
           incident_type,
           report_date,
           status
    FROM incident_reports
    WHERE officer_id=%s
    ORDER BY report_id DESC
    LIMIT 3
    """, (officer_id,))

    reports = cursor.fetchall()

    # Assigned Reports

    cursor.execute("""
    SELECT COUNT(*)
    FROM incident_reports
    WHERE officer_id=%s
    """, (officer_id,))

    total_reports = cursor.fetchone()[0]

  # In Progress Reports

    cursor.execute("""
    SELECT COUNT(*)
    FROM incident_reports
    WHERE officer_id=%s
    AND status='In Progress'
    """, (officer_id,))

    inprogress_reports = cursor.fetchone()[0]

    # Resolved Reports

    cursor.execute("""
    SELECT COUNT(*)
    FROM incident_reports
    WHERE officer_id=%s
    AND status='Resolved'
    """, (officer_id,))

    resolved_reports = cursor.fetchone()[0]

    return render_template(
        'officer_dashboard.html',
        officer_name=officer_name,
        reports=reports,
        total_reports=total_reports,
        inprogress_reports=inprogress_reports,
        resolved_reports=resolved_reports
    )
# ---------------- ADMIN LOGIN ----------------

@app.route('/adminlogin', methods=['GET','POST'])
def adminlogin():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor.execute("""
        SELECT *
        FROM admins
        WHERE email=%s
        AND password=%s
        """, (email, password))

        admin = cursor.fetchone()

        if admin:

            session['admin_id'] = admin[0]
            session['admin_name'] = admin[1]

            return redirect('/admindashboard')

        else:

            return "Invalid Admin Credentials"

    return render_template('admin_login.html')


#assign officers
@app.route('/startinvestigation/<int:report_id>')
def startinvestigation(report_id):

    cursor.execute("""
    UPDATE incident_reports
    SET status='In Progress'
    WHERE report_id=%s
    """, (report_id,))

    db.commit()

    return redirect('/allreports')

# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    user_name = session.get('user_name')

    first_letter = user_name[0].upper()

    return render_template(
        'user_dashboard.html',
        user_name=user_name,
        first_letter=first_letter
    )

# ---------------- REPORT INCIDENT ----------------

@app.route('/reportincident', methods=['GET', 'POST'])
def reportincident():

    if request.method == 'POST':

        incident_type = request.form['incident_type']
        location = request.form['location']
        description = request.form['description']

        user_id = session.get('user_id')

        sql = """
        INSERT INTO incident_reports
        (user_id, incident_type, description, location, status, report_date)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
        """

        values = (
            user_id,
            incident_type,
            description,
            location,
            'Pending'
        )

        cursor.execute(sql, values)
        db.commit()

        report_id = cursor.lastrowid

        return redirect(f'/reportsuccess/{report_id}')

    user_name = session.get('user_name')

    return render_template(
        'report_incident.html',
        first_letter=user_name[0].upper()
    )
# ---------------- REPORT SUCCESS ----------------

@app.route('/reportsuccess/<int:report_id>')
def reportsuccess(report_id):

    return render_template(
        'report_success.html',
        report_id=report_id
    )

# report status
@app.route('/reportstatus')
def reportstatus():

    user_id = session.get('user_id')
    user_name = session.get('user_name')

    sql = """
    SELECT
        r.report_id,
        r.incident_type,
        r.report_date,
        r.status,
        o.officer_name

    FROM incident_reports r

    LEFT JOIN officers o
    ON r.officer_id = o.officer_id

    WHERE r.user_id=%s

    ORDER BY r.report_id DESC
    """

    cursor.execute(sql, (user_id,))

    reports = cursor.fetchall()

    return render_template(
        'report_status.html',
        reports=reports,
        first_letter=user_name[0].upper()
    )
#manage officers
@app.route('/manageofficers', methods=['GET', 'POST'])
def manageofficers():

    if request.method == 'POST':

        officer_name = request.form['officer_name']
        email = request.form['email']
        phone = request.form['phone']
        station_name = request.form['station_name']
        password = request.form['password']

        cursor.execute("""
        INSERT INTO officers
        (officer_name, email, phone, station_name, password)
        VALUES (%s, %s, %s, %s, %s)
        """, (
            officer_name,
            email,
            phone,
            station_name,
            password
        ))

        db.commit()

        return redirect('/manageofficers')

    # Active SOS Count
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)

    active_sos = cursor.fetchone()[0]

    # Officers List
    cursor.execute("""
    SELECT officer_id,
           officer_name,
           email,
           phone,
           station_name
    FROM officers
    """)

    officers = cursor.fetchall()

    return render_template(
        'manage_officers.html',
        officers=officers,
        active_sos=active_sos
    )

#feedback
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():

    if request.method == 'POST':

        rating = request.form['rating']
        comments = request.form['comments']

        user_id = session.get('user_id')

        sql = """
        INSERT INTO feedback
        (user_id, rating, comments)
        VALUES (%s, %s, %s)
        """

        values = (
            user_id,
            rating,
            comments
        )

        cursor.execute(sql, values)
        db.commit()

        return redirect('/feedbacksuccess')

    return render_template('feedback.html')


@app.route('/feedbacksuccess')
def feedbacksuccess():

    return render_template('feedback_success.html')


#assigned reports

@app.route('/assignedreports')
def assignedreports():

    officer_id = session.get('officer_id')

    cursor.execute("""
    SELECT report_id,
           user_id,
           incident_type,
           report_date,
           status
    FROM incident_reports
    WHERE officer_id=%s
    ORDER BY report_id DESC
    """, (officer_id,))

    reports = cursor.fetchall()

    return render_template(
        'assigned_reports.html',
        reports=reports
    )

#------assign officer-----------
@app.route('/assignofficer/<int:report_id>', methods=['POST'])
def assignofficer(report_id):

    officer_id = request.form['officer_id']

    cursor.execute("""
    UPDATE incident_reports
    SET officer_id=%s,
        status='In Progress'
    WHERE report_id=%s
    """, (officer_id, report_id))

    db.commit()

    return redirect('/allreports')

#view report
@app.route('/viewreport/<int:report_id>')
def viewreport(report_id):

    cursor.execute("""
    SELECT report_id,
           user_id,
           incident_type,
           description,
           location,
           report_date,
           status
    FROM incident_reports
    WHERE report_id=%s
    """, (report_id,))

    report = cursor.fetchone()

    return render_template(
        'view_report.html',
        report=report
    )

#status update
@app.route('/resolvereport/<int:report_id>')
def resolvereport(report_id):

    cursor.execute("""
    UPDATE incident_reports
    SET status='Resolved'
    WHERE report_id=%s
    """, (report_id,))

    db.commit()

    return redirect('/assignedreports')

@app.route('/viewusers')
def viewusers():

    cursor.execute("""
    SELECT user_id,
           full_name,
           email,
           phone,
           address
    FROM users
    """)

    users = cursor.fetchall()

    return render_template(
        'view_users.html',
        users=users
    )

#sos alerts admin
@app.route('/sosalerts')
def sosalerts():

    # Active SOS Count
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)

    active_sos = cursor.fetchone()[0]

    # SOS Alerts List
    cursor.execute("""
    SELECT *
    FROM sos_alerts
    ORDER BY alert_id DESC
    """)

    alerts = cursor.fetchall()

    return render_template(
        'sos_alert.html',
        alerts=alerts,
        active_sos=active_sos
    )


# Resolve SOS Alert

@app.route('/resolvesos/<int:alert_id>')
def resolvesos(alert_id):

    cursor.execute("""
    UPDATE sos_alerts
    SET status='Resolved'
    WHERE alert_id=%s
    """, (alert_id,))

    db.commit()

    return redirect('/sosalerts')

#-------officer profile-----------
@app.route('/officerprofile')
def officerprofile():

    officer_id = session.get('officer_id')

    cursor.execute("""
    SELECT officer_id,
           officer_name,
           email,
           phone,
           station_name
    FROM officers
    WHERE officer_id=%s
    """, (officer_id,))

    officer = cursor.fetchone()

    return render_template(
        'officer_profile.html',
        officer=officer
    )
#edit profile
@app.route('/editprofile', methods=['GET', 'POST'])
def editprofile():

    user_id = session.get('user_id')

    if request.method == 'POST':

        full_name = request.form['full_name']
        phone = request.form['phone']
        email = request.form['email']
        dob = request.form['dob']
        address = request.form['address']

        cursor.execute("""
        UPDATE users
        SET full_name=%s,
            phone=%s,
            email=%s,
            dob=%s,
            address=%s
        WHERE user_id=%s
        """, (
            full_name,
            phone,
            email,
            dob,
            address,
            user_id
        ))

        db.commit()

        return redirect('/profile')

    cursor.execute("""
    SELECT full_name,
           phone,
           email,
           dob,
           address
    FROM users
    WHERE user_id=%s
    """, (user_id,))

    user = cursor.fetchone()

    return render_template(
        'edit_profile.html',
        user=user
    )
#logout
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')
#sos
# ---------------- SOS ----------------

@app.route('/sos', methods=['POST'])
def sos():

    phone = request.form['phone']
    location = request.form['location']

    sql = """
    INSERT INTO sos_alerts
    (phone_number, location)
    VALUES (%s, %s)
    """

    cursor.execute(sql, (phone, location))
    db.commit()

    alert_id = cursor.lastrowid

    return redirect(f'/sossuccess/{alert_id}')


@app.route('/sossuccess/<int:alert_id>')
def sossuccess(alert_id):

    return render_template(
        'sos.html',
        alert_id=alert_id
    )

# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():

    user_id = session.get('user_id')

    cursor.execute("""
    SELECT full_name,
           dob,
           email,
           phone,
           address
    FROM users
    WHERE user_id=%s
    """, (user_id,))

    user = cursor.fetchone()

    return render_template(
        'profile.html',
        user=user
    )
#-------admin dashboard------
@app.route('/admindashboard')
def admindashboard():

    admin_name = session.get('admin_name')

    # Total Users
    cursor.execute("""
    SELECT COUNT(*)
    FROM users
    """)
    total_users = cursor.fetchone()[0]

    # Total Officers
    cursor.execute("""
    SELECT COUNT(*)
    FROM officers
    """)
    total_officers = cursor.fetchone()[0]

    # Total Reports
    cursor.execute("""
    SELECT COUNT(*)
    FROM incident_reports
    """)
    total_reports = cursor.fetchone()[0]

    # Pending Reports
    cursor.execute("""
    SELECT COUNT(*)
    FROM incident_reports
    WHERE status='Pending'
    """)
    pending_reports = cursor.fetchone()[0]

    # Resolved Reports
    cursor.execute("""
    SELECT COUNT(*)
    FROM incident_reports
    WHERE status='Resolved'
    """)
    resolved_reports = cursor.fetchone()[0]

    # Active SOS Alerts
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)
    active_sos = cursor.fetchone()[0]

    return render_template(
        'admin_dashboard.html',
        admin_name=admin_name,
        total_users=total_users,
        total_officers=total_officers,
        total_reports=total_reports,
        pending_reports=pending_reports,
        resolved_reports=resolved_reports,
        active_sos=active_sos
    )


#---------Manage users
# ---- Manage Users

@app.route('/manageusers')
def manageusers():

    # Active SOS Count
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)

    active_sos = cursor.fetchone()[0]

    # Users List
    cursor.execute("""
    SELECT user_id,
           full_name,
           email,
           phone,
           address
    FROM users
    """)

    users = cursor.fetchall()

    return render_template(
        'manage_users.html',
        users=users,
        active_sos=active_sos
    )


# ---- Delete User

@app.route('/deleteuser/<int:user_id>')
def deleteuser(user_id):

    cursor.execute("""
    DELETE FROM users
    WHERE user_id=%s
    """, (user_id,))

    db.commit()

    return redirect('/manageusers')



#all reports

@app.route('/allreports')
def allreports():

    # Active SOS Count
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)

    active_sos = cursor.fetchone()[0]

    # All Reports
    cursor.execute("""
    SELECT report_id,
           user_id,
           incident_type,
           report_date,
           status
    FROM incident_reports
    ORDER BY report_id DESC
    """)

    reports = cursor.fetchall()

    return render_template(
        'all_reports.html',
        reports=reports,
        active_sos=active_sos
    )

#admin view report route
@app.route('/adminviewreport/<int:report_id>')
def adminviewreport(report_id):

    # Active SOS Count
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)

    active_sos = cursor.fetchone()[0]

    # Report Details
    cursor.execute("""
    SELECT report_id,
           user_id,
           incident_type,
           description,
           location,
           report_date,
           status,
           officer_id
    FROM incident_reports
    WHERE report_id=%s
    """, (report_id,))

    report = cursor.fetchone()

    # Officers List
    cursor.execute("""
    SELECT officer_id,
           officer_name
    FROM officers
    """)

    officers = cursor.fetchall()

    return render_template(
        'admin_view_report.html',
        report=report,
        officers=officers,
        active_sos=active_sos
    )
# ---------------- DATABASE TEST ----------------

@app.route('/testdb')
def testdb():

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    return str(users)

#----------admin feedback route
@app.route('/adminfeedback')
def adminfeedback():

    # Active SOS Count
    cursor.execute("""
    SELECT COUNT(*)
    FROM sos_alerts
    WHERE status='Active'
    """)

    active_sos = cursor.fetchone()[0]

    # All Feedbacks
    cursor.execute("""
    SELECT
        f.feedback_id,
        u.full_name,
        f.rating,
        f.comments
    FROM feedback f

    JOIN users u
    ON f.user_id = u.user_id
    """)

    feedbacks = cursor.fetchall()

    return render_template(
        'admin_feedback.html',
        feedbacks=feedbacks,
        active_sos=active_sos
    )

#----------officer feedback route
@app.route('/officerfeedback')
def officerfeedback():

    officer_id = session.get('officer_id')

    cursor.execute("""
    SELECT DISTINCT
        f.feedback_id,
        u.full_name,
        f.rating,
        f.comments

    FROM feedback f

    JOIN users u
    ON f.user_id = u.user_id

    JOIN incident_reports r
    ON f.user_id = r.user_id

    WHERE r.officer_id=%s
    """, (officer_id,))

    feedbacks = cursor.fetchall()

    return render_template(
        'officer_feedback.html',
        feedbacks=feedbacks
    )


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)