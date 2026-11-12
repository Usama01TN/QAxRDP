# coding=utf-8
"""
Life cycle of the ActiveX control (creation, version fallback, release, settings replay), tested on every platform
with a fake QAxWidget injected in place of the real one.
"""
from unittest import TestCase, main
from sys import modules

try:
    from .qtapp import application
except ImportError:
    from qtapp import application

application()
from ManyQt.QtWidgets import QWidget
from ManyQt.QtCore import QTimer
from QAxRDP import RemoteDesktopWidget


class FakeAxWidget(QWidget):
    """
    Minimal stand-in for QAxWidget: records the calls made by RemoteDesktopWidget.
    """
    ACCEPTED = None  # type: callable | None  # ProgID filter, None accepts every control.
    INSTANCES = []  # type: list[FakeAxWidget]

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(FakeAxWidget, self).__init__(*args, **kwargs)
        self.control = ''  # type: str
        self.cleared = False  # type: bool
        self.calls = []  # type: list[tuple]
        FakeAxWidget.INSTANCES.append(self)

    def setControl(self, name):
        """
        :param name: str
        :return: bool
        """
        if FakeAxWidget.ACCEPTED is None or FakeAxWidget.ACCEPTED(name):
            self.control = name  # type: str
            return True
        return False

    def isNull(self):
        """
        :return: bool
        """
        return not self.control

    def clear(self):
        """
        :return:
        """
        self.cleared = True  # type: bool
        self.control = ''  # type: str

    def dynamicCall(self, signature, *args):
        """
        :param signature: str
        :param args: any
        :return:
        """
        self.calls.append((signature,) + args)

    def querySubObject(self, name):
        """
        :param name: str
        :return: None
        """
        return None


class LifecycleTest(TestCase):
    """
    RemoteDesktopWidget with the fake control.
    """

    def setUp(self):
        """
        :return:
        """
        self.__m_module = modules[RemoteDesktopWidget.__module__]
        self.__m_original = self.__m_module.QAxWidget
        self.__m_module.QAxWidget = FakeAxWidget
        FakeAxWidget.ACCEPTED = None
        FakeAxWidget.INSTANCES = []

    def tearDown(self):
        """
        :return:
        """
        self.__m_module.QAxWidget = self.__m_original

    def test_create_and_release(self):
        """
        :return:
        """
        rdp = RemoteDesktopWidget(server='srv')  # type: RemoteDesktopWidget
        self.assertTrue(rdp.controlAvailable)
        self.assertEqual(rdp.activeControlName, 'MsTscAx.MsTscAx.11')
        ax = rdp.getAxWidget()
        rdp.releaseControl()
        self.assertFalse(rdp.controlAvailable)
        self.assertTrue(ax.cleared)
        self.assertEqual(rdp.getServer(), 'srv')

    def test_version_fallback(self):
        """
        :return:
        """
        FakeAxWidget.ACCEPTED = lambda name: name.endswith('.9')
        rdp = RemoteDesktopWidget()  # type: RemoteDesktopWidget
        self.assertEqual(rdp.activeControlName, 'MsTscAx.MsTscAx.9')
        FakeAxWidget.ACCEPTED = lambda name: False
        self.assertFalse(rdp.recreateControl())
        self.assertIn('not registered', rdp.errorString)

    def test_settings_replayed(self):
        """
        Settings set before a release are sent to the recreated control.
        :return:
        """
        rdp = RemoteDesktopWidget()  # type: RemoteDesktopWidget
        rdp.setServer('first.invalid')
        rdp.releaseControl()
        rdp.setUserName('bob')
        self.assertTrue(rdp.recreateControl())
        calls = rdp.getAxWidget().calls
        self.assertIn(('SetServer(QString)', 'first.invalid'), calls)
        self.assertIn(('SetUserName(QString)', 'bob'), calls)

    def test_released_when_application_quits(self):
        """
        :return:
        """
        rdp = RemoteDesktopWidget()  # type: RemoteDesktopWidget
        ax = rdp.getAxWidget()
        app = application()
        QTimer.singleShot(0, app.quit)
        (getattr(app, 'exec', None) or app.exec_)()
        self.assertFalse(rdp.controlAvailable)
        self.assertTrue(ax.cleared)


if __name__ == '__main__':
    main()
