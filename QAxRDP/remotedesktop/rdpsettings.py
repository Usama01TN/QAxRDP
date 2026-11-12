# -*- coding: utf-8 -*-
"""
Settings interfaces of the Microsoft RDP client ActiveX control (MsTscAx).
Every COM sub-object of the control (AdvancedSettings, SecuredSettings, TransportSettings, RemoteProgram...) is
exposed as a QObject whose options follow the usual Qt pattern: a getter, a @pyqtSlot setter and a pyqtProperty.
Features:
    - Values are validated (clamped ranges, color depths) before reaching the control.
    - Values are cached, so options can be set before the control exists, survive a control re-creation
      (version switch) and remain readable on platforms without ActiveX (Linux, macOS, CI).
    - Write-only ActiveX properties (exposed by QAxBase as "SetXxx" slots) are handled transparently.
    - Passwords are written to the control but never returned by the getters nor emitted by signals.
"""
from ManyQt.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty
from enum import IntEnum

COLOR_DEPTHS = (8, 15, 16, 24, 32)  # type: tuple[int]


def clamp(x, a=None, b=None):
    """
    :param x: float | int
    :param a: (float | int | None) Lower bound, None for no bound.
    :param b: (float | int | None) Upper bound, None for no bound.
    :return: float | int
    """
    if a is not None and x < a:
        return a
    if b is not None and x > b:
        return b
    return x


def toText(value):
    """
    :param value: any
    :return: str | unicode | QString
    """
    return u'' if value is None else u'{}'.format(value)


def axReadProperty(axObject, name):
    """
    Reads a property of an ActiveX object.
    :param axObject: QAxObject | QAxWidget
    :param name: (str | unicode | QString) ActiveX property name.
    :return: any, None if the property is not readable.
    """
    try:
        return None if axObject.metaObject().indexOfProperty(name) < 0 else axObject.property(name)
    except:
        return None


def axWriteProperty(axObject, name, value, axType):
    """
    Writes a property of an ActiveX object. QAxBase exposes write-only (put only) COM properties as "SetXxx(type)"
    slots instead of Qt properties, so the slot is called when the property is not in the meta-object.
    :param axObject: QAxObject | QAxWidget
    :param name: (str | unicode | QString) ActiveX property name.
    :param value: any
    :param axType: (str | unicode | QString) Qt type name used by the slot fallback: bool, int, uint or QString.
    :return: bool
    """
    try:
        mo = axObject.metaObject()
        index = mo.indexOfProperty(name)  # type: int
        if index >= 0 and mo.property(index).isWritable():
            return bool(axObject.setProperty(name, value))
        axObject.dynamicCall('Set{}({})'.format(name, axType), value)
        return True
    except:
        return False


class RdpSettingsInterface(QObject):
    """
    Base class of the MsTscAx settings interfaces: caches the values set by the user and forwards them to the
    ActiveX sub-object (queried once with QAxBase.querySubObject) when a hosting control is attached.
    """
    INTERFACE = ''  # type: str  # ActiveX sub-object name, '' = the control itself.
    COM_INTERFACE = ''  # type: str
    PROPERTIES = ()  # type: tuple[tuple[str, str, str, str]]
    settingChanged = pyqtSignal(str, object)  # type: pyqtSignal
    availabilityChanged = pyqtSignal(bool)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param host: (QAxWidget | None) Control hosting the interface.
        :param settingChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        host = kwargs.pop('host', None)  # type: QAxWidget | None
        settingChanged = kwargs.pop('settingChanged', None)  # type: callable | None
        super(RdpSettingsInterface, self).__init__(*args, **kwargs)
        self.__m_host = None  # type: QAxWidget | None
        self.__m_axObject = None  # type: QAxObject | QAxWidget | None
        self.__m_values = {}  # type: dict[str, object]
        self.__m_secrets = set()  # type: set[str]
        if callable(settingChanged):
            self.settingChanged.connect(settingChanged)
        if host is not None:
            self.attachHost(host)

    # ---------- Helpers ----------
    def _axObject(self):
        """
        :return: QAxObject | QAxWidget | None
        """
        if self.__m_axObject is None and self.__m_host is not None:
            if not self.INTERFACE:
                self.__m_axObject = self.__m_host  # type: QAxWidget
            else:
                try:
                    obj = self.__m_host.querySubObject(self.INTERFACE)  # type: QAxObject | None
                except:
                    obj = None  # type: None
                if obj is not None and not (hasattr(obj, 'isNull') and obj.isNull()):
                    self.__m_axObject = obj  # type: QAxObject
        return self.__m_axObject

    def _axType(self, axName):
        """
        :param axName: str | unicode | QString
        :return: str | unicode | QString
        """
        for _, ax, axType, _ in self.PROPERTIES:
            if ax == axName:
                return axType
        return 'QVariant'

    def _read(self, axName, default=None):
        """
        Reads a value from the control, or from the cache when the control is not available.
        :param axName: (str | unicode | QString) ActiveX property name.
        :param default: any
        :return: any
        """
        obj = self._axObject()  # type: QAxObject | QAxWidget | None
        if obj is not None:
            value = axReadProperty(obj, axName)  # type: any
            if value is not None:
                return value
        return self.__m_values.get(axName, default)

    def _write(self, axName, value, axType, secret=False):
        """
        Caches a value and forwards it to the control.
        :param axName: (str | unicode | QString) ActiveX property name.
        :param value: any
        :param axType: (str | unicode | QString) bool, int, uint or QString.
        :param secret: (bool) True for passwords: never emitted, never returned.
        :return: bool, True if the control accepted the value.
        """
        changed = self.__m_values.get(axName) != value  # type: bool
        self.__m_values[axName] = value
        if secret:
            self.__m_secrets.add(axName)
        obj = self._axObject()  # type: QAxObject | QAxWidget | None
        ok = axWriteProperty(obj, axName, value, axType) if obj is not None else False  # type: bool
        if changed:
            self.settingChanged.emit(axName, u'' if secret else value)
        return ok

    def _call(self, signature, *args):
        """
        Calls a method of the ActiveX sub-object.
        :param signature: (str | unicode | QString) e.g. 'Launch()'.
        :param args: any
        :return: any, None when the control is not available.
        """
        obj = self._axObject()  # type: QAxObject | QAxWidget | None
        if obj is None:
            return None
        try:
            return obj.dynamicCall(signature, *args)
        except:
            return None

    # ---------- Public API ----------
    def attachHost(self, host):
        """
        Attaches the interface to a (new) hosting control and sends it the cached values.
        :param host: QAxWidget | None
        :return:
        """
        self.__m_host = host  # type: QAxWidget | None
        self.__m_axObject = None  # type: None
        if host is not None:
            self.reapply()
        self.availabilityChanged.emit(self.isAvailable())

    def detachHost(self):
        """
        Detaches the interface from its hosting control (values stay cached).
        :return:
        """
        self.attachHost(None)

    def getHost(self):
        """
        :return: QAxWidget | None
        """
        return self.__m_host

    def getInterfaceName(self):
        """
        :return: (str | unicode | QString) ActiveX sub-object name ('' for the control itself).
        """
        return self.INTERFACE

    def getComInterfaceName(self):
        """
        :return: str | unicode | QString
        """
        return self.COM_INTERFACE

    def isAvailable(self):
        """
        :return: (bool) True when the ActiveX sub-object could be queried.
        """
        return self._axObject() is not None

    def propertyNames(self):
        """
        :return: (list[str | unicode | QString] | QStringList) Python property names of the interface.
        """
        return [name for name, _, _, _ in self.PROPERTIES]

    def findProperty(self, name):
        """
        Case-insensitive lookup accepting python names (smartSizing) and ActiveX names (SmartSizing).
        :param name: str | unicode | QString
        :return: (str | unicode | QString | None) Python property name.
        """
        key = toText(name).lower()  # type: str
        for pyName, axName, _, _ in self.PROPERTIES:
            if key in (pyName.lower(), axName.lower()):
                return pyName
        return None

    def values(self):
        """
        :return: (dict[str, any]) Cached values set by the user, keyed by ActiveX name (passwords excluded).
        """
        return dict((k, v) for k, v in self.__m_values.items() if k not in self.__m_secrets)

    @pyqtSlot()
    def clearValues(self):
        """
        Forgets the cached values (the control keeps its current state).
        :return:
        """
        self.__m_values.clear()
        self.__m_secrets.clear()

    @pyqtSlot()
    def reapply(self):
        """
        Sends every cached value to the control.
        :return: (int) Number of values accepted by the control.
        """
        obj = self._axObject()  # type: QAxObject | QAxWidget | None
        if obj is None:
            return 0
        count = 0  # type: int
        for axName, value in list(self.__m_values.items()):
            count += int(axWriteProperty(obj, axName, value, self._axType(axName)))
        return count


class RdpControlSettings(RdpSettingsInterface):
    """
    Top level properties of the MsTscAx control (server, credentials, display and texts) (IMsRdpClient10, the
    control itself).
    """
    INTERFACE = ''  # type: str
    COM_INTERFACE = 'IMsRdpClient10'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('server', 'Server', 'QString', 'rw'),
        ('domain', 'Domain', 'QString', 'rw'),
        ('userName', 'UserName', 'QString', 'rw'),
        ('colorDepth', 'ColorDepth', 'int', 'rw'),
        ('desktopWidth', 'DesktopWidth', 'int', 'rw'),
        ('desktopHeight', 'DesktopHeight', 'int', 'rw'),
        ('connectingText', 'ConnectingText', 'QString', 'rw'),
        ('connectedStatusText', 'ConnectedStatusText', 'QString', 'rw'),
        ('disconnectedText', 'DisconnectedText', 'QString', 'rw'),
        ('fullScreenTitle', 'FullScreenTitle', 'QString', 'w'),
        ('fullScreen', 'FullScreen', 'bool', 'rw'),
        ('startConnected', 'StartConnected', 'int', 'rw'),
        ('securedSettingsEnabled', 'SecuredSettingsEnabled', 'int', 'r'),
        ('version', 'Version', 'QString', 'r'),
        ('cipherStrength', 'CipherStrength', 'int', 'r'),
        ('horizontalScrollBarVisible', 'HorizontalScrollBarVisible', 'int', 'r'),
        ('verticalScrollBarVisible', 'VerticalScrollBarVisible', 'int', 'r'),
        ('connected', 'Connected', 'int', 'r'),
        ('extendedDisconnectReason', 'ExtendedDisconnectReason', 'int', 'r'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getServer(self):
        """
        Name or IP address of the server to connect to.
        ActiveX property: Server.
        :return: str | unicode | QString
        """
        return toText(self._read('Server', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setServer(self, server):
        """
        :param server: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('Server', toText(server), 'QString')

    def getDomain(self):
        """
        Domain to which the current user logs on.
        ActiveX property: Domain.
        :return: str | unicode | QString
        """
        return toText(self._read('Domain', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDomain(self, domain):
        """
        :param domain: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('Domain', toText(domain), 'QString')

    def getUserName(self):
        """
        Username logon credential.
        ActiveX property: UserName.
        :return: str | unicode | QString
        """
        return toText(self._read('UserName', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setUserName(self, userName):
        """
        :param userName: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('UserName', toText(userName), 'QString')

    def getColorDepth(self):
        """
        Color depth, in bits per pixel (8, 15, 16, 24 or 32).
        ActiveX property: ColorDepth.
        :return: int
        """
        return int(self._read('ColorDepth', 32))

    @pyqtSlot(int)
    def setColorDepth(self, colorDepth):
        """
        :param colorDepth: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('ColorDepth', min(COLOR_DEPTHS, key=lambda d: abs(d - int(colorDepth))), 'int')

    def getDesktopWidth(self):
        """
        Width, in pixels, of the initial remote desktop.
        ActiveX property: DesktopWidth.
        :return: int
        """
        return int(self._read('DesktopWidth', 0))

    @pyqtSlot(int)
    def setDesktopWidth(self, desktopWidth):
        """
        :param desktopWidth: int
        :return: bool, True if the control accepted the value.
        """
        desktopWidth = clamp(int(desktopWidth), 0, 8192)  # type: int
        return self._write('DesktopWidth', desktopWidth, 'int')

    def getDesktopHeight(self):
        """
        Height, in pixels, of the initial remote desktop.
        ActiveX property: DesktopHeight.
        :return: int
        """
        return int(self._read('DesktopHeight', 0))

    @pyqtSlot(int)
    def setDesktopHeight(self, desktopHeight):
        """
        :param desktopHeight: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('DesktopHeight', clamp(int(desktopHeight), 0, 8192), 'int')

    def getConnectingText(self):
        """
        Text displayed centered in the control while connecting.
        ActiveX property: ConnectingText.
        :return: str | unicode | QString
        """
        return toText(self._read('ConnectingText', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setConnectingText(self, connectingText):
        """
        :param connectingText: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectingText', toText(connectingText), 'QString')

    def getConnectedStatusText(self):
        """
        Text displayed in the control once connected.
        ActiveX property: ConnectedStatusText.
        :return: str | unicode | QString
        """
        return toText(self._read('ConnectedStatusText', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setConnectedStatusText(self, connectedStatusText):
        """
        :param connectedStatusText: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectedStatusText', toText(connectedStatusText), 'QString')

    def getDisconnectedText(self):
        """
        Text displayed centered in the control when disconnected.
        ActiveX property: DisconnectedText.
        :return: str | unicode | QString
        """
        return toText(self._read('DisconnectedText', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDisconnectedText(self, disconnectedText):
        """
        :param disconnectedText: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('DisconnectedText', toText(disconnectedText), 'QString')

    def getFullScreenTitle(self):
        """
        Window title displayed in full-screen mode (write-only).
        ActiveX property: FullScreenTitle.
        :return: str | unicode | QString
        """
        return toText(self._read('FullScreenTitle', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setFullScreenTitle(self, fullScreenTitle):
        """
        :param fullScreenTitle: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('FullScreenTitle', toText(fullScreenTitle), 'QString')

    def isFullScreen(self):
        """
        Full-screen state of the control.
        ActiveX property: FullScreen.
        :return: bool
        """
        return bool(self._read('FullScreen', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setFullScreen(self, fullScreen):
        """
        :param fullScreen: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('FullScreen', bool(fullScreen), 'bool')

    def getStartConnected(self):
        """
        Connect immediately upon startup (1) or not (0).
        ActiveX property: StartConnected.
        :return: int
        """
        return int(self._read('StartConnected', 0))

    @pyqtSlot(int)
    def setStartConnected(self, startConnected):
        """
        :param startConnected: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('StartConnected', int(startConnected), 'int')

    def getSecuredSettingsEnabled(self):
        """
        Whether the secured settings interface is available (read-only).
        ActiveX property: SecuredSettingsEnabled.
        :return: int
        """
        return int(self._read('SecuredSettingsEnabled', 0))

    def getVersion(self):
        """
        Version number of the control (read-only).
        ActiveX property: Version.
        :return: str | unicode | QString
        """
        return toText(self._read('Version', ''))

    def getCipherStrength(self):
        """
        Maximum encryption strength of the control (read-only).
        ActiveX property: CipherStrength.
        :return: int
        """
        return int(self._read('CipherStrength', 0))

    def getHorizontalScrollBarVisible(self):
        """
        Whether the control displays a horizontal scroll bar (read-only).
        ActiveX property: HorizontalScrollBarVisible.
        :return: int
        """
        return int(self._read('HorizontalScrollBarVisible', 0))

    def getVerticalScrollBarVisible(self):
        """
        Whether the control displays a vertical scroll bar (read-only).
        ActiveX property: VerticalScrollBarVisible.
        :return: int
        """
        return int(self._read('VerticalScrollBarVisible', 0))

    def getConnected(self):
        """
        Connection state: 0 disconnected, 1 connected, 2 connecting (read-only).
        ActiveX property: Connected.
        :return: int
        """
        return int(self._read('Connected', 0))

    def getExtendedDisconnectReason(self):
        """
        Extended information about the last disconnection (read-only).
        ActiveX property: ExtendedDisconnectReason.
        :return: int
        """
        return int(self._read('ExtendedDisconnectReason', 0))

    # ---------- Properties ----------
    server = pyqtProperty('QString', fget=getServer, fset=setServer)  # type: pyqtProperty
    domain = pyqtProperty('QString', fget=getDomain, fset=setDomain)  # type: pyqtProperty
    userName = pyqtProperty('QString', fget=getUserName, fset=setUserName)  # type: pyqtProperty
    colorDepth = pyqtProperty(int, fget=getColorDepth, fset=setColorDepth)  # type: pyqtProperty
    desktopWidth = pyqtProperty(int, fget=getDesktopWidth, fset=setDesktopWidth)  # type: pyqtProperty
    desktopHeight = pyqtProperty(int, fget=getDesktopHeight, fset=setDesktopHeight)  # type: pyqtProperty
    connectingText = pyqtProperty('QString', fget=getConnectingText, fset=setConnectingText)  # type: pyqtProperty
    connectedStatusText = pyqtProperty('QString', fget=getConnectedStatusText,
                                       fset=setConnectedStatusText)  # type: pyqtProperty
    disconnectedText = pyqtProperty('QString', fget=getDisconnectedText, fset=setDisconnectedText)  # type: pyqtProperty
    fullScreenTitle = pyqtProperty('QString', fget=getFullScreenTitle, fset=setFullScreenTitle)  # type: pyqtProperty
    fullScreen = pyqtProperty(bool, fget=isFullScreen, fset=setFullScreen)  # type: pyqtProperty
    startConnected = pyqtProperty(int, fget=getStartConnected, fset=setStartConnected)  # type: pyqtProperty
    securedSettingsEnabled = pyqtProperty(int, fget=getSecuredSettingsEnabled)  # type: pyqtProperty
    version = pyqtProperty('QString', fget=getVersion)  # type: pyqtProperty
    cipherStrength = pyqtProperty(int, fget=getCipherStrength)  # type: pyqtProperty
    horizontalScrollBarVisible = pyqtProperty(int, fget=getHorizontalScrollBarVisible)  # type: pyqtProperty
    verticalScrollBarVisible = pyqtProperty(int, fget=getVerticalScrollBarVisible)  # type: pyqtProperty
    connected = pyqtProperty(int, fget=getConnected)  # type: pyqtProperty
    extendedDisconnectReason = pyqtProperty(int, fget=getExtendedDisconnectReason)  # type: pyqtProperty


class RdpAdvancedSettings(RdpSettingsInterface):
    """
    Advanced settings of the control: bitmap caching, hot keys, redirection, timeouts, port
    (IMsRdpClientAdvancedSettings, the "AdvancedSettings" sub-object).
    """
    INTERFACE = 'AdvancedSettings'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('acceleratorPassthrough', 'AcceleratorPassthrough', 'bool', 'rw'),
        ('allowBackgroundInput', 'allowBackgroundInput', 'int', 'rw'),
        ('bitmapCacheSize', 'BitmapCacheSize', 'int', 'rw'),
        ('bitmapPeristence', 'BitmapPeristence', 'int', 'rw'),
        ('bitmapPersistence', 'BitmapPersistence', 'int', 'rw'),
        ('bitmapVirtualCache16BppSize', 'BitmapVirtualCache16BppSize', 'int', 'rw'),
        ('bitmapVirtualCache24BppSize', 'BitmapVirtualCache24BppSize', 'int', 'rw'),
        ('bitmapVirtualCacheSize', 'BitmapVirtualCacheSize', 'int', 'rw'),
        ('brushSupportLevel', 'brushSupportLevel', 'int', 'rw'),
        ('cachePersistenceActive', 'CachePersistenceActive', 'int', 'rw'),
        ('clearTextPassword', 'ClearTextPassword', 'QString', 'w'),
        ('compress', 'Compress', 'int', 'rw'),
        ('connectToServerConsole', 'ConnectToServerConsole', 'bool', 'rw'),
        ('connectWithEndpoint', 'ConnectWithEndpoint', 'int', 'w'),
        ('containerHandledFullScreen', 'ContainerHandledFullScreen', 'int', 'rw'),
        ('dedicatedTerminal', 'DedicatedTerminal', 'int', 'rw'),
        ('disableCtrlAltDel', 'DisableCtrlAltDel', 'int', 'rw'),
        ('disableRdpdr', 'DisableRdpdr', 'int', 'rw'),
        ('displayConnectionBar', 'DisplayConnectionBar', 'bool', 'rw'),
        ('doubleClickDetect', 'DoubleClickDetect', 'int', 'rw'),
        ('enableMouse', 'EnableMouse', 'int', 'rw'),
        ('enableWindowsKey', 'EnableWindowsKey', 'int', 'rw'),
        ('encryptionEnabled', 'EncryptionEnabled', 'int', 'rw'),
        ('grabFocusOnConnect', 'GrabFocusOnConnect', 'bool', 'rw'),
        ('hotKeyAltEsc', 'HotKeyAltEsc', 'int', 'rw'),
        ('hotKeyAltShiftTab', 'HotKeyAltShiftTab', 'int', 'rw'),
        ('hotKeyAltSpace', 'HotKeyAltSpace', 'int', 'rw'),
        ('hotKeyAltTab', 'HotKeyAltTab', 'int', 'rw'),
        ('hotKeyCtrlAltDel', 'HotKeyCtrlAltDel', 'int', 'rw'),
        ('hotKeyCtrlEsc', 'HotKeyCtrlEsc', 'int', 'rw'),
        ('hotKeyFullScreen', 'HotKeyFullScreen', 'int', 'rw'),
        ('iconFile', 'IconFile', 'QString', 'w'),
        ('iconIndex', 'IconIndex', 'int', 'rw'),
        ('inputEventsAtOnce', 'InputEventsAtOnce', 'int', 'rw'),
        ('keepAliveInterval', 'keepAliveInterval', 'int', 'rw'),
        ('keyboardFunctionKey', 'KeyboardFunctionKey', 'int', 'rw'),
        ('keyBoardLayoutStr', 'KeyBoardLayoutStr', 'QString', 'w'),
        ('keyboardSubType', 'KeyboardSubType', 'int', 'rw'),
        ('keyboardType', 'KeyboardType', 'int', 'rw'),
        ('loadBalanceInfo', 'LoadBalanceInfo', 'QString', 'rw'),
        ('maxEventCount', 'maxEventCount', 'int', 'rw'),
        ('maximizeShell', 'MaximizeShell', 'int', 'rw'),
        ('minInputSendInterval', 'minInputSendInterval', 'int', 'rw'),
        ('minutesToIdleTimeout', 'MinutesToIdleTimeout', 'int', 'rw'),
        ('notifyTSPublicKey', 'NotifyTSPublicKey', 'bool', 'rw'),
        ('numBitmapCaches', 'NumBitmapCaches', 'int', 'rw'),
        ('orderDrawThreshold', 'orderDrawThreshold', 'int', 'rw'),
        ('overallConnectionTimeout', 'overallConnectionTimeout', 'int', 'rw'),
        ('performanceFlags', 'PerformanceFlags', 'int', 'rw'),
        ('persistCacheDirectory', 'PersistCacheDirectory', 'QString', 'rw'),
        ('pinConnectionBar', 'PinConnectionBar', 'bool', 'rw'),
        ('pluginDlls', 'PluginDlls', 'QString', 'w'),
        ('rdpdrClipCleanTempDirString', 'RdpdrClipCleanTempDirString', 'QString', 'rw'),
        ('rdpdrClipPasteInfoString', 'RdpdrClipPasteInfoString', 'QString', 'rw'),
        ('rdpdrLocalPrintingDocName', 'RdpdrLocalPrintingDocName', 'QString', 'rw'),
        ('rdpPort', 'RDPPort', 'int', 'rw'),
        ('redirectDrives', 'RedirectDrives', 'bool', 'rw'),
        ('redirectPorts', 'RedirectPorts', 'bool', 'rw'),
        ('redirectPrinters', 'RedirectPrinters', 'bool', 'rw'),
        ('redirectSmartCards', 'RedirectSmartCards', 'bool', 'rw'),
        ('sasSequence', 'SasSequence', 'int', 'rw'),
        ('scaleBitmapCachesByBPP', 'ScaleBitmapCachesByBPP', 'int', 'rw'),
        ('shadowBitmap', 'ShadowBitmap', 'int', 'rw'),
        ('shutdownTimeout', 'shutdownTimeout', 'int', 'rw'),
        ('singleConnectionTimeout', 'singleConnectionTimeout', 'int', 'rw'),
        ('smartSizing', 'SmartSizing', 'bool', 'rw'),
        ('smoothScroll', 'SmoothScroll', 'int', 'rw'),
        ('transportType', 'TransportType', 'int', 'rw'),
        ('winceFixedPalette', 'WinceFixedPalette', 'int', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def isAcceleratorPassthrough(self):
        """
        Specifies whether accelerator passthrough is enabled.
        ActiveX property: AcceleratorPassthrough.
        :return: bool
        """
        return bool(self._read('AcceleratorPassthrough', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAcceleratorPassthrough(self, acceleratorPassthrough):
        """
        :param acceleratorPassthrough: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('AcceleratorPassthrough', bool(acceleratorPassthrough), 'bool')

    def getAllowBackgroundInput(self):
        """
        Specifies whether background input mode is enabled.
        ActiveX property: allowBackgroundInput.
        :return: int
        """
        return int(self._read('allowBackgroundInput', 0))

    @pyqtSlot(int)
    def setAllowBackgroundInput(self, allowBackgroundInput):
        """
        :param allowBackgroundInput: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('allowBackgroundInput', int(allowBackgroundInput), 'int')

    def getBitmapCacheSize(self):
        """
        Size, in kilobytes, of the bitmap cache file used for 8 bpp bitmaps (1 to 32).
        ActiveX property: BitmapCacheSize.
        :return: int
        """
        return int(self._read('BitmapCacheSize', 1))

    @pyqtSlot(int)
    def setBitmapCacheSize(self, bitmapCacheSize):
        """
        :param bitmapCacheSize: int
        :return: bool, True if the control accepted the value.
        """
        bitmapCacheSize = clamp(int(bitmapCacheSize), 1, 32)  # type: int
        return self._write('BitmapCacheSize', bitmapCacheSize, 'int')

    def getBitmapPeristence(self):
        """
        Specifies whether bitmap caching is enabled (the misspelling is in the released version of the control).
        ActiveX property: BitmapPeristence.
        :return: int
        """
        return int(self._read('BitmapPeristence', 0))

    @pyqtSlot(int)
    def setBitmapPeristence(self, bitmapPeristence):
        """
        :param bitmapPeristence: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('BitmapPeristence', int(bitmapPeristence), 'int')

    def getBitmapPersistence(self):
        """
        Specifies if persistent bitmap caching should be used.
        ActiveX property: BitmapPersistence.
        :return: int
        """
        return int(self._read('BitmapPersistence', 0))

    @pyqtSlot(int)
    def setBitmapPersistence(self, bitmapPersistence):
        """
        :param bitmapPersistence: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('BitmapPersistence', int(bitmapPersistence), 'int')

    def getBitmapVirtualCache16BppSize(self):
        """
        Size, in megabytes, of the persistent bitmap cache file for 15 and 16 bpp.
        ActiveX property: BitmapVirtualCache16BppSize.
        :return: int
        """
        return int(self._read('BitmapVirtualCache16BppSize', 0))

    @pyqtSlot(int)
    def setBitmapVirtualCache16BppSize(self, bitmapVirtualCache16BppSize):
        """
        :param bitmapVirtualCache16BppSize: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('BitmapVirtualCache16BppSize', int(bitmapVirtualCache16BppSize), 'int')

    def getBitmapVirtualCache24BppSize(self):
        """
        Size, in megabytes, of the persistent bitmap cache file for 24 bpp.
        ActiveX property: BitmapVirtualCache24BppSize.
        :return: int
        """
        return int(self._read('BitmapVirtualCache24BppSize', 0))

    @pyqtSlot(int)
    def setBitmapVirtualCache24BppSize(self, bitmapVirtualCache24BppSize):
        """
        :param bitmapVirtualCache24BppSize: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('BitmapVirtualCache24BppSize', int(bitmapVirtualCache24BppSize), 'int')

    def getBitmapVirtualCacheSize(self):
        """
        Size, in megabytes, of the persistent bitmap cache file for 8 bpp (1 to 32).
        ActiveX property: BitmapVirtualCacheSize.
        :return: int
        """
        return int(self._read('BitmapVirtualCacheSize', 1))

    @pyqtSlot(int)
    def setBitmapVirtualCacheSize(self, bitmapVirtualCacheSize):
        """
        :param bitmapVirtualCacheSize: int
        :return: bool, True if the control accepted the value.
        """
        bitmapVirtualCacheSize = clamp(int(bitmapVirtualCacheSize), 1, 32)  # type: int
        return self._write('BitmapVirtualCacheSize', bitmapVirtualCacheSize, 'int')

    def getBrushSupportLevel(self):
        """
        Specifies the level of brush support.
        ActiveX property: brushSupportLevel.
        :return: int
        """
        return int(self._read('brushSupportLevel', 0))

    @pyqtSlot(int)
    def setBrushSupportLevel(self, brushSupportLevel):
        """
        :param brushSupportLevel: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('brushSupportLevel', int(brushSupportLevel), 'int')

    def getCachePersistenceActive(self):
        """
        Specifies whether persistent bitmap caching should be used.
        ActiveX property: CachePersistenceActive.
        :return: int
        """
        return int(self._read('CachePersistenceActive', 0))

    @pyqtSlot(int)
    def setCachePersistenceActive(self, cachePersistenceActive):
        """
        :param cachePersistenceActive: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('CachePersistenceActive', int(cachePersistenceActive), 'int')

    def getClearTextPassword(self):
        """
        Password used to connect (write-only; the getter never returns it).
        ActiveX property: ClearTextPassword.
        :return: str | unicode | QString
        """
        return ''

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setClearTextPassword(self, clearTextPassword):
        """
        :param clearTextPassword: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('ClearTextPassword', toText(clearTextPassword), 'QString', secret=True)

    def getCompress(self):
        """
        Specifies whether compression is enabled.
        ActiveX property: Compress.
        :return: int
        """
        return int(self._read('Compress', 0))

    @pyqtSlot(int)
    def setCompress(self, compress):
        """
        :param compress: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('Compress', int(compress), 'int')

    def isConnectToServerConsole(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: ConnectToServerConsole.
        :return: bool
        """
        return bool(self._read('ConnectToServerConsole', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setConnectToServerConsole(self, connectToServerConsole):
        """
        :param connectToServerConsole: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectToServerConsole', bool(connectToServerConsole), 'bool')

    def getConnectWithEndpoint(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: ConnectWithEndpoint.
        :return: int
        """
        return int(self._read('ConnectWithEndpoint', 0))

    @pyqtSlot(int)
    def setConnectWithEndpoint(self, connectWithEndpoint):
        """
        :param connectWithEndpoint: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectWithEndpoint', int(connectWithEndpoint), 'int')

    def getContainerHandledFullScreen(self):
        """
        Specifies whether the container-handled full-screen mode is enabled.
        ActiveX property: ContainerHandledFullScreen.
        :return: int
        """
        return int(self._read('ContainerHandledFullScreen', 0))

    @pyqtSlot(int)
    def setContainerHandledFullScreen(self, containerHandledFullScreen):
        """
        :param containerHandledFullScreen: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('ContainerHandledFullScreen', int(containerHandledFullScreen), 'int')

    def getDedicatedTerminal(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: DedicatedTerminal.
        :return: int
        """
        return int(self._read('DedicatedTerminal', 0))

    @pyqtSlot(int)
    def setDedicatedTerminal(self, dedicatedTerminal):
        """
        :param dedicatedTerminal: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('DedicatedTerminal', int(dedicatedTerminal), 'int')

    def getDisableCtrlAltDel(self):
        """
        Specifies if the initial explanatory screen in Winlogon should display.
        ActiveX property: DisableCtrlAltDel.
        :return: int
        """
        return int(self._read('DisableCtrlAltDel', 0))

    @pyqtSlot(int)
    def setDisableCtrlAltDel(self, disableCtrlAltDel):
        """
        :param disableCtrlAltDel: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('DisableCtrlAltDel', int(disableCtrlAltDel), 'int')

    def getDisableRdpdr(self):
        """
        Specifies whether printer and clipboard redirection is enabled.
        ActiveX property: DisableRdpdr.
        :return: int
        """
        return int(self._read('DisableRdpdr', 0))

    @pyqtSlot(int)
    def setDisableRdpdr(self, disableRdpdr):
        """
        :param disableRdpdr: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('DisableRdpdr', int(disableRdpdr), 'int')

    def isDisplayConnectionBar(self):
        """
        Specifies whether to use the connection bar.
        ActiveX property: DisplayConnectionBar.
        :return: bool
        """
        return bool(self._read('DisplayConnectionBar', True))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setDisplayConnectionBar(self, displayConnectionBar):
        """
        :param displayConnectionBar: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('DisplayConnectionBar', bool(displayConnectionBar), 'bool')

    def getDoubleClickDetect(self):
        """
        Specifies if the client identifies double-clicks for the server.
        ActiveX property: DoubleClickDetect.
        :return: int
        """
        return int(self._read('DoubleClickDetect', 0))

    @pyqtSlot(int)
    def setDoubleClickDetect(self, doubleClickDetect):
        """
        :param doubleClickDetect: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('DoubleClickDetect', int(doubleClickDetect), 'int')

    def getEnableMouse(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: EnableMouse.
        :return: int
        """
        return int(self._read('EnableMouse', 0))

    @pyqtSlot(int)
    def setEnableMouse(self, enableMouse):
        """
        :param enableMouse: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('EnableMouse', int(enableMouse), 'int')

    def getEnableWindowsKey(self):
        """
        Specifies if the Windows key can be used in the remote session.
        ActiveX property: EnableWindowsKey.
        :return: int
        """
        return int(self._read('EnableWindowsKey', 0))

    @pyqtSlot(int)
    def setEnableWindowsKey(self, enableWindowsKey):
        """
        :param enableWindowsKey: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('EnableWindowsKey', int(enableWindowsKey), 'int')

    def getEncryptionEnabled(self):
        """
        Not supported: encryption cannot be disabled.
        ActiveX property: EncryptionEnabled.
        :return: int
        """
        return int(self._read('EncryptionEnabled', 0))

    @pyqtSlot(int)
    def setEncryptionEnabled(self, encryptionEnabled):
        """
        :param encryptionEnabled: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('EncryptionEnabled', int(encryptionEnabled), 'int')

    def isGrabFocusOnConnect(self):
        """
        Specifies if the client control should have the focus while connecting.
        ActiveX property: GrabFocusOnConnect.
        :return: bool
        """
        return bool(self._read('GrabFocusOnConnect', True))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setGrabFocusOnConnect(self, grabFocusOnConnect):
        """
        :param grabFocusOnConnect: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('GrabFocusOnConnect', bool(grabFocusOnConnect), 'bool')

    def getHotKeyAltEsc(self):
        """
        Virtual-key added to ALT to replace ALT+ESC (default VK_INSERT).
        ActiveX property: HotKeyAltEsc.
        :return: int
        """
        return int(self._read('HotKeyAltEsc', 45))

    @pyqtSlot(int)
    def setHotKeyAltEsc(self, hotKeyAltEsc):
        """
        :param hotKeyAltEsc: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyAltEsc', int(hotKeyAltEsc), 'int')

    def getHotKeyAltShiftTab(self):
        """
        Virtual-key added to ALT to replace ALT+SHIFT+TAB (default VK_NEXT).
        ActiveX property: HotKeyAltShiftTab.
        :return: int
        """
        return int(self._read('HotKeyAltShiftTab', 34))

    @pyqtSlot(int)
    def setHotKeyAltShiftTab(self, hotKeyAltShiftTab):
        """
        :param hotKeyAltShiftTab: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyAltShiftTab', int(hotKeyAltShiftTab), 'int')

    def getHotKeyAltSpace(self):
        """
        Virtual-key added to ALT to replace ALT+SPACE (default VK_DELETE).
        ActiveX property: HotKeyAltSpace.
        :return: int
        """
        return int(self._read('HotKeyAltSpace', 46))

    @pyqtSlot(int)
    def setHotKeyAltSpace(self, hotKeyAltSpace):
        """
        :param hotKeyAltSpace: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyAltSpace', int(hotKeyAltSpace), 'int')

    def getHotKeyAltTab(self):
        """
        Virtual-key added to ALT to replace ALT+TAB (default VK_PRIOR).
        ActiveX property: HotKeyAltTab.
        :return: int
        """
        return int(self._read('HotKeyAltTab', 33))

    @pyqtSlot(int)
    def setHotKeyAltTab(self, hotKeyAltTab):
        """
        :param hotKeyAltTab: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyAltTab', int(hotKeyAltTab), 'int')

    def getHotKeyCtrlAltDel(self):
        """
        Virtual-key added to CTRL+ALT to replace CTRL+ALT+DELETE (default VK_END).
        ActiveX property: HotKeyCtrlAltDel.
        :return: int
        """
        return int(self._read('HotKeyCtrlAltDel', 35))

    @pyqtSlot(int)
    def setHotKeyCtrlAltDel(self, hotKeyCtrlAltDel):
        """
        :param hotKeyCtrlAltDel: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyCtrlAltDel', int(hotKeyCtrlAltDel), 'int')

    def getHotKeyCtrlEsc(self):
        """
        Virtual-key added to ALT to replace CTRL+ESC (default VK_HOME).
        ActiveX property: HotKeyCtrlEsc.
        :return: int
        """
        return int(self._read('HotKeyCtrlEsc', 36))

    @pyqtSlot(int)
    def setHotKeyCtrlEsc(self, hotKeyCtrlEsc):
        """
        :param hotKeyCtrlEsc: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyCtrlEsc', int(hotKeyCtrlEsc), 'int')

    def getHotKeyFullScreen(self):
        """
        Virtual-key added to CTRL+ALT to switch to full-screen mode (default VK_CANCEL).
        ActiveX property: HotKeyFullScreen.
        :return: int
        """
        return int(self._read('HotKeyFullScreen', 3))

    @pyqtSlot(int)
    def setHotKeyFullScreen(self, hotKeyFullScreen):
        """
        :param hotKeyFullScreen: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyFullScreen', int(hotKeyFullScreen), 'int')

    def getIconFile(self):
        """
        File containing the icon displayed in full-screen mode (write-only).
        ActiveX property: IconFile.
        :return: str | unicode | QString
        """
        return toText(self._read('IconFile', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setIconFile(self, iconFile):
        """
        :param iconFile: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('IconFile', toText(iconFile), 'QString')

    def getIconIndex(self):
        """
        Index of the icon within the current icon file.
        ActiveX property: IconIndex.
        :return: int
        """
        return int(self._read('IconIndex', 0))

    @pyqtSlot(int)
    def setIconIndex(self, iconIndex):
        """
        :param iconIndex: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('IconIndex', int(iconIndex), 'int')

    def getInputEventsAtOnce(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: InputEventsAtOnce.
        :return: int
        """
        return int(self._read('InputEventsAtOnce', 0))

    @pyqtSlot(int)
    def setInputEventsAtOnce(self, inputEventsAtOnce):
        """
        :param inputEventsAtOnce: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('InputEventsAtOnce', int(inputEventsAtOnce), 'int')

    def getKeepAliveInterval(self):
        """
        Interval, in ms, of keep-alive messages (0 disables, minimum valid value is 10000).
        ActiveX property: keepAliveInterval.
        :return: int
        """
        return int(self._read('keepAliveInterval', 0))

    @pyqtSlot(int)
    def setKeepAliveInterval(self, keepAliveInterval):
        """
        :param keepAliveInterval: int
        :return: bool, True if the control accepted the value.
        """
        keepAliveInterval = clamp(int(keepAliveInterval), 0, None)  # type: int
        return self._write('keepAliveInterval', keepAliveInterval, 'int')

    def getKeyboardFunctionKey(self):
        """
        Valid for Windows CE only.
        ActiveX property: KeyboardFunctionKey.
        :return: int
        """
        return int(self._read('KeyboardFunctionKey', 0))

    @pyqtSlot(int)
    def setKeyboardFunctionKey(self, keyboardFunctionKey):
        """
        :param keyboardFunctionKey: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('KeyboardFunctionKey', int(keyboardFunctionKey), 'int')

    def getKeyBoardLayoutStr(self):
        """
        Active input locale identifier (keyboard layout) to use (write-only).
        ActiveX property: KeyBoardLayoutStr.
        :return: str | unicode | QString
        """
        return toText(self._read('KeyBoardLayoutStr', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setKeyBoardLayoutStr(self, keyBoardLayoutStr):
        """
        :param keyBoardLayoutStr: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('KeyBoardLayoutStr', toText(keyBoardLayoutStr), 'QString')

    def getKeyboardSubType(self):
        """
        Specifies the keyboard subtype.
        ActiveX property: KeyboardSubType.
        :return: int
        """
        return int(self._read('KeyboardSubType', 0))

    @pyqtSlot(int)
    def setKeyboardSubType(self, keyboardSubType):
        """
        :param keyboardSubType: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('KeyboardSubType', int(keyboardSubType), 'int')

    def getKeyboardType(self):
        """
        Specifies the keyboard type.
        ActiveX property: KeyboardType.
        :return: int
        """
        return int(self._read('KeyboardType', 0))

    @pyqtSlot(int)
    def setKeyboardType(self, keyboardType):
        """
        :param keyboardType: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('KeyboardType', int(keyboardType), 'int')

    def getLoadBalanceInfo(self):
        """
        Load balancing cookie placed in the X.224 Connection Request packet.
        ActiveX property: LoadBalanceInfo.
        :return: str | unicode | QString
        """
        return toText(self._read('LoadBalanceInfo', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setLoadBalanceInfo(self, loadBalanceInfo):
        """
        :param loadBalanceInfo: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('LoadBalanceInfo', toText(loadBalanceInfo), 'QString')

    def getMaxEventCount(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: maxEventCount.
        :return: int
        """
        return int(self._read('maxEventCount', 0))

    @pyqtSlot(int)
    def setMaxEventCount(self, maxEventCount):
        """
        :param maxEventCount: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('maxEventCount', int(maxEventCount), 'int')

    def getMaximizeShell(self):
        """
        Specifies if programs launched with StartProgram should be maximized.
        ActiveX property: MaximizeShell.
        :return: int
        """
        return int(self._read('MaximizeShell', 0))

    @pyqtSlot(int)
    def setMaximizeShell(self, maximizeShell):
        """
        :param maximizeShell: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('MaximizeShell', int(maximizeShell), 'int')

    def getMinInputSendInterval(self):
        """
        Minimum interval, in ms, between the sending of mouse events.
        ActiveX property: minInputSendInterval.
        :return: int
        """
        return int(self._read('minInputSendInterval', 0))

    @pyqtSlot(int)
    def setMinInputSendInterval(self, minInputSendInterval):
        """
        :param minInputSendInterval: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('minInputSendInterval', int(minInputSendInterval), 'int')

    def getMinutesToIdleTimeout(self):
        """
        Maximum time, in minutes, to stay connected without user input (0 to 240).
        ActiveX property: MinutesToIdleTimeout.
        :return: int
        """
        return int(self._read('MinutesToIdleTimeout', 0))

    @pyqtSlot(int)
    def setMinutesToIdleTimeout(self, minutesToIdleTimeout):
        """
        :param minutesToIdleTimeout: int
        :return: bool, True if the control accepted the value.
        """
        minutesToIdleTimeout = clamp(int(minutesToIdleTimeout), 0, 240)  # type: int
        return self._write('MinutesToIdleTimeout', minutesToIdleTimeout, 'int')

    def isNotifyTSPublicKey(self):
        """
        Specifies whether receivedTSPublicKey is emitted during connection.
        ActiveX property: NotifyTSPublicKey.
        :return: bool
        """
        return bool(self._read('NotifyTSPublicKey', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setNotifyTSPublicKey(self, notifyTSPublicKey):
        """
        :param notifyTSPublicKey: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('NotifyTSPublicKey', bool(notifyTSPublicKey), 'bool')

    def getNumBitmapCaches(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: NumBitmapCaches.
        :return: int
        """
        return int(self._read('NumBitmapCaches', 0))

    @pyqtSlot(int)
    def setNumBitmapCaches(self, numBitmapCaches):
        """
        :param numBitmapCaches: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('NumBitmapCaches', int(numBitmapCaches), 'int')

    def getOrderDrawThreshold(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: orderDrawThreshold.
        :return: int
        """
        return int(self._read('orderDrawThreshold', 0))

    @pyqtSlot(int)
    def setOrderDrawThreshold(self, orderDrawThreshold):
        """
        :param orderDrawThreshold: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('orderDrawThreshold', int(orderDrawThreshold), 'int')

    def getOverallConnectionTimeout(self):
        """
        Total time, in seconds, the control waits for a connection to complete (0 to 600).
        ActiveX property: overallConnectionTimeout.
        :return: int
        """
        return int(self._read('overallConnectionTimeout', 120))

    @pyqtSlot(int)
    def setOverallConnectionTimeout(self, overallConnectionTimeout):
        """
        :param overallConnectionTimeout: int
        :return: bool, True if the control accepted the value.
        """
        overallConnectionTimeout = clamp(int(overallConnectionTimeout), 0, 600)  # type: int
        return self._write('overallConnectionTimeout', overallConnectionTimeout, 'int')

    def getPerformanceFlags(self):
        """
        Set of features that can be set at the server to improve performance.
        ActiveX property: PerformanceFlags.
        :return: int
        """
        return int(self._read('PerformanceFlags', 0))

    @pyqtSlot(int)
    def setPerformanceFlags(self, performanceFlags):
        """
        :param performanceFlags: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('PerformanceFlags', int(performanceFlags), 'int')

    def getPersistCacheDirectory(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: PersistCacheDirectory.
        :return: str | unicode | QString
        """
        return toText(self._read('PersistCacheDirectory', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPersistCacheDirectory(self, persistCacheDirectory):
        """
        :param persistCacheDirectory: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('PersistCacheDirectory', toText(persistCacheDirectory), 'QString')

    def isPinConnectionBar(self):
        """
        State of the connection bar: True = pinned, False = auto-hide.
        ActiveX property: PinConnectionBar.
        :return: bool
        """
        return bool(self._read('PinConnectionBar', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setPinConnectionBar(self, pinConnectionBar):
        """
        :param pinConnectionBar: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('PinConnectionBar', bool(pinConnectionBar), 'bool')

    def getPluginDlls(self):
        """
        Names of virtual channel client DLLs to be loaded (write-only).
        ActiveX property: PluginDlls.
        :return: str | unicode | QString
        """
        return toText(self._read('PluginDlls', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPluginDlls(self, pluginDlls):
        """
        :param pluginDlls: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('PluginDlls', toText(pluginDlls), 'QString')

    def getRdpdrClipCleanTempDirString(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: RdpdrClipCleanTempDirString.
        :return: str | unicode | QString
        """
        return toText(self._read('RdpdrClipCleanTempDirString', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRdpdrClipCleanTempDirString(self, rdpdrClipCleanTempDirString):
        """
        :param rdpdrClipCleanTempDirString: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RdpdrClipCleanTempDirString', toText(rdpdrClipCleanTempDirString), 'QString')

    def getRdpdrClipPasteInfoString(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: RdpdrClipPasteInfoString.
        :return: str | unicode | QString
        """
        return toText(self._read('RdpdrClipPasteInfoString', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRdpdrClipPasteInfoString(self, rdpdrClipPasteInfoString):
        """
        :param rdpdrClipPasteInfoString: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RdpdrClipPasteInfoString', toText(rdpdrClipPasteInfoString), 'QString')

    def getRdpdrLocalPrintingDocName(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: RdpdrLocalPrintingDocName.
        :return: str | unicode | QString
        """
        return toText(self._read('RdpdrLocalPrintingDocName', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRdpdrLocalPrintingDocName(self, rdpdrLocalPrintingDocName):
        """
        :param rdpdrLocalPrintingDocName: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RdpdrLocalPrintingDocName', toText(rdpdrLocalPrintingDocName), 'QString')

    def getRdpPort(self):
        """
        Connection port (default 3389).
        ActiveX property: RDPPort.
        :return: int
        """
        return int(self._read('RDPPort', 3389))

    @pyqtSlot(int)
    def setRdpPort(self, rdpPort):
        """
        :param rdpPort: int
        :return: bool, True if the control accepted the value.
        """
        rdpPort = clamp(int(rdpPort), 1, 65535)  # type: int
        return self._write('RDPPort', rdpPort, 'int')

    def isRedirectDrives(self):
        """
        Specifies if redirection of disk drives is allowed.
        ActiveX property: RedirectDrives.
        :return: bool
        """
        return bool(self._read('RedirectDrives', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectDrives(self, redirectDrives):
        """
        :param redirectDrives: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectDrives', bool(redirectDrives), 'bool')

    def isRedirectPorts(self):
        """
        Specifies if redirection of local ports (COM, LPT) is allowed.
        ActiveX property: RedirectPorts.
        :return: bool
        """
        return bool(self._read('RedirectPorts', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectPorts(self, redirectPorts):
        """
        :param redirectPorts: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectPorts', bool(redirectPorts), 'bool')

    def isRedirectPrinters(self):
        """
        Specifies if redirection of printers is allowed.
        ActiveX property: RedirectPrinters.
        :return: bool
        """
        return bool(self._read('RedirectPrinters', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectPrinters(self, redirectPrinters):
        """
        :param redirectPrinters: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectPrinters', bool(redirectPrinters), 'bool')

    def isRedirectSmartCards(self):
        """
        Specifies if redirection of smart cards is allowed.
        ActiveX property: RedirectSmartCards.
        :return: bool
        """
        return bool(self._read('RedirectSmartCards', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectSmartCards(self, redirectSmartCards):
        """
        :param redirectSmartCards: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectSmartCards', bool(redirectSmartCards), 'bool')

    def getSasSequence(self):
        """
        Secure access sequence (SAS) used to access the login screen.
        ActiveX property: SasSequence.
        :return: int
        """
        return int(self._read('SasSequence', 0))

    @pyqtSlot(int)
    def setSasSequence(self, sasSequence):
        """
        :param sasSequence: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('SasSequence', int(sasSequence), 'int')

    def getScaleBitmapCachesByBPP(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: ScaleBitmapCachesByBPP.
        :return: int
        """
        return int(self._read('ScaleBitmapCachesByBPP', 0))

    @pyqtSlot(int)
    def setScaleBitmapCachesByBPP(self, scaleBitmapCachesByBPP):
        """
        :param scaleBitmapCachesByBPP: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('ScaleBitmapCachesByBPP', int(scaleBitmapCachesByBPP), 'int')

    def getShadowBitmap(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: ShadowBitmap.
        :return: int
        """
        return int(self._read('ShadowBitmap', 0))

    @pyqtSlot(int)
    def setShadowBitmap(self, shadowBitmap):
        """
        :param shadowBitmap: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('ShadowBitmap', int(shadowBitmap), 'int')

    def getShutdownTimeout(self):
        """
        Time, in seconds, to wait for the server to answer a disconnection request (0 to 600).
        ActiveX property: shutdownTimeout.
        :return: int
        """
        return int(self._read('shutdownTimeout', 10))

    @pyqtSlot(int)
    def setShutdownTimeout(self, shutdownTimeout):
        """
        :param shutdownTimeout: int
        :return: bool, True if the control accepted the value.
        """
        shutdownTimeout = clamp(int(shutdownTimeout), 0, 600)  # type: int
        return self._write('shutdownTimeout', shutdownTimeout, 'int')

    def getSingleConnectionTimeout(self):
        """
        Maximum time, in seconds, to wait for a connection to one IP address (0 to 600).
        ActiveX property: singleConnectionTimeout.
        :return: int
        """
        return int(self._read('singleConnectionTimeout', 0))

    @pyqtSlot(int)
    def setSingleConnectionTimeout(self, singleConnectionTimeout):
        """
        :param singleConnectionTimeout: int
        :return: bool, True if the control accepted the value.
        """
        singleConnectionTimeout = clamp(int(singleConnectionTimeout), 0, 600)  # type: int
        return self._write('singleConnectionTimeout', singleConnectionTimeout, 'int')

    def isSmartSizing(self):
        """
        Scale the remote display to fit the client area of the control.
        ActiveX property: SmartSizing.
        :return: bool
        """
        return bool(self._read('SmartSizing', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setSmartSizing(self, smartSizing):
        """
        :param smartSizing: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('SmartSizing', bool(smartSizing), 'bool')

    def getSmoothScroll(self):
        """
        This property is not supported by recent versions of the control (kept for completeness).
        ActiveX property: SmoothScroll.
        :return: int
        """
        return int(self._read('SmoothScroll', 0))

    @pyqtSlot(int)
    def setSmoothScroll(self, smoothScroll):
        """
        :param smoothScroll: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('SmoothScroll', int(smoothScroll), 'int')

    def getTransportType(self):
        """
        Transport type used by the client (not used by the ActiveX control).
        ActiveX property: TransportType.
        :return: int
        """
        return int(self._read('TransportType', 0))

    @pyqtSlot(int)
    def setTransportType(self, transportType):
        """
        :param transportType: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('TransportType', int(transportType), 'int')

    def getWinceFixedPalette(self):
        """
        Valid for Windows CE only.
        ActiveX property: WinceFixedPalette.
        :return: int
        """
        return int(self._read('WinceFixedPalette', 0))

    @pyqtSlot(int)
    def setWinceFixedPalette(self, winceFixedPalette):
        """
        :param winceFixedPalette: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('WinceFixedPalette', int(winceFixedPalette), 'int')

    # ---------- Properties ----------
    acceleratorPassthrough = pyqtProperty(bool, fget=isAcceleratorPassthrough,
                                          fset=setAcceleratorPassthrough)  # type: pyqtProperty
    allowBackgroundInput = pyqtProperty(int, fget=getAllowBackgroundInput,
                                        fset=setAllowBackgroundInput)  # type: pyqtProperty
    bitmapCacheSize = pyqtProperty(int, fget=getBitmapCacheSize, fset=setBitmapCacheSize)  # type: pyqtProperty
    bitmapPeristence = pyqtProperty(int, fget=getBitmapPeristence, fset=setBitmapPeristence)  # type: pyqtProperty
    bitmapPersistence = pyqtProperty(int, fget=getBitmapPersistence, fset=setBitmapPersistence)  # type: pyqtProperty
    bitmapVirtualCache16BppSize = pyqtProperty(int, fget=getBitmapVirtualCache16BppSize,
                                               fset=setBitmapVirtualCache16BppSize)  # type: pyqtProperty
    bitmapVirtualCache24BppSize = pyqtProperty(int, fget=getBitmapVirtualCache24BppSize,
                                               fset=setBitmapVirtualCache24BppSize)  # type: pyqtProperty
    bitmapVirtualCacheSize = pyqtProperty(int, fget=getBitmapVirtualCacheSize,
                                          fset=setBitmapVirtualCacheSize)  # type: pyqtProperty
    brushSupportLevel = pyqtProperty(int, fget=getBrushSupportLevel, fset=setBrushSupportLevel)  # type: pyqtProperty
    cachePersistenceActive = pyqtProperty(int, fget=getCachePersistenceActive,
                                          fset=setCachePersistenceActive)  # type: pyqtProperty
    clearTextPassword = pyqtProperty('QString', fget=getClearTextPassword, fset=setClearTextPassword)  # type: pyqtProperty
    compress = pyqtProperty(int, fget=getCompress, fset=setCompress)  # type: pyqtProperty
    connectToServerConsole = pyqtProperty(bool, fget=isConnectToServerConsole,
                                          fset=setConnectToServerConsole)  # type: pyqtProperty
    connectWithEndpoint = pyqtProperty(int, fget=getConnectWithEndpoint,
                                       fset=setConnectWithEndpoint)  # type: pyqtProperty
    containerHandledFullScreen = pyqtProperty(int, fget=getContainerHandledFullScreen,
                                              fset=setContainerHandledFullScreen)  # type: pyqtProperty
    dedicatedTerminal = pyqtProperty(int, fget=getDedicatedTerminal, fset=setDedicatedTerminal)  # type: pyqtProperty
    disableCtrlAltDel = pyqtProperty(int, fget=getDisableCtrlAltDel, fset=setDisableCtrlAltDel)  # type: pyqtProperty
    disableRdpdr = pyqtProperty(int, fget=getDisableRdpdr, fset=setDisableRdpdr)  # type: pyqtProperty
    displayConnectionBar = pyqtProperty(bool, fget=isDisplayConnectionBar,
                                        fset=setDisplayConnectionBar)  # type: pyqtProperty
    doubleClickDetect = pyqtProperty(int, fget=getDoubleClickDetect, fset=setDoubleClickDetect)  # type: pyqtProperty
    enableMouse = pyqtProperty(int, fget=getEnableMouse, fset=setEnableMouse)  # type: pyqtProperty
    enableWindowsKey = pyqtProperty(int, fget=getEnableWindowsKey, fset=setEnableWindowsKey)  # type: pyqtProperty
    encryptionEnabled = pyqtProperty(int, fget=getEncryptionEnabled, fset=setEncryptionEnabled)  # type: pyqtProperty
    grabFocusOnConnect = pyqtProperty(bool, fget=isGrabFocusOnConnect, fset=setGrabFocusOnConnect)  # type: pyqtProperty
    hotKeyAltEsc = pyqtProperty(int, fget=getHotKeyAltEsc, fset=setHotKeyAltEsc)  # type: pyqtProperty
    hotKeyAltShiftTab = pyqtProperty(int, fget=getHotKeyAltShiftTab, fset=setHotKeyAltShiftTab)  # type: pyqtProperty
    hotKeyAltSpace = pyqtProperty(int, fget=getHotKeyAltSpace, fset=setHotKeyAltSpace)  # type: pyqtProperty
    hotKeyAltTab = pyqtProperty(int, fget=getHotKeyAltTab, fset=setHotKeyAltTab)  # type: pyqtProperty
    hotKeyCtrlAltDel = pyqtProperty(int, fget=getHotKeyCtrlAltDel, fset=setHotKeyCtrlAltDel)  # type: pyqtProperty
    hotKeyCtrlEsc = pyqtProperty(int, fget=getHotKeyCtrlEsc, fset=setHotKeyCtrlEsc)  # type: pyqtProperty
    hotKeyFullScreen = pyqtProperty(int, fget=getHotKeyFullScreen, fset=setHotKeyFullScreen)  # type: pyqtProperty
    iconFile = pyqtProperty('QString', fget=getIconFile, fset=setIconFile)  # type: pyqtProperty
    iconIndex = pyqtProperty(int, fget=getIconIndex, fset=setIconIndex)  # type: pyqtProperty
    inputEventsAtOnce = pyqtProperty(int, fget=getInputEventsAtOnce, fset=setInputEventsAtOnce)  # type: pyqtProperty
    keepAliveInterval = pyqtProperty(int, fget=getKeepAliveInterval, fset=setKeepAliveInterval)  # type: pyqtProperty
    keyboardFunctionKey = pyqtProperty(int, fget=getKeyboardFunctionKey,
                                       fset=setKeyboardFunctionKey)  # type: pyqtProperty
    keyBoardLayoutStr = pyqtProperty('QString', fget=getKeyBoardLayoutStr, fset=setKeyBoardLayoutStr)  # type: pyqtProperty
    keyboardSubType = pyqtProperty(int, fget=getKeyboardSubType, fset=setKeyboardSubType)  # type: pyqtProperty
    keyboardType = pyqtProperty(int, fget=getKeyboardType, fset=setKeyboardType)  # type: pyqtProperty
    loadBalanceInfo = pyqtProperty('QString', fget=getLoadBalanceInfo, fset=setLoadBalanceInfo)  # type: pyqtProperty
    maxEventCount = pyqtProperty(int, fget=getMaxEventCount, fset=setMaxEventCount)  # type: pyqtProperty
    maximizeShell = pyqtProperty(int, fget=getMaximizeShell, fset=setMaximizeShell)  # type: pyqtProperty
    minInputSendInterval = pyqtProperty(int, fget=getMinInputSendInterval,
                                        fset=setMinInputSendInterval)  # type: pyqtProperty
    minutesToIdleTimeout = pyqtProperty(int, fget=getMinutesToIdleTimeout,
                                        fset=setMinutesToIdleTimeout)  # type: pyqtProperty
    notifyTSPublicKey = pyqtProperty(bool, fget=isNotifyTSPublicKey, fset=setNotifyTSPublicKey)  # type: pyqtProperty
    numBitmapCaches = pyqtProperty(int, fget=getNumBitmapCaches, fset=setNumBitmapCaches)  # type: pyqtProperty
    orderDrawThreshold = pyqtProperty(int, fget=getOrderDrawThreshold, fset=setOrderDrawThreshold)  # type: pyqtProperty
    overallConnectionTimeout = pyqtProperty(int, fget=getOverallConnectionTimeout,
                                            fset=setOverallConnectionTimeout)  # type: pyqtProperty
    performanceFlags = pyqtProperty(int, fget=getPerformanceFlags, fset=setPerformanceFlags)  # type: pyqtProperty
    persistCacheDirectory = pyqtProperty('QString', fget=getPersistCacheDirectory,
                                         fset=setPersistCacheDirectory)  # type: pyqtProperty
    pinConnectionBar = pyqtProperty(bool, fget=isPinConnectionBar, fset=setPinConnectionBar)  # type: pyqtProperty
    pluginDlls = pyqtProperty('QString', fget=getPluginDlls, fset=setPluginDlls)  # type: pyqtProperty
    rdpdrClipCleanTempDirString = pyqtProperty('QString', fget=getRdpdrClipCleanTempDirString,
                                               fset=setRdpdrClipCleanTempDirString)  # type: pyqtProperty
    rdpdrClipPasteInfoString = pyqtProperty('QString', fget=getRdpdrClipPasteInfoString,
                                            fset=setRdpdrClipPasteInfoString)  # type: pyqtProperty
    rdpdrLocalPrintingDocName = pyqtProperty('QString', fget=getRdpdrLocalPrintingDocName,
                                             fset=setRdpdrLocalPrintingDocName)  # type: pyqtProperty
    rdpPort = pyqtProperty(int, fget=getRdpPort, fset=setRdpPort)  # type: pyqtProperty
    redirectDrives = pyqtProperty(bool, fget=isRedirectDrives, fset=setRedirectDrives)  # type: pyqtProperty
    redirectPorts = pyqtProperty(bool, fget=isRedirectPorts, fset=setRedirectPorts)  # type: pyqtProperty
    redirectPrinters = pyqtProperty(bool, fget=isRedirectPrinters, fset=setRedirectPrinters)  # type: pyqtProperty
    redirectSmartCards = pyqtProperty(bool, fget=isRedirectSmartCards, fset=setRedirectSmartCards)  # type: pyqtProperty
    sasSequence = pyqtProperty(int, fget=getSasSequence, fset=setSasSequence)  # type: pyqtProperty
    scaleBitmapCachesByBPP = pyqtProperty(int, fget=getScaleBitmapCachesByBPP,
                                          fset=setScaleBitmapCachesByBPP)  # type: pyqtProperty
    shadowBitmap = pyqtProperty(int, fget=getShadowBitmap, fset=setShadowBitmap)  # type: pyqtProperty
    shutdownTimeout = pyqtProperty(int, fget=getShutdownTimeout, fset=setShutdownTimeout)  # type: pyqtProperty
    singleConnectionTimeout = pyqtProperty(int, fget=getSingleConnectionTimeout,
                                           fset=setSingleConnectionTimeout)  # type: pyqtProperty
    smartSizing = pyqtProperty(bool, fget=isSmartSizing, fset=setSmartSizing)  # type: pyqtProperty
    smoothScroll = pyqtProperty(int, fget=getSmoothScroll, fset=setSmoothScroll)  # type: pyqtProperty
    transportType = pyqtProperty(int, fget=getTransportType, fset=setTransportType)  # type: pyqtProperty
    winceFixedPalette = pyqtProperty(int, fget=getWinceFixedPalette, fset=setWinceFixedPalette)  # type: pyqtProperty


class RdpAdvancedSettings2(RdpSettingsInterface):
    """
    Automatic reconnection settings (IMsRdpClientAdvancedSettings2, the "AdvancedSettings2" sub-object).
    """
    INTERFACE = 'AdvancedSettings2'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings2'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('canAutoReconnect', 'CanAutoReconnect', 'bool', 'r'),
        ('enableAutoReconnect', 'EnableAutoReconnect', 'bool', 'rw'),
        ('maxReconnectAttempts', 'MaxReconnectAttempts', 'int', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getCanAutoReconnect(self):
        """
        Whether the control can reconnect automatically to the current session (read-only).
        ActiveX property: CanAutoReconnect.
        :return: bool
        """
        return bool(self._read('CanAutoReconnect', False))

    def isEnableAutoReconnect(self):
        """
        Enable automatic reconnection in the event of a network disconnection.
        ActiveX property: EnableAutoReconnect.
        :return: bool
        """
        return bool(self._read('EnableAutoReconnect', True))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setEnableAutoReconnect(self, enableAutoReconnect):
        """
        :param enableAutoReconnect: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('EnableAutoReconnect', bool(enableAutoReconnect), 'bool')

    def getMaxReconnectAttempts(self):
        """
        Number of times to try to reconnect during automatic reconnection (0 to 200).
        ActiveX property: MaxReconnectAttempts.
        :return: int
        """
        return int(self._read('MaxReconnectAttempts', 20))

    @pyqtSlot(int)
    def setMaxReconnectAttempts(self, maxReconnectAttempts):
        """
        :param maxReconnectAttempts: int
        :return: bool, True if the control accepted the value.
        """
        maxReconnectAttempts = clamp(int(maxReconnectAttempts), 0, 200)  # type: int
        return self._write('MaxReconnectAttempts', maxReconnectAttempts, 'int')

    # ---------- Properties ----------
    canAutoReconnect = pyqtProperty(bool, fget=getCanAutoReconnect)  # type: pyqtProperty
    enableAutoReconnect = pyqtProperty(bool, fget=isEnableAutoReconnect,
                                       fset=setEnableAutoReconnect)  # type: pyqtProperty
    maxReconnectAttempts = pyqtProperty(int, fget=getMaxReconnectAttempts,
                                        fset=setMaxReconnectAttempts)  # type: pyqtProperty


class RdpAdvancedSettings3(RdpSettingsInterface):
    """
    Connection bar buttons (IMsRdpClientAdvancedSettings3, the "AdvancedSettings3" sub-object).
    """
    INTERFACE = 'AdvancedSettings3'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings3'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('connectionBarShowMinimizeButton', 'ConnectionBarShowMinimizeButton', 'bool', 'rw'),
        ('connectionBarShowRestoreButton', 'ConnectionBarShowRestoreButton', 'bool', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def isConnectionBarShowMinimizeButton(self):
        """
        Display the Minimize button on the connection bar.
        ActiveX property: ConnectionBarShowMinimizeButton.
        :return: bool
        """
        return bool(self._read('ConnectionBarShowMinimizeButton', True))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setConnectionBarShowMinimizeButton(self, connectionBarShowMinimizeButton):
        """
        :param connectionBarShowMinimizeButton: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectionBarShowMinimizeButton', bool(connectionBarShowMinimizeButton), 'bool')

    def isConnectionBarShowRestoreButton(self):
        """
        Display the Restore button on the connection bar.
        ActiveX property: ConnectionBarShowRestoreButton.
        :return: bool
        """
        return bool(self._read('ConnectionBarShowRestoreButton', True))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setConnectionBarShowRestoreButton(self, connectionBarShowRestoreButton):
        """
        :param connectionBarShowRestoreButton: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectionBarShowRestoreButton', bool(connectionBarShowRestoreButton), 'bool')

    # ---------- Properties ----------
    connectionBarShowMinimizeButton = pyqtProperty(bool, fget=isConnectionBarShowMinimizeButton,
                                                   fset=setConnectionBarShowMinimizeButton)  # type: pyqtProperty
    connectionBarShowRestoreButton = pyqtProperty(bool, fget=isConnectionBarShowRestoreButton,
                                                  fset=setConnectionBarShowRestoreButton)  # type: pyqtProperty


class RdpAdvancedSettings4(RdpSettingsInterface):
    """
    Server authentication level (IMsRdpClientAdvancedSettings4, the "AdvancedSettings4" sub-object).
    """
    INTERFACE = 'AdvancedSettings4'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings4'  # type: str

    class AuthenticationLevel(IntEnum):
        """
        AuthenticationLevel enumeration class.
        """
        NoAuthentication = 0  # type: int
        AuthenticationRequired = 1  # type: int
        AuthenticationWarn = 2  # type: int

    NoAuthentication = AuthenticationLevel.NoAuthentication  # type: int
    AuthenticationRequired = AuthenticationLevel.AuthenticationRequired  # type: int
    AuthenticationWarn = AuthenticationLevel.AuthenticationWarn  # type: int

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('authenticationLevel', 'AuthenticationLevel', 'int', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getAuthenticationLevel(self):
        """
        Authentication level (see RdpAdvancedSettings4.AuthenticationLevel).
        ActiveX property: AuthenticationLevel.
        :return: int
        """
        return int(self._read('AuthenticationLevel', 0))

    @pyqtSlot(int)
    def setAuthenticationLevel(self, authenticationLevel):
        """
        :param authenticationLevel: int
        :return: bool, True if the control accepted the value.
        """
        authenticationLevel = clamp(int(authenticationLevel), 0, 2)  # type: int
        return self._write('AuthenticationLevel', authenticationLevel, 'int')

    # ---------- Properties ----------
    authenticationLevel = pyqtProperty(int, fget=getAuthenticationLevel,
                                       fset=setAuthenticationLevel)  # type: pyqtProperty


class RdpAdvancedSettings5(RdpSettingsInterface):
    """
    Audio, clipboard, devices and public mode (IMsRdpClientAdvancedSettings5, the "AdvancedSettings5" sub-
    object).
    """
    INTERFACE = 'AdvancedSettings5'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings5'  # type: str

    class AudioRedirectionMode(IntEnum):
        """
        AudioRedirectionMode enumeration class.
        """
        RedirectToClient = 0  # type: int
        PlayOnServer = 1  # type: int
        DoNotPlay = 2  # type: int

    RedirectToClient = AudioRedirectionMode.RedirectToClient  # type: int
    PlayOnServer = AudioRedirectionMode.PlayOnServer  # type: int
    DoNotPlay = AudioRedirectionMode.DoNotPlay  # type: int

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('audioRedirectionMode', 'AudioRedirectionMode', 'int', 'rw'),
        ('bitmapVirtualCache32BppSize', 'BitmapVirtualCache32BppSize', 'int', 'rw'),
        ('connectionBarShowPinButton', 'ConnectionBarShowPinButton', 'bool', 'rw'),
        ('publicMode', 'PublicMode', 'bool', 'rw'),
        ('redirectClipboard', 'RedirectClipboard', 'bool', 'rw'),
        ('redirectDevices', 'RedirectDevices', 'bool', 'rw'),
        ('redirectPOSDevices', 'RedirectPOSDevices', 'bool', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getAudioRedirectionMode(self):
        """
        Audio redirection mode (see RdpAdvancedSettings5.AudioRedirectionMode).
        ActiveX property: AudioRedirectionMode.
        :return: int
        """
        return int(self._read('AudioRedirectionMode', 0))

    @pyqtSlot(int)
    def setAudioRedirectionMode(self, audioRedirectionMode):
        """
        :param audioRedirectionMode: int
        :return: bool, True if the control accepted the value.
        """
        audioRedirectionMode = clamp(int(audioRedirectionMode), 0, 2)  # type: int
        return self._write('AudioRedirectionMode', audioRedirectionMode, 'int')

    def getBitmapVirtualCache32BppSize(self):
        """
        Virtual cache file size for 32 bpp bitmaps.
        ActiveX property: BitmapVirtualCache32BppSize.
        :return: int
        """
        return int(self._read('BitmapVirtualCache32BppSize', 0))

    @pyqtSlot(int)
    def setBitmapVirtualCache32BppSize(self, bitmapVirtualCache32BppSize):
        """
        :param bitmapVirtualCache32BppSize: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('BitmapVirtualCache32BppSize', int(bitmapVirtualCache32BppSize), 'int')

    def isConnectionBarShowPinButton(self):
        """
        Display the pin button on the connection bar.
        ActiveX property: ConnectionBarShowPinButton.
        :return: bool
        """
        return bool(self._read('ConnectionBarShowPinButton', True))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setConnectionBarShowPinButton(self, connectionBarShowPinButton):
        """
        :param connectionBarShowPinButton: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectionBarShowPinButton', bool(connectionBarShowPinButton), 'bool')

    def isPublicMode(self):
        """
        Public mode prevents the client from caching user data to the local system.
        ActiveX property: PublicMode.
        :return: bool
        """
        return bool(self._read('PublicMode', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setPublicMode(self, publicMode):
        """
        :param publicMode: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('PublicMode', bool(publicMode), 'bool')

    def isRedirectClipboard(self):
        """
        Clipboard redirection.
        ActiveX property: RedirectClipboard.
        :return: bool
        """
        return bool(self._read('RedirectClipboard', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectClipboard(self, redirectClipboard):
        """
        :param redirectClipboard: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectClipboard', bool(redirectClipboard), 'bool')

    def isRedirectDevices(self):
        """
        Device redirection.
        ActiveX property: RedirectDevices.
        :return: bool
        """
        return bool(self._read('RedirectDevices', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectDevices(self, redirectDevices):
        """
        :param redirectDevices: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectDevices', bool(redirectDevices), 'bool')

    def isRedirectPOSDevices(self):
        """
        Point of Service device redirection.
        ActiveX property: RedirectPOSDevices.
        :return: bool
        """
        return bool(self._read('RedirectPOSDevices', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectPOSDevices(self, redirectPOSDevices):
        """
        :param redirectPOSDevices: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectPOSDevices', bool(redirectPOSDevices), 'bool')

    # ---------- Properties ----------
    audioRedirectionMode = pyqtProperty(int, fget=getAudioRedirectionMode,
                                        fset=setAudioRedirectionMode)  # type: pyqtProperty
    bitmapVirtualCache32BppSize = pyqtProperty(int, fget=getBitmapVirtualCache32BppSize,
                                               fset=setBitmapVirtualCache32BppSize)  # type: pyqtProperty
    connectionBarShowPinButton = pyqtProperty(bool, fget=isConnectionBarShowPinButton,
                                              fset=setConnectionBarShowPinButton)  # type: pyqtProperty
    publicMode = pyqtProperty(bool, fget=isPublicMode, fset=setPublicMode)  # type: pyqtProperty
    redirectClipboard = pyqtProperty(bool, fget=isRedirectClipboard, fset=setRedirectClipboard)  # type: pyqtProperty
    redirectDevices = pyqtProperty(bool, fget=isRedirectDevices, fset=setRedirectDevices)  # type: pyqtProperty
    redirectPOSDevices = pyqtProperty(bool, fget=isRedirectPOSDevices, fset=setRedirectPOSDevices)  # type: pyqtProperty


class RdpAdvancedSettings6(RdpSettingsInterface):
    """
    Authentication and focus settings (IMsRdpClientAdvancedSettings6, the "AdvancedSettings6" sub-object).
    """
    INTERFACE = 'AdvancedSettings6'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings6'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('authenticationServiceClass', 'AuthenticationServiceClass', 'QString', 'rw'),
        ('authenticationType', 'AuthenticationType', 'int', 'r'),
        ('connectToAdministerServer', 'ConnectToAdministerServer', 'bool', 'rw'),
        ('enableCredSspSupport', 'EnableCredSspSupport', 'bool', 'rw'),
        ('hotKeyFocusReleaseLeft', 'HotKeyFocusReleaseLeft', 'int', 'rw'),
        ('hotKeyFocusReleaseRight', 'HotKeyFocusReleaseRight', 'int', 'rw'),
        ('pcb', 'PCB', 'QString', 'rw'),
        ('relativeMouseMode', 'RelativeMouseMode', 'bool', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getAuthenticationServiceClass(self):
        """
        Service principal name (SPN) used for authentication.
        ActiveX property: AuthenticationServiceClass.
        :return: str | unicode | QString
        """
        return toText(self._read('AuthenticationServiceClass', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setAuthenticationServiceClass(self, authenticationServiceClass):
        """
        :param authenticationServiceClass: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('AuthenticationServiceClass', toText(authenticationServiceClass), 'QString')

    def getAuthenticationType(self):
        """
        Type of authentication used for this connection (read-only).
        ActiveX property: AuthenticationType.
        :return: int
        """
        return int(self._read('AuthenticationType', 0))

    def isConnectToAdministerServer(self):
        """
        Connect to the server for administrative purposes.
        ActiveX property: ConnectToAdministerServer.
        :return: bool
        """
        return bool(self._read('ConnectToAdministerServer', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setConnectToAdministerServer(self, connectToAdministerServer):
        """
        :param connectToAdministerServer: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('ConnectToAdministerServer', bool(connectToAdministerServer), 'bool')

    def isEnableCredSspSupport(self):
        """
        Enable the Credential Security Service Provider (CredSSP / NLA).
        ActiveX property: EnableCredSspSupport.
        :return: bool
        """
        return bool(self._read('EnableCredSspSupport', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setEnableCredSspSupport(self, enableCredSspSupport):
        """
        :param enableCredSspSupport: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('EnableCredSspSupport', bool(enableCredSspSupport), 'bool')

    def getHotKeyFocusReleaseLeft(self):
        """
        Virtual-key added to CTRL+ALT to replace CTRL+ALT+LEFT ARROW.
        ActiveX property: HotKeyFocusReleaseLeft.
        :return: int
        """
        return int(self._read('HotKeyFocusReleaseLeft', 0))

    @pyqtSlot(int)
    def setHotKeyFocusReleaseLeft(self, hotKeyFocusReleaseLeft):
        """
        :param hotKeyFocusReleaseLeft: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyFocusReleaseLeft', int(hotKeyFocusReleaseLeft), 'int')

    def getHotKeyFocusReleaseRight(self):
        """
        Virtual-key added to CTRL+ALT to replace CTRL+ALT+RIGHT ARROW.
        ActiveX property: HotKeyFocusReleaseRight.
        :return: int
        """
        return int(self._read('HotKeyFocusReleaseRight', 0))

    @pyqtSlot(int)
    def setHotKeyFocusReleaseRight(self, hotKeyFocusReleaseRight):
        """
        :param hotKeyFocusReleaseRight: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('HotKeyFocusReleaseRight', int(hotKeyFocusReleaseRight), 'int')

    def getPcb(self):
        """
        Preconnection BLOB (PCB) sent to the server before connecting.
        ActiveX property: PCB.
        :return: str | unicode | QString
        """
        return toText(self._read('PCB', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPcb(self, pcb):
        """
        :param pcb: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('PCB', toText(pcb), 'QString')

    def isRelativeMouseMode(self):
        """
        True for relative mouse mode, False for absolute mode.
        ActiveX property: RelativeMouseMode.
        :return: bool
        """
        return bool(self._read('RelativeMouseMode', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRelativeMouseMode(self, relativeMouseMode):
        """
        :param relativeMouseMode: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RelativeMouseMode', bool(relativeMouseMode), 'bool')

    # ---------- Properties ----------
    authenticationServiceClass = pyqtProperty('QString', fget=getAuthenticationServiceClass,
                                              fset=setAuthenticationServiceClass)  # type: pyqtProperty
    authenticationType = pyqtProperty(int, fget=getAuthenticationType)  # type: pyqtProperty
    connectToAdministerServer = pyqtProperty(bool, fget=isConnectToAdministerServer,
                                             fset=setConnectToAdministerServer)  # type: pyqtProperty
    enableCredSspSupport = pyqtProperty(bool, fget=isEnableCredSspSupport,
                                        fset=setEnableCredSspSupport)  # type: pyqtProperty
    hotKeyFocusReleaseLeft = pyqtProperty(int, fget=getHotKeyFocusReleaseLeft,
                                          fset=setHotKeyFocusReleaseLeft)  # type: pyqtProperty
    hotKeyFocusReleaseRight = pyqtProperty(int, fget=getHotKeyFocusReleaseRight,
                                           fset=setHotKeyFocusReleaseRight)  # type: pyqtProperty
    pcb = pyqtProperty('QString', fget=getPcb, fset=setPcb)  # type: pyqtProperty
    relativeMouseMode = pyqtProperty(bool, fget=isRelativeMouseMode, fset=setRelativeMouseMode)  # type: pyqtProperty


class RdpAdvancedSettings7(RdpSettingsInterface):
    """
    Audio capture, network type, SuperPan and video playback (IMsRdpClientAdvancedSettings7, the
    "AdvancedSettings7" sub-object).
    """
    INTERFACE = 'AdvancedSettings7'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings7'  # type: str

    class AudioQualityMode(IntEnum):
        """
        AudioQualityMode enumeration class.
        """
        DynamicQuality = 0  # type: int
        MediumQuality = 1  # type: int
        HighQuality = 2  # type: int

    DynamicQuality = AudioQualityMode.DynamicQuality  # type: int
    MediumQuality = AudioQualityMode.MediumQuality  # type: int
    HighQuality = AudioQualityMode.HighQuality  # type: int

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('audioCaptureRedirectionMode', 'AudioCaptureRedirectionMode', 'bool', 'rw'),
        ('audioQualityMode', 'AudioQualityMode', 'int', 'rw'),
        ('enableSuperPan', 'EnableSuperPan', 'bool', 'rw'),
        ('networkConnectionType', 'NetworkConnectionType', 'uint', 'rw'),
        ('redirectDirectX', 'RedirectDirectX', 'bool', 'rw'),
        ('superPanAccelerationFactor', 'SuperPanAccelerationFactor', 'uint', 'rw'),
        ('videoPlaybackMode', 'VideoPlaybackMode', 'uint', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def isAudioCaptureRedirectionMode(self):
        """
        Redirect the default audio input device to the remote session.
        ActiveX property: AudioCaptureRedirectionMode.
        :return: bool
        """
        return bool(self._read('AudioCaptureRedirectionMode', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAudioCaptureRedirectionMode(self, audioCaptureRedirectionMode):
        """
        :param audioCaptureRedirectionMode: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('AudioCaptureRedirectionMode', bool(audioCaptureRedirectionMode), 'bool')

    def getAudioQualityMode(self):
        """
        Audio quality mode (see RdpAdvancedSettings7.AudioQualityMode).
        ActiveX property: AudioQualityMode.
        :return: int
        """
        return int(self._read('AudioQualityMode', 0))

    @pyqtSlot(int)
    def setAudioQualityMode(self, audioQualityMode):
        """
        :param audioQualityMode: int
        :return: bool, True if the control accepted the value.
        """
        audioQualityMode = clamp(int(audioQualityMode), 0, 2)  # type: int
        return self._write('AudioQualityMode', audioQualityMode, 'int')

    def isEnableSuperPan(self):
        """
        Enable SuperPan.
        ActiveX property: EnableSuperPan.
        :return: bool
        """
        return bool(self._read('EnableSuperPan', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setEnableSuperPan(self, enableSuperPan):
        """
        :param enableSuperPan: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('EnableSuperPan', bool(enableSuperPan), 'bool')

    def getNetworkConnectionType(self):
        """
        Network connection type.
        ActiveX property: NetworkConnectionType.
        :return: int
        """
        return int(self._read('NetworkConnectionType', 0))

    @pyqtSlot(int)
    def setNetworkConnectionType(self, networkConnectionType):
        """
        :param networkConnectionType: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('NetworkConnectionType', int(networkConnectionType), 'uint')

    def isRedirectDirectX(self):
        """
        This property is not used.
        ActiveX property: RedirectDirectX.
        :return: bool
        """
        return bool(self._read('RedirectDirectX', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRedirectDirectX(self, redirectDirectX):
        """
        :param redirectDirectX: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RedirectDirectX', bool(redirectDirectX), 'bool')

    def getSuperPanAccelerationFactor(self):
        """
        SuperPan acceleration factor.
        ActiveX property: SuperPanAccelerationFactor.
        :return: int
        """
        return int(self._read('SuperPanAccelerationFactor', 0))

    @pyqtSlot(int)
    def setSuperPanAccelerationFactor(self, superPanAccelerationFactor):
        """
        :param superPanAccelerationFactor: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('SuperPanAccelerationFactor', int(superPanAccelerationFactor), 'uint')

    def getVideoPlaybackMode(self):
        """
        Video playback mode.
        ActiveX property: VideoPlaybackMode.
        :return: int
        """
        return int(self._read('VideoPlaybackMode', 0))

    @pyqtSlot(int)
    def setVideoPlaybackMode(self, videoPlaybackMode):
        """
        :param videoPlaybackMode: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('VideoPlaybackMode', int(videoPlaybackMode), 'uint')

    # ---------- Properties ----------
    audioCaptureRedirectionMode = pyqtProperty(bool, fget=isAudioCaptureRedirectionMode,
                                               fset=setAudioCaptureRedirectionMode)  # type: pyqtProperty
    audioQualityMode = pyqtProperty(int, fget=getAudioQualityMode, fset=setAudioQualityMode)  # type: pyqtProperty
    enableSuperPan = pyqtProperty(bool, fget=isEnableSuperPan, fset=setEnableSuperPan)  # type: pyqtProperty
    networkConnectionType = pyqtProperty(int, fget=getNetworkConnectionType,
                                         fset=setNetworkConnectionType)  # type: pyqtProperty
    redirectDirectX = pyqtProperty(bool, fget=isRedirectDirectX, fset=setRedirectDirectX)  # type: pyqtProperty
    superPanAccelerationFactor = pyqtProperty(int, fget=getSuperPanAccelerationFactor,
                                              fset=setSuperPanAccelerationFactor)  # type: pyqtProperty
    videoPlaybackMode = pyqtProperty(int, fget=getVideoPlaybackMode, fset=setVideoPlaybackMode)  # type: pyqtProperty


class RdpAdvancedSettings8(RdpSettingsInterface):
    """
    Bandwidth detection (IMsRdpClientAdvancedSettings8, the "AdvancedSettings8" sub-object).
    """
    INTERFACE = 'AdvancedSettings8'  # type: str
    COM_INTERFACE = 'IMsRdpClientAdvancedSettings8'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('bandwidthDetection', 'BandwidthDetection', 'bool', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def isBandwidthDetection(self):
        """
        Specifies if bandwidth changes are automatically detected.
        ActiveX property: BandwidthDetection.
        :return: bool
        """
        return bool(self._read('BandwidthDetection', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setBandwidthDetection(self, bandwidthDetection):
        """
        :param bandwidthDetection: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('BandwidthDetection', bool(bandwidthDetection), 'bool')

    # ---------- Properties ----------
    bandwidthDetection = pyqtProperty(bool, fget=isBandwidthDetection, fset=setBandwidthDetection)  # type: pyqtProperty


class RdpSecuredSettings(RdpSettingsInterface):
    """
    Start program, keyboard hook, audio and full-screen state (IMsRdpClientSecuredSettings, the
    "SecuredSettings" sub-object).
    """
    INTERFACE = 'SecuredSettings'  # type: str
    COM_INTERFACE = 'IMsRdpClientSecuredSettings'  # type: str

    class KeyboardHookMode(IntEnum):
        """
        KeyboardHookMode enumeration class.
        """
        ApplyLocally = 0  # type: int
        ApplyRemotely = 1  # type: int
        ApplyInFullScreen = 2  # type: int

    class AudioRedirectionMode(IntEnum):
        """
        AudioRedirectionMode enumeration class.
        """
        RedirectToClient = 0  # type: int
        PlayOnServer = 1  # type: int
        DoNotPlay = 2  # type: int

    ApplyLocally = KeyboardHookMode.ApplyLocally  # type: int
    ApplyRemotely = KeyboardHookMode.ApplyRemotely  # type: int
    ApplyInFullScreen = KeyboardHookMode.ApplyInFullScreen  # type: int
    RedirectToClient = AudioRedirectionMode.RedirectToClient  # type: int
    PlayOnServer = AudioRedirectionMode.PlayOnServer  # type: int
    DoNotPlay = AudioRedirectionMode.DoNotPlay  # type: int

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('audioRedirectionMode', 'AudioRedirectionMode', 'int', 'rw'),
        ('fullScreen', 'FullScreen', 'int', 'rw'),
        ('keyboardHookMode', 'KeyboardHookMode', 'int', 'rw'),
        ('startProgram', 'StartProgram', 'QString', 'rw'),
        ('workDir', 'WorkDir', 'QString', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getAudioRedirectionMode(self):
        """
        Redirect sounds or play them on the server (see RdpSecuredSettings.AudioRedirectionMode).
        ActiveX property: AudioRedirectionMode.
        :return: int
        """
        return int(self._read('AudioRedirectionMode', 0))

    @pyqtSlot(int)
    def setAudioRedirectionMode(self, audioRedirectionMode):
        """
        :param audioRedirectionMode: int
        :return: bool, True if the control accepted the value.
        """
        audioRedirectionMode = clamp(int(audioRedirectionMode), 0, 2)  # type: int
        return self._write('AudioRedirectionMode', audioRedirectionMode, 'int')

    def getFullScreen(self):
        """
        Full-screen state of the client control.
        ActiveX property: FullScreen.
        :return: int
        """
        return int(self._read('FullScreen', 0))

    @pyqtSlot(int)
    def setFullScreen(self, fullScreen):
        """
        :param fullScreen: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('FullScreen', int(fullScreen), 'int')

    def getKeyboardHookMode(self):
        """
        Where Windows key combinations apply (see RdpSecuredSettings.KeyboardHookMode).
        ActiveX property: KeyboardHookMode.
        :return: int
        """
        return int(self._read('KeyboardHookMode', 0))

    @pyqtSlot(int)
    def setKeyboardHookMode(self, keyboardHookMode):
        """
        :param keyboardHookMode: int
        :return: bool, True if the control accepted the value.
        """
        keyboardHookMode = clamp(int(keyboardHookMode), 0, 2)  # type: int
        return self._write('KeyboardHookMode', keyboardHookMode, 'int')

    def getStartProgram(self):
        """
        Program started on the remote server upon connection.
        ActiveX property: StartProgram.
        :return: str | unicode | QString
        """
        return toText(self._read('StartProgram', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setStartProgram(self, startProgram):
        """
        :param startProgram: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('StartProgram', toText(startProgram), 'QString')

    def getWorkDir(self):
        """
        Working directory of the start program.
        ActiveX property: WorkDir.
        :return: str | unicode | QString
        """
        return toText(self._read('WorkDir', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setWorkDir(self, workDir):
        """
        :param workDir: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('WorkDir', toText(workDir), 'QString')

    # ---------- Properties ----------
    audioRedirectionMode = pyqtProperty(int, fget=getAudioRedirectionMode,
                                        fset=setAudioRedirectionMode)  # type: pyqtProperty
    fullScreen = pyqtProperty(int, fget=getFullScreen, fset=setFullScreen)  # type: pyqtProperty
    keyboardHookMode = pyqtProperty(int, fget=getKeyboardHookMode, fset=setKeyboardHookMode)  # type: pyqtProperty
    startProgram = pyqtProperty('QString', fget=getStartProgram, fset=setStartProgram)  # type: pyqtProperty
    workDir = pyqtProperty('QString', fget=getWorkDir, fset=setWorkDir)  # type: pyqtProperty


class RdpSecuredSettings2(RdpSettingsInterface):
    """
    Preconnection BLOB (IMsRdpClientSecuredSettings2, the "SecuredSettings2" sub-object).
    """
    INTERFACE = 'SecuredSettings2'  # type: str
    COM_INTERFACE = 'IMsRdpClientSecuredSettings2'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('pcb', 'PCB', 'QString', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getPcb(self):
        """
        Preconnection BLOB (PCB) sent to the server before connecting.
        ActiveX property: PCB.
        :return: str | unicode | QString
        """
        return toText(self._read('PCB', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPcb(self, pcb):
        """
        :param pcb: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('PCB', toText(pcb), 'QString')

    # ---------- Properties ----------
    pcb = pyqtProperty('QString', fget=getPcb, fset=setPcb)  # type: pyqtProperty


class RdpClientShell(RdpSettingsInterface):
    """
    RDP file / RD Web Access launcher (IMsRdpClientShell, the "MsRdpClientShell" sub-object).
    """
    INTERFACE = 'MsRdpClientShell'  # type: str
    COM_INTERFACE = 'IMsRdpClientShell'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('remoteProgramClientInstalled', 'IsRemoteProgramClientInstalled', 'bool', 'r'),
        ('publicMode', 'PublicMode', 'bool', 'rw'),
        ('rdpFileContents', 'RdpFileContents', 'QString', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def isRemoteProgramClientInstalled(self):
        """
        Whether the client supports Windows Server 2008 R2 RemoteApp (read-only).
        ActiveX property: IsRemoteProgramClientInstalled.
        :return: bool
        """
        return bool(self._read('IsRemoteProgramClientInstalled', False))

    def isPublicMode(self):
        """
        Specifies whether public mode is enabled.
        ActiveX property: PublicMode.
        :return: bool
        """
        return bool(self._read('PublicMode', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setPublicMode(self, publicMode):
        """
        :param publicMode: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('PublicMode', bool(publicMode), 'bool')

    def getRdpFileContents(self):
        """
        RDP file content to launch from RD Web Access or another web portal.
        ActiveX property: RdpFileContents.
        :return: str | unicode | QString
        """
        return toText(self._read('RdpFileContents', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRdpFileContents(self, rdpFileContents):
        """
        :param rdpFileContents: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RdpFileContents', toText(rdpFileContents), 'QString')

    # ---------- Methods ----------
    def getRdpProperty(self, name):
        """
        Retrieves a single named RDP property value (default value if the property has not been set).
        :param name: str | unicode
        :return: any
        """
        return self._call('GetRdpProperty(QString)', name)

    def setRdpProperty(self, name, value):
        """
        Specifies the value of a single RDP property (same names as in a .rdp file).
        :param name: str | unicode
        :param value: any
        :return: any
        """
        return self._call('SetRdpProperty(QString, QVariant)', name, value)

    @pyqtSlot()
    def launch(self):
        """
        Launches the remote file content given by rdpFileContents.
        :return: any
        """
        return self._call('Launch()')

    @pyqtSlot()
    def showTrustedSitesManagementDialog(self):
        """
        Shows the trusted sites management dialog.
        :return: any
        """
        return self._call('ShowTrustedSitesManagementDialog()')

    # ---------- Properties ----------
    remoteProgramClientInstalled = pyqtProperty(bool, fget=isRemoteProgramClientInstalled)  # type: pyqtProperty
    publicMode = pyqtProperty(bool, fget=isPublicMode, fset=setPublicMode)  # type: pyqtProperty
    rdpFileContents = pyqtProperty('QString', fget=getRdpFileContents, fset=setRdpFileContents)  # type: pyqtProperty


class RdpRemoteProgram(RdpSettingsInterface):
    """
    RemoteApp mode (ITSRemoteProgram, the "RemoteProgram" sub-object).
    """
    INTERFACE = 'RemoteProgram'  # type: str
    COM_INTERFACE = 'ITSRemoteProgram'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('remoteProgramMode', 'RemoteProgramMode', 'bool', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def isRemoteProgramMode(self):
        """
        The RemoteApp mode.
        ActiveX property: RemoteProgramMode.
        :return: bool
        """
        return bool(self._read('RemoteProgramMode', False))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRemoteProgramMode(self, remoteProgramMode):
        """
        :param remoteProgramMode: bool
        :return: bool, True if the control accepted the value.
        """
        return self._write('RemoteProgramMode', bool(remoteProgramMode), 'bool')

    # ---------- Methods ----------
    def serverStartProgram(self, executablePath, filePath='', workingDirectory='',
                           expandEnvVarInWorkingDirectoryOnServer=False, arguments='',
                           expandEnvVarInArgumentsOnServer=False):
        """
        Specifies a RemoteApp program to start in the remote session.
        :param executablePath: str | unicode
        :param filePath: str | unicode
        :param workingDirectory: str | unicode
        :param expandEnvVarInWorkingDirectoryOnServer: bool
        :param arguments: str | unicode
        :param expandEnvVarInArgumentsOnServer: bool
        :return: any
        """
        return self._call('ServerStartProgram(QString, QString, QString, bool, QString, bool)',
                          toText(executablePath), toText(filePath), toText(workingDirectory),
                          bool(expandEnvVarInWorkingDirectoryOnServer), toText(arguments),
                          bool(expandEnvVarInArgumentsOnServer))

    # ---------- Properties ----------
    remoteProgramMode = pyqtProperty(bool, fget=isRemoteProgramMode, fset=setRemoteProgramMode)  # type: pyqtProperty


class RdpRemoteProgram2(RdpSettingsInterface):
    """
    RemoteApp identification (ITSRemoteProgram2, the "RemoteProgram2" sub-object).
    """
    INTERFACE = 'RemoteProgram2'  # type: str
    COM_INTERFACE = 'ITSRemoteProgram2'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('remoteApplicationArgs', 'RemoteApplicationArgs', 'QString', 'w'),
        ('remoteApplicationName', 'RemoteApplicationName', 'QString', 'w'),
        ('remoteApplicationProgram', 'RemoteApplicationProgram', 'QString', 'w'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getRemoteApplicationArgs(self):
        """
        Command-line arguments of the RemoteApp (write-only).
        ActiveX property: RemoteApplicationArgs.
        :return: str | unicode | QString
        """
        return toText(self._read('RemoteApplicationArgs', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRemoteApplicationArgs(self, remoteApplicationArgs):
        """
        :param remoteApplicationArgs: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RemoteApplicationArgs', toText(remoteApplicationArgs), 'QString')

    def getRemoteApplicationName(self):
        """
        Name of the RemoteApp (write-only).
        ActiveX property: RemoteApplicationName.
        :return: str | unicode | QString
        """
        return toText(self._read('RemoteApplicationName', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRemoteApplicationName(self, remoteApplicationName):
        """
        :param remoteApplicationName: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RemoteApplicationName', toText(remoteApplicationName), 'QString')

    def getRemoteApplicationProgram(self):
        """
        Path and file name of the RemoteApp program (write-only).
        ActiveX property: RemoteApplicationProgram.
        :return: str | unicode | QString
        """
        return toText(self._read('RemoteApplicationProgram', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRemoteApplicationProgram(self, remoteApplicationProgram):
        """
        :param remoteApplicationProgram: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('RemoteApplicationProgram', toText(remoteApplicationProgram), 'QString')

    # ---------- Properties ----------
    remoteApplicationArgs = pyqtProperty('QString', fget=getRemoteApplicationArgs,
                                         fset=setRemoteApplicationArgs)  # type: pyqtProperty
    remoteApplicationName = pyqtProperty('QString', fget=getRemoteApplicationName,
                                         fset=setRemoteApplicationName)  # type: pyqtProperty
    remoteApplicationProgram = pyqtProperty('QString', fget=getRemoteApplicationProgram,
                                            fset=setRemoteApplicationProgram)  # type: pyqtProperty


class RdpRemoteProgram3(RdpSettingsInterface):
    """
    Start a packaged app in the remote session (ITSRemoteProgram3, the "RemoteProgram3" sub-object).
    """
    INTERFACE = 'RemoteProgram3'  # type: str
    COM_INTERFACE = 'ITSRemoteProgram3'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    # ---------- Methods ----------
    def serverStartApp(self, appUserModelId, arguments='', expandEnvVarInArgumentsOnServer=False):
        """
        Specifies an App (AppUserModelID) to start in the remote session.
        :param appUserModelId: str | unicode
        :param arguments: str | unicode
        :param expandEnvVarInArgumentsOnServer: bool
        :return: any
        """
        return self._call('ServerStartApp(QString, QString, bool)', toText(appUserModelId), toText(arguments),
                          bool(expandEnvVarInArgumentsOnServer))


class RdpTransportSettings(RdpSettingsInterface):
    """
    Remote Desktop Gateway settings (IMsRdpClientTransportSettings, the "TransportSettings" sub-object).
    """
    INTERFACE = 'TransportSettings'  # type: str
    COM_INTERFACE = 'IMsRdpClientTransportSettings'  # type: str

    class GatewayUsageMethod(IntEnum):
        """
        GatewayUsageMethod enumeration class.
        """
        NoneDirect = 0  # type: int
        Direct = 1  # type: int
        Detect = 2  # type: int
        Default = 3  # type: int
        NoneDetect = 4  # type: int

    class GatewayCredsSource(IntEnum):
        """
        GatewayCredsSource enumeration class.
        """
        UserPassword = 0  # type: int
        SmartCard = 1  # type: int
        Any = 4  # type: int

    NoneDirect = GatewayUsageMethod.NoneDirect  # type: int
    Direct = GatewayUsageMethod.Direct  # type: int
    Detect = GatewayUsageMethod.Detect  # type: int
    Default = GatewayUsageMethod.Default  # type: int
    NoneDetect = GatewayUsageMethod.NoneDetect  # type: int
    UserPassword = GatewayCredsSource.UserPassword  # type: int
    SmartCard = GatewayCredsSource.SmartCard  # type: int
    Any = GatewayCredsSource.Any  # type: int

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('gatewayCredsSource', 'GatewayCredsSource', 'uint', 'rw'),
        ('gatewayDefaultUsageMethod', 'GatewayDefaultUsageMethod', 'uint', 'r'),
        ('gatewayHostname', 'GatewayHostname', 'QString', 'rw'),
        ('gatewayIsSupported', 'GatewayIsSupported', 'int', 'r'),
        ('gatewayProfileUsageMethod', 'GatewayProfileUsageMethod', 'uint', 'rw'),
        ('gatewayUsageMethod', 'GatewayUsageMethod', 'uint', 'rw'),
        ('gatewayUserSelectedCredsSource', 'GatewayUserSelectedCredsSource', 'uint', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getGatewayCredsSource(self):
        """
        RD Gateway authentication method (see RdpTransportSettings.GatewayCredsSource).
        ActiveX property: GatewayCredsSource.
        :return: int
        """
        return int(self._read('GatewayCredsSource', 0))

    @pyqtSlot(int)
    def setGatewayCredsSource(self, gatewayCredsSource):
        """
        :param gatewayCredsSource: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayCredsSource', int(gatewayCredsSource), 'uint')

    def getGatewayDefaultUsageMethod(self):
        """
        Default RD Gateway usage method (read-only).
        ActiveX property: GatewayDefaultUsageMethod.
        :return: int
        """
        return int(self._read('GatewayDefaultUsageMethod', 0))

    def getGatewayHostname(self):
        """
        Host name of the RD Gateway server.
        ActiveX property: GatewayHostname.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayHostname', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayHostname(self, gatewayHostname):
        """
        :param gatewayHostname: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayHostname', toText(gatewayHostname), 'QString')

    def getGatewayIsSupported(self):
        """
        Whether RD Gateway is supported (read-only).
        ActiveX property: GatewayIsSupported.
        :return: int
        """
        return int(self._read('GatewayIsSupported', 0))

    def getGatewayProfileUsageMethod(self):
        """
        Whether to use default RD Gateway settings.
        ActiveX property: GatewayProfileUsageMethod.
        :return: int
        """
        return int(self._read('GatewayProfileUsageMethod', 0))

    @pyqtSlot(int)
    def setGatewayProfileUsageMethod(self, gatewayProfileUsageMethod):
        """
        :param gatewayProfileUsageMethod: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayProfileUsageMethod', int(gatewayProfileUsageMethod), 'uint')

    def getGatewayUsageMethod(self):
        """
        When to use an RD Gateway server (see RdpTransportSettings.GatewayUsageMethod).
        ActiveX property: GatewayUsageMethod.
        :return: int
        """
        return int(self._read('GatewayUsageMethod', 0))

    @pyqtSlot(int)
    def setGatewayUsageMethod(self, gatewayUsageMethod):
        """
        :param gatewayUsageMethod: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayUsageMethod', int(gatewayUsageMethod), 'uint')

    def getGatewayUserSelectedCredsSource(self):
        """
        User-specified RD Gateway credential source.
        ActiveX property: GatewayUserSelectedCredsSource.
        :return: int
        """
        return int(self._read('GatewayUserSelectedCredsSource', 0))

    @pyqtSlot(int)
    def setGatewayUserSelectedCredsSource(self, gatewayUserSelectedCredsSource):
        """
        :param gatewayUserSelectedCredsSource: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayUserSelectedCredsSource', int(gatewayUserSelectedCredsSource), 'uint')

    # ---------- Properties ----------
    gatewayCredsSource = pyqtProperty(int, fget=getGatewayCredsSource, fset=setGatewayCredsSource)  # type: pyqtProperty
    gatewayDefaultUsageMethod = pyqtProperty(int, fget=getGatewayDefaultUsageMethod)  # type: pyqtProperty
    gatewayHostname = pyqtProperty('QString', fget=getGatewayHostname, fset=setGatewayHostname)  # type: pyqtProperty
    gatewayIsSupported = pyqtProperty(int, fget=getGatewayIsSupported)  # type: pyqtProperty
    gatewayProfileUsageMethod = pyqtProperty(int, fget=getGatewayProfileUsageMethod,
                                             fset=setGatewayProfileUsageMethod)  # type: pyqtProperty
    gatewayUsageMethod = pyqtProperty(int, fget=getGatewayUsageMethod, fset=setGatewayUsageMethod)  # type: pyqtProperty
    gatewayUserSelectedCredsSource = pyqtProperty(int, fget=getGatewayUserSelectedCredsSource,
                                                  fset=setGatewayUserSelectedCredsSource)  # type: pyqtProperty


class RdpTransportSettings2(RdpSettingsInterface):
    """
    RD Gateway credentials and one-time password (IMsRdpClientTransportSettings2, the "TransportSettings2" sub-
    object).
    """
    INTERFACE = 'TransportSettings2'  # type: str
    COM_INTERFACE = 'IMsRdpClientTransportSettings2'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('gatewayCredSharing', 'GatewayCredSharing', 'uint', 'rw'),
        ('gatewayDomain', 'GatewayDomain', 'QString', 'rw'),
        ('gatewayEncryptedOtpCookie', 'GatewayEncryptedOtpCookie', 'QString', 'rw'),
        ('gatewayEncryptedOtpCookieSize', 'GatewayEncryptedOtpCookieSize', 'uint', 'rw'),
        ('gatewayPassword', 'GatewayPassword', 'QString', 'w'),
        ('gatewayPreAuthRequirement', 'GatewayPreAuthRequirement', 'int', 'rw'),
        ('gatewayPreAuthServerAddr', 'GatewayPreAuthServerAddr', 'QString', 'rw'),
        ('gatewaySupportUrl', 'GatewaySupportUrl', 'QString', 'rw'),
        ('gatewayUsername', 'GatewayUsername', 'QString', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getGatewayCredSharing(self):
        """
        Whether single sign-on for RD Gateway is enabled.
        ActiveX property: GatewayCredSharing.
        :return: int
        """
        return int(self._read('GatewayCredSharing', 0))

    @pyqtSlot(int)
    def setGatewayCredSharing(self, gatewayCredSharing):
        """
        :param gatewayCredSharing: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayCredSharing', int(gatewayCredSharing), 'uint')

    def getGatewayDomain(self):
        """
        Domain name used to connect to the RD Gateway server.
        ActiveX property: GatewayDomain.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayDomain', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayDomain(self, gatewayDomain):
        """
        :param gatewayDomain: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayDomain', toText(gatewayDomain), 'QString')

    def getGatewayEncryptedOtpCookie(self):
        """
        The encrypted OTP cookie.
        ActiveX property: GatewayEncryptedOtpCookie.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayEncryptedOtpCookie', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayEncryptedOtpCookie(self, gatewayEncryptedOtpCookie):
        """
        :param gatewayEncryptedOtpCookie: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayEncryptedOtpCookie', toText(gatewayEncryptedOtpCookie), 'QString')

    def getGatewayEncryptedOtpCookieSize(self):
        """
        Size, in bytes, of the encrypted OTP cookie.
        ActiveX property: GatewayEncryptedOtpCookieSize.
        :return: int
        """
        return int(self._read('GatewayEncryptedOtpCookieSize', 0))

    @pyqtSlot(int)
    def setGatewayEncryptedOtpCookieSize(self, gatewayEncryptedOtpCookieSize):
        """
        :param gatewayEncryptedOtpCookieSize: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayEncryptedOtpCookieSize', int(gatewayEncryptedOtpCookieSize), 'uint')

    def getGatewayPassword(self):
        """
        Password used to connect to the RD Gateway server (write-only; the getter never returns it).
        ActiveX property: GatewayPassword.
        :return: str | unicode | QString
        """
        return ''

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayPassword(self, gatewayPassword):
        """
        :param gatewayPassword: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayPassword', toText(gatewayPassword), 'QString', secret=True)

    def getGatewayPreAuthRequirement(self):
        """
        Whether the RD Gateway one-time password (OTP) feature is enabled.
        ActiveX property: GatewayPreAuthRequirement.
        :return: int
        """
        return int(self._read('GatewayPreAuthRequirement', 0))

    @pyqtSlot(int)
    def setGatewayPreAuthRequirement(self, gatewayPreAuthRequirement):
        """
        :param gatewayPreAuthRequirement: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayPreAuthRequirement', int(gatewayPreAuthRequirement), 'int')

    def getGatewayPreAuthServerAddr(self):
        """
        Web address of the pre-authentication server.
        ActiveX property: GatewayPreAuthServerAddr.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayPreAuthServerAddr', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayPreAuthServerAddr(self, gatewayPreAuthServerAddr):
        """
        :param gatewayPreAuthServerAddr: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayPreAuthServerAddr', toText(gatewayPreAuthServerAddr), 'QString')

    def getGatewaySupportUrl(self):
        """
        Web address of the RD Gateway technical support site.
        ActiveX property: GatewaySupportUrl.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewaySupportUrl', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewaySupportUrl(self, gatewaySupportUrl):
        """
        :param gatewaySupportUrl: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewaySupportUrl', toText(gatewaySupportUrl), 'QString')

    def getGatewayUsername(self):
        """
        Username used to connect to the RD Gateway server.
        ActiveX property: GatewayUsername.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayUsername', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayUsername(self, gatewayUsername):
        """
        :param gatewayUsername: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayUsername', toText(gatewayUsername), 'QString')

    # ---------- Properties ----------
    gatewayCredSharing = pyqtProperty(int, fget=getGatewayCredSharing, fset=setGatewayCredSharing)  # type: pyqtProperty
    gatewayDomain = pyqtProperty('QString', fget=getGatewayDomain, fset=setGatewayDomain)  # type: pyqtProperty
    gatewayEncryptedOtpCookie = pyqtProperty('QString', fget=getGatewayEncryptedOtpCookie,
                                             fset=setGatewayEncryptedOtpCookie)  # type: pyqtProperty
    gatewayEncryptedOtpCookieSize = pyqtProperty(int, fget=getGatewayEncryptedOtpCookieSize,
                                                 fset=setGatewayEncryptedOtpCookieSize)  # type: pyqtProperty
    gatewayPassword = pyqtProperty('QString', fget=getGatewayPassword, fset=setGatewayPassword)  # type: pyqtProperty
    gatewayPreAuthRequirement = pyqtProperty(int, fget=getGatewayPreAuthRequirement,
                                             fset=setGatewayPreAuthRequirement)  # type: pyqtProperty
    gatewayPreAuthServerAddr = pyqtProperty('QString', fget=getGatewayPreAuthServerAddr,
                                            fset=setGatewayPreAuthServerAddr)  # type: pyqtProperty
    gatewaySupportUrl = pyqtProperty('QString', fget=getGatewaySupportUrl, fset=setGatewaySupportUrl)  # type: pyqtProperty
    gatewayUsername = pyqtProperty('QString', fget=getGatewayUsername, fset=setGatewayUsername)  # type: pyqtProperty


class RdpTransportSettings3(RdpSettingsInterface):
    """
    RD Gateway cookie-based authentication (IMsRdpClientTransportSettings3, the "TransportSettings3" sub-
    object).
    """
    INTERFACE = 'TransportSettings3'  # type: str
    COM_INTERFACE = 'IMsRdpClientTransportSettings3'  # type: str

    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('gatewayAuthCookieServerAddr', 'GatewayAuthCookieServerAddr', 'QString', 'rw'),
        ('gatewayAuthLoginPage', 'GatewayAuthLoginPage', 'QString', 'rw'),
        ('gatewayCredSourceCookie', 'GatewayCredSourceCookie', 'uint', 'rw'),
        ('gatewayEncryptedAuthCookie', 'GatewayEncryptedAuthCookie', 'QString', 'rw'),
        ('gatewayEncryptedAuthCookieSize', 'GatewayEncryptedAuthCookieSize', 'uint', 'rw'),
    )  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getGatewayAuthCookieServerAddr(self):
        """
        Server address for cookie-based authentication.
        ActiveX property: GatewayAuthCookieServerAddr.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayAuthCookieServerAddr', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayAuthCookieServerAddr(self, gatewayAuthCookieServerAddr):
        """
        :param gatewayAuthCookieServerAddr: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayAuthCookieServerAddr', toText(gatewayAuthCookieServerAddr), 'QString')

    def getGatewayAuthLoginPage(self):
        """
        Address of the login webpage used to authenticate a user.
        ActiveX property: GatewayAuthLoginPage.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayAuthLoginPage', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayAuthLoginPage(self, gatewayAuthLoginPage):
        """
        :param gatewayAuthLoginPage: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayAuthLoginPage', toText(gatewayAuthLoginPage), 'QString')

    def getGatewayCredSourceCookie(self):
        """
        1 if the credential source is cookie-based, 0 otherwise.
        ActiveX property: GatewayCredSourceCookie.
        :return: int
        """
        return int(self._read('GatewayCredSourceCookie', 0))

    @pyqtSlot(int)
    def setGatewayCredSourceCookie(self, gatewayCredSourceCookie):
        """
        :param gatewayCredSourceCookie: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayCredSourceCookie', int(gatewayCredSourceCookie), 'uint')

    def getGatewayEncryptedAuthCookie(self):
        """
        The encrypted authentication cookie.
        ActiveX property: GatewayEncryptedAuthCookie.
        :return: str | unicode | QString
        """
        return toText(self._read('GatewayEncryptedAuthCookie', ''))

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setGatewayEncryptedAuthCookie(self, gatewayEncryptedAuthCookie):
        """
        :param gatewayEncryptedAuthCookie: str | unicode
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayEncryptedAuthCookie', toText(gatewayEncryptedAuthCookie), 'QString')

    def getGatewayEncryptedAuthCookieSize(self):
        """
        Size, in characters, of GatewayEncryptedAuthCookie.
        ActiveX property: GatewayEncryptedAuthCookieSize.
        :return: int
        """
        return int(self._read('GatewayEncryptedAuthCookieSize', 0))

    @pyqtSlot(int)
    def setGatewayEncryptedAuthCookieSize(self, gatewayEncryptedAuthCookieSize):
        """
        :param gatewayEncryptedAuthCookieSize: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayEncryptedAuthCookieSize', int(gatewayEncryptedAuthCookieSize), 'uint')

    # ---------- Properties ----------
    gatewayAuthCookieServerAddr = pyqtProperty('QString', fget=getGatewayAuthCookieServerAddr,
                                               fset=setGatewayAuthCookieServerAddr)  # type: pyqtProperty
    gatewayAuthLoginPage = pyqtProperty('QString', fget=getGatewayAuthLoginPage,
                                        fset=setGatewayAuthLoginPage)  # type: pyqtProperty
    gatewayCredSourceCookie = pyqtProperty(int, fget=getGatewayCredSourceCookie,
                                           fset=setGatewayCredSourceCookie)  # type: pyqtProperty
    gatewayEncryptedAuthCookie = pyqtProperty('QString', fget=getGatewayEncryptedAuthCookie,
                                              fset=setGatewayEncryptedAuthCookie)  # type: pyqtProperty
    gatewayEncryptedAuthCookieSize = pyqtProperty(int, fget=getGatewayEncryptedAuthCookieSize,
                                                  fset=setGatewayEncryptedAuthCookieSize)  # type: pyqtProperty


class RdpTransportSettings4(RdpSettingsInterface):
    """
    RD Gateway brokering (IMsRdpClientTransportSettings4, the "TransportSettings4" sub-object).
    """
    INTERFACE = 'TransportSettings4'  # type: str
    COM_INTERFACE = 'IMsRdpClientTransportSettings4'  # type: str
    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------
    PROPERTIES = (
        ('gatewayBrokeringType', 'GatewayBrokeringType', 'uint', 'rw'),)  # type: tuple[tuple[str, str, str, str]]

    # ---------- Public API ----------
    def getGatewayBrokeringType(self):
        """
        The gateway brokering type.
        ActiveX property: GatewayBrokeringType.
        :return: int
        """
        return int(self._read('GatewayBrokeringType', 0))

    @pyqtSlot(int)
    def setGatewayBrokeringType(self, gatewayBrokeringType):
        """
        :param gatewayBrokeringType: int
        :return: bool, True if the control accepted the value.
        """
        return self._write('GatewayBrokeringType', int(gatewayBrokeringType), 'uint')

    # ---------- Properties ----------
    gatewayBrokeringType = pyqtProperty(
        int, fget=getGatewayBrokeringType, fset=setGatewayBrokeringType)  # type: pyqtProperty


#: (sub-object name, class) of every settings interface of the control, in declaration order.
INTERFACES = (
    ('AdvancedSettings', RdpAdvancedSettings),
    ('AdvancedSettings2', RdpAdvancedSettings2),
    ('AdvancedSettings3', RdpAdvancedSettings3),
    ('AdvancedSettings4', RdpAdvancedSettings4),
    ('AdvancedSettings5', RdpAdvancedSettings5),
    ('AdvancedSettings6', RdpAdvancedSettings6),
    ('AdvancedSettings7', RdpAdvancedSettings7),
    ('AdvancedSettings8', RdpAdvancedSettings8),
    ('SecuredSettings', RdpSecuredSettings),
    ('SecuredSettings2', RdpSecuredSettings2),
    ('MsRdpClientShell', RdpClientShell),
    ('RemoteProgram', RdpRemoteProgram),
    ('RemoteProgram2', RdpRemoteProgram2),
    ('RemoteProgram3', RdpRemoteProgram3),
    ('TransportSettings', RdpTransportSettings),
    ('TransportSettings2', RdpTransportSettings2),
    ('TransportSettings3', RdpTransportSettings3),
    ('TransportSettings4', RdpTransportSettings4),
)  # type: tuple[tuple[str, type]]

__all__ = ['clamp', 'toText', 'axReadProperty', 'axWriteProperty', 'COLOR_DEPTHS', 'INTERFACES',
           'RdpSettingsInterface',
           'RdpControlSettings',
           'RdpAdvancedSettings',
           'RdpAdvancedSettings2',
           'RdpAdvancedSettings3',
           'RdpAdvancedSettings4',
           'RdpAdvancedSettings5',
           'RdpAdvancedSettings6',
           'RdpAdvancedSettings7',
           'RdpAdvancedSettings8',
           'RdpSecuredSettings',
           'RdpSecuredSettings2',
           'RdpClientShell',
           'RdpRemoteProgram',
           'RdpRemoteProgram2',
           'RdpRemoteProgram3',
           'RdpTransportSettings',
           'RdpTransportSettings2',
           'RdpTransportSettings3',
           'RdpTransportSettings4']  # type: list[str]
