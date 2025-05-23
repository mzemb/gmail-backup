**Gmail-Backup**
===================
A simple Python script to download all your mail from Gmail to your local hard drive.

**Forks**
--------------
abjennings/gmail-backup > xyb/gmail-backup > mzemb/gmail-backup

**Introduction**
--------------
I love Gmail.  But sometimes I worry that all my emails are stored on Google's servers and if they ever
lost them, then I would be hurting in a bad way.  And it would only be my own fault because I had never
backed them up anywhere.

So I wrote a simple Python script to download all my emails and save them in files on my local hard
drive.  Sure, I could use another mail client, but I don't want to install more software on my computer
than I need to.  I don't want to worry about that database getting corrupted.  I don't want to worry
about whether several gigabytes of data is too much for it to handle.  I don't want to worry about
whether it's storing them in an efficient format, or building indexes it doesn't need to.  And I don't
really want it to store my Gmail password in some obfuscated format that other programs might be able
to get access to.

**Notes**
---------
1. Make sure IMAP is enabled in your Gmail settings.

2. `cd` into an empty directory where you want your emails downloaded.

2. Run ```python path-to-gmail-backup/dobackup.py``` and put in your Gmail address and password when prompted.

3. Your emails will be downloaded to the current directory and named 1.eml, 2.eml, etc.

4. Numbering is not necessarily sequential.  The file is named after the message's "unique id", which,
as part of the IMAP protocol, is assigned by Gmail and should stay the same forever.  They look to be
sequential but with numbers missing for messages that got deleted.

5. You can stop the process with a Ctrl+C if you need to.  If you stop the process or it errors out,
when you run it again it will pick up where it left off.

6. Attachments are not extracted into separate files, they're just embedded in the eml file as MIME
attachments.

7. This is not intended to be a complete email client, just a simple failsafe in case Gmail ever loses
your data.  However, it does allow you to do things like sort by file size so you can see which emails
to delete if you want to reclaim space in Gmail.

**Would be nice to add**
--------------------
 - Log in to Gmail with OAuth instead of Gmail password?
