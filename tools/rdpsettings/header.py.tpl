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
        if axObject.metaObject().indexOfProperty(name) < 0:
            return None
        return axObject.property(name)
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
        self.__m_values = {}  # type: dict[str, any]
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


{{CLASSES}}


#: (sub-object name, class) of every settings interface of the control, in declaration order.
INTERFACES = (
{{INTERFACE_MAP}}
)  # type: tuple[tuple[str, type]]

__all__ = ['clamp', 'toText', 'axReadProperty', 'axWriteProperty', 'COLOR_DEPTHS', 'INTERFACES',
           'RdpSettingsInterface',
           {{ALL}}]  # type: list[str]
