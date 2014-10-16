#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getpass
import imaplib
import os
import re
import time

from fix import get_message_ctime, update_file_time

LAST_ID_FILE = 'last_fetched_id.dat'

UID_RE = re.compile(r"\d+\s+\(UID (\d+)\)$")
FILE_RE = re.compile(r"(\d+).eml$")
GMAIL_FOLDER_NAME = "[Gmail]/All Mail"


def getUIDForMessage(svr, n):
    resp, lst = svr.fetch(n, 'UID')
    m = UID_RE.match(lst[0])
    if not m:
        raise Exception(
            "Internal error parsing UID response: %s %s.  Please try again" % (
                resp, lst))
    return m.group(1)


def get_filename_by_date(uid, ctime):
    localtime = time.localtime(ctime)
    year = localtime.tm_year
    month = localtime.tm_mon
    dir = '%s-%s' % (year, month)
    fname = '%s/%s.eml' % (dir, uid)
    return fname


def downloadMessage(svr, n, uid):
    resp, lst = svr.fetch(n, '(RFC822)')
    if resp != 'OK':
        raise Exception("Bad response: %s %s" % (resp, lst))
    content = lst[0][1]

    ctime = get_message_ctime(content)
    fname = get_filename_by_date(uid, ctime)
    dir = os.path.dirname(fname)
    if not os.path.exists(dir):
        os.makedirs(dir)

    with open(fname, 'w') as f:
        f.write(content)
    if ctime:
        update_file_time(fname, ctime)


def UIDFromFilename(fname):
    m = FILE_RE.match(fname)
    if m:
        return int(m.group(1))


def get_credentials():
    try:
        user, pwd = open('account.conf').read().strip().split()
    except:
        user = raw_input("Gmail address: ")
        pwd = getpass.getpass("Gmail password: ")
        with open('account.conf', 'w') as f:
            f.write('%s %s' % (user, pwd))
    return user, pwd


def write_last_id(uid):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(uid))


def read_last_id():
    try:
        return open(LAST_ID_FILE).read().strip()
    except:
        return 0


def do_backup():
    svr = imaplib.IMAP4_SSL('imap.gmail.com')
    user, pwd = get_credentials()
    print 'login...'
    svr.login(user, pwd)

    resp, [countstr] = svr.select(GMAIL_FOLDER_NAME, True)
    count = int(countstr)

    lastdownloaded = read_last_id()

    # A simple binary search to see where we left off
    gotten, ungotten = 0, count + 1
    while (ungotten - gotten) > 1:
        attempt = (gotten + ungotten) / 2
        uid = getUIDForMessage(svr, attempt)
        if int(uid) <= lastdownloaded:
            print "Finding starting point: %d/%d (UID: %s) too low" % (
                attempt, count, uid)
            gotten = attempt
        else:
            print "Finding starting point: %d/%d (UID: %s) too high" % (
                attempt, count, uid)
            ungotten = attempt

    # The download loop
    for i in range(ungotten, count + 1):
        uid = getUIDForMessage(svr, i)
        print "Downloading %d/%d (UID: %s)" % (i, count, uid)
        downloadMessage(svr, i, uid)
        write_last_id(uid)

    svr.close()
    svr.logout()

if __name__ == "__main__":
    do_backup()
