# coding=utf-8
"""
Demo window for RemoteDesktopWidget: a server field, Connect / Disconnect actions and an event log.
"""
from ManyQt.QtWidgets import QMainWindow, QLineEdit, QToolBar, QDockWidget, QPlainTextEdit, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from functools import partial
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .remotedesktop import RemoteDesktopWidget, EVENTS
except:
    from remotedesktop import RemoteDesktopWidget, EVENTS


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
        self.setWindowTitle(self.tr(u'RemoteDesktopWidget demo'))
        self.resize(1024, 700)
        # Same options as the QAxRDP 1.x demo.
        self.rdp = RemoteDesktopWidget(smartSizing=True, disconnectedText='Disconnected!',
                                       connected=self.onConnected, disconnected=self.onDisconnected,
                                       controlException=self.onControlException)  # type: RemoteDesktopWidget
        self.setCentralWidget(self.rdp)
        # Toolbar.
        bar = QToolBar(self.tr(u'Connection'), self)  # type: QToolBar
        bar.setMovable(False)
        bar.addWidget(QLabel(self.tr(u' Server: ')))
        self.serverBox = QLineEdit()  # type: QLineEdit
        self.serverBox.setPlaceholderText(self.tr(u'host or IP address'))
        self.serverBox.setMaximumWidth(260)
        self.serverBox.returnPressed.connect(self.onConnect)
        bar.addWidget(self.serverBox)
        bar.addAction(self.tr(u'Connect'), self.onConnect)
        bar.addAction(self.tr(u'Disconnect'), self.rdp.disconnectFromServer)
        self.addToolBar(bar)
        # Event log: every ActiveX event of the widget is printed here.
        self.log = QPlainTextEdit()  # type: QPlainTextEdit
        self.log.setReadOnly(True)
        dock = QDockWidget(self.tr(u'Events'), self)  # type: QDockWidget
        dock.setWidget(self.log)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        self.resizeDocks([dock], [140], Qt.Vertical)
        for _, _, name in EVENTS:
            getattr(self.rdp, name).connect(partial(self.logEvent, name))
        self.log.appendPlainText('Control: {}'.format(self.rdp.getActiveControlName() or self.rdp.getErrorString()))

    def logEvent(self, name, *args):
        """
        :param name: (str | unicode | QString) Signal name.
        :param args: any, signal arguments.
        :return:
        """
        self.log.appendPlainText('{}{}'.format(name, args if args else '()'))

    @pyqtSlot()
    def onConnect(self):
        """
        :return:
        """
        self.rdp.setServer(self.serverBox.text())
        self.rdp.setConnectingText('Connecting to {}...'.format(self.rdp.getServer()))
        self.rdp.connectToServer()

    @pyqtSlot()
    def onConnected(self):
        """
        :return:
        """
        print(self.tr(u'RDP is connected!'))

    @pyqtSlot(int)
    def onDisconnected(self, reason):
        """
        :param reason: int
        :return:
        """
        print(self.tr(u'RDP is disconnected: {}').format(self.rdp.getErrorDescription(reason)))

    @pyqtSlot(int, str, str, str)
    def onControlException(self, code, source, description, helpText):
        """
        :param code: int
        :param source: str | unicode | QString
        :param description: str | unicode | QString
        :param helpText: str | unicode | QString
        :return:
        """
        self.statusBar().showMessage(description, 8000)
