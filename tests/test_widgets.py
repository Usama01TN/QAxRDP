# coding=utf-8
"""
Tests of RemoteDesktopWidget (logic that does not need the ActiveX control), ConnectionBar and StatusDot.
"""
from unittest import TestCase, main, skipIf
from os.path import dirname
from sys import path

ROOT = dirname(__file__)  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

try:
    from .qtapp import application, processEvents
except:
    from qtapp import application, processEvents

application()
from QAxRDP import RemoteDesktopWidget, ConnectionBar, StatusDot, RemoteConnector, isActiveXAvailable


class RemoteDesktopWidgetTest(TestCase):
    """
    RemoteDesktopWidget tests.
    """

    def test_options(self):
        """
        :return:
        """
        rdp = RemoteDesktopWidget(
            server=' srv ', port=3390, userName='bob', password='pw', smartSizing=True,
            settings={'redirectClipboard': True,
                      'AdvancedSettings2.MaxReconnectAttempts': 5})  # type: RemoteDesktopWidget
        self.assertEqual(rdp.server, 'srv')
        self.assertEqual(rdp.getPort(), 3390)
        self.assertEqual(rdp.userName, 'bob')
        self.assertEqual(rdp.password, '')
        self.assertTrue(rdp.isSmartSizing())
        self.assertTrue(rdp.advancedSettings5.isRedirectClipboard())
        self.assertEqual(rdp.advancedSettings2.maxReconnectAttempts, 5)
        self.assertIs(rdp.advancedSettings, rdp.getAdvancedSettings())
        self.assertEqual(len(rdp.settingsInterfaces()), 19)

    def test_apply_settings(self):
        """
        :return:
        """
        rdp = RemoteDesktopWidget()  # type: RemoteDesktopWidget
        rejected = rdp.applySettings({'unknown': 1, 'version': 'x', 'securedSettings.workDir': 'C:\\'},
                                     colorDepth=16)
        self.assertEqual(sorted(rejected), ['unknown', 'version'])
        self.assertEqual(rdp.securedSettings.getWorkDir(), 'C:\\')
        self.assertEqual(rdp.colorDepth, 16)

    def test_state(self):
        """
        :return:
        """
        states = []
        rdp = RemoteDesktopWidget(connectionStateChanged=states.append)  # type: RemoteDesktopWidget
        rdp.connecting.emit()
        rdp.connected.emit()
        self.assertTrue(rdp.isConnected() or isActiveXAvailable())
        rdp.disconnected.emit(2)
        if not isActiveXAvailable():
            self.assertEqual(states, [2, 1, 0])
            self.assertEqual(rdp.connectionState, 0)

    @skipIf(isActiveXAvailable(), 'ActiveX available: placeholder not used')
    def test_placeholder(self):
        """
        :return:
        """
        errors = []
        rdp = RemoteDesktopWidget(
            server='srv', controlException=lambda *a: errors.append(a))  # type: RemoteDesktopWidget
        self.assertFalse(rdp.controlAvailable)
        self.assertTrue(rdp.errorString)
        self.assertFalse(rdp.connectToServer())
        self.assertEqual(errors[0][0], -1)
        self.assertEqual(rdp.getErrorDescription(2055), 'Login failed.')
        rdp.resize(320, 200)
        self.assertFalse(rdp.grabScreenshot().isNull())


class ConnectionBarTest(TestCase):
    """
    ConnectionBar and StatusDot tests.
    """

    def test_request(self):
        """
        :return:
        """
        requests = []
        bar = ConnectionBar(address='10.0.0.5:3390', userName='CONTOSO\\bob', password='pw',
                            connectRequested=lambda *a: requests.append(a))  # type: ConnectionBar
        self.assertTrue(bar.requestConnect())
        self.assertEqual(requests, [('10.0.0.5', 3390, 'CONTOSO', 'bob', 'pw')])
        self.assertFalse(bar.isPasswordVisible())

    def test_empty_address(self):
        """
        :return:
        """
        bar = ConnectionBar()  # type: ConnectionBar
        self.assertFalse(bar.requestConnect())
        self.assertEqual(bar.state, ConnectionBar.Error)

    def test_states(self):
        """
        :return:
        """
        bar = ConnectionBar(address='srv')  # type: ConnectionBar
        bar.setState(ConnectionBar.Connecting)
        self.assertFalse(bar.requestConnect())
        self.assertEqual(bar.getStatusDot().state, StatusDot.Connecting)
        bar.setState(ConnectionBar.Connected)
        self.assertEqual(bar.statusText, 'Connected')

    def test_status_dot_timer(self):
        """
        The pulse timer only runs while connecting.
        :return:
        """
        dot = StatusDot()  # type: StatusDot
        dot.show()
        dot.setState(StatusDot.Connecting)
        processEvents(50)
        timers = [t for t in dot.findChildren(object) if type(t).__name__ == 'QTimer']
        self.assertTrue(any(t.isActive() for t in timers))
        dot.setState(StatusDot.Connected)
        self.assertFalse(any(t.isActive() for t in timers))


class RemoteConnectorTest(TestCase):
    """
    Application window test.
    """

    def test_window(self):
        """
        :return:
        """
        w = RemoteConnector()  # type: RemoteConnector
        w.bar.setAddress('srv:3391')
        w.bar.setUserName('D\\u')
        w.bar.requestConnect()
        self.assertEqual((w.rdp.server, w.rdp.port, w.rdp.domain, w.rdp.userName), ('srv', 3391, 'D', 'u'))
        w.deleteLater()


if __name__ == '__main__':
    main()
