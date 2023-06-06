from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField,IntegerField
from wtforms.validators import DataRequired, URL,Email,Length
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class ContactForm(FlaskForm):
    name=StringField("Name",validators=[DataRequired()])
    email=StringField("Enter your email",validators=[DataRequired(), Email(message="Please enter a valid email with '@' and '.'"),Length(min=8)])
    phone_number=IntegerField("Phone Number",validators=[DataRequired()])
    message=CKEditorField('Message',validators=[DataRequired()])
    submit=SubmitField("SEND")

class RegisterForm(FlaskForm):
    email=StringField("Email",validators=[DataRequired(),Email(message='Enter a valid email')])
    password=PasswordField("Password",validators=[DataRequired(),Length(min=8)])
    name=StringField("Name",validators=[DataRequired()])
    submit=SubmitField("SIGN ME UP")

class LoginForm(FlaskForm):
    email=StringField("Email",validators=[DataRequired(),Email(message='Enter a valid email')])
    password=PasswordField("Password",validators=[DataRequired()])
    submit=SubmitField("Let Me In")
class CommentForm(FlaskForm):
    comment=CKEditorField("Add New Comment")
    submit=SubmitField("Submit Comment")