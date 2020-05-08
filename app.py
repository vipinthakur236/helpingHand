from flask import Flask, render_template, flash, redirect, url_for, session, logging
#from data import Articles
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask import request, Response
from flask_mysqldb import MySQL
from functools import wraps

app=Flask(__name__)

#config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Vipin@8086'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init mysql
mysql=MySQL(app)

#Articles=Articles()

@app.route('/')
def index():
	return render_template('home.html')

# About
@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	# Create Cursor
	cur= mysql.connection.cursor()

	#Get articles
	result= cur.execute("SELECT * FROM articles ORDER BY create_date DESC")

	articles= cur.fetchall()

	if result>0:
		return render_template('articles.html', articles=articles)
	else:
		msg='NO Article Found'
		return render_template('articles.html', msg=msg)

	# Close connection
	cur.close()

@app.route('/article/<string:id>/')
def article(id):
	# Create Cursor
	cur= mysql.connection.cursor()

	#Get articles
	result= cur.execute("SELECT * FROM articles WHERE id=%s", [id])

	article= cur.fetchone()

	return render_template('article.html', article=article)

#Register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name= form.name.data
		email= form.email.data
		username= form.username.data
		password= sha256_crypt.encrypt(str(form.password.data))

		#create cursor
		cur= mysql.connection.cursor()

		result=cur.execute("SELECT * FROM users WHERE username=%s",[username])
		Result=cur.execute("SELECT * FROM users WHERE email=%s",[email])

		if Result>0:
			#commit to DB
			mysql.connection.commit()

			#Cursor close
			cur.close()

			flash('Email ID already exists','danger')

			redirect(url_for('login'))

		elif result>0:
			#commit to DB
			mysql.connection.commit()

			#Cursor close
			cur.close()

			flash('Username already exists','danger')

			redirect(url_for('login'))

		else:

			#Execute query
			cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

			#commit to DB
			mysql.connection.commit()

			#Cursor close
			cur.close()

			flash('you are now registered and can log in','success')

			redirect(url_for('login'))
	return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method== 'POST':
		#Get form fields
		username=request.form['username']
		password_candidate=request.form['password']

		#Create cursor
		cur=mysql.connection.cursor()

		#Get user by username
		result=cur.execute("SELECT * from users WHERE username=%s",[username])

		if result>0 :
			#Get stored hash
			data=cur.fetchone()
			password=data['password']
			user=data['username']

			#compare Passwords
			if sha256_crypt.verify(password_candidate, password) :
				session['logged_in']= True
				session['username']= username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard',user=user))

			else:
				error= 'Invalid Login'
				return render_template('login.html', error=error)
			cur.close()
		else:
			error= 'Username Not Found'
			return render_template('login.html', error=error)

	return render_template('login.html')

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please Login', 'danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard/<string:user>')
@is_logged_in
def dashboard(user):
	# Create Cursor
	cur= mysql.connection.cursor()

	#Get articles
	result= cur.execute("SELECT * FROM articles WHERE author=%s",[user])

	articles= cur.fetchall()

	if result>0:
		return render_template('dashboard.html', articles=articles)
	else:
		msg='No Article Found'
		return render_template('dashboard.html', msg=msg)

	# Close connection
	cur.close()

#Article form class
class ArticleForm(Form):
    title = StringField('Name', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form= ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title= form.title.data
		body= form.body.data
		user=session['username']
		#Create cursor
		cur= mysql.connection.cursor()

		#Execute
		cur.execute("INSERT INTO articles(title, body, author) VALUES (%s, %s, %s)",(title, body, session['username']))

		#Commit to DB
		mysql.connection.commit()

		#Close connection
		cur.close()

		flash('Article Created', 'success')

		return redirect(url_for('dashboard',user=user))

	return render_template('add_article.html', form=form)


# Edit article
@app.route('/edit_article/<string:username>/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(username,id):
	#Create Cursor
	cur=mysql.connection.cursor()

	#Get Article by Id
	result=cur.execute("SELECT * FROM articles WHERE id=%s",id)

	article=cur.fetchone()

	# Get Form
	form= ArticleForm(request.form)

	#Populate article from fields
	form.title.data=article['title']
	form.body.data=article['body']

	if request.method == 'POST' and form.validate():
		title= request.form['title']
		body= request.form['body']

		#Create cursor
		cur= mysql.connection.cursor()
		app.logger.info(title)

		#Execute
		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))

		#Commit to DB
		mysql.connection.commit()

		#Close connection
		cur.close()

		flash('Article Updated', 'success')

		return redirect(url_for('dashboard',user=username))


	return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>/<string:username>', methods=['POST'])
@is_logged_in
def delete_article(id,username):


	
	#Create cursor
	cur= mysql.connection.cursor()

	#Execute
	cur.execute("DELETE FROM articles WHERE id=%s",id)

	#Commit to DB
	mysql.connection.commit()

	#Close connection
	cur.close()

	flash('Article Deleted', 'success')

	return redirect(url_for('dashboard',user=username))


if __name__=='__main__':
	app.secret_key='secret123'
	app.run(debug=True)
