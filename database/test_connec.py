#!/usr/bin/env python3
# Test connection to the database after it has been set up

import mariadb

conn = mariadb.connect(
    user="cielo",
    password="cielo",
    host="localhost",
    port=3306,
    database="cielo"
)

cur = conn.cursor()

cur.execute("SELECT count(*) FROM events")
if len([el for el in cur]) == 1:
    print("Yep we connected and events table exists.")
# If doesn't hit error, that's all we're looking to exercise here
