#!/usr/bin/python
# coding: utf-8

# BlueSensor database functions

import sys, os
import traceback
import datetime, time, pytz
from pprint import pprint
import json
import psycopg2
import psycopg2.extensions
from threading import Lock

DBHOST = 'localhost'
DBNAME = 'bluesensor'
DBUSER = 'postgres'
DBPWD  = 'password'
TABLE  = 'data'

db = None
cs = None
db_lock = Lock()

tz = pytz.timezone('Europe/Ljubljana')

def print_exc(f_name, msg=''):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    exc = traceback.format_exception_only(exc_type, exc_obj)
    err = '{}({}): {}'.format(f_name, exc_tb.tb_lineno, msg) + exc[-1].strip()
    sys.stderr.write(err + '\n')

def time_now_ms():
    tt = datetime.datetime.now(tz).timetuple()
    now = time.mktime(tt) + 3600 # WTF?!
    if tt.tm_isdst: now += 3600
    return int(now)*1000

def sqlDate(dt=None):
    # PostgreSQL timestamp (ISO 8601) without time zone
    #sdt = '1980-01-01 12:00:00.000000'# + '+00:00'
    sdt = None
    try:
        if dt is None:
            dt = datetime.datetime.now()
        sdt = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        #sdt += '+00:00'
    except:
        print_exc(sys._getframe().f_code.co_name)
    return sdt

def dbInsert(source, data):
    rc = False
    try:
        # Table DATA: 0: id (serial, primary key),
        # 1: date, 2: source, 3: data
        values = (sqlDate(), source, data)
        cs.execute("INSERT INTO {tn} ("\
            "date, source, data"\
            ") VALUES (%s,%s,%s)"\
            .format(tn=TABLE), values)
        db.commit()
        rc = True
    except:
        print_exc(sys._getframe().f_code.co_name)
    return rc

def dbOpen():
    global db, cs
    rc = False
    try:
        with db_lock:
            if db is None or cs is None:
                sys.stderr.write('Connecting to db {0}:{1} as user {2}\n'\
                    .format(DBHOST, DBNAME, DBUSER))
                db = psycopg2.connect(host=DBHOST, dbname=DBNAME, user=DBUSER, password=DBPWD)
                db.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cs = db.cursor()
        # Table DATA: 0: id (serial, primary key),
        # 1: date, 2: source, 3: data
        cs.execute("CREATE TABLE IF NOT EXISTS {tn} (id serial PRIMARY KEY, "\
            "date timestamp, source text, data jsonb"\
            ")".format(tn=TABLE))
        db.commit()
        rc = True
    except:
        print_exc(sys._getframe().f_code.co_name)
    return rc
