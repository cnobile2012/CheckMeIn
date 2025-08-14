# -*- coding: utf-8 -*-
#
# src/cherrypy_SSEE.py
#

import threading
import cherrypy


class Portier(threading.Thread):
    """
    The Doorman (Portier) detects changes of message by listening to the
    subscribed channel, opens 'the door' as a message appears, yield it
    and closes the door once trough.

    channel: the cherrypy bus channel to listen to.
    """
    def __init__(self, channel):
        super().__init__()
        self._channel = channel
        self._e = threading.Event()
        #self.name = f"Portier-{self.name}"
        cherrypy.engine.subscribe(channel, self._msgs)

    @property
    def message(self):
        """
        Contains the last message published to the bus channel.
        """
        return self._message

    @message.setter
    def message(self, msg):
        """
        Sets the latest message and triggers the 'door' to open.
        """
        self._e.set()
        self._message = msg

    def messages(self):
        """
        The Doorman's door, yields the messages as they appear on
        the bus channel.
        """
        while True:
            self._e.wait()
            yield self._message
            self._e.clear()

    def _msgs(self, message):
        """
        Receives the messages from the bus.
        """
        self.message = message

    def unsubscribe(self):
        """
        Unsubscribe from the message stream, signals to remove the thread
        from the heartbet stream
        """
        cherrypy.engine.unsubscribe(self._channel, self._msgs)
