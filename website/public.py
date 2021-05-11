from flask import Blueprint, render_template, request
from .DB_connector import conn
from datetime import datetime

public = Blueprint('public', __name__)


@public.route('/')
def hello():
    return render_template('index.html')

#searching for flights in public, in that anyone can access it.
@public.route('/searching_for_flights', methods=['GET', 'POST'])

def searching_for_flights():
    cursor = conn.cursor()

    departure_airport = request.form['departure_airport']

    arrival_airport = request.form['arrival_airport']

    departure_date = request.form['departure_date']

    return_date = request.form['return_date']

    #We check to see if the airline date has passed our own date.

    if datetime.strptime(departure_date, "%Y-%m-%d") < datetime.now():

        error = "The dates you just entered are invalid, please enter dates that are in the valid."

        return render_template("index.html", error = error)





    query1 = "select * from flight natural join airplane, airport as A, airport as B \
                where flight.departure_airport = A.airport_name and flight.arrival_airport = B.airport_name \
                and (A.airport_name = %s or A.airport_city = %s) and (B.airport_name = %s or B.airport_city = %s) \
                and date(departure_time) = %s "


    cursor.execute(query1, (departure_airport, departure_airport, arrival_airport, arrival_airport, departure_date))

    #storing the results
    data_1 = cursor.fetchall()

    print("THIS IS DATA_1 \n", data_1)

    if return_date:

        if datetime.strptime(departure_date, "%Y-%m-%d") > datetime.strptime(return_date, "%Y-%m-%d"):

            return render_template("search.html", error = "The dates you entered are invalid. Please go back and enter valid dates.")

        query2 = "select * from flight natural join airplane, airport as A, airport as B \
                where flight.departure_airport = A.airport_name and flight.arrival_airport = B.airport_name \
                and (A.airport_name = %s or A.airport_city = %s) and (B.airport_name = %s or B.airport_city = %s) \
                and date(departure_time) = %s "

        cursor.execute(query2, ( arrival_airport, arrival_airport, departure_airport, departure_airport, return_date))

    data_2 = cursor.fetchall()

    print("THIS IS DATA_2 \n", data_2)


    conn.commit()

    cursor.close()

    error = None

    if data_1:  #make sure your input is valid
        #Now check if the user entered the correct value

        if return_date:

            if data_2:

                return render_template("search.html", flights=data_1, returnFlights=data_2)

            else:

                error = "The Return Flight You are Searching Is Empty"

                return render_template("search.html", error=error)
        #This is a one way trip

        else:

            return render_template("search.html", flights=data_1)
    else:

        # returns an error message to the html page because data_1 is None

        error = "The Flight You are Searching Is Empty"

        return render_template("search.html", error=error)

@public.route('/check_for_flights', methods=['GET', 'POST'])

def check_fight_status():
    airline_name = request.form['airline_name']
    flight_num = request.form['flight_num']
    departure_date = request.form['departure_date']
    return_date = request.form['return_date']

    # open cursor
    cursor = conn.cursor()

    if departure_date and return_date:
        query = "select * from flight \
            where airline_name = %s and flight_num = %s and date(departure_time) = %s and date(arrival_time) = %s"
        cursor.execute(query, (airline_name, flight_num, departure_date, return_date))
    elif departure_date:
        query = "select * from flight \
            where airline_name = %s and flight_num = %s and date(departure_time) = %s"
        cursor.execute(query, (airline_name, flight_num, departure_date))
    elif return_date:
        query = "select * from flight \
            where airline_name = %s and flight_num = %s and date(arrival_time) = %s"
        cursor.execute(query, (airline_name, flight_num, return_date))
    else:
        pass
    data_3 = cursor.fetchall()
    #print("HIIIIIIIII")
    #print(data_3)
    cursor.close()
    conn.commit()
    error = None

    if data_3:
        #print("YOU ARE HEREE")
        return render_template("check.html", status=data_3)
    else:
        error = "The Flight You are Searching Is Empty"
        return render_template("check.html", error=error)

