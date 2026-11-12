# coding=utf-8
"""
Tests of the pure helper functions.
"""
from unittest import TestCase, main
from os.path import dirname
from sys import path

ROOT = dirname(__file__)  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

try:
    from .qtapp import application
except:
    from qtapp import application

application()
from QAxRDP import parseAddress, parseUserName, disconnectReasonText, isNormalDisconnect, controlProgId


class ParseAddressTest(TestCase):
    """
    parseAddress tests.
    """

    def test_forms(self):
        """
        :return:
        """
        self.assertEqual(parseAddress('host'), ('host', 3389))
        self.assertEqual(parseAddress(' host:3390 '), ('host', 3390))
        self.assertEqual(parseAddress('[fe80::1]:3391'), ('fe80::1', 3391))
        self.assertEqual(parseAddress('fe80::1'), ('fe80::1', 3389))
        self.assertEqual(parseAddress('host', 4000), ('host', 4000))

    def test_invalid(self):
        """
        :return:
        """
        self.assertEqual(parseAddress(''), ('', 3389))
        self.assertEqual(parseAddress(None), ('', 3389))
        self.assertEqual(parseAddress('host:abc'), ('host', 3389))
        self.assertEqual(parseAddress('host:99999'), ('host', 3389))
        self.assertEqual(parseAddress('host:0'), ('host', 3389))


class ParseUserNameTest(TestCase):
    """
    parseUserName tests.
    """

    def test_forms(self):
        """
        :return:
        """
        self.assertEqual(parseUserName('CONTOSO\\bob'), ('CONTOSO', 'bob'))
        self.assertEqual(parseUserName(' CONTOSO \\ bob '), ('CONTOSO', 'bob'))
        self.assertEqual(parseUserName('bob@contoso.com'), ('', 'bob@contoso.com'))
        self.assertEqual(parseUserName('bob'), ('', 'bob'))
        self.assertEqual(parseUserName(None), ('', ''))


class DisconnectReasonTest(TestCase):
    """
    Disconnect reason helpers tests.
    """

    def test_texts(self):
        """
        :return:
        """
        self.assertEqual(disconnectReasonText(2055), 'Login failed.')
        self.assertIn('0x3039', disconnectReasonText(12345))
        self.assertTrue(isNormalDisconnect(1))
        self.assertTrue(isNormalDisconnect(3))
        self.assertFalse(isNormalDisconnect(264))

    def test_progid(self):
        """
        :return:
        """
        self.assertEqual(controlProgId(11), 'MsTscAx.MsTscAx.11')
        self.assertEqual(controlProgId(0), 'MsTscAx.MsTscAx')


if __name__ == '__main__':
    main()
