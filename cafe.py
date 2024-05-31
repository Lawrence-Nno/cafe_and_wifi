from flask import Flask, render_template, redirect, request, jsonify, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, RadioField, EmailField, TextAreaField
from wtforms.validators import input_required
from flask_bootstrap import Bootstrap
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from datetime import datetime
from flask_mail import Mail, Message


class HTTPMethodOverrideMiddleware(object):
    allowed_methods = frozenset([
        'GET',
        'HEAD',
        'POST',
        'DELETE',
        'PUT',
        'PATCH',
        'OPTIONS'
    ])
    bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        method = environ.get('HTTP_X_HTTP_METHOD_OVERRIDE', '').upper()
        if method in self.allowed_methods:
            environ['REQUEST_METHOD'] = method
        if method in self.bodyless_methods:
            environ['CONTENT_LENGTH'] = '0'
        return self.app(environ, start_response)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
Bootstrap(app)

# Connects to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')
db.init_app(app)
api_key = os.getenv('API_KEY')

app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv("EMAIL")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PWD",)
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

current_time = datetime.now()
year = current_time.strftime("%Y")


# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


class AddForm(FlaskForm):
    name = StringField(label='Name of cafe', validators=[input_required()], render_kw={"placeholder": "Name of Cafe", "class": "form-control"})
    map_url = StringField(label='Google Map Url', validators=[input_required()], render_kw={"placeholder": "Google Map Url", "class": "form-control"})
    img_url = StringField(label='Cafe Image Url', validators=[input_required()], render_kw={"placeholder": "Cafe Image Url", "class": "form-control"})
    location = StringField(label='Cafe Location', validators=[input_required()], render_kw={"placeholder": "Cafe Location", "class": "form-control"})
    seats = StringField(label='Number of Seats', validators=[input_required()], render_kw={"placeholder": "Number of Seats", "class": "form-control"})
    has_toilet = RadioField(choices=[('True', "Has a toilet"), ('', "Has no toilet")], validators=[input_required()], render_kw={"class": "form-check-input"})
    has_wifi = RadioField(choices=[('True', "Has a Wifi"), ('', "Has no Wifi")], validators=[input_required()], render_kw={"class": "form-check-input"})
    has_sockets = RadioField(choices=[('True', "Enough sockets"), ('', "Few sockets")], validators=[input_required()], render_kw={"class": "form-check-input"})
    can_take_calls = RadioField(choices=[('True', "Can take calls"), ('', "Can't take calls")], validators=[input_required()], render_kw={"class": "form-check-input"})
    coffee_price = StringField(label='Price of Coffee', validators=[input_required()], render_kw={"placeholder": "Coffee Price", "class": "form-control"})
    submit = SubmitField(label="Add Cafe", render_kw={"class": "btn btn-outline-warning"})


class PopUpForm(FlaskForm):
    key = StringField(label='Enter Delete Key', render_kw={"placeholder": "Enter Delete Key"})
    close = SubmitField(label="Close", render_kw={"class": "btn btn-outline-warning", "type": "button", "onclick": "closeForm()"})
    submit = SubmitField(label="Submit", render_kw={"class": "btn btn-outline-warning"})


class ContactForm(FlaskForm):
    name = StringField(label="Your Name", validators=[input_required()], render_kw={"placeholder": "Your Name", "class": "form-control"})
    email = EmailField(label="Your Email", validators=[input_required()], render_kw={"placeholder": "Your Email", "class": "form-control"})
    subject = StringField(label="Subject", validators=[input_required()], render_kw={"placeholder": "Subject", "class": "form-control"})
    body = TextAreaField(label="Your Message here...", validators=[input_required()], render_kw={"placeholder": "Your message here...", "class": "form-control textarea"})
    submit = SubmitField(label="Send", render_kw={"class": "btn btn-outline-warning"})


@app.route("/", methods=["GET", "POST"])
def index():
    cafes = db.session.execute(db.select(Cafe)).scalars()
    # cafes = Cafe.query.all()
    indexed_cafes = [(num + 1, item) for num, item in enumerate(cafes)]
    form = AddForm()
    contact_form = ContactForm()
    if request.method == "POST":
        new_cafe = Cafe(
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data,
            seats=form.seats.data,
            has_toilet=bool(form.has_toilet.data),
            has_wifi=bool(form.has_wifi.data),
            has_sockets=bool(form.has_sockets.data),
            can_take_calls=bool(form.can_take_calls.data),
            coffee_price=form.coffee_price.data
        )
        db.session.add(new_cafe)
        db.session.commit()
        flash("You successfully added a new cafe", 'success')
        return redirect(url_for("index") + "#cafes")
    return render_template("index.html", cafes=indexed_cafes, form=form, contact_form=contact_form, year=year)


@app.route('/edit/<cafe_id>', methods=["GET", "POST", "PUT"])
def update_cafe(cafe_id):
    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if cafe:
        edit_form = AddForm()
        edit_form.submit.label.text = "Update Cafe"
        edit_form.name.data = cafe.name
        edit_form.map_url.data = cafe.map_url
        edit_form.img_url.data = cafe.img_url
        edit_form.location.data = cafe.location
        edit_form.seats.data = cafe.seats
        edit_form.coffee_price.data = cafe.coffee_price
        if request.method == "POST":
            method = request.form.get('_method', '').upper()
            if method in ['PUT', 'DELETE']:
                edit_form = AddForm()
                cafe.name = edit_form.name.data
                cafe.map_url = edit_form.map_url.data
                cafe.img_url = edit_form.img_url.data
                cafe.location = edit_form.location.data
                cafe.seats = edit_form.seats.data
                cafe.has_toilet = bool(edit_form.has_toilet.data)
                cafe.has_wifi = bool(edit_form.has_wifi.data)
                cafe.has_sockets = bool(edit_form.has_sockets.data)
                cafe.can_take_calls = bool(edit_form.can_take_calls.data)
                cafe.coffee_price = edit_form.coffee_price.data
                db.session.commit()
                flash(f"You successfully edited {cafe.name}", 'success')
            else:
                flash(f"Couldn't edit {cafe.name} at this time")
            return redirect(url_for("index") + "#cafes")
        return render_template("edit.html", form=edit_form, cafe=cafe, year=year)
    else:
        return redirect(url_for("index"))


@app.route('/delete/<cafe_id>', methods=["GET", "POST", "DELETE"])
def delete(cafe_id):
    cafes = db.session.execute(db.select(Cafe)).scalars()
    delete_form = PopUpForm()
    api_key_user = delete_form.key.data
    if request.method == "POST":
        cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
        if cafe:
            method = request.form.get('_method', '').upper()
            if method in ['PUT', 'DELETE']:
                if api_key_user == api_key:
                    db.session.delete(cafe)
                    db.session.commit()
                    flash(f"You have successfully removed {cafe.name}", "success")
                    return redirect(url_for("index") + "#cafes")
                else:
                    flash(f"Wrong delete-key, couldn't remove {cafe.name}")
                    return redirect(url_for("index") + "#cafes")
            else:
                flash("Method not allowed", "failure")
                return redirect(url_for("index") + "#cafes")

    return render_template("delete.html", cafes=cafes, delete_form=delete_form, year=year)


@app.route('/#contact', methods=["POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        subject = "CafeandWifi " + form.subject.data
        body = form.body.data

        msg = Message(subject, sender=os.environ["EMAIL"], recipients=["lawrence.nno@gmail.com"])
        msg.body = f"Name: {name}\n Email: {email}\n content: {body}"
        mail.send(msg)
        flash("Message sent", "success")
        return redirect(url_for("index") + '#contact')


@app.route('/about')
def about():
    return render_template("about.html", year=year)


if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host='0.0.0.0')
