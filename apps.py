#/usr/bin/python

import re
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from flask import Flask, redirect, request, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from flask import Flask,session, request, flash, url_for, redirect, render_template, abort,g


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
app.secret_key = "managaassQW"

db = SQLAlchemy(app)

regex = "^((http[s]?|ftp):\/)?\/?([^:\/\s]+)"
reg = re.compile(regex)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.Text, unique=True, index=True)
    email=db.Column('email', db.Text, index=True)
    password=db.Column('password', db.Text, unique=True)
    registered_date = db.Column('registered_date', db.DateTime)
    hoax = db.relationship('Hoax', backref='hoax', lazy='dynamic')

    def __init__(self, username, password, email):
        self.username = username
        self.set_password(password)
        self.email = email
        self.registered_date = datetime.utcnow()

    def is_authenticated(self):
        return True 

    def is_active(self):
        return True 

    def is_anonymous(self):
        return True 

    def get_id(self):
        return unicode(self.id)

    def set_password(self , password):
        self.password = generate_password_hash(password)

    def check_password(self , password):
        return check_password_hash(self.password , password)

    def __repr__(self):
        return '<User %r>'% (self.username)

class Hoax(db.Model):
    __tablename__ = ""
    id = db.Column('hoax_id',db.Integer, primary_key=True)
    url = db.Column('hoax_url', db.Text)
    title = db.Column('hoax_title', db.Text)
    hoax_score = db.Column('hoax_score', db.Integer)
    domain = db.Column('hoax_domain', db.Text)
    pub_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __init__(self, url, title, hoax_score):
        self.url = url 
        self.title = title 
        self.pub_date = datetime.utcnow()
        self.domain = find_domain_name(url)
        self.hoax_score = 0

def find_domain_name(url):
    return reg.findall(url)[0][2]

@app.route('/register', methods=['GET', 'POST'])    
def register():
    if request.method == "GET":
        return render_template('register.html')
    user = Users(request.form['username'], request.form['password'], request.form['email'])
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = Users.query.filter_by(username=username).first()
    if registered_user == None:
        flash('username is invalid', 'error')
        return redirect(url_for('login'))
    if not registered_user.check_password(password):
        flash('password is invalid', 'error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('berhasil login')
    return redirect(request.args.get('next') or url_for('create_report'))

@app.route('/')
def index_page():
    return render_template("landing.html")

@app.route('/hoax')
def hoax_index():
    return render_template('hoax_index.html', data=Hoax.query.order_by(Hoax.pub_date.desc()).all())

@app.route('/create',methods=['GET','POST'])
@login_required
def create_report():
    if request.method == "GET":
        return render_template("submit.html")
    if request.method == "POST":
        url = request.form["url"]
        judul = request.form["judul"]
        domain = find_domain_name(url)
        note = Hoax(url=url, title=judul, hoax_score=0)
        #if judul in Note.query.filter_by(url=url).first()
        db.session.add(note)
        db.session.commit()
        flash('submition success!')
        return redirect(url_for('hoax_index'))

@app.route("/hoax/<int:id>")
def view_by_id(id):
    if id:
        return render_template("hoax_page.html",data=Hoax.query.filter_by(id=id))
    return redirect("/hoax/"+str(id))

@app.route("/upvote/<int:id>", methods=["GET", "POST"])
@login_required
def upvote(id):
    if id:
        val = Hoax.query.filter_by(id=id).first()
        val.hoax_score += 1
        db.session.commit()
        return redirect("/hoax/"+str(id))

@app.route("/downvote/<int:id>", methods=["GET", "POST"])
@login_required
def downvote(id):
    if id:
        val = Hoax.query.filter_by(id=id).first()
        val.hoax_score -= 1
        db.session.commit()
        return redirect("/hoax/"+str(id))

@app.route("/cari", methods=["GET", "POST"])
def cari_item():
    if request.method == "POST":
        return render_template("hoax_index.html", data=Hoax.query.filter_by(url=request.form['text']))
    redirect(url_for("hoax_index"))

@app.route("/domain")
def view_by_domain():
    data=Hoax.query.order_by(Hoax.domain.desc()).all()
    #data=Note.query.filter_by(domain=domain_name)
    return render_template("hoax_index.html", data=data)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("hoax_index"))

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

if __name__ == "__main__":
    db.create_all()
    app.debug = True
    app.run(host="0.0.0.0", port=2020, threaded=True)


