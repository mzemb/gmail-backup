#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import email
import email.utils
import datetime
import time
import calendar


FILE_RE = re.compile(r"(\d+).eml$")
LAST_DATE_FIXED_FILENAME = "last_email_fixed.dat"


def get_message_ctime(d):
    orig_d = d
    dt_src = email.utils.parsedate_tz(d)
    if not dt_src:
        return None
    if not dt_src[-1]:
        # TZ INFO IS MESSY
        if " --" in d:
            d = d.replace(" --", " -")
            dt_src = email.utils.parsedate_tz(d)
    try:
        dt = datetime.datetime(*dt_src[:6])
    except Exception, e:
        print e
        print "orig date: %r, curr date: %r, dt_src: %r" % (orig_d, d, dt_src)
        return None
    if dt_src[-1]:
        dt = dt - datetime.timedelta(seconds=dt_src[-1])
    dt = datetime.datetime.fromtimestamp(calendar.timegm(dt.timetuple()))
    message_ctime = time.mktime(dt.timetuple())
    return message_ctime


def update_file_time(fname):
    with open(fname) as f:
        file_contents = f.read()
    message = email.message_from_string(file_contents)
    message_ctime = get_message_ctime(message['date'])
    if message_ctime:
        os.utime(fname, (message_ctime, message_ctime))


def read_last_file():
    try:
        with open(LAST_DATE_FIXED_FILENAME) as f:
            last_file_int_fixed = int(f.read().strip())
    except:
        last_file_int_fixed = -1
    return last_file_int_fixed


def write_last_file(last):
    f = open(LAST_DATE_FIXED_FILENAME, 'w')
    f.write(str(last))
    f.close()


def load_file_to_handle(last_file_int_fixed):
    emails = []
    for fname in os.listdir("."):
        m = FILE_RE.match(fname)
        if m:
            file_int = int(m.group(1))
            if file_int > last_file_int_fixed:
                emails.append([int(m.group(1)), fname])

    emails.sort()
    return emails


def main():
    last_file_int_fixed = read_last_file()

    emails = load_file_to_handle(last_file_int_fixed)

    for i, (file_int, fname) in enumerate(emails):
        print "(%d of %d) %s" % (i + 1, len(emails), fname)
        update_file_time(fname)

    if emails:
        write_last_file(emails[-1][0])

if __name__ == '__main__':
    main()
