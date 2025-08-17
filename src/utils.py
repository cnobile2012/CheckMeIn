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
        self._log = AppConfig().log

    def send_email(self, to_name, to_email, subject, message, cc_name="",
                   cc_email=""):
        msg = MIMEText(message)
        msg['To'] = email.utils.formataddr((to_name, to_email))

        if cc_email:
            msg['Cc'] = email.utils.formataddr((cc_name, cc_email))

        msg['From'] = email.utils.formataddr((self.FROM_NAME, self.FROM_EMAIL))
        msg['Subject'] = subject

        try:
            with smtplib.SMTP('localhost') as smtp:
                smtp.sendmail(self.FROM_EMAIL, [to_email], msg.as_string())
        except IOError:
            self._log.warning('Email would have been:\n%s', msg)
