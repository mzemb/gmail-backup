#!/usr/bin/env python
# -*- coding: utf-8 -*-

import calendar
import datetime
import email
import email.utils
import hashlib
import os
import re
import time

FILE_RE = re.compile(r"(\d+).eml$")
LAST_DATE_FIXED_FILENAME = "last_email_fixed.dat"
LARGE_FILE_SIZE = 100000  # 100K
LAST_HASH_FILENAME = "last.hash"
SEEN_HASH = {}


def get_message_ctime(message):
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


def fix_file_time(fname, message):
    ctime = get_message_ctime(message)
    update_file_mtime(fname, ctime)
    return ctime


def fix_file_name(uid, fname, message, ctime):
    from dobackup import get_filename_by_date
    archive_path = get_filename_by_date(uid, ctime)
    if not fname.endswith(archive_path):
        os.renames(fname, archive_path)
        return archive_path
    return fname


def read_hash_data():
    try:
        content = open(LAST_HASH_FILENAME).read()
        return dict(line.split(' ', 1) for line in content.split('\n'))
    except:
        return {}

SEEN_HASH = read_hash_data()


def write_hash_data():
    with open(LAST_HASH_FILENAME, 'w') as f:
        f.write('\n'.join('%s %s' % (hash, SEEN_HASH[hash])
                          for hash in sorted(SEEN_HASH.keys())))


def fix_large_duplication(fname, message):
    changed = False
    path = os.path.normpath(fname)
    for part in message.walk():
        if part.get_filename():
            content = part.get_payload()
            size = len(content)
            if size > LARGE_FILE_SIZE:
                hash = hashlib.md5(content).hexdigest()
                origin_file = SEEN_HASH.get(hash)
                if not origin_file:
                    SEEN_HASH[hash] = path
                elif origin_file != path:
                    part.set_payload('duplication removed, origin: %s' %
                                     origin_file)
                    with open(fname, 'w') as f:
                        f.write(message.as_string())
                    changed = True
    if changed:
        write_hash_data()
    return changed


def fix_file(uid, fname):
    with open(fname) as f:
        file_content = f.read()
    message = email.message_from_string(file_content)
    message_ctime = get_message_ctime(message)

    fname = fix_file_name(uid, fname, message, message_ctime)

    fix_large_duplication(fname, message)

    fix_file_time(fname, message)


def update_file_mtime(fname, mtime):
    if mtime and os.stat(fname).st_mtime != mtime:
        atime = mtime
        os.utime(fname, (atime, mtime))


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
        write_hash_data()

if __name__ == '__main__':
    main()
