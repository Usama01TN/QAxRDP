# coding=utf-8
"""
Demo window for ConnectionBar: requests are printed and a connection is simulated with timers.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from ManyQt.QtCore import Qt, QTimer, pyqtSlot
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .connectionbar import ConnectionBar
except:
    from connectionbar import ConnectionBar


class MainWindow(QMainWindow):
    """
    MainWindow class.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr(u'ConnectionBar demo'))
        self.resize(980, 220)
        self.bar = ConnectionBar(address='10.0.0.5:3390', userName='CONTOSO\\bob',
                                 connectRequested=self.onConnectRequested,
                                 disconnectRequested=self.onDisconnectRequested)  # type: ConnectionBar
        self.info = QLabel(self.tr(u'Press Connect (the connection is simulated).'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.info, 1)
        layout.addWidget(self.bar)
        self.setCentralWidget(wdg)

    @pyqtSlot(str, int, str, str, str)
    def onConnectRequested(self, host, port, domain, user, password):
        """
        :param host: str | unicode | QString
        :param port: int
        :param domain: str | unicode | QString
        :param user: str | unicode | QString
        :param password: str | unicode | QString
        :return:
        """
        self.info.setText('connectRequested(host={!r}, port={}, domain={!r}, user={!r}, password={})'.format(
            host, port, domain, user, '*' * len(password)))
        self.bar.setState(ConnectionBar.Connecting)
        QTimer.singleShot(1500, lambda: self.bar.setState(ConnectionBar.Connected))

    @pyqtSlot()
    def onDisconnectRequested(self):
        """
        :return:
        """
        self.info.setText('disconnectRequested()')
        self.bar.setState(ConnectionBar.Disconnected)
