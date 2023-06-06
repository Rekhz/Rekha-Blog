from flask import Flask, render_template, redirect, url_for, flash,request,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm,ContactForm
from flask_gravatar import Gravatar
import secrets
import smtplib,os
import psycopg2

# my_email=os.environ["MY_EMAIL"]
my_email=os.environ.get('MY_EMAIL')
password=os.environ.get('MY_EMAIL_PASSWORD')

# password=os.environ["MY_EMAIL_PASSWORD"]
smtplib.SMTP("smtp.gmail.com", port=587)

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_DB_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

###Gravator

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

#CONFIGURE TABLES


class UserDetails(UserMixin,db.Model):
    __tablename__="user_details"
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(250), nullable=False,unique=True)
    password=db.Column(db.String(250), nullable=False)
    name=db.Column(db.String(250), nullable=False)
    ##User can have many posts
    ## if we use back populates then both the tables should have a back populates column.otherwise it will throw an error.
    posts=db.relationship("BlogPost",back_populates="author",lazy='subquery')
### However we can use backref as well.In this case only Parent table need to have this statement.
### But,in html templates we need to refer this as {{posts.poster.name}}
    # posts=db.relationship("BlogPost",backref="poster")
    comments = db.relationship("Comments", back_populates="author", lazy='subquery')

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    #### Adding Foreign Key and referring back to userdetails table
    author_id=db.Column(db.Integer,db.ForeignKey("user_details.id"))
### if we use backref in parent table then we can comment out the author declaration below.
    author = relationship("UserDetails", back_populates="posts",lazy='subquery')
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    blog_comments=db.relationship("Comments", back_populates="which_blogpost", lazy='subquery')

class Comments(db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    comment_body=db.Column(db.Text,nullable=False)
    author_id=db.Column(db.Integer,db.ForeignKey("user_details.id"))
    post_id=db.Column(db.Integer,db.ForeignKey("blog_posts.id"))
    author=relationship("UserDetails",back_populates="comments",lazy="subquery")
    which_blogpost=relationship("BlogPost",back_populates="blog_comments",lazy="subquery")
#Line below only required once, when creating DB.
# with app.app_context():
#     db.create_all()

## FLASK_LOGIN

login_manager=LoginManager()
login_manager.init_app(app)
# login_manager.login_view = 'login'
# login_manager.login_message = "User needs to be logged in to view this page"
# login_manager.login_message_category = "warning"

@login_manager.unauthorized_handler
def unauthorized():
    return abort(401, description="You are not authorized ! Only admins have access to this page!!.")
@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return db.session.get(UserDetails, int(user_id))



def admin_only_check(function):
    def wrapper_function(*args,**kwargs):
       if current_user.id != 1:
           abort(401, description="You are not authorized ! Only admins have access to this page.")
       return function(*args, **kwargs)
    wrapper_function.__name__ = function.__name__
    return wrapper_function


@app.route('/')


def get_all_posts():
    with app.app_context():
        all_posts = db.session.execute(db.select(BlogPost)).scalars().all()
        if current_user.is_authenticated:
            return render_template("index.html", all_posts=all_posts,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name,user_id=current_user.id)
        current_user.name="blank"
        return render_template("index.html", all_posts=all_posts,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)

# def get_all_posts():
#     with app.app_context():
#         all_posts = db.session.execute(db.select(BlogPost)).scalars().all()
#         try:
#             return render_template("index.html", all_posts=all_posts,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name,user_id=current_user.id)
#         except AttributeError:
#             current_user.name="blank"
#             return render_template("index.html", all_posts=all_posts,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)


@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    try:

        if form.validate_on_submit():
            password = request.form["password"]
            salt_length = 8
            new_password = generate_password_hash(password, method='pbkdf2:sha256:100000',salt_length=salt_length)
            email=request.form["email"]
            # Set the number of iterations for hashing here (e.g. 100000)

            with app.app_context():
                check_user=UserDetails.query.filter_by(email=email).first()
                if check_user==None:
                    new_user=UserDetails()
                    new_user.email=request.form["email"]## form.email.data will also work
                    new_user.password=new_password
                    new_user.name=request.form["name"]
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user)
                    flash("You have successfully registered!")
                    login_user(new_user)
                    return redirect(url_for("get_all_posts"))
                else:
                    flash("User already exists!")
                    return redirect(url_for("login"))

        return render_template("register.html", form=form, logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)

    except AttributeError:
        current_user.name = "blank"
        return render_template("register.html",form=form,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    try:
        if form.validate_on_submit():
            email=request.form["email"]
            password=request.form["password"]
            with app.app_context():
                existing_user=UserDetails.query.filter_by(email=email).first()
                if existing_user==None:
                    flash("User Doesn't exist.Please Register!")
                    return redirect(url_for("register"))
                elif check_password_hash(existing_user.password,password):
                    login_user(existing_user)
                    flash("You are logged in")
                    return redirect(url_for("get_all_posts",logged_in_or_not=True))
                else:
                    flash("Wrong Details!")
        return render_template("login.html",form=form,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)
    except AttributeError:
        current_user.name="blank"
        return render_template("login.html",form=form,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)



@login_required
@app.route('/logout')
def logout():
    logout_user()
    flash("You are logged out")
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    form=CommentForm()
    try:
        with app.app_context():
            requested_post=db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
            comments_of_the_post=db.session.execute(db.select(Comments).filter_by(post_id=post_id)).scalars().all()
            if form.validate_on_submit():
                new_comment=Comments(
                    comment_body=request.form["comment"],
                    author_id=current_user.id,
                    post_id=post_id
                )
                db.session.add(new_comment)
                db.session.commit()
                flash("Comments has been successfully added")
                return redirect(url_for("show_post",post_id=post_id))

            return render_template("post.html",comments_of_the_post=comments_of_the_post,form=form,post=requested_post,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name,user_id=current_user.id)
    except AttributeError:
        current_user.name="blank"
        if form.validate_on_submit():
            flash("You need to login first to add a comment!")
            return redirect(url_for("login"))
        return render_template("post.html",comments_of_the_post=comments_of_the_post,form=form,post=requested_post, logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)


@app.route("/about")
def about():
    try:
        return render_template("about.html",logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)
    except AttributeError:
        current_user.name="blank"
        return render_template("about.html",logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)



@app.route("/contact",methods=['GET','POST'])
def contact():
    form=ContactForm()
    try:
        if form.validate_on_submit():
            email_body = f"Name :- {form.name.data}\nEmail:- {form.email.data}\nPhone Number:-{form.phone_number.data}\nMessage:-\n{form.message.data}\n"
            with smtplib.SMTP_SSL("smtp.gmail.com") as connection:
                connection.login(user=my_email, password=password)
                connection.sendmail(from_addr=my_email, to_addrs="rekharevathy@gmail.com",
                                    msg=f"Subject:A New Message\n\nHi,\n\n{email_body}\n")
            flash("Thanks for contacting.You will hear soon!")
            return redirect(url_for('get_all_posts'))
        return render_template("contact.html",logged_in_or_not=current_user.is_authenticated,user_name=current_user.name,form=form)
    except AttributeError:
        current_user.name="blank"
        return render_template("contact.html",logged_in_or_not=current_user.is_authenticated,user_name=current_user.name,form=form)


@app.route("/new-post",methods=['GET','POST'])
@login_required
@admin_only_check
def add_new_post():
    form = CreatePostForm()
    try:
        if form.validate_on_submit():
            with app.app_context():
                new_post = BlogPost(
                    title=form.title.data,
                    subtitle=form.subtitle.data,
                    body=form.body.data,
                    img_url=form.img_url.data,
                    author_id=current_user.id,
                    date=date.today().strftime("%B %d, %Y")
                )
                db.session.add(new_post)
                db.session.commit()
            return redirect(url_for("get_all_posts"))
        return render_template("make-post.html", form=form,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)
    except AttributeError:
        current_user.name="blank"
        return render_template("make-post.html", form=form,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)

@app.route("/edit-post/<int:post_id>",methods=['GET','POST'])
@login_required
@admin_only_check
def edit_post(post_id):
    try:
        print(post_id)
        with app.app_context():
            blog_to_update = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
            edit_form = CreatePostForm(title=blog_to_update.title,
                                       subtitle=blog_to_update.subtitle,
                                       img_url=blog_to_update.img_url,
                                       body=blog_to_update.body)
            if edit_form.validate_on_submit():
                blog_to_update.title = edit_form.title.data
                blog_to_update.subtitle = edit_form.subtitle.data
                blog_to_update.img_url = edit_form.img_url.data
                blog_to_update.body = edit_form.body.data
                db.session.commit()
                return redirect(url_for('show_post',post_id=blog_to_update.id))
            return render_template("make-post.html", form=edit_form,logged_in_or_not=current_user.is_authenticated,user_name=current_user.name,user_id=current_user.id)
            # return render_template("make-post.html", form=edit_form, to_edit=True)
    except AttributeError:
        current_user.name="blank"
        return render_template("make-post.html", form=edit_form, logged_in_or_not=current_user.is_authenticated,user_name=current_user.name)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only_check
def delete_post(post_id):
    with app.app_context():
        blog_to_delete = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
        db.session.delete(blog_to_delete)
        db.session.commit()
    flash("You have successfully deleted the post!")

    return redirect(url_for('get_all_posts'))

@app.route("/delete")
@login_required
def delete_comment():
    comment_id=request.args.get('comment_id')
    with app.app_context():
        comment_to_delete = db.session.execute(db.select(Comments).filter_by(id=comment_id)).scalar_one()
        db.session.delete(comment_to_delete)
        db.session.commit()
    flash("You have successfully deleted the comment!")
    return redirect(url_for('show_post', post_id=request.args.get('post_id')))


if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)
