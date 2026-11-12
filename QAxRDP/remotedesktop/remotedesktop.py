# -*- coding: utf-8 -*-
"""
RemoteDesktopWidget: a Qt widget embedding the Microsoft Remote Desktop (RDP) client ActiveX control (MsTscAx).
Ported from QAxRemoteDesktop (QAxRDP 1.x) to plain Qt logic on top of ManyQt:
    - every ActiveX event is re-emitted as a typed pyqtSignal (connected, disconnected(int), logonError(int)...),
      and every signal can also be given as a callable kwarg;
    - every option is a kwarg, a getter, a @pyqtSlot setter and a pyqtProperty (server, userName, port...);
    - the ActiveX sub-objects (AdvancedSettings, SecuredSettings, TransportSettings...) are QObjects exposed as
      read-only properties (advancedSettings, securedSettings, transportSettings...);
    - settings are cached, so they can be set before connecting, survive a control version switch, and the
      widget stays usable (painted placeholder) on platforms without ActiveX support.
The control itself only exists on Windows with a Qt binding that ships the QAxContainer module.
"""
from ManyQt.QtCore import Qt, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty, QObject
from ManyQt.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QFontMetrics
from ManyQt.QtWidgets import QWidget, QVBoxLayout, QApplication
from os.path import dirname
from enum import IntEnum
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .rdpsettings import clamp, toText, RdpSettingsInterface, RdpControlSettings, RdpAdvancedSettings, \
        RdpAdvancedSettings2, RdpAdvancedSettings3, RdpAdvancedSettings4, RdpAdvancedSettings5, \
        RdpAdvancedSettings6, RdpAdvancedSettings7, RdpAdvancedSettings8, RdpSecuredSettings, RdpSecuredSettings2, \
        RdpClientShell, RdpRemoteProgram, RdpRemoteProgram2, RdpRemoteProgram3, RdpTransportSettings, \
        RdpTransportSettings2, RdpTransportSettings3, RdpTransportSettings4
except:
    from rdpsettings import clamp, toText, RdpSettingsInterface, RdpControlSettings, RdpAdvancedSettings, \
        RdpAdvancedSettings2, RdpAdvancedSettings3, RdpAdvancedSettings4, RdpAdvancedSettings5, \
        RdpAdvancedSettings6, RdpAdvancedSettings7, RdpAdvancedSettings8, RdpSecuredSettings, RdpSecuredSettings2, \
        RdpClientShell, RdpRemoteProgram, RdpRemoteProgram2, RdpRemoteProgram3, RdpTransportSettings, \
        RdpTransportSettings2, RdpTransportSettings3, RdpTransportSettings4

try:
    from ManyQt.QAxContainer import QAxWidget
except:  # Not Windows, or the selected binding has no QAxContainer module.
    QAxWidget = None

CONTROL_PROGID = 'MsTscAx.MsTscAx'  # type: str
DEFAULT_CONTROL_VERSION = 11  # type: int
DEFAULT_RDP_PORT = 3389  # type: int
#: Disconnect reasons of IMsTscAxEvents::OnDisconnected (used when the control cannot describe them itself).
DISCONNECT_REASONS = {
    0: 'No information is available.',
    1: 'Local disconnection.',
    2: 'Remote disconnection by user.',
    3: 'Remote disconnection by server.',
    260: 'DNS name lookup failure.',
    262: 'Out of memory.',
    264: 'Connection timed out.',
    516: 'WinSock socket connect failure.',
    518: 'Out of memory.',
    520: 'Host not found error.',
    772: 'WinSock send call failure.',
    774: 'Out of memory.',
    776: 'Invalid IP address specified.',
    1028: 'WinSock recv call failure.',
    1030: 'Invalid security data.',
    1032: 'Internal error.',
    1286: 'Invalid encryption method specified.',
    1288: 'DNS lookup failed.',
    1540: 'GetHostByName call failed.',
    1542: 'Invalid server security data.',
    1544: 'Internal timer error.',
    1796: 'Time-out occurred.',
    1798: 'Failed to unpack server certificate.',
    2052: 'Bad IP address specified.',
    2055: 'Login failed.',
    2056: 'License negotiation failed.',
    2308: 'Socket closed.',
    2310: 'Internal security error.',
    2312: 'Licensing time-out.',
    2566: 'Internal security error.',
    2822: 'Encryption error.',
    3078: 'Decryption error.',
    3080: 'Decompression error.',
}  # type: dict[int, str]

#: Disconnect reasons that are not errors (the user or the server closed the session).
NORMAL_DISCONNECT_REASONS = (1, 2, 3)  # type: tuple[int]

#: ActiveX event name, overload types used to pick the PyQt signal, name of the re-emitting pyqtSignal.
EVENTS = (
    ('OnAuthenticationWarningDismissed', None, 'authenticationWarningDismissed'),
    ('OnAuthenticationWarningDisplayed', None, 'authenticationWarningDisplayed'),
    ('OnAutoReconnected', None, 'autoReconnected'),
    ('OnAutoReconnecting', (int, int), 'autoReconnecting'),
    ('OnAutoReconnecting2', (int, bool, int, int), 'autoReconnecting2'),
    ('OnChannelReceivedData', (str, str), 'channelReceivedData'),
    ('OnConfirmClose', None, 'confirmClose'),
    ('OnConnected', None, 'connected'),
    ('OnConnecting', None, 'connecting'),
    ('OnConnectionBarPullDown', None, 'connectionBarPullDown'),
    ('OnDevicesButtonPressed', None, 'devicesButtonPressed'),
    ('OnDisconnected', (int,), 'disconnected'),
    ('OnEnterFullScreenMode', None, 'enterFullScreenMode'),
    ('OnFatalError', (int,), 'fatalError'),
    ('OnFocusReleased', (int,), 'focusReleased'),
    ('OnIdleTimeoutNotification', None, 'idleTimeoutNotification'),
    ('OnLeaveFullScreenMode', None, 'leaveFullScreenMode'),
    ('OnLoginComplete', None, 'loginComplete'),
    ('OnLogonError', (int,), 'logonError'),
    ('OnMouseInputModeChanged', (bool,), 'mouseInputModeChanged'),
    ('OnNetworkStatusChanged', None, 'networkStatusChanged'),
    ('OnReceivedTSPublicKey', (str,), 'receivedTSPublicKey'),
    ('OnRemoteDesktopSizeChange', (int, int), 'remoteDesktopSizeChange'),
    ('OnRemoteProgramDisplayed', None, 'remoteProgramDisplayed'),
    ('OnRemoteProgramResult', None, 'remoteProgramResult'),
    ('OnRemoteWindowDisplayed', None, 'remoteWindowDisplayed'),
    ('OnRequestContainerMinimize', None, 'requestContainerMinimize'),
    ('OnRequestGoFullScreen', None, 'requestGoFullScreen'),
    ('OnRequestLeaveFullScreen', None, 'requestLeaveFullScreen'),
    ('OnServiceMessageReceived', (str,), 'serviceMessageReceived'),
    ('OnUserNameAcquired', (str,), 'userNameAcquired'),
    ('OnWarning', (int,), 'warning'),
    ('exception', (int, str, str, str), 'controlException'),
    ('propertyChanged', (str,), 'controlPropertyChanged'),
)  # type: tuple[tuple[str, tuple | None, str]]

#: Attribute name and class of every settings interface owned by the widget.
SETTINGS_INTERFACES = (
    ('controlSettings', RdpControlSettings),
    ('advancedSettings', RdpAdvancedSettings),
    ('advancedSettings2', RdpAdvancedSettings2),
    ('advancedSettings3', RdpAdvancedSettings3),
    ('advancedSettings4', RdpAdvancedSettings4),
    ('advancedSettings5', RdpAdvancedSettings5),
    ('advancedSettings6', RdpAdvancedSettings6),
    ('advancedSettings7', RdpAdvancedSettings7),
    ('advancedSettings8', RdpAdvancedSettings8),
    ('securedSettings', RdpSecuredSettings),
    ('securedSettings2', RdpSecuredSettings2),
    ('clientShell', RdpClientShell),
    ('remoteProgram', RdpRemoteProgram),
    ('remoteProgram2', RdpRemoteProgram2),
    ('remoteProgram3', RdpRemoteProgram3),
    ('transportSettings', RdpTransportSettings),
    ('transportSettings2', RdpTransportSettings2),
    ('transportSettings3', RdpTransportSettings3),
    ('transportSettings4', RdpTransportSettings4),
)  # type: tuple[tuple[str, type]]


def isActiveXAvailable():
    """
    :return: (bool) True when the selected Qt binding provides QAxWidget (Windows only).
    """
    return QAxWidget is not None


def controlProgId(version):
    """
    :param version: (int) Control version, <= 0 for the version independent ProgID.
    :return: (str | unicode | QString) e.g. 'MsTscAx.MsTscAx.11'.
    """
    version = int(version)  # type: int
    return CONTROL_PROGID if version <= 0 else '{}.{}'.format(CONTROL_PROGID, version)


def disconnectReasonText(reason):
    """
    :param reason: (int) Disconnect reason of the disconnected signal.
    :return: str | unicode | QString
    """
    reason = int(reason)  # type: int
    return DISCONNECT_REASONS.get(reason, 'Disconnected (reason {0} / 0x{0:X}).'.format(reason))


def isNormalDisconnect(reason):
    """
    :param reason: (int) Disconnect reason of the disconnected signal.
    :return: (bool) True if the session was closed on purpose (not an error).
    """
    return int(reason) in NORMAL_DISCONNECT_REASONS


class RemoteDesktopWidget(QWidget):
    """
    Widget hosting the Microsoft RDP client ActiveX control, with a Qt API (signals, slots and properties).
    """
    #: Default of the autoCreateControl option (the Qt Designer plugin sets it to False in the Designer process).
    DEFAULT_AUTO_CREATE_CONTROL = True  # type: bool

    class ConnectionState(IntEnum):
        """
        ConnectionState enumeration class (values of the control's Connected property).
        """
        Disconnected = 0  # type: int
        Connected = 1  # type: int
        Connecting = 2  # type: int

    Disconnected = ConnectionState.Disconnected  # type: int
    Connected = ConnectionState.Connected  # type: int
    Connecting = ConnectionState.Connecting  # type: int

    class ExtendedDisconnectReason(IntEnum):
        """
        ExtendedDisconnectReason enumeration class (values of the extendedDisconnectReason property).
        """
        NoInfo = 0  # type: int
        APIInitiatedDisconnect = 1  # type: int
        APIInitiatedLogoff = 2  # type: int
        ServerIdleTimeout = 3  # type: int
        ServerLogonTimeout = 4  # type: int
        ReplacedByOtherConnection = 5  # type: int
        OutOfMemory = 6  # type: int
        ServerDeniedConnection = 7  # type: int
        ServerDeniedConnectionFips = 8  # type: int
        ServerInsufficientPrivileges = 9  # type: int
        ServerFreshCredsRequired = 10  # type: int
        RpcInitiatedDisconnectByUser = 11  # type: int
        LogoffByUser = 12  # type: int
        LicenseInternal = 256  # type: int
        LicenseNoLicenseServer = 257  # type: int
        LicenseNoLicense = 258  # type: int
        LicenseErrClientMsg = 259  # type: int
        LicenseHwidDoesntMatchLicense = 260  # type: int
        LicenseErrClientLicense = 261  # type: int
        LicenseCantFinishProtocol = 262  # type: int
        LicenseClientEndedProtocol = 263  # type: int
        LicenseErrClientEncryption = 264  # type: int
        LicenseCantUpgradeLicense = 265  # type: int
        LicenseNoRemoteConnections = 266  # type: int
        LicenseCreatingLicStoreAccDenied = 267  # type: int
        RdpEncInvalidCredentials = 768  # type: int
        ProtocolRangeStart = 4096  # type: int
        ProtocolRangeEnd = 32767  # type: int

    class RemoteSessionAction(IntEnum):
        """
        RemoteSessionAction enumeration class (argument of sendRemoteAction).
        """
        Charms = 0  # type: int
        Appbar = 1  # type: int
        Snap = 2  # type: int
        StartScreen = 3  # type: int
        AppSwitch = 4  # type: int
        ActionCenter = 5  # type: int

    # ---------- ActiveX events ----------
    authenticationWarningDismissed = pyqtSignal()  # type: pyqtSignal
    authenticationWarningDisplayed = pyqtSignal()  # type: pyqtSignal
    autoReconnected = pyqtSignal()  # type: pyqtSignal
    autoReconnecting = pyqtSignal(int, int)  # type: pyqtSignal  # disconnectReason, attemptCount
    autoReconnecting2 = pyqtSignal(int, bool, int, int)  # type: pyqtSignal  # reason, network, attempt, max
    channelReceivedData = pyqtSignal(str, str)  # type: pyqtSignal  # channelName, data
    confirmClose = pyqtSignal()  # type: pyqtSignal
    connected = pyqtSignal()  # type: pyqtSignal
    connecting = pyqtSignal()  # type: pyqtSignal
    connectionBarPullDown = pyqtSignal()  # type: pyqtSignal
    devicesButtonPressed = pyqtSignal()  # type: pyqtSignal
    disconnected = pyqtSignal(int)  # type: pyqtSignal  # disconnectReason
    enterFullScreenMode = pyqtSignal()  # type: pyqtSignal
    fatalError = pyqtSignal(int)  # type: pyqtSignal  # errorCode
    focusReleased = pyqtSignal(int)  # type: pyqtSignal  # direction
    idleTimeoutNotification = pyqtSignal()  # type: pyqtSignal
    leaveFullScreenMode = pyqtSignal()  # type: pyqtSignal
    loginComplete = pyqtSignal()  # type: pyqtSignal
    logonError = pyqtSignal(int)  # type: pyqtSignal  # error
    mouseInputModeChanged = pyqtSignal(bool)  # type: pyqtSignal  # relative
    networkStatusChanged = pyqtSignal(int, int, int)  # type: pyqtSignal  # qualityLevel, bandwidth, rtt
    receivedTSPublicKey = pyqtSignal('QString')  # type: pyqtSignal  # publicKey
    remoteDesktopSizeChange = pyqtSignal(int, int)  # type: pyqtSignal  # width, height
    remoteProgramDisplayed = pyqtSignal(bool, int)  # type: pyqtSignal  # displayed, displayInformation
    remoteProgramResult = pyqtSignal(str, int, bool)  # type: pyqtSignal  # program, error, isExecutable
    remoteWindowDisplayed = pyqtSignal(bool, object, int)  # type: pyqtSignal  # displayed, hwnd, attribute
    requestContainerMinimize = pyqtSignal()  # type: pyqtSignal
    requestGoFullScreen = pyqtSignal()  # type: pyqtSignal
    requestLeaveFullScreen = pyqtSignal()  # type: pyqtSignal
    serviceMessageReceived = pyqtSignal('QString')  # type: pyqtSignal  # message
    userNameAcquired = pyqtSignal('QString')  # type: pyqtSignal  # userName
    warning = pyqtSignal(int)  # type: pyqtSignal  # warningCode
    controlException = pyqtSignal(int, str, str, str)  # type: pyqtSignal  # code, source, description, help
    controlPropertyChanged = pyqtSignal('QString')  # type: pyqtSignal  # name
    # ---------- Widget signals ----------
    controlChanged = pyqtSignal('QString')  # type: pyqtSignal  # ProgID of the created control ('' if none)
    connectionStateChanged = pyqtSignal(int)  # type: pyqtSignal  # ConnectionState

    def __init__(self, *args, **kwargs):
        """
        :param server: (str | unicode | None) Server name or IP address.
        :param port: (int | None) RDP port (3389 by default).
        :param domain: str | unicode | None
        :param userName: str | unicode | None
        :param password: (str | unicode | None) Clear text password (write-only).
        :param colorDepth: (int | None) 8, 15, 16, 24 or 32 bits per pixel.
        :param desktopWidth: (int | None) Width of the remote desktop in px.
        :param desktopHeight: (int | None) Height of the remote desktop in px.
        :param smartSizing: (bool | None) Scale the remote desktop to the widget size.
        :param fullScreenMode: (bool | None) Full-screen state of the control.
        :param connectingText: str | unicode | None
        :param connectedStatusText: str | unicode | None
        :param disconnectedText: str | unicode | None
        :param fullScreenTitle: str | unicode | None
        :param settings: (dict | None) Any other setting, see applySettings(), e.g. {'redirectClipboard': True}.
        :param controlVersion: (int) Version of the MsTscAx control to create (11 by default).
        :param allowVersionFallback: (bool) Try older control versions when the requested one is not registered.
        :param autoCreateControl: (bool) Create the ActiveX control immediately (False: only paint a placeholder
            until setAutoCreateControl(True) or recreateControl(), as in Qt Designer).
        :param backgroundColor: (QColor | Qt.GlobalColor | int | str) Placeholder background.
        :param textColor: (QColor | Qt.GlobalColor | int | str) Placeholder text.
        :param accentColor: (QColor | Qt.GlobalColor | int | str) Placeholder drawing.
        :param connected: callable | None (and every other signal name: disconnected, logonError...)
        :param args: any
        :param kwargs: any
        """
        server = kwargs.pop('server', None)  # type: str | None
        port = kwargs.pop('port', None)  # type: int | None
        domain = kwargs.pop('domain', None)  # type: str | None
        userName = kwargs.pop('userName', None)  # type: str | None
        password = kwargs.pop('password', None)  # type: str | None
        colorDepth = kwargs.pop('colorDepth', None)  # type: int | None
        desktopWidth = kwargs.pop('desktopWidth', None)  # type: int | None
        desktopHeight = kwargs.pop('desktopHeight', None)  # type: int | None
        smartSizing = kwargs.pop('smartSizing', None)  # type: bool | None
        fullScreenMode = kwargs.pop('fullScreenMode', None)  # type: bool | None
        connectingText = kwargs.pop('connectingText', None)  # type: str | None
        connectedStatusText = kwargs.pop('connectedStatusText', None)  # type: str | None
        disconnectedText = kwargs.pop('disconnectedText', None)  # type: str | None
        fullScreenTitle = kwargs.pop('fullScreenTitle', None)  # type: str | None
        settings = kwargs.pop('settings', None)  # type: dict | None
        controlVersion = kwargs.pop('controlVersion', DEFAULT_CONTROL_VERSION)  # type: int
        allowVersionFallback = kwargs.pop('allowVersionFallback', True)  # type: bool
        autoCreateControl = kwargs.pop('autoCreateControl',
                                       RemoteDesktopWidget.DEFAULT_AUTO_CREATE_CONTROL)  # type: bool
        backgroundColor = kwargs.pop('backgroundColor', '#1E1F26')  # type: QColor
        textColor = kwargs.pop('textColor', '#C9D1E0')  # type: QColor
        accentColor = kwargs.pop('accentColor', '#4C8BF5')  # type: QColor
        callbacks = {}  # type: dict[str, callable]
        for name in [e[2] for e in EVENTS] + ['controlChanged', 'connectionStateChanged']:
            callback = kwargs.pop(name, None)  # type: callable | None
            if callable(callback):
                callbacks[name] = callback
        super(RemoteDesktopWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_controlVersion = int(controlVersion)  # type: int
        self.__m_allowVersionFallback = bool(allowVersionFallback)  # type: bool
        self.__m_autoCreateControl = bool(autoCreateControl)  # type: bool
        self.__m_backgroundColor = QColor(backgroundColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        # State.
        self.__m_ax = None  # type: QAxWidget | None
        self.__m_activeControlName = ''  # type: str
        self.__m_errorString = ''  # type: str
        self.__m_unconnectedEvents = []  # type: list[str]
        self.__m_state = RemoteDesktopWidget.Disconnected  # type: int
        # Settings interfaces (QObjects, children of the widget).
        self.__m_settings = []  # type: list[tuple[str, RdpSettingsInterface]]
        for attr, cls in SETTINGS_INTERFACES:
            self.__m_settings.append((attr, cls(self)))
        # Layout hosting the ActiveX control.
        self.__m_layout = QVBoxLayout(self)  # type: QVBoxLayout
        self.__m_layout.setContentsMargins(0, 0, 0, 0)
        self.__m_layout.setSpacing(0)
        # Signals.
        self.connecting.connect(self._onConnecting)
        self.connected.connect(self._onConnected)
        self.disconnected.connect(self._onDisconnected)
        for name, callback in callbacks.items():
            getattr(self, name).connect(callback)
        # Control.
        if self.__m_autoCreateControl:
            self._createControl()
        # Options given to the constructor (None = keep the control default).
        options = (('server', server), ('port', port), ('domain', domain), ('userName', userName),
                   ('password', password), ('colorDepth', colorDepth), ('desktopWidth', desktopWidth),
                   ('desktopHeight', desktopHeight), ('smartSizing', smartSizing), ('fullScreenMode', fullScreenMode),
                   ('connectingText', connectingText), ('connectedStatusText', connectedStatusText),
                   ('disconnectedText', disconnectedText),
                   ('fullScreenTitle', fullScreenTitle))  # type: tuple[tuple[str, object]]
        for name, value in options:
            if value is not None:
                self.setProperty(name, value)
        if settings:
            self.applySettings(settings)

    # ---------- Helpers ----------
    def _settings(self, attr):
        """
        :param attr: (str | unicode | QString) Attribute name, e.g. 'advancedSettings'.
        :return: RdpSettingsInterface
        """
        for name, obj in self.__m_settings:
            if name == attr:
                return obj
        raise KeyError(attr)

    def _candidateControlNames(self):
        """
        :return: (list[str | unicode | QString] | QStringList) ProgIDs to try, the requested version first.
        """
        names = [controlProgId(self.__m_controlVersion)]  # type: list[str]
        if self.__m_allowVersionFallback:
            names += [controlProgId(v) for v in range(self.__m_controlVersion - 1, 1, -1)]
            names.append(controlProgId(0))
        return names

    def _createControl(self):
        """
        (Re)creates the ActiveX control and attaches the settings interfaces to it.
        :return: (bool) True on success.
        """
        self._destroyControl()
        if QAxWidget is None:
            self.__m_errorString = self.tr(u'The Remote Desktop ActiveX control is only available on Windows with a '
                                           'Qt binding providing QAxContainer.')  # type: str
            self.controlChanged.emit('')
            self.update()
            return False
        ax = None  # type: QAxWidget | None
        for name in self._candidateControlNames():
            ax = QAxWidget(self)  # type: QAxWidget
            try:
                ok = bool(ax.setControl(name)) and not ax.isNull()  # type: bool
            except:
                ok = False  # type: bool
            if ok:
                self.__m_activeControlName = name  # type: str
                break
            ax.deleteLater()
            ax = None  # type: None
        if ax is None:
            self.__m_errorString = self.tr(
                u'The Remote Desktop ActiveX control ({}) is not registered on this system.').format(controlProgId(
                self.__m_controlVersion))  # type: str
            self.controlChanged.emit('')
            self.update()
            return False
        self.__m_ax = ax  # type: QAxWidget
        self.__m_errorString = ''  # type: str
        self.__m_layout.addWidget(ax)
        self.__m_unconnectedEvents = self._connectControlEvents(ax)  # type: list[str]
        for _, obj in self.__m_settings:
            obj.attachHost(ax)
        self.controlChanged.emit(self.__m_activeControlName)
        self.update()
        return True

    def _destroyControl(self):
        """
        Disconnects and releases the current ActiveX control.
        :return:
        """
        ax = self.__m_ax  # type: QAxWidget | None
        if ax is None:
            return
        try:
            if self.isConnected():
                ax.dynamicCall('Disconnect()')
        except:
            pass
        for _, obj in self.__m_settings:
            obj.detachHost()
        self.__m_layout.removeWidget(ax)
        try:
            ax.clear()
        except:
            pass
        ax.deleteLater()
        self.__m_ax = None  # type: None
        self.__m_activeControlName = ''  # type: str
        self._setState(RemoteDesktopWidget.Disconnected)

    def _connectControlEvents(self, ax):
        """
        Forwards the dynamic signals of the ActiveX control to the typed signals of the widget.
        :param ax: QAxWidget
        :return: (list[str | unicode | QString] | QStringList) Events that the binding could not connect.
        """
        failed = []  # type: list[str]
        for axName, types, signalName in EVENTS:
            if not self._connectAxSignal(ax, axName, types, getattr(self, signalName).emit):
                failed.append(axName)
        return failed

    @staticmethod
    def _connectAxSignal(ax, name, types, slot):
        """
        :param ax: QAxWidget
        :param name: (str | unicode | QString) ActiveX event name.
        :param types: (tuple | None) Overload to select.
        :param slot: callable
        :return: bool
        """
        try:
            signal = getattr(ax, name)  # type: pyqtBoundSignal
        except:
            return False
        candidates = []  # type: list
        if types:
            try:
                candidates.append(signal[types[0]] if len(types) == 1 else signal[types])
            except:
                pass
        candidates.append(signal)
        for candidate in candidates:
            try:
                candidate.connect(slot)
                return True
            except:
                continue
        return False

    def _call(self, signature, *args):
        """
        :param signature: (str | unicode | QString) e.g. 'Connect()'.
        :param args: any
        :return: any, None without control.
        """
        if self.__m_ax is None:
            return None
        try:
            return self.__m_ax.dynamicCall(signature, *args)
        except:
            return None

    def _setState(self, state):
        """
        :param state: int
        :return:
        """
        if state != self.__m_state:
            self.__m_state = RemoteDesktopWidget.ConnectionState(state)  # type: int
            self.connectionStateChanged.emit(int(state))
            self.update()

    def _reportError(self, message):
        """
        Emits controlException for errors detected by the widget itself.
        :param message: str | unicode | QString
        :return: bool, always False.
        """
        self.controlException.emit(-1, 'QAxRDP', message, '')
        return False

    @pyqtSlot()
    def _onConnecting(self):
        """
        :return:
        """
        self._setState(RemoteDesktopWidget.Connecting)

    @pyqtSlot()
    def _onConnected(self):
        """
        :return:
        """
        self._setState(RemoteDesktopWidget.Connected)

    @pyqtSlot(int)
    def _onDisconnected(self, reason):
        """
        :param reason: int
        :return:
        """
        self._setState(RemoteDesktopWidget.Disconnected)

    # ---------- Public API: control ----------
    def getAxWidget(self):
        """
        :return: (QAxWidget | None) The hosted ActiveX control, for direct QAxBase access.
        """
        return self.__m_ax

    def isControlAvailable(self):
        """
        :return: (bool) True when the ActiveX control has been created.
        """
        return self.__m_ax is not None

    def getActiveControlName(self):
        """
        :return: (str | unicode | QString) ProgID of the created control, '' if none.
        """
        return self.__m_activeControlName

    def getErrorString(self):
        """
        :return: (str | unicode | QString) Why the control could not be created, '' when it was.
        """
        return self.__m_errorString

    def getUnconnectedEvents(self):
        """
        :return: (list[str | unicode | QString] | QStringList) ActiveX events the Qt binding could not forward.
        """
        return list(self.__m_unconnectedEvents)

    @pyqtSlot()
    def recreateControl(self):
        """
        Recreates the ActiveX control and sends it every cached setting.
        :return: bool
        """
        return self._createControl()

    def getControlVersion(self):
        """
        :return: int
        """
        return self.__m_controlVersion

    @pyqtSlot(int)
    def setControlVersion(self, controlVersion):
        """
        Switches to another version of the MsTscAx control (the control is recreated).
        :param controlVersion: (int) <= 0 for the version independent ProgID.
        :return:
        """
        controlVersion = int(controlVersion)  # type: int
        if controlVersion != self.__m_controlVersion:
            self.__m_controlVersion = controlVersion  # type: int
            if self.__m_autoCreateControl or self.__m_ax is not None:
                self._createControl()

    def isAllowVersionFallback(self):
        """
        :return: bool
        """
        return self.__m_allowVersionFallback

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAllowVersionFallback(self, allowVersionFallback):
        """
        :param allowVersionFallback: bool
        :return:
        """
        self.__m_allowVersionFallback = bool(allowVersionFallback)  # type: bool

    def isAutoCreateControl(self):
        """
        :return: bool
        """
        return self.__m_autoCreateControl

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAutoCreateControl(self, autoCreateControl):
        """
        True creates the ActiveX control now if it does not exist yet; False only disables the automatic creation
        (an existing control is kept).
        :param autoCreateControl: bool
        :return:
        """
        self.__m_autoCreateControl = bool(autoCreateControl)  # type: bool
        if self.__m_autoCreateControl and self.__m_ax is None:
            self._createControl()

    # ---------- Public API: settings interfaces ----------
    def settingsInterfaces(self):
        """
        :return: (list[RdpSettingsInterface]) Every settings interface, control settings first.
        """
        return [obj for _, obj in self.__m_settings]

    def getControlSettings(self):
        """
        :return: RdpControlSettings
        """
        return self._settings('controlSettings')

    def getAdvancedSettings(self):
        """
        :return: RdpAdvancedSettings
        """
        return self._settings('advancedSettings')

    def getAdvancedSettings2(self):
        """
        :return: RdpAdvancedSettings2
        """
        return self._settings('advancedSettings2')

    def getAdvancedSettings3(self):
        """
        :return: RdpAdvancedSettings3
        """
        return self._settings('advancedSettings3')

    def getAdvancedSettings4(self):
        """
        :return: RdpAdvancedSettings4
        """
        return self._settings('advancedSettings4')

    def getAdvancedSettings5(self):
        """
        :return: RdpAdvancedSettings5
        """
        return self._settings('advancedSettings5')

    def getAdvancedSettings6(self):
        """
        :return: RdpAdvancedSettings6
        """
        return self._settings('advancedSettings6')

    def getAdvancedSettings7(self):
        """
        :return: RdpAdvancedSettings7
        """
        return self._settings('advancedSettings7')

    def getAdvancedSettings8(self):
        """
        :return: RdpAdvancedSettings8
        """
        return self._settings('advancedSettings8')

    def getSecuredSettings(self):
        """
        :return: RdpSecuredSettings
        """
        return self._settings('securedSettings')

    def getSecuredSettings2(self):
        """
        :return: RdpSecuredSettings2
        """
        return self._settings('securedSettings2')

    def getClientShell(self):
        """
        :return: RdpClientShell
        """
        return self._settings('clientShell')

    def getRemoteProgram(self):
        """
        :return: RdpRemoteProgram
        """
        return self._settings('remoteProgram')

    def getRemoteProgram2(self):
        """
        :return: RdpRemoteProgram2
        """
        return self._settings('remoteProgram2')

    def getRemoteProgram3(self):
        """
        :return: RdpRemoteProgram3
        """
        return self._settings('remoteProgram3')

    def getTransportSettings(self):
        """
        :return: RdpTransportSettings
        """
        return self._settings('transportSettings')

    def getTransportSettings2(self):
        """
        :return: RdpTransportSettings2
        """
        return self._settings('transportSettings2')

    def getTransportSettings3(self):
        """
        :return: RdpTransportSettings3
        """
        return self._settings('transportSettings3')

    def getTransportSettings4(self):
        """
        :return: RdpTransportSettings4
        """
        return self._settings('transportSettings4')

    def findSetting(self, key):
        """
        Resolves a setting name to the object declaring it.
        Accepted keys: 'server', 'smartSizing', 'SmartSizing' (ActiveX name), 'advancedSettings.smartSizing',
        'AdvancedSettings.SmartSizing'. Lookup is case-insensitive.
        :param key: str | unicode | QString
        :return: (tuple[QObject, str] | tuple[None, None]) Object and python property name.
        """
        key = toText(key).strip()  # type: str
        if '.' in key:
            prefix, name = key.split('.', 1)
            prefix = prefix.lower()  # type: str
            for attr, obj in self.__m_settings:
                if prefix in (attr.lower(), obj.getInterfaceName().lower(), type(obj).__name__.lower()):
                    found = obj.findProperty(name)  # type: str | None
                    return (obj, found) if found else (None, None)
            return None, None
        lowered = key.lower()  # type: str
        mo = self.metaObject()
        for i in range(QWidget.staticMetaObject.propertyCount(), mo.propertyCount()):
            prop = mo.property(i)
            if prop.isWritable() and toText(prop.name()).lower() == lowered:
                return self, toText(prop.name())
        for _, obj in self.__m_settings:
            found = obj.findProperty(key)  # type: str | None
            if found:
                return obj, found
        return None, None

    def applySettings(self, settings=None, **kwargs):
        """
        Applies many settings at once (the QAxRDP 1.x parseArguments() replacement), e.g.
        applySettings({'server': 'host', 'advancedSettings.redirectClipboard': True}, smartSizing=True).
        :param settings: (dict | None) Setting name -> value (see findSetting() for the accepted names).
        :param kwargs: any, same as settings.
        :return: (list[str | unicode | QString] | QStringList) Keys that are unknown or read-only.
        """
        items = dict(settings or {})  # type: dict
        items.update(kwargs)
        rejected = []  # type: list[str]
        for key, value in items.items():
            obj, name = self.findSetting(key)
            if obj is None or not obj.setProperty(name, value):
                rejected.append(key)
        return rejected

    # ---------- Public API: connection ----------
    def getServer(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getServer()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setServer(self, server):
        """
        :param server: (str | unicode | QString) Name or IP address of the server.
        :return:
        """
        self.getControlSettings().setServer(toText(server).strip())

    def getPort(self):
        """
        :return: int
        """
        return self.getAdvancedSettings().getRdpPort()

    @pyqtSlot(int)
    def setPort(self, port):
        """
        :param port: (int) 1 to 65535.
        :return:
        """
        self.getAdvancedSettings().setRdpPort(port)

    def getDomain(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getDomain()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDomain(self, domain):
        """
        :param domain: str | unicode
        :return:
        """
        self.getControlSettings().setDomain(domain)

    def getUserName(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getUserName()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setUserName(self, userName):
        """
        :param userName: str | unicode
        :return:
        """
        self.getControlSettings().setUserName(userName)

    def getPassword(self):
        """
        The password is write-only: this getter always returns an empty string.
        :return: str | unicode | QString
        """
        return ''

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPassword(self, password):
        """
        :param password: (str | unicode | QString) Clear text password (AdvancedSettings.ClearTextPassword).
        :return:
        """
        self.getAdvancedSettings().setClearTextPassword(password)

    def getConnectionState(self):
        """
        :return: (int) RemoteDesktopWidget.ConnectionState.
        """
        if self.__m_ax is not None:
            try:
                return int(self.getControlSettings().getConnected())
            except:
                pass
        return int(self.__m_state)

    def isConnected(self):
        """
        :return: bool
        """
        return self.getConnectionState() == RemoteDesktopWidget.Connected

    def getExtendedDisconnectReason(self):
        """
        :return: (int) RemoteDesktopWidget.ExtendedDisconnectReason.
        """
        return self.getControlSettings().getExtendedDisconnectReason()

    @pyqtSlot()
    def connectToServer(self):
        """
        Initiates a connection using the current settings.
        :return: (bool) False if the connection could not be started.
        """
        if self.__m_ax is None:
            return self._reportError(self.__m_errorString or self.tr(u'No Remote Desktop control.'))
        if not self.getServer():
            return self._reportError(self.tr(u'No server specified.'))
        self._call('Connect()')
        return True

    def connectTo(self, server, port=DEFAULT_RDP_PORT, userName=None, password=None, domain=None):
        """
        Sets the connection settings and connects.
        :param server: str | unicode
        :param port: int
        :param userName: str | unicode | None
        :param password: str | unicode | None
        :param domain: str | unicode | None
        :return: bool
        """
        self.setServer(server)
        self.setPort(port)
        if userName is not None:
            self.setUserName(userName)
        if password is not None:
            self.setPassword(password)
        if domain is not None:
            self.setDomain(domain)
        return self.connectToServer()

    @pyqtSlot()
    def disconnectFromServer(self):
        """
        Disconnects the active connection.
        :return:
        """
        self._call('Disconnect()')

    def reconnect(self, width, height):
        """
        Reconnects the session with a new desktop size (IMsRdpClient8::Reconnect).
        :param width: int
        :param height: int
        :return: (int | None) 0 = started, 1 = blocked.
        """
        return self._call('Reconnect(uint, uint)', int(width), int(height))

    @pyqtSlot()
    def requestClose(self):
        """
        Asks the control whether the session can be closed (an answer may come with confirmClose).
        :return: (int | None) 0 = can proceed, 1 = wait for events.
        """
        return self._call('RequestClose()')

    def getErrorDescription(self, disconnectReason, extendedDisconnectReason=None):
        """
        :param disconnectReason: (int) Reason of the disconnected signal.
        :param extendedDisconnectReason: (int | None) None to read the current extendedDisconnectReason.
        :return: str | unicode | QString
        """
        if extendedDisconnectReason is None:
            extendedDisconnectReason = self.getExtendedDisconnectReason()  # type: int
        text = self._call(
            'GetErrorDescription(uint, uint)', int(disconnectReason), int(extendedDisconnectReason)
        )  # type: str | None
        return toText(text) if text else disconnectReasonText(disconnectReason)

    def getStatusText(self, statusCode):
        """
        :param statusCode: int
        :return: str | unicode | QString
        """
        return toText(self._call('GetStatusText(uint)', int(statusCode)))

    @pyqtSlot(RemoteSessionAction)
    @pyqtSlot(int)
    def sendRemoteAction(self, action):
        """
        :param action: RemoteDesktopWidget.RemoteSessionAction | int.
        :return:
        """
        self._call('SendRemoteAction(int)', int(action))

    @pyqtSlot()
    def syncSessionDisplaySettings(self):
        """
        Synchronizes the session display settings with the control size.
        :return:
        """
        self._call('SyncSessionDisplaySettings()')

    def updateSessionDisplaySettings(self, desktopWidth, desktopHeight, physicalWidth=0, physicalHeight=0,
                                     orientation=0, desktopScaleFactor=100, deviceScaleFactor=100):
        """
        Updates the remote session display settings (dynamic resolution).
        :param desktopWidth: int
        :param desktopHeight: int
        :param physicalWidth: (int) mm.
        :param physicalHeight: (int) mm.
        :param orientation: (int) 0, 90, 180 or 270.
        :param desktopScaleFactor: (int) percent.
        :param deviceScaleFactor: (int) percent.
        :return:
        """
        self._call('UpdateSessionDisplaySettings(uint, uint, uint, uint, uint, uint, uint)', int(desktopWidth),
                   int(desktopHeight), int(physicalWidth), int(physicalHeight), int(orientation),
                   int(desktopScaleFactor), int(deviceScaleFactor))

    # ---------- Public API: virtual channels ----------
    def createVirtualChannels(self, names):
        """
        Creates client-side virtual channels (must be called before connecting).
        :param names: (str | list[str | unicode | QString] | QStringList) Comma separated names or a list of names (8 characters max each).
        :return:
        """
        if not isinstance(names, (list, tuple)):
            names = toText(names).split(',')  # type: list[str]
        self._call('CreateVirtualChannels(QString)', ','.join(toText(n).strip() for n in names if toText(n).strip()))

    def sendOnVirtualChannel(self, channelName, data):
        """
        :param channelName: str | unicode
        :param data: str | unicode
        :return:
        """
        self._call('SendOnVirtualChannel(QString, QString)', toText(channelName), toText(data))

    def virtualChannelOptions(self, channelName):
        """
        :param channelName: str | unicode
        :return: (int | None) Options of the virtual channel.
        """
        return self._call('GetVirtualChannelOptions(QString)', toText(channelName))

    def setVirtualChannelOptions(self, channelName, options):
        """
        :param channelName: str | unicode
        :param options: int
        :return:
        """
        self._call('SetVirtualChannelOptions(QString, int)', toText(channelName), int(options))

    # ---------- Public API: screenshots ----------
    def grabScreenshot(self):
        """
        :return: (QPixmap) Image of the remote desktop (native window grab, ActiveX content included).
        """
        if self.__m_ax is not None:
            screen = self.screen() if hasattr(self, 'screen') else QApplication.primaryScreen()
            if screen is not None:
                return screen.grabWindow(self.__m_ax.winId())
        return self.grab()

    def saveScreenshot(self, fileName, fmt=None, quality=-1):
        """
        :param fileName: (str | unicode | QString) The image format is deduced from the suffix when fmt is None.
        :param fmt: (str | unicode | QString | None) e.g. 'PNG', 'JPG'.
        :param quality: (int) 0 to 100, -1 for the default.
        :return: bool
        """
        return self.grabScreenshot().save(fileName, fmt, int(quality))

    # ---------- Public API: display ----------
    def getColorDepth(self):
        """
        :return: int
        """
        return self.getControlSettings().getColorDepth()

    @pyqtSlot(int)
    def setColorDepth(self, colorDepth):
        """
        :param colorDepth: (int) 8, 15, 16, 24 or 32 (other values snap to the nearest one).
        :return:
        """
        self.getControlSettings().setColorDepth(colorDepth)

    def getDesktopWidth(self):
        """
        :return: int
        """
        return self.getControlSettings().getDesktopWidth()

    @pyqtSlot(int)
    def setDesktopWidth(self, desktopWidth):
        """
        :param desktopWidth: int
        :return:
        """
        self.getControlSettings().setDesktopWidth(desktopWidth)

    def getDesktopHeight(self):
        """
        :return: int
        """
        return self.getControlSettings().getDesktopHeight()

    @pyqtSlot(int)
    def setDesktopHeight(self, desktopHeight):
        """
        :param desktopHeight: int
        :return:
        """
        self.getControlSettings().setDesktopHeight(desktopHeight)

    def setDesktopSize(self, size):
        """
        :param size: QSize
        :return:
        """
        self.setDesktopWidth(size.width())
        self.setDesktopHeight(size.height())

    def isSmartSizing(self):
        """
        :return: bool
        """
        return self.getAdvancedSettings().isSmartSizing()

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setSmartSizing(self, smartSizing):
        """
        :param smartSizing: (bool) Scale the remote desktop to the widget size.
        :return:
        """
        self.getAdvancedSettings().setSmartSizing(bool(smartSizing))

    def isFullScreenMode(self):
        """
        :return: bool
        """
        return self.getControlSettings().isFullScreen()

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setFullScreenMode(self, fullScreenMode):
        """
        :param fullScreenMode: (bool) Full-screen state of the control (not of this widget).
        :return:
        """
        self.getControlSettings().setFullScreen(bool(fullScreenMode))

    def getConnectingText(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getConnectingText()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setConnectingText(self, connectingText):
        """
        :param connectingText: str | unicode
        :return:
        """
        self.getControlSettings().setConnectingText(connectingText)

    def getConnectedStatusText(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getConnectedStatusText()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setConnectedStatusText(self, connectedStatusText):
        """
        :param connectedStatusText: str | unicode
        :return:
        """
        self.getControlSettings().setConnectedStatusText(connectedStatusText)

    def getDisconnectedText(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getDisconnectedText()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDisconnectedText(self, disconnectedText):
        """
        :param disconnectedText: str | unicode
        :return:
        """
        self.getControlSettings().setDisconnectedText(disconnectedText)

    def getFullScreenTitle(self):
        """
        :return: str | unicode | QString
        """
        return self.getControlSettings().getFullScreenTitle()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setFullScreenTitle(self, fullScreenTitle):
        """
        :param fullScreenTitle: str | unicode
        :return:
        """
        self.getControlSettings().setFullScreenTitle(fullScreenTitle)

    def getVersion(self):
        """
        :return: (str | unicode | QString) Version of the control, '' without control.
        """
        return self.getControlSettings().getVersion()

    def getCipherStrength(self):
        """
        :return: int
        """
        return self.getControlSettings().getCipherStrength()

    def isSecuredSettingsEnabled(self):
        """
        :return: bool
        """
        return bool(self.getControlSettings().getSecuredSettingsEnabled())

    # ---------- Public API: placeholder colours ----------
    def getBackgroundColor(self):
        """
        :return: QColor
        """
        return self.__m_backgroundColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setBackgroundColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_backgroundColor != color:
            self.__m_backgroundColor = color  # type: QColor
            self.update()

    def getTextColor(self):
        """
        :return: QColor
        """
        return self.__m_textColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setTextColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_textColor != color:
            self.__m_textColor = color  # type: QColor
            self.update()

    def getAccentColor(self):
        """
        :return: QColor
        """
        return self.__m_accentColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setAccentColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_accentColor != color:
            self.__m_accentColor = color  # type: QColor
            self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(800, 600)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(160, 120)

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        Paints a placeholder when the ActiveX control is not available (otherwise the control covers the widget).
        :param event: QPaintEvent
        :return:
        """
        if self.__m_ax is not None:
            return
        p = QPainter(self)  # type: QPainter
        p.setRenderHint(QPainter.Antialiasing, True)
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        p.fillRect(self.rect(), self.__m_backgroundColor)
        # Monitor drawing.
        unit = max(8.0, min(w, h) / 6.0)  # type: float
        screen = QRectF(w / 2.0 - unit, h / 2.0 - unit * 1.35, unit * 2.0, unit * 1.35)  # type: QRectF
        pen = QPen(self.__m_accentColor)  # type: QPen
        pen.setWidthF(max(1.5, unit / 14.0))
        p.setPen(pen)
        fill = QColor(self.__m_accentColor)  # type: QColor
        fill.setAlpha(40)
        p.setBrush(QBrush(fill))
        p.drawRoundedRect(screen, unit / 10.0, unit / 10.0)
        stand = QPainterPath()  # type: QPainterPath
        stand.moveTo(QPointF(w / 2.0, screen.bottom()))
        stand.lineTo(QPointF(w / 2.0, screen.bottom() + unit * 0.25))
        stand.moveTo(QPointF(w / 2.0 - unit * 0.4, screen.bottom() + unit * 0.25))
        stand.lineTo(QPointF(w / 2.0 + unit * 0.4, screen.bottom() + unit * 0.25))
        p.setBrush(Qt.NoBrush)
        p.drawPath(stand)
        # Texts.
        title = QFont(self.font())  # type: QFont
        title.setPointSizeF(max(9.0, unit / 4.0))
        title.setBold(True)
        p.setFont(title)
        p.setPen(self.__m_textColor)
        titleRect = QRectF(0.0, screen.bottom() + unit * 0.45, w, QFontMetrics(title).height() * 1.4)  # type: QRectF
        p.drawText(titleRect, Qt.AlignHCenter | Qt.AlignTop, self.tr(u'Remote Desktop'))
        body = QFont(self.font())  # type: QFont
        body.setPointSizeF(max(8.0, unit / 6.0))
        p.setFont(body)
        dim = QColor(self.__m_textColor)  # type: QColor
        dim.setAlpha(170)
        p.setPen(dim)
        margin = max(12.0, w * 0.1)  # type: float
        textRect = QRectF(margin, titleRect.bottom(), max(0.0, w - 2.0 * margin),
                          max(0.0, h - titleRect.bottom()))  # type: QRectF
        message = self.__m_errorString or self.tr(u'The ActiveX control is created at run time.')  # type: str
        p.drawText(textRect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, message)
        p.end()

    # ---------- Properties ----------
    controlSettings = pyqtProperty(QObject, fget=getControlSettings, designable=False)  # type: pyqtProperty
    advancedSettings = pyqtProperty(QObject, fget=getAdvancedSettings, designable=False)  # type: pyqtProperty
    advancedSettings2 = pyqtProperty(QObject, fget=getAdvancedSettings2, designable=False)  # type: pyqtProperty
    advancedSettings3 = pyqtProperty(QObject, fget=getAdvancedSettings3, designable=False)  # type: pyqtProperty
    advancedSettings4 = pyqtProperty(QObject, fget=getAdvancedSettings4, designable=False)  # type: pyqtProperty
    advancedSettings5 = pyqtProperty(QObject, fget=getAdvancedSettings5, designable=False)  # type: pyqtProperty
    advancedSettings6 = pyqtProperty(QObject, fget=getAdvancedSettings6, designable=False)  # type: pyqtProperty
    advancedSettings7 = pyqtProperty(QObject, fget=getAdvancedSettings7, designable=False)  # type: pyqtProperty
    advancedSettings8 = pyqtProperty(QObject, fget=getAdvancedSettings8, designable=False)  # type: pyqtProperty
    securedSettings = pyqtProperty(QObject, fget=getSecuredSettings, designable=False)  # type: pyqtProperty
    securedSettings2 = pyqtProperty(QObject, fget=getSecuredSettings2, designable=False)  # type: pyqtProperty
    clientShell = pyqtProperty(QObject, fget=getClientShell, designable=False)  # type: pyqtProperty
    remoteProgram = pyqtProperty(QObject, fget=getRemoteProgram, designable=False)  # type: pyqtProperty
    remoteProgram2 = pyqtProperty(QObject, fget=getRemoteProgram2, designable=False)  # type: pyqtProperty
    remoteProgram3 = pyqtProperty(QObject, fget=getRemoteProgram3, designable=False)  # type: pyqtProperty
    transportSettings = pyqtProperty(QObject, fget=getTransportSettings, designable=False)  # type: pyqtProperty
    transportSettings2 = pyqtProperty(QObject, fget=getTransportSettings2, designable=False)  # type: pyqtProperty
    transportSettings3 = pyqtProperty(QObject, fget=getTransportSettings3, designable=False)  # type: pyqtProperty
    transportSettings4 = pyqtProperty(QObject, fget=getTransportSettings4, designable=False)  # type: pyqtProperty
    controlAvailable = pyqtProperty(bool, fget=isControlAvailable, designable=False)  # type: pyqtProperty
    activeControlName = pyqtProperty('QString', fget=getActiveControlName, designable=False)  # type: pyqtProperty
    errorString = pyqtProperty('QString', fget=getErrorString, designable=False)  # type: pyqtProperty
    controlVersion = pyqtProperty(int, fget=getControlVersion, fset=setControlVersion)  # type: pyqtProperty
    allowVersionFallback = pyqtProperty(bool, fget=isAllowVersionFallback,
                                        fset=setAllowVersionFallback)  # type: pyqtProperty
    autoCreateControl = pyqtProperty(bool, fget=isAutoCreateControl, fset=setAutoCreateControl,
                                     designable=False)  # type: pyqtProperty
    server = pyqtProperty('QString', fget=getServer, fset=setServer)  # type: pyqtProperty
    port = pyqtProperty(int, fget=getPort, fset=setPort)  # type: pyqtProperty
    domain = pyqtProperty('QString', fget=getDomain, fset=setDomain)  # type: pyqtProperty
    userName = pyqtProperty('QString', fget=getUserName, fset=setUserName)  # type: pyqtProperty
    password = pyqtProperty('QString', fget=getPassword, fset=setPassword, designable=False)  # type: pyqtProperty
    connectionState = pyqtProperty(int, fget=getConnectionState, notify=connectionStateChanged,
                                   designable=False)  # type: pyqtProperty
    extendedDisconnectReason = pyqtProperty(int, fget=getExtendedDisconnectReason,
                                            designable=False)  # type: pyqtProperty
    colorDepth = pyqtProperty(int, fget=getColorDepth, fset=setColorDepth)  # type: pyqtProperty
    desktopWidth = pyqtProperty(int, fget=getDesktopWidth, fset=setDesktopWidth)  # type: pyqtProperty
    desktopHeight = pyqtProperty(int, fget=getDesktopHeight, fset=setDesktopHeight)  # type: pyqtProperty
    smartSizing = pyqtProperty(bool, fget=isSmartSizing, fset=setSmartSizing)  # type: pyqtProperty
    fullScreenMode = pyqtProperty(bool, fget=isFullScreenMode, fset=setFullScreenMode)  # type: pyqtProperty
    connectingText = pyqtProperty('QString', fget=getConnectingText, fset=setConnectingText)  # type: pyqtProperty
    connectedStatusText = pyqtProperty('QString', fget=getConnectedStatusText,
                                       fset=setConnectedStatusText)  # type: pyqtProperty
    disconnectedText = pyqtProperty('QString', fget=getDisconnectedText, fset=setDisconnectedText)  # type: pyqtProperty
    fullScreenTitle = pyqtProperty('QString', fget=getFullScreenTitle, fset=setFullScreenTitle)  # type: pyqtProperty
    version = pyqtProperty('QString', fget=getVersion, designable=False)  # type: pyqtProperty
    cipherStrength = pyqtProperty(int, fget=getCipherStrength, designable=False)  # type: pyqtProperty
    securedSettingsEnabled = pyqtProperty(bool, fget=isSecuredSettingsEnabled, designable=False)  # type: pyqtProperty
    backgroundColor = pyqtProperty(QColor, fget=getBackgroundColor, fset=setBackgroundColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
