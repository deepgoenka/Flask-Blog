import math
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)
app.secret_key = 'secret-key'
local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-username'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    SNo = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30), nullable=False)
    Email = db.Column(db.String(30), nullable=False)
    Phone_num = db.Column(db.String(15), nullable=False)
    Message = db.Column(db.String(500), nullable=False)
    Date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    SNo = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(100), nullable=False)
    SubHeading = db.Column(db.String(100), nullable=False)
    Author = db.Column(db.String(100), nullable=False)    
    Slug = db.Column(db.String(30), nullable=False)
    Content = db.Column(db.String(1000), nullable=False)
    Img_file = db.Column(db.String(12), nullable=False)
    Date = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    # post = Posts.query.filter_by().all()[0:params['no_of_posts']]
    post = Posts.query.filter_by().all()
    last = math.ceil(len(post)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    post = post[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template('home.html', params=params, post=post, next=next, prev=prev)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
            posts = Posts.query.all()
            return render_template('/dashboard.html', params=params, posts=posts)
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_username'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('/dashboard.html', params=params, posts=posts)
    else:
        return render_template('login.html', params=params)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(Slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/edit/<string:SNo>", methods=['GET', 'POST'])
def edit(SNo):
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == 'POST':
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            author = request.form.get('author')
            slug = request.form.get('slug')
            content = request.form.get('content')
            imagefile = request.form.get('imagefile')
            date = datetime.now()
            if (SNo == '0'):
                post = Posts(Title=title, SubHeading=subheading, Author=author, Slug=slug, Content=content, Img_file=imagefile, Date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(SNo=SNo).first()
                post.Title = title
                post.SubHeading = subheading
                post.Author = author
                post.Slug = slug
                post.Content = content
                post.Img_file = imagefile
                post.Date = date
                db.session.commit()
                return redirect('/dashboard')
        post = Posts.query.filter_by(SNo=SNo).first()
        return render_template('edit.html', params=params, post=post, SNo=SNo)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(params['upload_location'], secure_filename(f.filename)))
            return "Uploaded Successfully"
        
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:SNo>")
def delete(SNo):
    if ('user' in session and session['user'] == params['admin_username']):
        post = Posts.query.filter_by(SNo=SNo).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')
     
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entity = Contacts(Name=name, Email=email, Phone_num=phone, Message=message, Date=datetime.now())
        db.session.add(entity)
        db.session.commit()
        mail.send_message ('New message from ' + name,
                           sender=email,
                           recipients=[params['gmail-username']],
                           body=message + '\n' + phone
                           )
    return render_template('contact.html', params=params)
app.run(debug=True)