# -*- coding: utf-8 -*-
#
# tests/utils_test.py
#

import smtplib
import unittest

from unittest.mock import patch, MagicMock

from src.utils import Utilities


class TestUtilities(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        self._utils = Utilities()

    #@unittest.skip("Temporarily skipped")
    def test_send_email(self):
        """
        Test that the send_email method accumulates the information
        necessary to send an email.
        """
        data = ('TestPerson', 'fake0@email.org', 'Test email',
                'A not too long message.', 'Another CC Name',
                'fake1@email.org')
        expected = ('Content-Type: text/plain; charset="us-ascii"\n'
                    'MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nTo: '
                    'TestPerson <fake0@email.org>\nCc: Another CC Name '
                    '<fake1@email.org>\nFrom: TFI CheckMeIn '
                    '<noreply@theforgeinitiative.org>\nSubject: '
                    'Test email\n\nA not too long message.')

        with patch("smtplib.SMTP", autospec=True) as mock_smtp:
            instance = mock_smtp.return_value.__enter__.return_value
            self._utils.send_email(*data)
            instance.sendmail.assert_called_once_with(
                'noreply@theforgeinitiative.org', [data[1]], expected)
