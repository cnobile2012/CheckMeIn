# -*- coding: utf-8 -*-
#
# src/__init__.py
#
__docformat__ = "restructuredtext en"

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

__all__ = ('BASE_DIR', 'Borg', 'AppConfig')

PWD = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PWD)


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


class Logger:
    """
    Setup some basic logging. This uses the borg pattern, it's kind of like a
    singleton but has a side affect of assimilation.
    """
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(module)s "
                       "%(funcName)s [line:%(lineno)d] %(message)s")

    def __init__(self, format_str=None):
        self._format = format_str if format_str else self._DEFAULT_FORMAT
        self.logger = None

    def config(self, logger_name=None, file_path=None, max_bytes=50000000,
               backup_count=5, level=logging.INFO, initial_msg=True):
        """
        Config the logger.

        :param logger_name: The name of the specific logger needed.
        :type logger_name: str
        :param file_path: The path to the logging file. If left as None
                          logging will be to the screen.
        :type file_path: str
        :param level: The lowest level to generate logs for. See the
                      Python logger docs.
        :type level: int
        :param initial_msg: Print the initial log message. The default is True.
        :type initial_msg: bool
        """
        if logger_name and file_path:  # Creates a custom file logger.
            self._make_log_dir(file_path)
            self.logger = logging.getLogger(logger_name)

            if not self.logger.handlers:
                self.logger.setLevel(level)
                handler = RotatingFileHandler(file_path, maxBytes=max_bytes,
                                              backupCount=backup_count)
                formatter = logging.Formatter(self._format)
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        elif file_path:  # Creates a file root logger.
            self.logger = logging.getLogger()

            if not self.logger.handlers:
                self._make_log_dir(file_path)
                logging.basicConfig(filename=file_path, format=self._format,
                                    level=level, force=True)
        else:  # Creates a stdout root logger.
            self.logger = logging.getLogger()

            if not self.logger.handlers:
                logging.basicConfig(stream=sys.stdout, format=self._format,
                                    level=level, force=True)

        if logger_name:
            log = logging.getLogger(logger_name)
        else:
            log = logging.getLogger()

        if initial_msg:
            log.info("Logging start for %s.", logger_name)

    def _make_log_dir(self, full_path):
        path, filename = os.path.split(full_path)

        if not os.path.exists(path):
            os.mkdir(path)

    @property
    def level(self):
        assert self.logger, "The 'config()' method must be called first."
        return self.logger.getEffectiveLevel()

    @level.setter
    def level(self, level):
        assert self.logger, "The 'config()' method must be called first."
        self.logger.setLevel(level)


class AppConfig(Borg):
    _LOGGER_PATH = os.path.join(BASE_DIR, 'logs', )
    _LOG_FILENAME = 'checkmein.log'
    _LOGGER_NAME = 'checkmein'
    _TEST_LOG_FILENAME = 'testing.log'
    _TEST_LOGGER_NAME = 'testing'
    _MIGRATE_LOG_FILENAME = 'migration.log'
    _MIGRATE_LOGGER_NAME = 'migrate'
    _ENVIRONMENT = 'production'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        root_logger = logging.getLogger()

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        if self._ENVIRONMENT == 'testing':
            self._fullpath = os.path.join(self._LOGGER_PATH,
                                          self._TEST_LOG_FILENAME)
            self._logger = self._TEST_LOGGER_NAME
            self._level = logging.DEBUG
            logging.getLogger("cherrypy.error").setLevel(logging.WARNING)
            logging.getLogger("cherrypy.access").setLevel(logging.WARNING)
        elif self._ENVIRONMENT == 'migration':
            self._fullpath = os.path.join(self._LOGGER_PATH,
                                          self._MIGRATE_LOG_FILENAME)
            self._logger = self._MIGRATE_LOGGER_NAME
            self._level = logging.DEBUG
        else:
            self._fullpath = os.path.join(self._LOGGER_PATH,
                                          self._LOG_FILENAME)
            self._logger = self._LOGGER_NAME
            self._level = logging.INFO

        Logger().config(logger_name=self.logger_name,
                        file_path=self.full_log_path, level=self._level,
                        initial_msg=False)
        # Disable asyncio debug messages for all loggers.
        logging.getLogger("asyncio").setLevel(logging.ERROR)

    @classmethod
    def start_logging(cls, testing=False, migration=False):
        """
        Create the logger for the required environment.

        :param bool testing: A true value indicates testing mode else false
                             (default) for production mode.
        :param bool migration: A true value overrides the `testing` argument
                               creating logging files for migration else false
                               (default) and the `testing` argument value id
                               used.
        :returns: The logger object.
        :rtype: logging.Logger
        """
        if testing:
            cls._ENVIRONMENT = 'testing'
            filename = cls._TEST_LOG_FILENAME
        elif migration:
            cls._ENVIRONMENT = 'migration'
            filename = cls._MIGRATE_LOG_FILENAME
        else:
            filename = cls._LOG_FILENAME

        log = logging.getLogger(AppConfig().logger_name)
        log.info("Logger configured as '%s' with file '%s'.",
                 cls._ENVIRONMENT, os.path.join(cls._LOGGER_PATH, filename))
        return log

    @property
    def log(self):
        return logging.getLogger(self.logger_name)

    @property
    def logger_name(self):
        return self._logger

    @property
    def full_log_path(self):
        return self._fullpath
