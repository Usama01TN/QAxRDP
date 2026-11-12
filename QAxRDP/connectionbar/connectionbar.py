# -*- coding: utf-8 -*-
"""
ConnectionBar: the "IP & Port / Domain & User / Password / Connect / Disconnect" bar of the QAxRDP connector,
rewritten as a self-contained Qt widget emitting a single connectRequested signal with parsed values.
Also provides:
    - StatusDot: a small painted status indicator that pulses while connecting;
    - parseAddress('host:port' | '[ipv6]:port' | 'host') -> (host, port);
    - parseUserName('DOMAIN\\user' | 'user@domain' | 'user') -> (domain, user).
"""
from ManyQt.QtWidgets import QWidget, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QBrush, QRadialGradient
from enum import IntEnum
from math import sin, pi

DEFAULT_RDP_PORT = 3389  # type: int


def clamp(x, a, b):
    """
    :param x: float | int
    :param a: float | int
    :param b: float | int
    :return: float | int
    """
    return a if x < a else b if x > b else x


def parseAddress(text, defaultPort=DEFAULT_RDP_PORT):
    """
    Splits a server address into host and port.
    Accepted forms: 'host', 'host:port', '10.0.0.5:3390', '[fe80::1]:3390', 'fe80::1' (IPv6 without port).
    :param text: str | unicode
    :param defaultPort: (int) Port used when the address has none, or one outside 1..65535.
    :return: (tuple[str, int]) host, port.
    """
    text = (u'{}'.format(text) if text is not None else u'').strip()  # type: str
    host, port = text, int(defaultPort)  # type: str, int
    if text.startswith('['):
        end = text.find(']')  # type: int
        if end > 0:
            host = text[1:end]  # type: str
            rest = text[end + 1:]  # type: str
            if rest.startswith(':') and rest[1:].strip().isdigit():
                port = int(rest[1:])  # type: int
    elif text.count(':') == 1:
        host, rawPort = text.split(':')
        if rawPort.strip().isdigit():
            port = int(rawPort)  # type: int
    if not 1 <= port <= 65535:
        port = int(defaultPort)  # type: int
    return host.strip(), port


def parseUserName(text):
    """
    Splits a logon name into domain and user. A UPN (user@domain) is kept whole as the user name.
    :param text: (str | unicode | QString) 'DOMAIN\\user', 'user@domain' or 'user'.
    :return: (tuple[str, str]) domain, user.
    """
    text = (u'{}'.format(text) if text is not None else u'').strip()  # type: str
    if '\\' in text:
        domain, user = text.split('\\', 1)
        return domain.strip(), user.strip()
    return u'', text


class StatusDot(QWidget):
    """
    Round status indicator: grey (disconnected), pulsing amber (connecting), green (connected), red (error).
    """

    class State(IntEnum):
        """
        State enumeration class.
        """
        Disconnected = 0  # type: int
        Connecting = 1  # type: int
        Connected = 2  # type: int
        Error = 3  # type: int

    Disconnected = State.Disconnected  # type: int
    Connecting = State.Connecting  # type: int
    Connected = State.Connected  # type: int
    Error = State.Error  # type: int

    def __init__(self, *args, **kwargs):
        """
        :param state: (int) StatusDot.State.
        :param diameter: (int) Dot diameter in px.
        :param pulsePeriod: (int) ms of one pulse while connecting.
        :param disconnectedColor: QColor | Qt.GlobalColor | int | str
        :param connectingColor: QColor | Qt.GlobalColor | int | str
        :param connectedColor: QColor | Qt.GlobalColor | int | str
        :param errorColor: QColor | Qt.GlobalColor | int | str
        :param args: any
        :param kwargs: any
        """
        state = kwargs.pop('state', StatusDot.Disconnected)  # type: int
        diameter = kwargs.pop('diameter', 12)  # type: int
        pulsePeriod = kwargs.pop('pulsePeriod', 1200)  # type: int
        disconnectedColor = kwargs.pop('disconnectedColor', '#9E9E9E')  # type: QColor
        connectingColor = kwargs.pop('connectingColor', '#FFB300')  # type: QColor
        connectedColor = kwargs.pop('connectedColor', '#43A047')  # type: QColor
        errorColor = kwargs.pop('errorColor', '#E53935')  # type: QColor
        super(StatusDot, self).__init__(*args, **kwargs)
        # Options.
        self.__m_state = StatusDot.State(int(state))  # type: int
        self.__m_diameter = max(4, int(diameter))  # type: int
        self.__m_pulsePeriod = max(100, int(pulsePeriod))  # type: int
        self.__m_colors = [QColor(disconnectedColor), QColor(connectingColor), QColor(connectedColor),
                           QColor(errorColor)]  # type: list[QColor]
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # Animation.
        self.__m_phase = 0.0  # type: float
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self._updateAnimation()

    # ---------- Helpers ----------
    def _updateAnimation(self):
        """
        Runs the pulse only while connecting.
        :return:
        """
        if self.__m_state == StatusDot.Connecting:
            if not self.__m_timer.isActive():
                self.__m_clock.start()
                self.__m_timer.start(16)
        else:
            self.__m_timer.stop()
            self.__m_phase = 0.0  # type: float
        self.update()

    def _setColor(self, index, color):
        """
        :param index: int
        :param color: QColor | Qt.GlobalColor | int | str
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_colors[index] != color:
            self.__m_colors[index] = color
            self.update()

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        self.__m_phase = (self.__m_clock.elapsed() % self.__m_pulsePeriod) / float(self.__m_pulsePeriod)  # type: float
        self.update()

    # ---------- Public API ----------
    def getState(self):
        """
        :return: int
        """
        return int(self.__m_state)

    @pyqtSlot(State)
    @pyqtSlot(int)
    def setState(self, state):
        """
        :param state: (StatusDot.State | int).
        :return:
        """
        state = StatusDot.State(int(clamp(int(state), 0, 3)))  # type: int
        if state != self.__m_state:
            self.__m_state = state  # type: int
            self._updateAnimation()

    def getDiameter(self):
        """
        :return: int
        """
        return self.__m_diameter

    @pyqtSlot(int)
    def setDiameter(self, diameter):
        """
        :param diameter: int
        :return:
        """
        self.__m_diameter = max(4, int(diameter))  # type: int
        self.updateGeometry()
        self.update()

    def getPulsePeriod(self):
        """
        :return: int
        """
        return self.__m_pulsePeriod

    @pyqtSlot(int)
    def setPulsePeriod(self, pulsePeriod):
        """
        :param pulsePeriod: (int) ms.
        :return:
        """
        self.__m_pulsePeriod = max(100, int(pulsePeriod))  # type: int

    def getDisconnectedColor(self):
        """
        :return: QColor
        """
        return self.__m_colors[0]

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDisconnectedColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        self._setColor(0, color)

    def getConnectingColor(self):
        """
        :return: QColor
        """
        return self.__m_colors[1]

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setConnectingColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        self._setColor(1, color)

    def getConnectedColor(self):
        """
        :return: QColor
        """
        return self.__m_colors[2]

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setConnectedColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        self._setColor(2, color)

    def getErrorColor(self):
        """
        :return: QColor
        """
        return self.__m_colors[3]

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setErrorColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        self._setColor(3, color)

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(self.__m_diameter + 8, self.__m_diameter + 8)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return self.sizeHint()

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(StatusDot, self).hideEvent(event)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(StatusDot, self).showEvent(event)
        self._updateAnimation()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        p = QPainter(self)  # type: QPainter
        p.setRenderHint(QPainter.Antialiasing, True)
        color = QColor(self.__m_colors[int(self.__m_state)])  # type: QColor
        d = float(min(self.__m_diameter, self.width(), self.height()))  # type: float
        cx = self.width() / 2.0  # type: float
        cy = self.height() / 2.0  # type: float
        if self.__m_state == StatusDot.Connecting:
            # Expanding halo.
            halo = QColor(color)  # type: QColor
            halo.setAlphaF(0.45 * (1.0 - self.__m_phase))
            r = d / 2.0 + 4.0 * self.__m_phase  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(halo)
            p.drawEllipse(QRectF(cx - r, cy - r, 2.0 * r, 2.0 * r))
            color.setAlphaF(0.75 + 0.25 * sin(self.__m_phase * 2.0 * pi))
        gradient = QRadialGradient(cx - d * 0.15, cy - d * 0.15, d * 0.6)  # type: QRadialGradient
        gradient.setColorAt(0.0, color.lighter(140))
        gradient.setColorAt(1.0, color)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(gradient))
        p.drawEllipse(QRectF(cx - d / 2.0, cy - d / 2.0, d, d))
        p.end()

    # ---------- Properties ----------
    state = pyqtProperty(int, fget=getState, fset=setState)  # type: pyqtProperty
    diameter = pyqtProperty(int, fget=getDiameter, fset=setDiameter)  # type: pyqtProperty
    pulsePeriod = pyqtProperty(int, fget=getPulsePeriod, fset=setPulsePeriod)  # type: pyqtProperty
    disconnectedColor = pyqtProperty(QColor, fget=getDisconnectedColor, fset=setDisconnectedColor)  # type: pyqtProperty
    connectingColor = pyqtProperty(QColor, fget=getConnectingColor, fset=setConnectingColor)  # type: pyqtProperty
    connectedColor = pyqtProperty(QColor, fget=getConnectedColor, fset=setConnectedColor)  # type: pyqtProperty
    errorColor = pyqtProperty(QColor, fget=getErrorColor, fset=setErrorColor)  # type: pyqtProperty


class ConnectionBar(QFrame):
    """
    Connection bar: address, logon name and password fields, Connect / Disconnect buttons and a status indicator.
    """
    Disconnected = StatusDot.Disconnected  # type: int
    Connecting = StatusDot.Connecting  # type: int
    Connected = StatusDot.Connected  # type: int
    Error = StatusDot.Error  # type: int
    STATE_TEXTS = ('Disconnected', 'Connecting...', 'Connected', 'Error')  # type: tuple[str]
    connectRequested = pyqtSignal(str, int, str, str, str)  # type: pyqtSignal  # host, port, domain, user, password
    disconnectRequested = pyqtSignal()  # type: pyqtSignal
    stateChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param address: (str | unicode | QString) 'host[:port]'.
        :param userName: (str | unicode | QString) '[DOMAIN\\]user'.
        :param password: str | unicode
        :param defaultPort: (int) Port used when the address has none.
        :param state: (int) ConnectionBar.Disconnected, Connecting, Connected or Error.
        :param passwordVisible: (bool) Show the password in clear text.
        :param connectRequested: callable | None
        :param disconnectRequested: callable | None
        :param stateChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        address = kwargs.pop('address', '')  # type: str
        userName = kwargs.pop('userName', '')  # type: str
        password = kwargs.pop('password', '')  # type: str
        defaultPort = kwargs.pop('defaultPort', DEFAULT_RDP_PORT)  # type: int
        state = kwargs.pop('state', ConnectionBar.Disconnected)  # type: int
        passwordVisible = kwargs.pop('passwordVisible', False)  # type: bool
        connectRequested = kwargs.pop('connectRequested', None)  # type: callable | None
        disconnectRequested = kwargs.pop('disconnectRequested', None)  # type: callable | None
        stateChanged = kwargs.pop('stateChanged', None)  # type: callable | None
        super(ConnectionBar, self).__init__(*args, **kwargs)
        # Options.
        self.__m_defaultPort = int(clamp(int(defaultPort), 1, 65535))  # type: int
        self.__m_state = ConnectionBar.Disconnected  # type: int
        self.__m_statusText = ''  # type: str
        if callable(connectRequested):
            self.connectRequested.connect(connectRequested)
        if callable(disconnectRequested):
            self.disconnectRequested.connect(disconnectRequested)
        if callable(stateChanged):
            self.stateChanged.connect(stateChanged)
        # Widgets.
        self.__m_addressBox = QLineEdit(address)  # type: QLineEdit
        self.__m_addressBox.setObjectName('addressBox')
        self.__m_addressBox.setPlaceholderText(self.tr(u'host[:port]'))
        self.__m_userBox = QLineEdit(userName)  # type: QLineEdit
        self.__m_userBox.setObjectName('userBox')
        self.__m_userBox.setPlaceholderText(self.tr(u'[DOMAIN\\]user'))
        self.__m_passwordBox = QLineEdit(password)  # type: QLineEdit
        self.__m_passwordBox.setObjectName('passwordBox')
        self.__m_connectButton = QPushButton(self.tr(u'Connect'))  # type: QPushButton
        self.__m_connectButton.setObjectName('connectButton')
        self.__m_connectButton.setDefault(True)
        self.__m_disconnectButton = QPushButton(self.tr(u'Disconnect'))  # type: QPushButton
        self.__m_disconnectButton.setObjectName('disconnectButton')
        self.__m_dot = StatusDot()  # type: StatusDot
        self.__m_statusLabel = QLabel()  # type: QLabel
        self.__m_statusLabel.setObjectName('statusLabel')
        metrics = self.__m_statusLabel.fontMetrics()  # type: QFontMetrics
        width = metrics.horizontalAdvance if hasattr(metrics, 'horizontalAdvance') else metrics.width
        self.__m_statusLabel.setMinimumWidth(max(width(self.tr(t)) for t in ConnectionBar.STATE_TEXTS) + 4)
        self.__m_statusLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.__m_addressBox.setMinimumWidth(140)
        self.__m_userBox.setMinimumWidth(110)
        self.__m_passwordBox.setMinimumWidth(90)
        layout = QHBoxLayout(self)  # type: QHBoxLayout
        layout.setContentsMargins(8, 6, 8, 6)
        for label, field, stretch in ((self.tr(u'IP && Port:'), self.__m_addressBox, 3),
                                      (self.tr(u'Domain && User:'), self.__m_userBox, 2),
                                      (self.tr(u'Password:'), self.__m_passwordBox, 2)):
            text = QLabel(label)  # type: QLabel
            text.setBuddy(field)
            layout.addWidget(text)
            layout.addWidget(field, stretch)
            field.returnPressed.connect(self.requestConnect)
        layout.addWidget(self.__m_connectButton)
        layout.addWidget(self.__m_disconnectButton)
        layout.addSpacing(6)
        layout.addWidget(self.__m_dot)
        layout.addWidget(self.__m_statusLabel, 2)
        self.__m_connectButton.clicked.connect(self.requestConnect)
        self.__m_disconnectButton.clicked.connect(self.requestDisconnect)
        self.setPasswordVisible(passwordVisible)
        self.__m_state = -1  # type: int  # Forces the first refresh.
        self.setState(state)

    # ---------- Helpers ----------
    def _refresh(self):
        """
        Enables the controls that make sense in the current state.
        :return:
        """
        idle = self.__m_state in (ConnectionBar.Disconnected, ConnectionBar.Error)  # type: bool
        for field in (self.__m_addressBox, self.__m_userBox, self.__m_passwordBox):
            field.setEnabled(idle)
        self.__m_connectButton.setEnabled(idle)
        self.__m_disconnectButton.setEnabled(not idle)
        self.__m_dot.setState(self.__m_state)

    def _elideStatus(self):
        """
        Elides the status text to the width of its label (the full text stays in the tooltip).
        :return:
        """
        label = self.__m_statusLabel  # type: QLabel
        width = max(label.minimumWidth(), label.width())  # type: int
        label.setText(label.fontMetrics().elidedText(self.__m_statusText, Qt.ElideRight, width))

    # ---------- Qt overrides ----------
    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(ConnectionBar, self).resizeEvent(event)
        self._elideStatus()

    # ---------- Public API ----------
    @pyqtSlot()
    def requestConnect(self):
        """
        Validates the fields and emits connectRequested(host, port, domain, user, password).
        :return: (bool) False if the address is empty or a connection is in progress.
        """
        if self.__m_state not in (ConnectionBar.Disconnected, ConnectionBar.Error):
            return False
        host, port = parseAddress(self.__m_addressBox.text(), self.__m_defaultPort)
        if not host:
            self.setState(ConnectionBar.Error)
            self.setStatusText(self.tr(u'Enter a server address'))
            self.__m_addressBox.setFocus()
            return False
        domain, user = parseUserName(self.__m_userBox.text())
        self.connectRequested.emit(host, port, domain, user, self.__m_passwordBox.text())
        return True

    @pyqtSlot()
    def requestDisconnect(self):
        """
        Emits disconnectRequested.
        :return:
        """
        self.disconnectRequested.emit()

    def getAddress(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_addressBox.text()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setAddress(self, address):
        """
        :param address: (str | unicode | QString) 'host[:port]'.
        :return:
        """
        self.__m_addressBox.setText(address)

    def getUserName(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_userBox.text()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setUserName(self, userName):
        """
        :param userName: (str | unicode | QString) '[DOMAIN\\]user'.
        :return:
        """
        self.__m_userBox.setText(userName)

    def getPassword(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_passwordBox.text()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPassword(self, password):
        """
        :param password: str | unicode
        :return:
        """
        self.__m_passwordBox.setText(password)

    def isPasswordVisible(self):
        """
        :return: bool
        """
        return self.__m_passwordBox.echoMode() == QLineEdit.Normal

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setPasswordVisible(self, passwordVisible):
        """
        :param passwordVisible: bool
        :return:
        """
        self.__m_passwordBox.setEchoMode(QLineEdit.Normal if passwordVisible else QLineEdit.Password)

    def getDefaultPort(self):
        """
        :return: int
        """
        return self.__m_defaultPort

    @pyqtSlot(int)
    def setDefaultPort(self, defaultPort):
        """
        :param defaultPort: (int) 1 to 65535.
        :return:
        """
        self.__m_defaultPort = int(clamp(int(defaultPort), 1, 65535))  # type: int

    def getState(self):
        """
        :return: int
        """
        return self.__m_state

    @pyqtSlot(int)
    def setState(self, state):
        """
        Updates buttons, fields and indicator; resets the status text to the state's default text.
        :param state: (int) ConnectionBar.Disconnected, Connecting, Connected or Error.
        :return:
        """
        state = int(clamp(int(state), 0, 3))  # type: int
        if state != self.__m_state:
            self.__m_state = state  # type: int
            self._refresh()
            self.setStatusText(self.tr(ConnectionBar.STATE_TEXTS[state]))
            self.stateChanged.emit(state)

    def getStatusText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_statusText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setStatusText(self, statusText):
        """
        :param statusText: str | unicode
        :return:
        """
        self.__m_statusText = statusText  # type: str
        self.__m_statusLabel.setToolTip(statusText)
        self._elideStatus()

    def getStatusDot(self):
        """
        :return: StatusDot
        """
        return self.__m_dot

    # ---------- Properties ----------
    address = pyqtProperty('QString', fget=getAddress, fset=setAddress)  # type: pyqtProperty
    userName = pyqtProperty('QString', fget=getUserName, fset=setUserName)  # type: pyqtProperty
    password = pyqtProperty('QString', fget=getPassword, fset=setPassword, designable=False)  # type: pyqtProperty
    passwordVisible = pyqtProperty(bool, fget=isPasswordVisible, fset=setPasswordVisible)  # type: pyqtProperty
    defaultPort = pyqtProperty(int, fget=getDefaultPort, fset=setDefaultPort)  # type: pyqtProperty
    state = pyqtProperty(int, fget=getState, fset=setState, notify=stateChanged)  # type: pyqtProperty
    statusText = pyqtProperty('QString', fget=getStatusText, fset=setStatusText)  # type: pyqtProperty
