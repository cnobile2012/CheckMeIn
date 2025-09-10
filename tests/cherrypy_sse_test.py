# -*- coding: utf-8 -*-
#
# tests/cherrypi_sse_tests.py
#

import unittest
import threading
import cherrypy
import time

from src.cherrypy_sse import Portier


class TestPortier(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        self.doorman = Portier("updates")

    def tearDown(self):
        self.doorman.unsubscribe()

    #@unittest.skip("Temporarily skipped")
    def test_message(self):
        """
        Test that the message setter and getter properties set and get
        messages.
        """
        msg = "I love spinach."
        self.doorman.message = msg
        self.assertEqual(msg, self.doorman.message)

    #@unittest.skip("Temporarily skipped")
    def test_messages_generator_receives_direct_set(self):
        """
        Test that the messages method works with a directly set message.
        """
        initial_msg = "I love spinach."
        gen = self.doorman.messages()

        # Set a message in another thread so generator can unblock
        def setter():
            time.sleep(0.05)
            self.doorman.message = initial_msg

        threading.Thread(target=setter).start()

        msg = next(gen)
        self.assertEqual(initial_msg, msg)

    def test_messages_generator_receives_bus_publish(self):
        """
        Test that the messages method works with a published message.
        """
        initial_msg = "I love spinach."
        gen = self.doorman.messages()

        # Publish to the CherryPy bus in another thread
        def publisher():
            time.sleep(0.05)
            cherrypy.engine.publish("updates", initial_msg)

        threading.Thread(target=publisher).start()

        msg = next(gen)
        self.assertEqual(initial_msg, msg)
