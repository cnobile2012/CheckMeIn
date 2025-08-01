# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
import email.utils
import smtplib

from . import AppConfig

FROM_EMAIL = "noreply@theforgeinitiative.org"
FROM_NAME = "TFI CheckMeIn"


def sendEmail(toName, toEmail, subject, message, ccName="", ccEmail=""):
    msg = MIMEText(message)
    msg['To'] = email.utils.formataddr((toName, toEmail))

    if ccEmail:
        msg['Cc'] = email.utils.formataddr((ccName, ccEmail))

    msg['From'] = email.utils.formataddr((FROM_NAME, FROM_EMAIL))
    msg['Subject'] = subject

    try:  # pragma: no cover
        server = smtplib.SMTP('localhost')
        server.sendmail(FROM_EMAIL, [toEmail], msg.as_string())
        server.quit()
    except IOError:
        log = AppConfig().log
        log.warning('Email would have been:\n%s', msg)
