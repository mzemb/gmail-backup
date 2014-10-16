#!/usr/bin/env python
# -*- coding: utf-8 -*-

import calendar
import datetime
import email
import email.utils
import os
import re
import time

FILE_RE = re.compile(r"(\d+).eml$")
LAST_DATE_FIXED_FILENAME = "last_email_fixed.dat"


def get_message_ctime(content):
    message = email.message_from_string(content)
    ctime = message['date']
    d = ctime
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
        print "orig date: %r, curr date: %r, dt_src: %r" % (ctime, d, dt_src)
        return None
    if dt_src[-1]:
        dt = dt - datetime.timedelta(seconds=dt_src[-1])
    dt = datetime.datetime.fromtimestamp(calendar.timegm(dt.timetuple()))
    message_ctime = time.mktime(dt.timetuple())
    return message_ctime


def fix_file(uid, fname):
    with open(fname) as f:
        file_content = f.read()
    message_ctime = get_message_ctime(file_content)
    if message_ctime:
        update_file_time(fname, message_ctime)

    from dobackup import get_filename_by_date
    archive_path = get_filename_by_date(uid, message_ctime)
    if not fname.endswith(archive_path):
        os.renames(fname, archive_path)


def update_file_time(fname, ctime):
    os.utime(fname, (ctime, ctime))


def read_last_file():
    try:
        with open(LAST_DATE_FIXED_FILENAME) as f:
            last_file_int_fixed = int(f.read().strip())
    except:
        last_file_int_fixed = -1
    return last_file_int_fixed


def write_last_file(last):
    with open(LAST_DATE_FIXED_FILENAME, 'w') as f:
        f.write(str(last))


def load_file_to_handle(last_file_int_fixed):
    emails = []
    for dir, _, fnames in os.walk("."):
        for fname in fnames:
            path = os.path.join(dir, fname)
            m = FILE_RE.match(fname)
            if m:
                file_int = int(m.group(1))
                if file_int > last_file_int_fixed:
                    emails.append([int(m.group(1)), path])

    emails.sort()
    return emails


def main():
    last_file_int_fixed = read_last_file()

    emails = load_file_to_handle(last_file_int_fixed)

    for i, (file_int, fname) in enumerate(emails):
        print "(%d of %d) %s" % (i + 1, len(emails), fname)
        fix_file(file_int, fname)

    if emails:
        write_last_file(emails[-1][0])

if __name__ == '__main__':
    main()
