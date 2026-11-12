# coding=utf-8
"""
Tests needing the real MsTscAx control (Windows only, skipped elsewhere). No connection is made.
"""
from unittest import TestCase, main, skipUnless
from os.path import dirname
from sys import path

ROOT = dirname(__file__)  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

try:
    from .qtapp import application, deleteNow
except:
    from qtapp import application, deleteNow

application()
from QAxRDP import RemoteDesktopWidget, isActiveXAvailable


@skipUnless(isActiveXAvailable(), 'QAxContainer is not available (Windows only)')
class ActiveXTest(TestCase):
    """
    MsTscAx control tests.
    """

    def setUp(self):
        """
        :return:
        """
        self.rdp = RemoteDesktopWidget()  # type: RemoteDesktopWidget

    def tearDown(self):
        """
        Deletes the widget now (inside the event loop, as an application does), not at interpreter exit.
        :return:
        """
        if self.rdp is not None:
            self.assertTrue(deleteNow(self.rdp))

    def test_delete_with_live_control(self):
        """
        Deleting a widget whose RDP control is alive (e.g. closing a tab) must not crash.
        :return:
        """
        self.assertTrue(self.rdp.controlAvailable)
        self.assertTrue(deleteNow(self.rdp))
        self.rdp = None  # type: None

    def test_delete_after_release(self):
        """
        :return:
        """
        self.rdp.releaseControl()
        self.assertFalse(self.rdp.controlAvailable)
        self.assertTrue(deleteNow(self.rdp))
        self.rdp = None  # type: None

    def test_control(self):
        """
        :return:
        """
        self.assertTrue(self.rdp.controlAvailable, self.rdp.errorString)
        self.assertTrue(self.rdp.activeControlName.startswith('MsTscAx.MsTscAx'))
        self.assertTrue(self.rdp.version)

    def test_events_forwarded(self):
        """
        :return:
        """
        missing = self.rdp.getUnconnectedEvents()
        for event in ('OnConnecting', 'OnConnected', 'OnDisconnected', 'OnLoginComplete', 'OnFatalError'):
            self.assertNotIn(event, missing)

    def test_settings_reach_control(self):
        """
        :return:
        """
        self.assertTrue(self.rdp.advancedSettings.isAvailable())
        self.rdp.setServer('qaxrdp.invalid')
        self.assertEqual(self.rdp.getControlSettings().getServer(), 'qaxrdp.invalid')
        self.rdp.setSmartSizing(True)
        self.assertTrue(self.rdp.isSmartSizing())

    def test_version_switch_keeps_settings(self):
        """
        :return:
        """
        self.rdp.setServer('kept.invalid')
        self.rdp.setControlVersion(self.rdp.getControlVersion() - 1)
        self.assertTrue(self.rdp.controlAvailable)
        self.assertEqual(self.rdp.getServer(), 'kept.invalid')


if __name__ == '__main__':
    main()
