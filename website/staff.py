from flask import Blueprint, render_template, request, session, url_for, redirect, flash
from .DB_connector import conn
from datetime import datetime
from .login_required import staff_login_required

staff = Blueprint('staff', __name__)


@staff.route('/staffHome')
@staff_login_required
def staffHome():
    # fetch data from session
    username = session["username"]
    cursor = conn.cursor()
    query = 'SELECT first_name, last_name, airline_name FROM airline_staff WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    cursor.close()
    # debugging
    print(data["first_name"], data["last_name"], data["airline_name"])
    cursor.close()
    return render_template("staffHome.html", username=username, info=data)


@staff.route('/flightManage', methods=['GET', 'POST'])
@staff_login_required
def viewFlight():
    # get airline name
    airline_name = session['airline_name']
    default = ""
    if request.method == "POST":
        # grabs information from the forms
        dept_from = request.form['dept_from']
        arrival_airport = request.form['arr_at']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
            return render_template("flightManage.html", error="The dates you entered are invalid.")

        # database query
        cursor = conn.cursor()
        query = "SELECT * FROM flight NATURAL JOIN airplane, airport as A, airport as B \
        where airline_name = %s AND date(departure_time) >= %s AND date(departure_time) <= %s \
        AND flight.departure_airport = A.airport_name and flight.arrival_airport = B.airport_name and (A.airport_name = %s or A.airport_city = %s) \
            and (B.airport_name = %s or B.airport_city = %s)"
        cursor.execute(query,
                       (airline_name, start_date, end_date, dept_from, dept_from, arrival_airport, arrival_airport))
        data1 = cursor.fetchall()
        cursor.close()
        msg = (dept_from, arrival_airport, start_date, end_date)

    else:
        # default views 
        cursor = conn.cursor()
        query = 'SELECT * FROM flight WHERE airline_name = %s AND DATE(departure_time) BETWEEN DATE(CURRENT_TIMESTAMP) \
        AND DATE(CURRENT_TIMESTAMP) + INTERVAL 30 DAY'
        cursor.execute(query, (airline_name))
        data1 = cursor.fetchall()
        cursor.close()
        default = "Default: Future 30 Days"
        msg = "Default: Future 30 Days"

    # send to the html   
    if data1:
        for each in data1:
            print("Received Data:/n", each['airline_name'], each['flight_num'], each['departure_time'])
            return render_template('flightManage.html', flights=data1, msg=msg)
    else:
        # returns an error message to the html page
        noFound = "No flights available within the given conditions"
        return render_template('flightManage.html', default=default, noFound=noFound)


@staff.route('/addFlight', methods=['GET', 'POST'])
@staff_login_required
def add_flight():
    # get airline name
    airline_name = session['airline_name']

    if request.method == "POST":
        # grabs information from the forms
        flight_num = request.form['flight_num1']
        dept_time = request.form['dept_time1']
        arr_time = request.form['arr_time1']
        base_price = float(request.form['base_price1'])
        flight_status = "on time"
        dept_from = request.form['dept_from1']
        arrival_airport = request.form['arr_at1']
        airplane_id = request.form['airplane_id1']
        print(dept_time)
        if datetime.strptime(dept_time, "%Y-%m-%dT%H:%M:%S") > datetime.strptime(arr_time, "%Y-%m-%dT%H:%M:%S"):
            return render_template("flightManage.html", error="The dates you entered are invalid.")

        cursor = conn.cursor()

        # check foreign_key constraint and duplicate
        # airplane
        query = "SELECT airplane_id FROM airplane"
        cursor.execute(query)
        data = cursor.fetchall()
        airplane_list = []
        for line in data:
            airplane_list.append(str(line["airplane_id"]))
        # for debugging purpose
        print(airplane_list)
        print(type(airplane_list[0]))
        if airplane_id not in airplane_list:
            noFound = "Airplane ID Not Found"
            return render_template('flightManage.html', noFound=noFound)
        # airport
        query = "SELECT airport_name FROM airport"
        cursor.execute(query)
        data = cursor.fetchall()
        airport_list = []
        for line in data:
            airport_list.append(line["airport_name"])
        if dept_from not in airport_list or arrival_airport not in airport_list:
            noFound = "Airport Not Found"
            return render_template('flightManage.html', noFound=noFound)

        query = "SELECT * FROM flight WHERE (airline_name, flight_num) = (%s, %s)"
        cursor.execute(query, (airline_name, flight_num))
        data = cursor.fetchall()
        if data:
            noFound = "Flight Already Exist"
            return render_template('flightManage.html', noFound=noFound)

        # update database
        query = "INSERT INTO flight VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (airline_name, flight_num, dept_from, dept_time, arrival_airport, arr_time,
                               base_price, flight_status, airplane_id))
        msg = "Add Flights Success"
        print(msg)
        cursor.close()
        conn.commit()
        session["flight_created"] = True
        return redirect("/flightManage")
    else:
        render_template("flightManage.html")


@staff.route('/updateFlight/<flight_num>', methods=['GET', 'POST'])
@staff_login_required
def updateFlight(flight_num):
    # get airline name
    airline_name = session['airline_name']

    if request.method == "POST":
        # fetch selection
        new_status = request.form.get('statusSelect')
        print("new-status", new_status)
        # update database
        cursor = conn.cursor()
        query = "UPDATE flight SET status = %s WHERE (airline_name, flight_num) = (%s, %s)"
        cursor.execute(query, (new_status, airline_name, flight_num))
        cursor.close()
        conn.commit()
        message = "Update Flights Success"
        session["flight_updated"] = True
        return redirect("/flightManage")
    else:
        cursor = conn.cursor()
        # check if such flight exits
        query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s"
        cursor.execute(query, (airline_name, flight_num))
        data = cursor.fetchone()
        cursor.close()
        if data:
            print(data)
            return render_template("updateFlight.html", flight=data)
        else:
            noFound = "There's an issue in updating the flight: such flight does not exist"
            return render_template('flightManage.html', noFound=noFound)


@staff.route('/airSystemManage/airplane', methods=['GET', 'POST'])
@staff_login_required
def managePlane():
    # get airline name
    airline_name = session['airline_name']

    if request.method == "POST":
        # fetch data
        airplane_id = request.form["airplane_id"]
        seats = request.form["seats"]

        # check duplicates
        cursor = conn.cursor()
        query = "SELECT * FROM airplane WHERE (airline_name, airplane_id) = (%s, %s)"
        cursor.execute(query, (airline_name, airplane_id))
        data = cursor.fetchall()
        if data:
            noFound = "Such airplane ID already exists"
            return render_template("airSystemManage.html", noFound=noFound, message="airplane", state_plane=True)
        cursor.close()

        # initiate query
        cursor = conn.cursor()
        query = "INSERT INTO airplane VALUES (%s, %s, %s)"
        cursor.execute(query, (airline_name, airplane_id, seats))
        cursor.close()
        conn.commit()
        session["airplane_updated"] = True
        return redirect("/airSystemManage/airplane")

    else:
        # display all the planes operated by the airline
        cursor = conn.cursor()
        query = "SELECT * FROM airplane WHERE airline_name = %s"
        cursor.execute(query, (airline_name))
        data = cursor.fetchall()
        cursor.close()
        if data:
            for each in data:
                print("data:", each)
            return render_template("airSystemManage.html", airplane=data, state_plane=True)
        else:
            noFound = "There is not airplane in the system"
            return render_template("airSystemManage.html", noFound=noFound, state_plane=True)


@staff.route('/airSystemManage/airport', methods=['GET', 'POST'])
@staff_login_required
def manageAirport():
    if request.method == "POST":
        # fetch data
        name = request.form["name"]
        city = request.form["city"]

        # check duplicates
        cursor = conn.cursor()
        query = "SELECT * FROM airport WHERE airport_name = %s"
        cursor.execute(query, (name))
        data = cursor.fetchall()
        if data:
            noFound = "Such airport name already exists"
            return render_template("airSystemManage.html", noFound=noFound, message="airport", state_airport=True)
        cursor.close()

        # initiate query
        cursor = conn.cursor()
        query = "INSERT INTO airport VALUES (%s, %s)"
        cursor.execute(query, (name, city))
        cursor.close()
        conn.commit()
        session["airport_updated"] = True
        return redirect("/airSystemManage/airport")

    else:
        # display all the planes operated by the airline
        cursor = conn.cursor()
        query = "SELECT * FROM airport"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        if data:
            for each in data:
                print("data:", each)
            return render_template("airSystemManage.html", airport=data, state_airport=True)
        else:
            noFound = "There is no airport in the system"
            return render_template("airSystemManage.html", noFound=noFound, state_airport=True)


@staff.route('/report/topAgent', methods=['GET', 'POST'])
@staff_login_required
def viewTopAgent():
    # get airline name
    airline_name = session['airline_name']

    if request.method == 'POST':
        # fetch data
        option = request.form.get("viewSelect")
        cursor = conn.cursor()
        # three options:
        if option == "by_sales_month":
            title = "Top 5 booking agents by ticket sales for the past month"
            query = "SELECT  booking_agent_id, COUNT(*) AS total_sales FROM purchases \
            WHERE booking_agent_id IS NOT NULL AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 30 DAY AND NOW()\
            GROUP BY booking_agent_id ORDER BY total_sales DESC LIMIT 5"
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            if data:
                for each in data:
                    print(each)
                return render_template("report.html", title=title, by_sales=data)
            else:
                noFound = "There is an issue in displaying the information you want"
                return render_template("report.html", noFound=noFound)
        elif option == "by_sales_year":
            title = "Top 5 booking agents by ticket sales for the past year"
            query = "SELECT  booking_agent_id, COUNT(*) AS total_sales FROM purchases \
            WHERE booking_agent_id IS NOT NULL AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 1 YEAR AND NOW()\
            GROUP BY booking_agent_id ORDER BY total_sales DESC LIMIT 5"
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            if data:
                for each in data:
                    print(each)
                return render_template("report.html", title=title, by_sales=data)
            else:
                noFound = "There is an issue in displaying the information you want"
                return render_template("report.html", noFound=noFound)
        else:
            title = "Top 5 booking agents by total commission for the past year"
            query = "SELECT booking_agent_id, SUM(price) * 0.1 AS commission FROM purchases NATURAL JOIN ticket NATURAL JOIN flight\
                     WHERE booking_agent_id IS NOT NULL AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 1 YEAR AND NOW()\
                     GROUP BY booking_agent_id ORDER BY commission DESC LIMIT 5"
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            if data:
                for each in data:
                    print(each)
                return render_template("report.html", title=title, by_commission=data)
            else:
                noFound = "There is an issue in displaying the information you want"
                return render_template("report.html", title=title, noFound=noFound)

    else:
        title = "Default: Top 5 booking agents by ticket sales for the past month"
        cursor = conn.cursor()
        query = "SELECT  booking_agent_id, COUNT(*) AS total_sales FROM purchases \
        WHERE booking_agent_id IS NOT NULL AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 30 DAY AND NOW()\
        GROUP BY booking_agent_id ORDER BY total_sales DESC LIMIT 5"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        if data:
            for each in data:
                print(each)
            return render_template("report.html", by_sales=data)
        else:
            noFound = "There is an issue in displaying the information you want."
            return render_template("report.html", noFound=noFound)


@staff.route('/report/topCustomer')
@staff_login_required
def viewTopCustomer():
    # get airline name
    airline_name = session['airline_name']

    # start to fetch the data
    cursor = conn.cursor()
    query = "SELECT customer_email, COUNT(*) AS travel_times FROM purchases NATURAL JOIN ticket \
    WHERE airline_name = %s AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 1 YEAR AND NOW() \
    GROUP BY customer_email"

    cursor.execute(query, (airline_name))

    data1 = cursor.fetchall()
    max_times = 0
    for each in data1:
        if each["travel_times"] > max_times:
            max_times = each["travel_times"]

    query2 = "SELECT customer_email, COUNT(*) AS travel_times FROM purchases NATURAL JOIN ticket\
     WHERE airline_name = %s GROUP BY customer_email HAVING travel_times = %s"
    cursor.execute(query2, (airline_name, max_times))
    data = cursor.fetchall()
    cursor.close()
    if data:
        for each in data:
            print(data)
        return render_template("report.html", passenger=data)
    else:
        noFound = "There is an issue in displaying the information you want"
        return render_template("report.html", noFound=noFound)


@staff.route('/report/topCustomer/<string:email>')
@staff_login_required
def viewCustomerFlight(email):
    # get airline name
    airline_name = session['airline_name']

    # fetch data
    cursor = conn.cursor()
    query = "SELECT airline_name, flight_num, departure_time, purchase_date, price, customer_email \
    FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE customer_email = %s"
    cursor.execute(query, (email))
    data = cursor.fetchall()
    cursor.close()
    if data:
        for each in data:
            print(data)
        return render_template("report.html", people_flight=data)
    else:
        noFound = "There is an issue in displaying the information you want"
        return render_template("report.html", noFound=noFound)


@staff.route('/report/salesReport/<string:message>', methods=['GET', 'POST'])
@staff_login_required
def viewReport(message):
    # get airline name
    airline_name = session['airline_name']

    if message == "default":
        # access total_sales and date range
        cursor = conn.cursor()
        query = "SELECT DATE(NOW()) - INTERVAL 1 MONTH AS curr_prev, DATE(NOW()) AS current,  COUNT(*) AS total_sales \
            FROM purchases NATURAL JOIN ticket WHERE date(purchase_date) between DATE(NOW()) - INTERVAL 1 MONTH AND DATE(NOW()) and airline_name = %s"
        cursor.execute(query, (airline_name))
        info = cursor.fetchone()
        total_sales = info['total_sales']  # total sales
        from_date = info['curr_prev']  # from_date
        to_date = info['current']  # to_date
        from_date_format = from_date
        to_date_format = to_date
        default = "Default:"
        title = "Total Sales for the Past Month"

    elif message == "date_range":
        # fetch input
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        if datetime.strptime(from_date, "%Y-%m-%d") > datetime.strptime(to_date, "%Y-%m-%d"):
            return render_template("flightManage.html", error="The dates you entered are invalid.")
        from_date_format = datetime.strptime(from_date, '%Y-%m-%d')
        to_date_format = datetime.strptime(to_date, '%Y-%m-%d')
        # access total_sales
        cursor = conn.cursor()
        query = "SELECT COUNT(*) as total_sales FROM purchases NATURAL JOIN ticket WHERE date(purchase_date) >= %s \
        AND date(purchase_date) <= %s and airline_name = %s"
        cursor.execute(query, (from_date, to_date, airline_name))
        info = cursor.fetchone()
        total_sales = info['total_sales']  # total sales
        default = ""
        title = ""

    else:
        option = request.form.get("salesSelect")
        if option == "sales_past_month":
            # access total_sales and date range
            cursor = conn.cursor()
            query = "SELECT DATE(NOW()) - INTERVAL 1 MONTH AS curr_prev, DATE(NOW()) AS current,  COUNT(*) AS total_sales \
            FROM purchases NATURAL JOIN ticket WHERE date(purchase_date) between DATE(NOW()) - INTERVAL 1 MONTH AND DATE(NOW()) and airline_name = %s"
            cursor.execute(query, (airline_name))
            info = cursor.fetchone()
            total_sales = info['total_sales']  # total sales
            from_date = info['curr_prev']  # from_date
            to_date = info['current']  # to_date
            from_date_format = from_date
            to_date_format = to_date
            default = ""
            title = "Total Sales for the Past Month"

        else:
            # access total_sales and date range
            cursor = conn.cursor()
            query = "SELECT DATE(NOW()) AS current, DATE(NOW()) - INTERVAL 1 YEAR AS curr_prev , COUNT(*) as total_sales \
                FROM purchases NATURAL JOIN ticket WHERE date(purchase_date) between DATE(NOW()) - INTERVAL 1 YEAR AND DATE(NOW()) and airline_name = %s"
            cursor.execute(query, (airline_name))
            info = cursor.fetchone()
            print(info)
            total_sales = info['total_sales']  # total sales
            from_date = info['curr_prev']  # from_date
            to_date = info['current']  # to_date
            from_date_format = from_date
            to_date_format = to_date
            default = ""
            title = "Total Sales for the Past Year"

    # access sales by month
    query = "SELECT YEAR(purchase_date) as year, MONTH(purchase_date) as month, COUNT(*) as total_sales \
    FROM purchases NATURAL JOIN ticket WHERE date(purchase_date) >= %s AND date(purchase_date) <= %s and airline_name = %s \
    GROUP BY year, month \
    ORDER BY year, month ASC"
    cursor.execute(query, (from_date, to_date, airline_name))
    raw_data = cursor.fetchall()
    print("raw", raw_data)
    cursor.close()

    # create empty dictionary
    sales_dict = {}
    start_year = from_date_format.year
    start_month = from_date_format.month
    end_year = to_date_format.year
    end_month = to_date_format.month
    sales_dict["{}-{}".format(start_year, start_month)] = 0
    print(start_year, start_month, end_year, end_month)

    if start_year != end_year:
        while start_year < end_year:
            while start_month < 12:
                sales_dict["{}-{}".format(start_year, start_month + 1)] = 0
                start_month += 1
            start_year += 1
            start_month = 0
            if start_year == end_year:
                while start_month < end_month:
                    sales_dict["{}-{}".format(start_year, start_month + 1)] = 0
                    start_month += 1
    else:
        while start_month < end_month:
            sales_dict["{}-{}".format(start_year, start_month + 1)] = 0
            start_month += 1

    print("empty_dict:", sales_dict)

    for each in raw_data:
        print(each)
        sales_dict["{}-{}".format(each["year"], each["month"])] = each["total_sales"]
    print("full_dict:", sales_dict)
    label_list = []
    values_list = []

    for keys in sales_dict:
        label_list.append(keys)
        values_list.append(str(sales_dict[keys]))

    print("labels", label_list)
    print("values", values_list)

    try:
        mymax = max(values_list)
    except:
        mymax = 100

    return render_template('report.html', sales=True, default=default, title=title, total_sales=total_sales,
                           max=mymax, from_date=from_date, to_date=to_date, labels=label_list, values=values_list)


@staff.route('/report/revenueCompare', methods=['GET', 'POST'])
@staff_login_required
def revenueCompare():

    cursor = conn.cursor()

    # colors:
    colors = ["#FFB6C1", "#EE82EE"]
    if request.method == "POST":
        default = ""
        option = request.form.get("revSelect")
        if option == "rev_past_month":
            title = "Revenue comparison for the past month"
            query_direct = "SELECT SUM(price) as total_price FROM ticket NATURAL JOIN purchases NATURAL JOIN flight\
                WHERE booking_agent_id IS NULL and DATE(purchase_date) BETWEEN DATE(NOW()) - INTERVAL 1 MONTH and DATE(NOW())"
            query_indirect = "SELECT SUM(price) as total_price FROM ticket NATURAL JOIN purchases NATURAL JOIN flight \
                WHERE booking_agent_id IS NOT NULL and DATE(purchase_date) BETWEEN DATE(NOW()) - INTERVAL 1 MONTH and DATE(NOW())"
        else:
            title = "Revenue comparison for the past year"
            query_direct = "SELECT SUM(price) as total_price FROM ticket NATURAL JOIN purchases NATURAL JOIN flight \
                WHERE booking_agent_id IS NULL and DATE(purchase_date) BETWEEN DATE(NOW()) - INTERVAL 1 YEAR and DATE(NOW())"
            query_indirect = "SELECT SUM(price) as total_price FROM ticket NATURAL JOIN purchases NATURAL JOIN flight \
                WHERE booking_agent_id IS NOT NULL and DATE(purchase_date) BETWEEN DATE(NOW()) - INTERVAL 1 YEAR and DATE(NOW())"

    else:
        default = "Default:"
        title = "Revenue comparison for the past month"
        query_direct = "SELECT SUM(price) as total_price FROM ticket NATURAL JOIN purchases NATURAL JOIN flight \
            WHERE booking_agent_id IS NULL and DATE(purchase_date) BETWEEN DATE(NOW()) - INTERVAL 1 MONTH and DATE(NOW())"
        query_indirect = "SELECT SUM(price) as total_price FROM ticket NATURAL JOIN purchases NATURAL JOIN flight \
            WHERE booking_agent_id IS NOT NULL and DATE(purchase_date) BETWEEN DATE(NOW()) - INTERVAL 1 MONTH and DATE(NOW())"

    cursor.execute(query_direct)
    direct_sales = cursor.fetchone()

    cursor.execute(query_indirect)
    indirect_sales = cursor.fetchone()

    labels = ['direct_sales', 'indirect_sales']
    values = [float(direct_sales["total_price"]) if direct_sales["total_price"] is not None else 0,
              float(indirect_sales["total_price"]) if indirect_sales["total_price"] is not None else 0]

    print(values)

    try:
        mymax = max(values)
    except:
        mymax = 100000

    return render_template("report.html", default=default, title=title, revenue=True, \
                           max=mymax, set=zip(values, labels, colors))


@staff.route('/report/topDestination', methods=['GET', 'POST'])
@staff_login_required
def topDestination():

    # different query
    if request.method == "POST":
        chosen = request.form.get("seeSelect")
        if chosen == "by_3month":
            title = "Top Three Destinations for the Past Three Months"
            query = "SELECT arrival_airport, airport_city, count(*) as visit_time \
                    FROM purchases NATURAL JOIN ticket NATURAL JOIN flight as S, airport \
                    WHERE S.arrival_airport  = airport.airport_name AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 3 MONTH and NOW()\
                    GROUP BY arrival_airport ORDER BY visit_time DESC LIMIT 3"
        else:
            title = "Top Three Destinations for the Past Year"
            query = "SELECT arrival_airport, airport_city, count(*) as visit_time \
                    FROM purchases NATURAL JOIN ticket NATURAL JOIN flight as S, airport \
                    WHERE S.arrival_airport  = airport.airport_name AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 1 YEAR and NOW()\
                    GROUP BY arrival_airport ORDER BY visit_time DESC LIMIT 3"
    else:
        title = "Default: Top Three Destinations for the Past Year"
        query = "SELECT arrival_airport, airport_city, count(*) as visit_time \
                FROM purchases NATURAL JOIN ticket NATURAL JOIN flight as S, airport \
                WHERE S.arrival_airport  = airport.airport_name AND DATE(purchase_date) BETWEEN NOW() - INTERVAL 1 YEAR and NOW() \
                GROUP BY arrival_airport ORDER BY visit_time DESC LIMIT 3"
    # execute the query
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    if data:
        for each in data:
            print(data)
        return render_template("report.html", title=title, destinations=data)
    else:
        noFound = "Sorry, there's an issue in displaying the information"
        return render_template("report.html", noFound=noFound, destinations=data)
