import pymysql.cursors

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='M!sc4106/',
                       db='ATRS',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)