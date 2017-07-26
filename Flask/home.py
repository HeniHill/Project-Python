from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,make_response
from data import Talks
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.wrappers import BaseResponse as response

app=Flask(__name__)


# Config MtSQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='heni@hill'
app.config['MYSQL_DB']='users'
app.config['MYSQL_CURSORCLASS']='DictCursor'

mysql=MySQL(app)




Talks=Talks()

@app.errorhandler(404)
def pagenotfound(error):
    return render_template('page_not_found.html'),404

@app.route("/")
def home():
    resp=make_response(render_template('index.html'))
    #resp.set_cookie('username',session['username'])
    return resp#render_template("index.html")



@app.route("/logout")
def logout():
    session.clear()
    flash("You Are Logout")
    return redirect(url_for('login'))

@app.route("/aboutus")
def about():
    return render_template('about.html')

@app.route("/talk")
def talk():
    cur=mysql.connection.cursor()

    result=cur.execute("SELECT id,title FROM articles")

    articles=cur.fetchall()
    if result>0:
        return render_template("talk.html",articles=articles)
    else:
        msg="No Articles found"
        return render_template("talk.html",msg=msg)
    cur.close()

@app.route("/gotalk/<string:id>/")
def gotalk(id):
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * from articles WHERE id=%s",[id])
    article=cur.fetchone()
    if result>0:
        return render_template("gotalk.html",article=article)
    else:
        msg="No Article With ID",id, "Found"
        return render_template("gotalk.html",msg=msg)
    cur.close()


class RegisterForm(Form):
    name=StringField(u'Name',[validators.Length(min=5,max=50)])
    username=StringField(u'User Name',[validators.Length(min=4,max=25)])
    email=StringField(u'Eamil',[validators.Length(min=6,max=50)])
    password=PasswordField(u'Password',[
    validators.DataRequired(),
    validators.EqualTo('confirm',message='Passwords Do Not Match.')
    ])
    confirm=PasswordField('Confirm Password')

@app.route("/register",methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO user(name,email,username,password) VALUES(%s,%s,%s,%s)",
        (name,email,username,password))
        mysql.connection.commit()
        cur.close()
        flash("You Are Registered, And Can Log In",'success')
        return redirect(url_for('home'))
    return render_template("register.html",form=form)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Unauthorized access",'danger')
            return redirect(url_for('login'))
    return wrap

@app.route("/dashboard")
@is_logged_in
def dashboard():

    cur=mysql.connection.cursor()

    result=cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()

    if result>0:
        return render_template("dashboard.html",articles=articles)
    else:
        msg="No Article Found"
        return render_template("dashboard.html",msg=msg)
    cur.close()

class ArticleForm(Form):
    title=StringField(u'Title',[validators.Length(min=5,max=100)])
    body=TextAreaField(u'Body ',[validators.Length(min=5)])

@app.route("/add_article",methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title=form.title.data
        body=form.body.data


        cur=mysql.connection.cursor()

        cur.execute("INSERT INTO articles (title,author,body) VALUES(%s,%s,%s)",(
        title,session["username"],body
        ))
        mysql.connection.commit()
        cur.close()
        flash("New Article Created",'success')
        return redirect(url_for('dashboard'))
    return render_template("add_article.html",form=form)


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username=request.form["username"]
        password_user=request.form["password"]

        cur=mysql.connection.cursor()
        result=cur.execute("SELECT password FROM user WHERE username= %s",[username])

        if result >0:
            data=cur.fetchone()
            password=data["password"]
            if sha256_crypt.verify(password_user,password):
                session["logged_in"]=True
                session["username"]=username
                resp=make_response(redirect(url_for("dashboard")))
                resp.set_cookie(username,password_user,60000)
                flash("You are loged in",'success')
                return resp#redirect(url_for("dashboard"))
            else:
                error="Invalid Login"
                return render_template("login.html",error=error)
            cur.close()

        else:
            error="User Name Not Found"
            return render_template("login.html",error=error)

    return render_template("login.html")

if  __name__=="__main__":
    app.secret_key="\x87\t>\xf9\x7fp\x96i$\xd4\x04\x87:\x1a\xa6!$\x04\x0c\x8c\xfaUxd"
    app.run(debug=True)
