#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
from flask import request
from flask import make_response
from flask import session
from flask import flash
from flask import g
from flask import url_for
from flask import redirect
from flask import copy_current_request_context
import pdfkit
from config import DevelopmentConfig
from flask_bootstrap import Bootstrap
from models import db
from models import User
from models import Comment
from flask_login import LoginManager

from flask_wtf import CsrfProtect
import forms
import json

from helper import date_format

from flask_mail import Mail
from flask_mail import Message

import threading
from flask_weasyprint import HTML, render_pdf
from weasyprint import HTML


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CsrfProtect()
mail = Mail()
bootstrap = Bootstrap(app)

@app.route("/dd")
def function():
	HTML(string=render_template('factura_rollo.html')).write_pdf("repo.pdf")
	return ("GRACIAS POR TODO SU ARCHIVO ES CONVERTIDO A PDF")


#@app.route('/<name>/<location>/')
#def pdf(name,location):
#	rendered = render_template('pdf_template.html', name=name , location=location)
#	pdf = pdfkit.from_string(rendered,False)

#	response = make_response(pdf)
#	response.headers['Content-Type'] = 'application/pdf'
#	response.headers['Content-Disposition'] = 'inline; filename =output.pdf'

#	return response



def send_email(user_email, username):
	msg = Message('Gracias por tu registro!',
									sender =  app.config['MAIL_USERNAME'],
									recipients = [user_email]  )

	msg.html = render_template('email.html', username = username)
	mail.send(msg)


def create_session(username = '', user_id = ''):
	session['username'] = username
	session['user_id'] = use_id

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.before_request
def before_request():
	if 'username' not in session and request.endpoint in ['comment','reviews', 'create']:
		return redirect(url_for('login'))

	elif 'username' in session and request.endpoint in ['login']:
		return redirect(url_for('index'))		

@app.after_request
def after_request(response):
	return response

@app.route('/')
def index():
	if 'username' in session:
		username = session['username']
	title = 'Index'
	return render_template('index.html', title = title)

@app.route('/logout')
def logout():
	if 'username' in session:
		session.pop('username')
	return redirect(url_for('login'))

@app.route('/login', methods = ['GET', 'POST'])
def login():
	login_form = forms.LoginForm(request.form)
	if request.method == 'POST' and login_form.validate():
		username = login_form.username.data
		password = login_form.password.data

		user = User.query.filter_by(username = username).first()
		if user is not None and user.verify_password(password):
			success_message = 'Bienvenido {}'.format(username)
			flash(success_message)
			
			session['username'] = username
			session['user_id'] = user.id
			
			return redirect( url_for('index') )

		else:
			error_message= 'Usuario o password no validos!'
			flash(error_message)

		session['username'] = login_form.username.data
	return render_template('login.html', form = login_form)

@app.route('/comment', methods = ['GET', 'POST'])
def comment():
	comment_form = forms.CommentForm(request.form)
	if request.method == 'POST' and comment_form.validate():
		
		user_id = session['user_id']
		comment = Comment(user_id = user_id,
											text = comment_form.comment.data)
		

		db.session.add(comment)
		db.session.commit()


		success_message = 'Nuevo comentario creado!'
		flash(success_message)

	title = "Curso Flask"
	return render_template('comment.html', title = title, form = comment_form)


@app.route('/reviews/', methods=['GET'])
@app.route('/reviews/<int:page>', methods=['GET'])
def reviews(page = 1):
	per_page = 10
	comments = Comment.query.join(User).add_columns(
																		User.username,
																		Comment.text,
																		Comment.created_date
																		).paginate(page,per_page,False)

	return render_template('reviews.html', comments = comments, date_format = date_format)

@app.route('/users/', methods=['GET'])
def users():

	users = User.query.all()

	return render_template('users.html', users = users, date_format = date_format)	


@app.route('/create', methods = ['GET', 'POST'])
def create():
	create_form = forms.CreateForm(request.form)
	if request.method == 'POST' and create_form.validate():

		user = User(create_form.username.data,
								create_form.email.data,
								create_form.password.data)

		db.session.add(user)
		db.session.commit()

		@copy_current_request_context
		def send_message(email, username):
			send_email(email, username)
			
		sender = threading.Thread(name='mail_sender',
															target = send_message,
															args = (user.email, user.username))
		sender.start()

		success_message = 'Usuario registrado en la base de datos!'
		flash(success_message)
		
	return render_template('create.html', form = create_form)


if __name__ == '__main__':
	csrf.init_app(app)
	db.init_app(app)
	mail.init_app(app)

	with app.app_context():
		db.create_all()

	app.run(port=8001)

