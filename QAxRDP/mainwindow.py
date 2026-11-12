# coding=utf-8
"""
RemoteConnector: the QAxRDP application window (RemoteDesktopWidget + ConnectionBar + menus + status bar).
"""
from ManyQt.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QApplication, QMenu, \
    QAction
from ManyQt.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QKeySequence
from ManyQt.QtCore import Qt, QSettings, QRectF, pyqtSlot, QRect, QByteArray
from os.path import dirname, expanduser, join, abspath, isfile
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .remotedesktop import RemoteDesktopWidget, isNormalDisconnect
    from .connectionbar import ConnectionBar
    from .version import __version__
except:
    from remotedesktop import RemoteDesktopWidget, isNormalDisconnect
    from connectionbar import ConnectionBar
    from version import __version__

APP_NAME = 'RDP Connector'  # type: str
ORGANIZATION_NAME = 'QAxRDP'  # type: str


LOGO_FILE = join(dirname(abspath(__file__)), 'images', 'logo.png')  # type: str


def createAppIcon(color='#4C8BF5', size=64):
    """
    Returns the QAxRDP logo (images/logo.png), or paints a simple monitor icon when the file is missing.
    :param color: (QColor | Qt.GlobalColor | int | str) Colour of the painted fallback.
    :param size: (int) px, size of the painted fallback.
    :return: QIcon
    """
    if isfile(LOGO_FILE):
        icon = QIcon(LOGO_FILE)  # type: QIcon
        if not icon.isNull():
            return icon
    color = QColor(color)  # type: QColor
    pixmap = QPixmap(size, size)  # type: QPixmap
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)  # type: QPainter
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(color)  # type: QPen
    pen.setWidthF(size / 14.0)
    p.setPen(pen)
    fill = QColor(color)  # type: QColor
    fill.setAlpha(60)
    p.setBrush(fill)
    p.drawRoundedRect(QRectF(size * 0.1, size * 0.14, size * 0.8, size * 0.56), size * 0.06, size * 0.06)
    p.drawLine(int(size * 0.5), int(size * 0.7), int(size * 0.5), int(size * 0.84))
    p.drawLine(int(size * 0.3), int(size * 0.86), int(size * 0.7), int(size * 0.86))
    p.end()
    return QIcon(pixmap)


class RemoteConnector(QMainWindow):
    """
    RemoteConnector class: a minimal Remote Desktop client window.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(RemoteConnector, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr(APP_NAME))
        self.setWindowIcon(createAppIcon())
        self.resize(1080, 700)
        self.__m_settings = QSettings(ORGANIZATION_NAME, APP_NAME)  # type: QSettings
        self.__m_host = ''  # type: str
        # Remote desktop: remote resolution = local screen, scaled to the window (as in QAxRDP 1.x).
        screen = QApplication.primaryScreen()  # type: QScreen | None
        geometry = screen.geometry() if screen is not None else None  # type: QRect | None
        self.rdp = RemoteDesktopWidget(smartSizing=True, disconnectedText=self.tr(u'Disconnected!'),
                                       desktopWidth=geometry.width() if geometry is not None else None,
                                       desktopHeight=geometry.height() if geometry is not None else None,
                                       settings={'enableCredSspSupport': True},
                                       connecting=self.onConnecting, connected=self.onConnected,
                                       loginComplete=self.onLoginComplete, disconnected=self.onDisconnected,
                                       fatalError=self.onFatalError, warning=self.onWarning,
                                       logonError=self.onLogonError,
                                       controlException=self.onControlException)  # type: RemoteDesktopWidget
        # Connection bar, pre-filled with the last address and user.
        self.bar = ConnectionBar(address=self.__m_settings.value('address', '', type=str),
                                 userName=self.__m_settings.value('userName', '', type=str),
                                 connectRequested=self.onConnectRequested,
                                 disconnectRequested=self.onDisconnectRequested)  # type: ConnectionBar
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.rdp, 1)
        layout.addWidget(self.bar)
        self.setCentralWidget(wdg)
        self._createMenus()
        # Status bar.
        self.controlLabel = QLabel()  # type: QLabel
        self.statusBar().addPermanentWidget(self.controlLabel)
        self.rdp.controlChanged.connect(self.onControlChanged)
        self.onControlChanged(self.rdp.getActiveControlName())
        geometry = self.__m_settings.value('geometry')  # type: QByteArray | None
        if geometry is not None:
            self.restoreGeometry(geometry)

    # ---------- Helpers ----------
    def _createMenus(self):
        """
        :return:
        """
        session = self.menuBar().addMenu(self.tr(u'&Session'))  # type: QMenu
        self.connectAction = session.addAction(self.tr(u'&Connect'), self.bar.requestConnect)  # type: QAction
        self.connectAction.setShortcut(QKeySequence('Ctrl+Return'))
        self.disconnectAction = session.addAction(self.tr(u'&Disconnect'), self.bar.requestDisconnect)  # type: QAction
        self.disconnectAction.setShortcut(QKeySequence('Ctrl+D'))
        session.addSeparator()
        screenshot = session.addAction(self.tr(u'Save &screenshot...'), self.onSaveScreenshot)  # type: QAction
        screenshot.setShortcut(QKeySequence('Ctrl+S'))
        session.addSeparator()
        quitAction = session.addAction(self.tr(u'&Quit'), self.close)  # type: QAction
        quitAction.setShortcut(QKeySequence('Ctrl+Q'))
        view = self.menuBar().addMenu(self.tr(u'&View'))  # type: QMenu
        self.smartSizingAction = view.addAction(self.tr(u'S&mart sizing'))  # type: QAction
        self.smartSizingAction.setCheckable(True)
        self.smartSizingAction.setChecked(self.rdp.isSmartSizing())
        self.smartSizingAction.toggled.connect(self.rdp.setSmartSizing)
        fullScreen = view.addAction(self.tr(u'&Full screen'), self.onFullScreen)  # type: QAction
        fullScreen.setShortcut(QKeySequence('F11'))
        barAction = view.addAction(self.tr(u'Connection &bar'))  # type: QAction
        barAction.setCheckable(True)
        barAction.setChecked(True)
        barAction.toggled.connect(self.bar.setVisible)
        helpMenu = self.menuBar().addMenu(self.tr(u'&Help'))  # type: QMenu
        helpMenu.addAction(self.tr(u'&About'), self.onAbout)

    def _setError(self, message):
        """
        :param message: str | unicode | QString
        :return:
        """
        self.bar.setState(ConnectionBar.Error)
        self.bar.setStatusText(message)

    # ---------- Slots: connection bar ----------
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
        self.__m_host = host  # type: str
        self.__m_settings.setValue('address', self.bar.getAddress())
        self.__m_settings.setValue('userName', self.bar.getUserName())
        self.rdp.setDomain(domain)
        self.rdp.setConnectingText(self.tr(u'Connecting to {}...').format(host))
        self.bar.setState(ConnectionBar.Connecting)
        if not self.rdp.connectTo(host, port, user, password):
            self.bar.setState(ConnectionBar.Error)

    @pyqtSlot()
    def onDisconnectRequested(self):
        """
        :return:
        """
        if self.rdp.isControlAvailable():
            self.rdp.disconnectFromServer()
        else:
            self.bar.setState(ConnectionBar.Disconnected)

    # ---------- Slots: remote desktop ----------
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def onControlChanged(self, name):
        """
        :param name: (str | unicode | QString) ProgID of the created control, '' if none.
        :return:
        """
        self.controlLabel.setText(name or self.tr(u'ActiveX unavailable'))
        self.controlLabel.setToolTip(self.rdp.getErrorString() or name)

    @pyqtSlot()
    def onConnecting(self):
        """
        :return:
        """
        self.bar.setState(ConnectionBar.Connecting)

    @pyqtSlot()
    def onConnected(self):
        """
        :return:
        """
        self.bar.setState(ConnectionBar.Connected)
        self.setWindowTitle('{} - {}'.format(self.__m_host, self.tr(APP_NAME)))
        print(self.tr(u'RDP is connected!'))

    @pyqtSlot()
    def onLoginComplete(self):
        """
        :return:
        """
        self.statusBar().showMessage(self.tr(u'Logged on to {}').format(self.__m_host), 5000)

    @pyqtSlot(int)
    def onDisconnected(self, reason):
        """
        :param reason: (int) Disconnect reason.
        :return:
        """
        self.setWindowTitle(self.tr(APP_NAME))
        description = self.rdp.getErrorDescription(reason)  # type: str
        if isNormalDisconnect(reason):
            self.bar.setState(ConnectionBar.Disconnected)
            self.statusBar().showMessage(description, 5000)
        else:
            self._setError(description)

    @pyqtSlot(int)
    def onFatalError(self, errorCode):
        """
        :param errorCode: int
        :return:
        """
        self._setError(self.tr(u'Fatal error {}').format(errorCode))

    @pyqtSlot(int)
    def onWarning(self, warningCode):
        """
        :param warningCode: int
        :return:
        """
        self.statusBar().showMessage(self.tr(u'Warning {}').format(warningCode), 5000)

    @pyqtSlot(int)
    def onLogonError(self, error):
        """
        :param error: (int) Logon error or logon event code.
        :return:
        """
        self.statusBar().showMessage(self.tr(u'Logon event {}').format(error), 5000)

    @pyqtSlot(int, str, str, str)
    def onControlException(self, code, source, description, helpText):
        """
        :param code: int
        :param source: str | unicode | QString
        :param description: str | unicode | QString
        :param helpText: str | unicode | QString
        :return:
        """
        self._setError(description or self.tr(u'Error {} in {}').format(code, source))

    # ---------- Slots: menus ----------
    @pyqtSlot()
    def onSaveScreenshot(self):
        """
        :return:
        """
        fileName, _ = QFileDialog.getSaveFileName(self, self.tr(u'Save screenshot'),
                                                  join(expanduser('~'), 'remote-desktop.png'),
                                                  self.tr(u'Images (*.png *.jpg *.bmp)'))
        if fileName and not self.rdp.saveScreenshot(fileName):
            QMessageBox.warning(self, self.tr(APP_NAME), self.tr(u'Could not save {}').format(fileName))

    @pyqtSlot()
    def onFullScreen(self):
        """
        :return:
        """
        if self.rdp.isConnected():
            self.rdp.setFullScreenMode(True)
        else:
            self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)

    @pyqtSlot()
    def onAbout(self):
        """
        :return:
        """
        import ManyQt
        QMessageBox.about(self, self.tr(u'About {}').format(APP_NAME), self.tr(
            u'<b>{} {}</b><br>Microsoft Remote Desktop client control hosted in Qt.<br><br>'
            u'Qt binding: {} (through ManyQt {})<br>Control: {}').format(
            APP_NAME, __version__, ManyQt.USED_API, ManyQt.__version__,
            self.rdp.getActiveControlName() or self.rdp.getErrorString()))

    # ---------- Qt overrides ----------
    def closeEvent(self, event):
        """
        :param event: QCloseEvent
        :return:
        """
        self.__m_settings.setValue('geometry', self.saveGeometry())
        if self.rdp.isConnected():
            self.rdp.disconnectFromServer()
        super(RemoteConnector, self).closeEvent(event)
