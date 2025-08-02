# -*- coding: utf-8 -*-
#
# src/utils.py
#

from email.mime.text import MIMEText
import email.utils
import smtplib

from . import AppConfig


class Utilities:
    """
    This class must be inherited by other classes or logging will
    cause errors.
    """
    FROM_EMAIL = "noreply@theforgeinitiative.org"
    FROM_NAME = "TFI CheckMeIn"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_email(self, toName, toEmail, subject, message, ccName="",
                   ccEmail=""):
        msg = MIMEText(message)
        msg['To'] = email.utils.formataddr((toName, toEmail))

        if ccEmail:
            msg['Cc'] = email.utils.formataddr((ccName, ccEmail))

        msg['From'] = email.utils.formataddr((self.FROM_NAME, self.FROM_EMAIL))
        msg['Subject'] = subject

        try:  # pragma: no cover
            server = smtplib.SMTP('localhost')
            server.sendmail(self.FROM_EMAIL, [toEmail], msg.as_string())
            server.quit()
        except IOError:
            self._log.warning('Email would have been:\n%s', msg)
