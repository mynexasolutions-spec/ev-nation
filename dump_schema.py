import sqlite3
import pprint

conn = sqlite3.connect(r'C:\Users\aamir\AppData\Local\EV_Nation\ev_nation.db')
c = conn.cursor()
for row in c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
    print("--", row[0])
    print(row[1])
for row in c.execute("SELECT name, sql FROM sqlite_master WHERE type='index'"):
    print("--", row[0])
    print(row[1])
