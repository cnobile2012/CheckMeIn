# -*- coding: utf-8 -*-
#
# tests/test__init__.py
#

import os
import logging
import shutil
import unittest

from src import BASE_DIR
from src.__init__ import Borg, Logger, AppConfig

from .base_test import BaseTests


class TestBorg(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        class A(Borg):
            foo = False

            def __init__(self, value='', *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.value = value

            def do_domething(self):
                self.foo = True
                self.bar = True

            def get_state(self):
                return self.__dict__

        class B(A):
            pass

        self.A = A
        self.B = B

    def tearDown(self):
        self.A().clear_state()

    #@unittest.skip("Temporarily skipped")
    def test_normal_borg_pattern(self):
        """
        Test that the normal Borg patter works. This is Two instances of
        the same class have the same data in them.
        """
        a0 = self.A()
        a1 = self.A()
        b = self.B()
        data = (
            (a0, None, a1, 'foo', False),
            (a0, None, b, 'foo', False),
            (a0, 'do_domething', a1, 'foo', True),
            (a0, None, a1, 'bar', True),
            (a0, None, b, 'foo', True),
            (a0, None, b, 'bar', True),
            )
        msg = "Expected {}, found {}."

        for a0, method, a1, var, expected in data:
            if method:
                getattr(a0, method)()

            result0 = getattr(a0, var)
            result1 = getattr(a1, var)
            self.assertEqual(expected, result0, msg.format(expected, result0))
            self.assertEqual(expected, result1, msg.format(expected, result1))

    #@unittest.skip("Temporarily skipped")
    def test_normal_borg_pattern_with_arg(self):
        """
        """
        a = self.A()
        b = self.B()
        c = self.A('Something')
        data = (
            (a, b, c, 'value', 'Something'),
            )
        msg = "Expected '{}', found '{}'."

        for a, b, c, var, expected in data:
            result0 = getattr(a, var)
            result1 = getattr(b, var)
            result2 = getattr(c, var)
            self.assertEqual(expected, result0, msg.format(expected, result0))
            self.assertEqual(expected, result1, msg.format(expected, result1))
            self.assertEqual(expected, result2, msg.format(expected, result2))


class TestLogger(BaseTests, unittest.TestCase):
    LOG_PATH = os.path.join(BASE_DIR, 'tests', 'logs')
    LOGGER_NAMES = ['test_logger', 'root']

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        self.logger = Logger()

    def tearDown(self):
        self.logger = None

        for log_name in self.LOGGER_NAMES:
            log = logging.getLogger(log_name)
            log.handlers.clear()

        try:
            shutil.rmtree(self.LOG_PATH)
        except Exception:
            pass

    #@unittest.skip("Temporarily skipped")
    def test_config_rotating_logger(self):
        """
        Test that the config method properly configures the rotating file
        logging system.
        """
        name = 'test_logger'
        filepath = os.path.join(self.LOG_PATH, 'testfile_rotate.log')
        log_msg = ("Test" * 20 + " ") * 100
        expected = 3
        msg = "Expected '{}', found '{}'."
        self.logger.config(name, filepath, 500, 2)
        log = logging.getLogger(name)

        for m in log_msg.split(' '):
            log.info(m)

        files = os.listdir(self.LOG_PATH)
        self.assertEqual(expected, len(files), msg.format(
            expected, len(files)))

    #@unittest.skip("Temporarily skipped")
    def test_config_basic_file_logger(self):
        """
        Test that the config method properly configures the basic file
        logging systems.
        """
        filepath = os.path.join(self.LOG_PATH, 'testfile_basic_file.log')
        msg = "Expected '{}', found '{}'."
        self.logger.config(file_path=filepath)
        log = logging.getLogger()
        log_msg = "Testing the basic file logger."
        log.warning(log_msg)
        full_log = self.read_text_file(filepath)
        result = self.find_text(full_log, log_msg, 1, full_log)
        self.assertIn(log_msg, result, msg.format(log_msg, result))

    #@unittest.skip("Temporarily skipped")
    def test_config_basic_stdout_logger(self):
        """
        Test that the config method properly configures the basic stdout
        logging systems.
        """
        msg = "Expected '{}', found '{}'."
        log_msg = "Testing the basic file logger."
        self.logger.config(initial_msg=False)

        with self.assertLogs(level="DEBUG") as cm:
            log = logging.getLogger()
            log.warning(log_msg)

        result = "\n".join(cm.output)
        self.assertIn(log_msg, result)

    #@unittest.skip("Temporarily skipped")
    def test_level_setter_and_getter(self):
        """
        Test that the level setter and getter work properly.
        """
        err_msg = self.logger._ASSERT_MSG
        data = (
            (True, False, None, err_msg),
            (False, True, None, err_msg),
            (None, None, logging.DEBUG, logging.DEBUG),
            (None, None, logging.INFO, logging.INFO),
            )
        msg = "Expected '{}', found '{}'."

        for set_err, get_err, level, expected in data:
            if set_err:
                with self.assertRaises(AssertionError) as cm:
                    self.logger.level = logging.DEBUG

                result = str(cm.exception)
            elif get_err:
                with self.assertRaises(AssertionError) as cm:
                    self.logger.level

                result = str(cm.exception)
            else:
                self.logger.config(initial_msg=False)
                self.logger.level = level
                result = self.logger.level

            self.assertEqual(expected, result, msg.format(expected, result))


class TestAppConfig(BaseTests, unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    #@unittest.skip("Temporarily skipped")
    def test_start_logging(self):
        """
        Test that the start_logging method starts the logger.
        """
        filepath0 = os.path.join(AppConfig._LOGGER_PATH,
                                 AppConfig._LOG_FILENAME)
        filepath1 = os.path.join(AppConfig._LOGGER_PATH,
                                 AppConfig._TEST_LOG_FILENAME)
        filepath2 = os.path.join(AppConfig._LOGGER_PATH,
                                 AppConfig._MIGRATE_LOG_FILENAME)
        msg_err0 = ("The arguments 'testing' and 'migrations' can both be "
                    "False or one or the other can be True.")
        expect0 = "Logger configured as '{}' with file '{}'."
        data = (
            (False, False, filepath0, ('production',
                                       expect0.format('production', filepath0),
                                       AppConfig._LOG_FILENAME)),
            (True, False, filepath1, ('testing',
                                      expect0.format('testing', filepath1),
                                      AppConfig._TEST_LOG_FILENAME)),
            (False, True, filepath2, ('migration',
                                      expect0.format('migration', filepath2),
                                      AppConfig._MIGRATE_LOG_FILENAME)),
           )
        msg = "Expected '{}', found '{}'."

        for testing, migration, path, expected in data:
            log = AppConfig.start_logging(testing, migration)
            self.assertIsInstance(log, logging.Logger, msg.format(
                type(log), logging.Logger))
            env = AppConfig._ENVIRONMENT
            self.assertEqual(expected[0], env, msg.format(expected[0], env))
            full_log = self.read_text_file(path)
            result = self.find_text(full_log, expected[1], 3, expected[1])
            self.assertIn(expected[1], result, msg.format(expected[1], result))
            self.assertIn(expected[2], result, msg.format(expected[2], result))

    #@unittest.skip("Temporarily skipped")
    def test_log(self):
        """
        Test that the log property returns the logger object.
        """
        msg = "Expected '{}', found '{}'."
        app_conf = AppConfig()
        result = app_conf.log
        self.assertIsInstance(result, logging.Logger, msg.format(
            type(result), logging.Logger))

    #@unittest.skip("Temporarily skipped")
    def test_logger_name(self):
        """
        Test that the logger_name property returns the logger name.
        """
        app_conf = AppConfig()
        self.assertEqual(app_conf._LOGGER_NAME, app_conf.logger_name)

    #@unittest.skip("Temporarily skipped")
    def test_full_log_path(self):
        """
        Test that the full_log_path property returns the full path to
        the log file.
        """
        app_conf = AppConfig()
        self.assertEqual(app_conf._fullpath, app_conf.full_log_path)
