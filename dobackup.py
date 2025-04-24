#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import email
import getpass
import imaplib
import os
import re
import time

from fix import fix_large_duplication, get_message_ctime, update_file_mtime, \
    write_hash_data, EMAILS_ENCODING

LAST_ID_FILE = 'last_fetched_id.dat'

UID_RE = re.compile(rb"\d+\s+\(UID (\d+)\)$")
FILE_RE = re.compile(rb"(\d+).eml$")
GMAIL_FOLDER_NAME = '"[Gmail]/All Mail"'


def getUIDForMessage(svr, n):
    resp, lst = svr.fetch(n, 'UID')
    m = UID_RE.match(lst[0])
    if not m:
        raise Exception(
            "Internal error parsing UID response: %s %s.  Please try again" % (
                resp, lst))
    return int(m.group(1))


def get_filename_by_date(uid, ctime):
    localtime = time.localtime(ctime)
    year = localtime.tm_year
    month = localtime.tm_mon
    dir = '%s-%02d' % (year, month)
    fname = '%s/%s.eml' % (dir, uid)
    return fname


def downloadMessage(svr, n, uid):
    resp, lst = svr.fetch(n, '(RFC822)')
    if resp != 'OK':
        raise Exception("Bad response: %s %s" % (resp, lst))
    content = lst[0][1]
    
    if isinstance(content, bytes):
        content = content.decode(EMAILS_ENCODING)
    
    message = email.message_from_string(content)
    ctime = get_message_ctime(message)
    fname = get_filename_by_date(uid, ctime)
    dir = os.path.dirname(fname)
    if not os.path.exists(dir):
        os.makedirs(dir)

    with open(fname, 'w', encoding=EMAILS_ENCODING) as f:
        f.write(content)

    fix_large_duplication(fname, message)

    update_file_mtime(fname, ctime)


def UIDFromFilename(fname):
    m = FILE_RE.match(fname)
    if m:
        return int(m.group(1))


def get_credentials():
    try:
        user, pwd = open('account.conf').read().strip().split()
    except:
        user = input("Gmail address: ")
        pwd = getpass.getpass("Gmail password: ")
        with open('account.conf', 'w') as f:
            f.write('%s %s' % (user, pwd))
    return user, pwd


def write_last_id(uid):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(uid))


def read_last_id():
    try:
        return int(open(LAST_ID_FILE).read().strip())
    except:
        return 0


def do_backup():
    print('login...')
    user, pwd = get_credentials()
    svr = imaplib.IMAP4_SSL('imap.gmail.com')
    svr.login(user, pwd)

    #resp, folders = svr.list()
    #if resp == 'OK':
    #    print("Available folders:")
    #    for folder in folders:
    #        print(folder.decode())

    resp, [countstr] = svr.select(GMAIL_FOLDER_NAME, readonly=True)
    count = int(countstr)

    lastdownloaded = read_last_id()

    # A simple binary search to see where we left off
    gotten, ungotten = 0, count + 1
    while (ungotten - gotten) > 1:
        attempt = int((gotten + ungotten) / 2)
        uid = getUIDForMessage(svr, str(attempt))
        if int(uid) <= lastdownloaded:
            print("Finding starting point: %d/%d (UID: %s) too low" % (
                attempt, count, uid))
            gotten = attempt
        else:
            print("Finding starting point: %d/%d (UID: %s) too high" % (
                attempt, count, uid))
            ungotten = attempt

    # The download loop
    for i in range(ungotten, count + 1):
        uid = getUIDForMessage(svr, str(i))
        print("Downloading %d/%d (UID: %s)" % (i, count, uid))
        downloadMessage(svr, str(i), (uid))
        write_last_id(uid)

    write_hash_data()
    svr.close()
    svr.logout()

if __name__ == "__main__":
    do_backup()
