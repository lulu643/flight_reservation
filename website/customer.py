from flask import Blueprint, render_template, request
from .DB_connector import conn
import datetime
from .login_required import *
from decimal import *
import copy


customer = Blueprint('customer', __name__)


@customer.route('/customerHome')

@customer_login_required
def customerHome():
    email = session['email']
    username = session['username']
    return render_template('customerHome.html', username=username)

def customer_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('role')!= None and session['role'] == 'customer':
            return f(*args, **kwargs)
        else:
            flash("You can't access this if you havent logged in as customer")
            return redirect(url_for('registerandlogin.login'))
    return wrap

@customer.route('/logout')

@customer_login_required
def logout():

    session.clear()

    return redirect(url_for('registerandlogin.login'))


@customer.route('/viewMyFlights')
@customer_or_agent_login_required
def viewMyFlights():
    cursor = conn.cursor()

    if session['role'] == 'customer':


        email = session['email']

        cursor = conn.cursor()

        current_date = datetime.datetime.now()

        query = "select * from ticket natural join purchases join flight  where customer_email = %s and departure_time > %s"

        cursor.execute(query, (email, current_date))

        data1 = cursor.fetchall()



        print(data1)

        conn.commit()

        cursor.close()

    elif session['role'] == 'agent':

        email = session['email']

        cursor = conn.cursor()

        current_date = datetime.datetime.now()

        query = "select * from ticket natural join purchases natural join flight  join booking_agent  where booking_agent.email =  %s and flight.departure_time > %s"

        cursor.execute(query, (email, current_date))

        data1 = cursor.fetchall()

        print(data1)

        conn.commit()

        cursor.close()

    return render_template('viewMyFlights.html', flights=data1, role=session["role"])



@customer.route('/searchForFlights')

@customer_or_agent_login_required

def customerSearchForFlights():

    return render_template('searchForFlights.html', role=session['role'])


@customer.route('/searchFlightsResults', methods=['GET', 'POST'])

@customer_or_agent_login_required

def search_for_flights():

    departure_airport = request.form['departure_airport']

    arrival_airport = request.form['arrival_airport']

    dept_date = request.form['dept_date']

    return_date = request.form['return_date']

    if datetime.datetime.strptime(dept_date, "%Y-%m-%d") < datetime.datetime.now():

        return render_template("searchForFlights.html", error="Please enter valid dates.")

    # open
    cursor = conn.cursor()

    query = "select * from flight natural join airplane, airport as A, airport as B \
        where flight.departure_airport" \
            " = A.airport_name and flight.arrival_airport = B.airport_name and (A.airport_name = %s or A.airport_city = %s) and (B.airport_name = %s or B.airport_city = %s) and date(departure_time) = %s"
    cursor.execute(query, (departure_airport, departure_airport, arrival_airport, arrival_airport, dept_date))
    # store the results
    data = cursor.fetchall()

    if return_date:
        if datetime.datetime.strptime(dept_date, "%Y-%m-%d") > datetime.datetime.strptime(return_date, "%Y-%m-%d"):
            return render_template("searchForFlights.html", error="The dates you entered are invalid.")
        query2 = "select * from flight natural join airplane, airport as A, airport as B where flight.departure_airport = A.airport_name and flight.arrival_airport = B.airport_name and (A.airport_name = %s or A.airport_city = %s) and (B.airport_name = %s or B.airport_city = %s) and date(departure_time) = %s "
        cursor.execute(query2, (arrival_airport, arrival_airport, departure_airport, departure_airport, return_date))

    # store the results
    data2 = cursor.fetchall()


    conn.commit()
    cursor.close()


    if data:  # input is valid
        # for each in data: #for debugging
        #     print(each)
        if return_date:

            if data2:

                return render_template("searchForFlights.html", flights=data, returnFlights=data2, role=session['role'])

            else:

                error = "The Return Flight You are Searching Is Empty"

                return render_template("searchForFlights.html", error=error, role=session['role'])
        else:
            return render_template("searchForFlights.html", flights=data, role=session['role'])
    else:
        # returns an error message to the html page
        error = "The Flight You are Searching Is Empty"

        return render_template("searchForFlights.html", error=error, role=session['role'])


@customer.route('/purchaseTickets', methods=['GET', 'POST'])
@customer_or_agent_login_required
def purchaseTickets():
    f = request.form

    data_1 = ' '
    if request.method == 'POST':

        customer_email = request.form['customer_email']
        airline_name = request.form['airline_name']
        print("HERERERRRERRERRERRRERE\n",airline_name )
        flight_num = request.form['flight_num']
        print("FLight_NUM\n", type(flight_num))



        ##customer_email = request.form['customer_email']

        cursor = conn.cursor()

        #query = "select * from ticket natural  join flight  where flight_num = %s and airline_name = %s "
        query = "select * from ticket natural join flight where flight_num = %s and airline_name= %s and ticket_id not in (select ticket_id from purchases)"


        cursor.execute(query, (int(flight_num), airline_name))

        # store the results
        data_1 = cursor.fetchone()
        print(data_1)
        if data_1==None:
            return render_template("purchaseTickets.html", error="No available tickets, sorry!")

        ticket_id = data_1["ticket_id"]
        now = datetime.datetime.now()
        print("THIS IS THE DATETIME", now)
        query = "insert into purchases(ticket_id, customer_email, purchase_date) values (%s,%s,%s)"
        cursor.execute(query, (int(ticket_id), customer_email, now))
        flash("purchased!", "success")

        conn.commit()
        cursor.close()


    return render_template("purchaseTickets.html", flight = data_1, role=session["role"])



@customer.route('/trackMySpending', methods=['GET', 'POST'])
@customer_login_required
def trackMySpending():

    if request.method == 'POST':

        to_date = request.form['to_date']

        from_date = request.form['from_date']

        if datetime.datetime.strptime(from_date, "%Y-%m-%d") > datetime.datetime.strptime(to_date, "%Y-%m-%d"):

            return render_template('trackMySpending.html', error="The dates are invalid, please enter them again. ")

        to_date_format = datetime.datetime.strptime(to_date, '%Y-%m-%d')

        from_date_format = datetime.datetime.strptime(from_date, '%Y-%m-%d')

        year = to_date_format.year

        month = to_date_format.month

        from_year = from_date_format.year
        from_month = from_date_format.month
        from_date_date = from_date_format.day

        #calculate the total number of months

        totalmonth = (year - from_year) * 12 + month - from_month

    else:

        to_date = datetime.datetime.now()

        year = to_date.year

        #go back one year

        from_year = to_date.year - 1

        month = to_date.month



        totalmonth = 5

        string = '{} 1 {} 00:00'.format(month, from_year)

        from_date = datetime.datetime.strptime(string, '%m %d %Y %H:%M')



    cursor = conn.cursor()
    query = "SELECT COALESCE( SUM(price), 0) as total FROM flight natural join purchases WHERE purchase_date > %s AND purchase_date < %s AND customer_email = %s"
    cursor.execute(query, (from_date, to_date, session['email']))

    total = float(cursor.fetchone()['total'])

    print(month)

    if month < 12:

        string = '{} 1 {} 00:00'.format(month + 1, year + 1)

    else:

        string = '{} 1 {} 00:00'.format(1, year + 2)

    temp_date = datetime.datetime.strptime(string, '%m %d %Y %H:%M')

    x = []
    y = []
    temp_year = year
    temp_month = month
    for i in range(0, totalmonth + 1):
        this_date = temp_date
        this_month = temp_month
        temp_month = (month - i) % 12
        if temp_month == 0:
            temp_month = 12
        if temp_month > this_month:
            temp_year = temp_year - 1
        string = '{} 1 {} 00:00'.format(temp_month, temp_year)
        temp_date = datetime.datetime.strptime(string, '%m %d %Y %H:%M')
        query = "SELECT COALESCE( SUM(price), 0)  as monthly FROM flight natural join purchases  WHERE purchase_date > %s and purchase_date < %s AND customer_email = %s"
        cursor.execute(query, (temp_date, this_date, session['email']))
        data = cursor.fetchone()
        label = '{}-{}'.format(temp_year, temp_month)
        x.append(label)
        y.append(float(data['monthly']))
    cursor.close()
    x.reverse()
    y.reverse()
    print(x)
    try:
        mymax = max(y)
    except:
        mymax = 100
    return render_template('trackMySpending.html', total_spending=total, max=mymax, from_date=from_date,
                           to_date=to_date, labels=x, values=y)
