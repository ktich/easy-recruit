import os

import shutil

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# To enable file uploads
from werkzeug.utils import secure_filename

from helpers import apology, login_required, lookup, usd, allowed_file, stafflogin_required, userorstafflogin_required

# Configure application
app = Flask(__name__)

# set upload folder for CV uploads
UPLOAD_FOLDER = './static/cvs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")

@app.route("/jobs")
@userorstafflogin_required
def jobs():
    return render_template("jobs.html")

@app.route("/thanks")
@stafflogin_required
def thanks():
    return render_template("thanks.html")

@app.route("/", methods=["GET"])
@userorstafflogin_required
def index():
    if session.get("staff_id"):
        return redirect("/staff")
    elif session.get("user_id"):
        details = db.execute("SELECT * FROM profile WHERE applicantid=:id", id=session["user_id"])
        cvlink = db.execute("SELECT cv FROM CVs WHERE applicantid=:id", id=session["user_id"])
        cv = cvlink[0]['cv']
        details[0]['cv']=cv
        interests = db.execute("SELECT interest FROM interests WHERE applicantid=:id", id=session["user_id"])
        details[0]['interests'] = interests

        return render_template("index.html", details=details)

@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/staff", methods=["GET"])
@stafflogin_required
def staff():
    reviewed = db.execute("SELECT * FROM review")
    i = 0
    for i in range(len(reviewed)):
        id_current = reviewed[i]['applicantid']
        interests = db.execute("SELECT interest FROM interests WHERE applicantid=:id", id=id_current)
        reviewed[i]['interests'] = interests
        name = db.execute("SELECT name FROM applicant WHERE id=:id", id=id_current)
        email = db.execute("SELECT email FROM applicant WHERE id=:id", id=id_current)
        reviewed[i]['name'] = name[0]['name']
        reviewed[i]['email'] = email[0]['email']

        staffname = db.execute("SELECT name FROM staff WHERE id=:id", id=reviewed[i]['staffid'])
        reviewed[i]['staffname'] = staffname[0]['Name']

    return render_template("staff.html", reviewed=reviewed)


@app.route("/review", methods=["GET"])
@stafflogin_required
def reviewget():
    allapplicants = db.execute("SELECT * FROM profile")
    newapplicants = []
    i = 0
    for i in range(len(allapplicants)):
        id_current = allapplicants[i]['applicantid']
        reviewedapplicant = db.execute("SELECT * FROM review WHERE applicantid=:id", id=id_current)
        if reviewedapplicant:
            print("CURRENT")
        else:
            newapplicants.append(allapplicants[i])
            print(allapplicants[i])
            print(newapplicants)

    for i in range(len(newapplicants)):
        interests = db.execute("SELECT interest FROM interests WHERE applicantid=:id", id=newapplicants[i]['applicantid'])
        newapplicants[i]['interests'] = interests
        cvlink = db.execute("SELECT cv FROM CVs WHERE applicantid=:id", id=newapplicants[i]['applicantid'])
        newapplicants[i]['cvlink'] = cvlink[0]['cv']

    return render_template("review.html", newapplicants=newapplicants, interests=interests)


@app.route("/review", methods=["POST"])
@stafflogin_required
def review():
    ''' show a table which displays all applicants' information and allows staff members to download (or view?) CVs, etc.'''
    allapplicants = db.execute("SELECT * FROM profile")
    print(allapplicants)
    i = 0
    for i in range(len(allapplicants)):
        id_current = allapplicants[i]['applicantid']
        select=request.form.get("decision"+allapplicants[i]['name'])

        if select=="reject":
            db.execute("INSERT INTO review(applicantid, staffid, decision) VALUES (:applicantid, :staffid, :decision)",
                        applicantid=allapplicants[i]['applicantid'], staffid=session["staff_id"], decision="reject")

        elif select=="accept":
            db.execute("INSERT INTO review(applicantid, staffid, decision) VALUES (:applicantid, :staffid, :decision)",
                            applicantid=allapplicants[i]['applicantid'], staffid=session["staff_id"], decision="accept")

        else:
            print("none")

    if request.form.get("confirm"):
        return render_template("thanks.html")

    else:
        return apology("Please select 'confirm' in order to submit", 402)


@app.route("/stafflogin", methods=["GET", "POST"])
def stafflogin():
        # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email address", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = db.execute("SELECT * FROM staff WHERE email = :email",
                          email=request.form.get("email"))

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("Invalid email and/or password. If you are a staff member but do not have a password, please register for one first. If you are not a staff member, please login as an applicant.", 403)

        # Remember which user has logged in
        session["staff_id"] = rows[0]["id"]

        # Redirect user to home
        return redirect("/review")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("stafflogin.html")

@app.route("/profile", methods=["GET"])
@login_required
def checkprofile():
    #check if the profile is already in the database
    checkprofile = db.execute("SELECT * FROM profile WHERE applicantid=:id", id=session["user_id"])
    print(checkprofile)
    if checkprofile:
        print("here?")
        check = "no"
        return render_template("profile.html", check=check)
    else:
        return render_template("profile.html")

#code for below learned from: http://flask.pocoo.org/docs/1.0/patterns/fileuploads/#uploading-files
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == 'POST':

        #full name
        if not request.form.get("name"):
            return apology("Please enter your name", 403)

        elif not request.form.get("interest_research" or "interest_policy" or "interest_training"):
            return apology("Please enter all the required information", 403)

        elif not request.form.get("inst1" or "inst2"):
            return apology("Please enter all the required information", 403)

        elif not request.form.get("degree1" or "degree2"):
            return apology("Please enter all the required information", 403)

        elif not request.form.get("major1" or "major2"):
            return apology("Please enter all the required information", 403)

        elif not request.form.get("year1" or "year2"):
            return apology("Please enter all the required information", 403)

        else:
            db.execute("INSERT INTO profile (applicantID, name, inst1, inst2, degree1, degree2, major1, major2, year1, year2, additional) VALUES (:applicantID, :name, :inst1, :inst2, :degree1, :degree2, :major1, :major2, :year1, :year2, :additional)",
                        applicantID=session["user_id"], name=request.form.get("name"), inst1=request.form.get("inst1"), inst2=request.form.get("inst2"),
                        degree1=request.form.get("degree1"), degree2=request.form.get("degree2"), major1=request.form.get("major1"), major2=request.form.get("major2"), year1=request.form.get("year1"), year2=request.form.get("year2"), additional=request.form.get("additional"))
            if request.form.get("interest_research"):
                db.execute("INSERT INTO interests(applicantID, interest) VALUES (:applicantID, :interest)",
                        applicantID=session["user_id"], interest="research")
            if request.form.get("interest_training"):
                db.execute("INSERT INTO interests(applicantID, interest) VALUES (:applicantID, :interest)",
                        applicantID=session["user_id"], interest="training")
            if request.form.get("interest_policy"):
                db.execute("INSERT INTO interests(applicantID, interest) VALUES (:applicantID, :interest)",
                        applicantID=session["user_id"], interest="policy")


        # CV upload -- put the cv in a folder in this directory
        # save the filepath to the database for easy retrieval
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            db.execute("INSERT INTO CVs (applicantID, cv) VALUES (:applicantID, :cv)",
                           applicantID=session["user_id"], cv=filepath)

        return render_template("jobs.html")

    else:
        return redirect("/user")

    return render_template("profile.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email address", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = db.execute("SELECT * FROM applicant WHERE email = :email",
                          email=request.form.get("email"))

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to the profile page...
        return redirect("/profile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/staffregister", methods=["GET", "POST"])
def staffregister():
    """Register staff user -- email already in database"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email address", 400)

        elif not request.form.get("name"):
            return apology("must provide name", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        elif not db.execute("SELECT email FROM staff WHERE email=:email", email=request.form.get("email")):
            return apology("only staff members already in the system may register - contact Kim for access", 400)

        else:
            # Input hash into database
            rows = db.execute("UPDATE staff SET password=:password, name=:name WHERE email=:email",
                    password=generate_password_hash(request.form.get("password")), name=request.form.get("name"), email=request.form.get("email"))

        # Redirect user to home page
        return render_template("stafflogin.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("staffregister.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email address", 400)

        elif db.execute("SELECT email FROM applicant WHERE email=:email", email=request.form.get("email")):
            return apology("sorry", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Input email and hash into database
        rows = db.execute("INSERT INTO applicant (email, hash, name) VALUES (:email, :hash, :name)",
                          email=request.form.get("email"), hash=generate_password_hash(request.form.get("password")), name=request.form.get("name"))

        # Redirect user to home page
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

