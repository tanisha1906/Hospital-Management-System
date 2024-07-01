from flask import Flask,redirect,render_template,flash,request,session
from flask.globals import request
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,login_required,logout_user,login_user,login_manager,LoginManager,current_user
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import json
from flask_mail import Mail
from datetime import datetime

# mydatabase connection

local_server = True
app = Flask(__name__)
app.secret_key="tanishakar"

with open('config.json','r') as c:
    params = json.load(c)["params"]

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)
#for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'


# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/databasename'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/covid'
db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))


class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique = True)
    email=db.Column(db.String(100))
    dob=db.Column(db.String(1000))

class Hospitaluser(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(100))
    password=db.Column(db.String(1000))

class Hospitaldata(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20),unique = True)
    hname=db.Column(db.String(100))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)

class Bookingpatient(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    bedtype=db.Column(db.String(100))
    hcode=db.Column(db.String(20))
    spo2=db.Column(db.Integer)
    pname=db.Column(db.String(100))
    pphone=db.Column(db.String(100))
    paddress=db.Column(db.String(100))

class Trig(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)
    querys=db.Column(db.String(50))
    date=db.Column(db.String(50))

# Contact model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/trigers")
def trigers():
    query=Trig.query.all() 
    return render_template("trigers.html",query=query)

@app.route("/usersignup")
def usersignup():
    return render_template("usersignup.html")

@app.route("/userlogin")
def userlogin():
    return render_template("userlogin.html")

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=="POST":
        srfid =request.form.get('srf')
        email =request.form.get('email')
        dob = request.form.get('dob')
        # print(srfid,email,dob)
        encpassword = generate_password_hash(dob)

        user=User.query.filter_by(srfid=srfid).first()
        emailUser=User.query.filter_by(email=email).first()
        
        if user or emailUser:
            flash("Email or srif already taken","warning")
            return render_template("usersignup.html")

        # Create a new connection
        new_user = User(srfid=srfid, email=email, dob=encpassword)

        try:
            # Add and commit the new user to the database
            db.session.add(new_user)
            db.session.commit()
            user1=User.query.filter_by(srfid=srfid).first()
            if user1 and check_password_hash(user1.dob, dob):
                login_user(user1)
                flash("SignIn Success","success")
                return render_template("index.html")
        except SQLAlchemyError as e:
            db.session.rollback()
            return f"An error occurred: {e}"
        
    return render_template("usersignup.html")

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        srfid =request.form.get('srf')
        dob = request.form.get('dob')
        user=User.query.filter_by(srfid=srfid).first()
        
        # Debugging statements
        # if user is None:
        #     print("No user found with the given SRFID.")
        #     return 'Login Fail'

        # if user.dob is None:
        #     print("User found, but dob is None in the database.")
        #     return 'Login Fail'

        # print(f"User found: {user.srfid}, DOB stored in DB: {user.dob}")

        if user and check_password_hash(user.dob, dob):
            login_user(user)
            flash("Login Success","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")
        
    return render_template("userlogin.html")


@app.route('/hospitallogin',methods=['POST','GET'])
def hospitallogin():
    if request.method=="POST":
        email =request.form.get('email')
        password = request.form.get('password')
        user=Hospitaluser.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Success","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html")
        
    return render_template("hospitallogin.html")


@app.route('/hospital_dashboard')
@login_required
def hospital_dashboard():
    if hasattr(current_user, 'hcode'):
        hcode = current_user.hcode
        patients = Bookingpatient.query.filter_by(hcode=hcode).all()
        return render_template('hospital_dashboard.html', patients=patients)
    else:
        flash("Access denied: You are not a hospital user", "danger")
        return redirect(url_for('hospitallogin.html'))


@app.route('/admin',methods=['POST','GET'])
def admin():
    if request.method=="POST":
        username =request.form.get('username')
        password = request.form.get('password')
        
        if(username == params['user'] and password == params['password']):
            session['user'] = username
            flash("login success","info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials","danger")

    return render_template("admin.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful","warning")
    return redirect(url_for('login'))

@app.route('/addHospitalUser',methods=['POST','GET'])
def hospitalUser():
    if('user' in session and session['user'] == params['user']):
        if request.method=="POST":
            hcode =request.form.get('hcode')
            email =request.form.get('email')
            password = request.form.get('password')
        # print(srfid,email,dob)
            encpassword = generate_password_hash(password)
            hcode=hcode.upper()
            emailUser=Hospitaluser.query.filter_by(email=email).first()
            
            if emailUser:
                flash("Email already exists","warning")

            # Create a new connection
            new_user = Hospitaluser(hcode=hcode, email=email, password=encpassword)

            try:
            # Add and commit the new user to the database
                db.session.add(new_user)
                db.session.commit()

                mail.send_message('COVID CARE CENTER',sender=params['gmail-user'],recipients=[email],body=f"Welcome thanks for choosing us \nYour Login Credentials are:\nEmail Address:{email}\nPassword:{password}\n\nHospital Code:{hcode}\n\n Do not share your password\n\n\nThank You")

                flash("Data Sent to your mail and Inserted Successfully","warning")
                return render_template("addHosUser.html")

            except SQLAlchemyError as e:
                db.session.rollback()
                return f"An error occurred: {e}"
    
    else:
        flash("Login and try Again","warning")
        return redirect('/admin')
    
    return render_template("addHosUser.html")


#testing whether db is connected or not
@app.route("/test")
def test():
    if current_user.is_authenticated:
        em = current_user.email
        print(f"Authenticated user email: {em}")
        try:
            a = Test.query.all()
            print(a)
            return 'Connected'
        except Exception as e:
            print(e)
            return 'Not Connected'
    else:
        return 'User not authenticated'


@app.route('/logoutadmin')
def logoutadmin():
    session.pop('user')
    flash("You are Logout admin","primary")

    return redirect('/admin')

@app.route('/addhospitalinfo', methods=['POST', 'GET'])
def addhospitalinfo():
    email=current_user.email
    posts = Hospitaluser.query.filter_by(email=email).first()
    code = posts.hcode
    postsdata = Hospitaldata.query.filter_by(hcode=code).first()
    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')

        hcode = hcode.upper()
        huser = Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser = Hospitaldata.query.filter_by(hcode=hcode).first()

        if hduser:
            flash("Data is already present. You can update it.", "primary")
            return render_template("hospitaldata.html")
        
        if huser:
            new_data = Hospitaldata(
                hcode=hcode, 
                hname=hname, 
                normalbed=nbed, 
                hicubed=hbed, 
                icubed=ibed, 
                vbed=vbed
            )
            try:
                db.session.add(new_data)
                db.session.commit()
                flash("Data is added", "primary")
                return redirect('/addhospitalinfo')
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"An error occurred: {e}", "danger")
        else:
            flash("Hospital Code doesn't exist", "warning")
            return redirect('/addhospitalinfo')


    return render_template("hospitaldata.html",postsdata=postsdata)

@app.route("/hedit/<string:id>",methods=['POST','GET'])
@login_required
def hedit(id):
    posts=Hospitaldata.query.filter_by(id=id).first()
  
    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        nbed=request.form.get('normalbed')
        hbed=request.form.get('hicubeds')
        ibed=request.form.get('icubeds')
        vbed=request.form.get('ventbeds')
        hcode=hcode.upper()
        # db.engine.execute(f"UPDATE `hospitaldata` SET `hcode` ='{hcode}',`hname`='{hname}',`normalbed`='{nbed}',`hicubed`='{hbed}',`icubed`='{ibed}',`vbed`='{vbed}' WHERE `hospitaldata`.`id`={id}")
        post=Hospitaldata.query.filter_by(id=id).first()
        post.hcode=hcode
        post.hname=hname
        post.normalbed=nbed
        post.hicubed=hbed
        post.icubed=ibed
        post.vbed=vbed
        db.session.commit()
        flash("Slot Updated","info")
        return redirect("/addhospitalinfo")

    posts=Hospitaldata.query.filter_by(id=id).first()
    return render_template("hedit.html",posts=posts)


@app.route("/hdelete/<string:id>",methods=['POST','GET'])
@login_required
def hdelete(id):
    # db.engine.execute(f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    post=Hospitaldata.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    flash("Date Deleted","danger")
    return redirect("/addhospitalinfo")

@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Bookingpatient.query.filter_by(srfid=code).first()
    return render_template("details.html",data=data)

@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query1 = Hospitaldata.query.all()
    query = Hospitaldata.query.all()
    if request.method == "POST":
        srfid = request.form.get('srfid')
        bedtype = request.form.get('bedtype')
        hcode = request.form.get('hcode')
        spo2 = request.form.get('spo2')
        pname = request.form.get('pname')
        pphone = request.form.get('pphone')
        paddress = request.form.get('paddress')
        
        check2 = Hospitaldata.query.filter_by(hcode=hcode).first()
        checkpatient = Bookingpatient.query.filter_by(srfid=srfid).first()
        if checkpatient:
            flash("already srf id is registered", "warning")
            return render_template("booking.html", query=query, query1=query1)
        
        if not check2:
            flash("Hospital Code not exist", "warning")
            return render_template("booking.html", query=query, query1=query1)

        code = hcode
        dbb = Hospitaldata.query.filter_by(hcode=hcode).first()
        if dbb:
            if bedtype == "NormalBed":
                seat = dbb.normalbed
                if seat > 0:
                    dbb.normalbed = seat - 1
            elif bedtype == "HICUBed":
                seat = dbb.hicubed
                if seat > 0:
                    dbb.hicubed = seat - 1
            elif bedtype == "ICUBed":
                seat = dbb.icubed
                if seat > 0:
                    dbb.icubed = seat - 1
            elif bedtype == "VENTILATORBed":
                seat = dbb.vbed
                if seat > 0:
                    dbb.vbed = seat - 1
            else:
                seat = 0
            
            if seat > 0:
                db.session.commit()
                res = Bookingpatient(srfid=srfid, bedtype=bedtype, hcode=hcode, spo2=spo2, pname=pname, pphone=pphone, paddress=paddress)
                db.session.add(res)
                db.session.commit()
                flash("Slot is Booked kindly Visit Hospital for Further Procedure", "success")
            else:
                flash("No available beds of the selected type", "danger")
        else:
            flash("Give the proper hospital Code", "info")

        return render_template("booking.html", query=query, query1=query1)

    return render_template("booking.html", query=query, query1=query1)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        # Create a new contact instance
        new_contact = Contact(name=name, email=email, subject=subject, message=message)
        
        try:
            # Add to the database
            db.session.add(new_contact)
            db.session.commit()
            flash('Your message has been sent successfully!', 'success')
        except:
            db.session.rollback()
            flash('Error saving your message. Please try again.', 'danger')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

app.run(debug=True)