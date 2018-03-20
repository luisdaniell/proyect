#!/usr/bin/python
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
import os
from flask_wtf import CsrfProtect
import forms
import json
from forms import CommentForm
from helper import date_format

from flask_mail import Mail
from flask_mail import Message

import threading
from flask_wkhtmltopdf import Wkhtmltopdf
from flask_login import current_user, login_required

#from flask_weasyprint import HTML, render_pdf
#from cffi import FFI

def check_admin():
    # prevent non-admins from accessing the page
    if not current_user.is_admin:
        abort(403)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CsrfProtect()
mail = Mail()
bootstrap = Bootstrap(app)
wkhtmltopdf = Wkhtmltopdf(app)


@app.route('/demo1',methods = ['GET','POST'])
#@csrf.exempt
def demo1():
	json1 = {
  				"id": 1001,
  				"email": "jon@doe.ca",
  				"total_price": "479.00",
 			    "created_at": "2017-09-22T14:07:04-04:00",
  				"updated_at": "2017-09-22T14:07:04-04:00",
  				"fecha": "10/03/2018",
  				"number": 234,
  				"pago" : "Efectivo",
  				"tipo" : "Entrega a Domicilio",
  				
                "customer": {
   						 "nit": 8936756,
    					 "first_name": u"dániel",
    					 "last_name": u"montaño"},

                "line_items": [
    			{
     			 "id": 866550311766439020,
      			 "title": "IPod - 16GB exportado desde bolivia",
     			 "quantity": 1,
     			 "price": "280.00",
     			 "grams": 567},
     			 {
     			 "id": 866550311766439020,
      			 "title": "IPod - 16GB",
     			 "quantity": 1,
     			 "price": "280.00",
     			 "grams": 567},
   			   {
        		 "id": 141249953214522974,
   			     "title": "IPod Nano - 8GB",
    			 "quantity": 1,
   			     "price": "199.00",
      			 "grams": 567}
  				]
  				}
  	
	return render_template('factura_prueba.html' , json1 = json1 ) 

@app.route('/demo',methods = ['GET','POST'])
#@csrf.exempt
def demo():
    
	datoss = render_template('factura_rollo.html', download=True, save=False , test ='hola')
    	return datoss

#@app.route('/<name>/<location>/')
#def pdf(name,location):
#	rendered = render_template('factura_rollo.html', name=name , location=location)
#	css = ['rollo.css']
#	pdf = pdfkit.from_string(rendered,False, css=css  )
#
#	response = make_response(pdf)
#	response.headers['Content-Type'] = 'application/pdf'
#	response.headers['Content-Disposition'] = 'inline; filename =output.pdf'
#
#	return response
#
    # inline = pdf en linea
    #attachment = descargar pdf en linea

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
	if 'username' not in session and request.endpoint in ['comment','reviews']:
		return redirect(url_for('login'))

	elif 'username' in session and request.endpoint in ['login', 'create']:
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
       # return redirect(url_for("../reviews"))


	title = "daniel"
    

	return render_template('comment.html', title = title, form = comment_form)
    

@app.route('/reviews/', methods=['GET'])
@app.route('/reviews/<int:page>', methods=['GET'])
def reviews(page = 1):
	per_page = 10
	comments = Comment.query.join(User).add_columns(                    Comment.id,
																		User.username,
																		Comment.text,
																		Comment.created_date
																		).paginate(page,per_page,False)

	return render_template('reviews.html', comments = comments, date_format = date_format)



@app.route('/reviews/delete/<int:id>', methods=['GET', 'POST'])
def delete_comment(id):
    """
    Delete a comment from the database
    """

    comment = Comment.query.filter_by(id=id).first()
    db.session.delete(comment)
    db.session.commit()

    flash('Has eliminado correctamente el comentario.')

    # redirect to the roles page
    return redirect(url_for('reviews'))

    return render_template(title="Delete Comment")

@app.route('/users/', methods=['GET'])
def users():

	users = User.query.all()

	return render_template('users.html', users = users, date_format = date_format)

@app.route('/reviews/edit/<int:id>', methods=['GET', 'POST'])
def edit_comment(id):
	comment = Comment.query.filter_by(id=id).first()
	comment_form = forms.CommentForm(request.form)
	if request.method == 'POST' and comment_form.validate():
		
		
		comment.text = comment_form.comment.data
		

		#db.session.add(comment)
		db.session.commit()
		success_message = 'comentario actualizado!'
		flash(success_message)
		return redirect(url_for("reviews"))
		#comment_form.comment.data = comment.text
		# redirect to the roles page
        #return redirect(url_for('/'))
    
	title = "daniel"
    
	return render_template('comment.html', title = title, form = comment_form)


@app.route('/factura/', methods=['GET'])
def factura():

	users = User.query.all()

	return render_template('factura_rollo.html', users = users, date_format = date_format)	

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

	app.run(port=8008 , host='0.0.0.0')

