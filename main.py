import math
import os
from werkzeug.utils import secure_filename
import flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json


with open('config.json', 'r') as  c:
    params = json.load(c)["params"]

localserver = True
app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.secret_key = 'super-secret-key'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL='True',
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

if (localserver):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mess = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    tagline = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(120), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last= math.ceil(len(posts)/int(params['no_of_posts']))
    page = flask.request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int((params['no_of_posts']))]
    #Pagination
    if(page==1):
        prev="#"
        next= "/?page=" + str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page -1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page + 1)


    return flask.render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if ('user' in flask.session and flask.session['user'] == params['admin_user']):

        if flask.request.method == 'POST':

            box_title = flask.request.form.get('title')
            tline = flask.request.form.get('tline')
            slug = flask.request.form.get('slug')
            content = flask.request.form.get('content')
            img_file = flask.request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return flask.redirect('/edit/' + sno)
    post = Posts.query.filter_by(sno=sno).first()
    return flask.render_template('edit.html', params=params, post=post)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in flask.session and flask.session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return flask.render_template('dashboard.html', params=params, posts=posts)

    if flask.request.method == 'POST':
        username = flask.request.form.get('uname')
        userpass = flask.request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            flask.session['user'] = username
            posts = Posts.query.all()
            return flask.render_template('dashboard.html', params=params)

    return flask.render_template('login.html', params=params)


@app.route("/about")
def about():
    return flask.render_template('about.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return flask.render_template('post.html', params=params, post=post)


@app.route("/uploader", methods=['GET', 'POST'])
def upload():
    if ('user' in flask.session and flask.session['user'] == params['admin_user']):
        if (flask.request.method == 'POST'):
            f = flask.request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "uploaded sucessfully"

@app.route("/delete/<string:sno>", methods=['GET', 'POST'] )
def delete(sno):
    if ('user' in flask.session and flask.session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return flask.redirect('/dashboard')


@app.route("/logout")
def logout():
    flask.session.pop('user')
    return flask.redirect('/dashboard')


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if flask.request.method == 'POST':
        name = flask.request.form.get('name')
        email = flask.request.form.get('email')
        phone = flask.request.form.get('phone')
        message = flask.request.form.get('message')
        entry = Contacts(name=name, email=email, phone_num=phone, mess=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from blog' + '' + name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=message + "\n" + phone
                          )
    return flask.render_template('contact.html', params=params)


app.run(debug=True)
