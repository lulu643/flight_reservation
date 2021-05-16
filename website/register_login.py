from flask import Blueprint, render_template, request, session, url_for, redirect, flash
from .DB_connector import conn
from passlib.hash import sha256_crypt

registerandlogin = Blueprint('registerandlogin', __name__)

@registerandlogin.route('/login')

def login():

    return render_template("login.html")

@registerandlogin.route('/register')
def register():
    return render_template('register.html')

@registerandlogin.route('/loginCustomer', methods=['GET', 'POST'])

def loginCustomer():


    email = request.form['email']

    password = request.form['password']
    #cursor = conn.cursor(dictionry=True, buffered=True)

    cursor = conn.cursor()

    #executes query

    cursor.execute("SELECT * FROM customer where email=%s", [email])


    data = cursor.fetchone()


    cursor.close()

    conn.commit()


    if(data):
        if(sha256_crypt.verify(password, data['password'])):
            #creating a session for user
            session['email'] = email
            session['role'] = 'customer'
            session['username'] = data['name']
            #if successful, redirect to a new customer home page
            flash("LOGGED IN SUCCESSFULLY", "success")

            return redirect(url_for('customer.customerHome'))
        else:
            #This means that the passwords did not match
            error = 'The password incorrect, please try again'
            return render_template('login.html', error=error)
    else:
        #this means that the email is not registered
        error = 'The email you entered was not found'
        return render_template('login.html', error=error)
@registerandlogin.route('/loginAuthStaff', methods=['GET', 'POST'])
def loginAuthStaff():
    username = request.form['username']
    password = request.form['password']
    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    cursor.close()
    conn.commit()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        if (sha256_crypt.verify(password, data['password'])):
            # creates a session for the the user
            # session is a built in
            session['username'] = username
            session['role'] = "staff"
            session['first_name'] = data["first_name"]
            session['last_name'] = data["last_name"]
            session['airline_name'] = data["airline_name"]
            return redirect(url_for('staff.staffHome'))
        else:
            # returns an error message to the html page
            error = 'Invalid password'
            return render_template('login.html', error=error)
    else:
        # returns an error message to the html page
        error = 'Invalid username'
        return render_template('login.html', error=error)

@registerandlogin.route('/loginAuthAgent', methods=['GET', 'POST'])
def loginAuthAgent():
    email = request.form['email']
    password = request.form['password']
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM booking_agent WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    conn.commit()
    error = None
    if(data):
        if(sha256_crypt.verify(password, data['password'])):
            #creates a session for the the user
            #session is a built in
            session['email'] = email
            session['role'] = 'agent'
            return redirect(url_for('agent.agentHome'))
        else:
            #returns an error message to the html page
            error = 'Invalid password'
            return render_template('login.html', error=error)
    else:
        #returns an error message to the html page
        error = 'Invalid username'
        return render_template('login.html', error=error)


@registerandlogin.route('/registerCustomer', methods=['GET', 'POST'])

def registerCustomer():

    email = request.form['email']
    password = sha256_crypt.encrypt(request.form['password'])
    name = request.form['name']
    building_number = request.form['building_number']
    street = request.form['street']
    city = request.form['city']
    state = request.form['state']
    phone_number = request.form['phone_number']
    passport_number = request.form['passport_number']
    passport_expiration = request.form['passport_expiration']
    passport_country = request.form['passport_country']
    date_of_birth = request.form['date_of_birth']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query

    query = 'SELECT * FROM customer WHERE email = %s'

    cursor.execute(query, (email))

    #stores the results in a variable
    data = cursor.fetchone()


    if data:
        return render_template("register.html", error = "THIS USER ALREADY EXISTS")

    q = 'INSERT INTO customer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(q, (email,name, password,  building_number, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth))
    conn.commit()
    cursor.close()
    #go back to the home page and login in again
    return render_template('index.html')

@registerandlogin.route('/registerAuthAgent', methods=['GET', 'POST'])
def registerAuthAgent():
    email = request.form['email']
    password = sha256_crypt.encrypt(request.form['password'])
    agent_id = request.form['id']
    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM booking_agent WHERE email = %s'
    cursor.execute(query, (email))
    # stores the results in a variable
    data = cursor.fetchone()
    if data:
        return render_template("register.html", error = "THIS USER ALREADY EXISTS")

    query = 'SELECT * FROM booking_agent WHERE booking_agent_id = %s'
    cursor.execute(query, (agent_id))
    data2 = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        cursor.close()
        conn.commit()
        return render_template('register.html', error=error)
    elif (data2):
        # If the previous query returns data, then user exists
        error = "This agent id already exists"
        cursor.close()
        conn.commit()
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO booking_agent VALUES(%s, %s, %s)'
        cursor.execute(ins, (email, password, agent_id))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@registerandlogin.route('/registerAuthStaff', methods=['GET', 'POST'])
def registerAuthStaff():
    username = request.form['username']
    password = sha256_crypt.encrypt(request.form['password'])
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    DOB = request.form['DOB']
    airline_name = request.form['airline_name']
    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        cursor.close()
        conn.commit()
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO airline_staff VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, first_name, last_name, DOB, airline_name))
        conn.commit()
        cursor.close()
        return render_template('index.html')

