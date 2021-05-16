import pymysql.cursors

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='Airline_Tickets',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
