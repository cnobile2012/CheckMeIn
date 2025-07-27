# -*- coding: utf-8 -*-

import logging
from email.mime.text import MIMEText
import email.utils
import smtplib

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
        from . import AppConfig
        log = logging.getLogger(AppConfig().logger_name)
        log.warning('Email would have been:\n%s', msg)


class Borg:
    """
    We store the instances instead of the __dict__. This alows the updating
    of future instances with the data from the previous instances. Without
    this, new instances would not have all the data.
    """
    _instances = []

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        cls._instances.append(instance)

        if cls._instances:
            for key, value in cls._instances[0].__dict__.items():
                # Avoid copying test framework internals
                if not key.startswith('_') and not key.startswith('__'):
                    instance.__dict__[key] = value

        return instance

    def __setattr__(self, name, value):
        # Let built-in Python attributes work as normal
        object.__setattr__(self, name, value)

        if not name.startswith('__') and not name.endswith('__'):
            # Propagate to others (excluding private/dunder)
            for inst in self._instances:
                if inst is not self:
                    inst.__dict__[name] = value

    def clear_state(self):
        for inst in self._instances:
            keys_to_clear = [k for k in inst.__dict__
                             if (not k.startswith('_') and
                                 not k.startswith('__'))]

            for key in keys_to_clear:
                del inst.__dict__[key]

        self._instances.clear()
