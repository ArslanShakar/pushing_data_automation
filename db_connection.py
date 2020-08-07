# -*- coding: utf-8 -*-

import time
from mysql.connector import connect, Error

local_db_credentials = {
    "host": "localhost",
    "user": "root",
    "passwd": "toor",
    "database": "demodb"
}

live_db_credentials = {
    "host": "localhost",
    "user": "root",
    "passwd": "toor",
    "database": "quick_delivery",
    "port": 3306,
}

live_db_credentials = {
    "host": "162.0.227.242",
    "user": "quick_delivery2",
    "passwd": "tXKekhGvBKEbWXTA6kE67XEVvHrgsHr3KFMNUtenyt7zeqWkRYusHZNsZPP2Pu",
    "database": "quick_delivery",
    "port": 6446,
}


class DBConnection:
    def __init__(self):
        self.open_sql_connection()

    def open_sql_connection(self):
        connection_tries = 0
        while connection_tries < 5:
            try:
                self.sql_connection, self.sql_conn_cursor, self.sql_dict_cursor = \
                    self.get_connection(local_db_credentials)
                print("Local Database Connected Successfully.")

                self.live_sql_connection, self.live_sql_conn_cursor, self.live_sql_dict_cursor = \
                    self.get_connection(live_db_credentials)

                print("Live Database Connected Successfully.")
                return True
            except Error as err:
                print(f"Exception While Connecting Database: {err}")
                connection_tries += 1
                time.sleep(30)

        if connection_tries == 5:
            print('Failed 5 times to establish database connection')

    def get_connection(self, credentials):
        sql_connection = connect(**credentials)
        return sql_connection, sql_connection.cursor(), sql_connection.cursor(dictionary=True)

    def update_mysql_connection(self):
        if self.sql_connection.is_connected() and self.live_sql_connection.is_connected():
            return True
        return self.open_sql_connection()

    def close_db_connection(self):
        self.sql_conn_cursor.close()
        self.sql_dict_cursor.close()
        self.sql_connection.close()

        self.live_sql_connection.close()
        self.live_sql_conn_cursor.close()
        self.live_sql_dict_cursor.close()
