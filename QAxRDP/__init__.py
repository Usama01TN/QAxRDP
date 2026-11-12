# coding=utf-8
"""
QAxRDP: Microsoft Remote Desktop (RDP) client ActiveX control for Qt applications, written on top of ManyQt
(PyQt4 / PyQt5 / PyQt6 / PySide / PySide2 / PySide6).
Packages:
    - remotedesktop: RemoteDesktopWidget and the MsTscAx settings interfaces (Rdp*Settings).
    - connectionbar: ConnectionBar, StatusDot, parseAddress and parseUserName.
Application:
    - RemoteConnector (mainwindow.py) and main() (main.py), also run with "python -m QAxRDP" or "qaxrdp".
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .version import __version__, __author__, __email__, __license__
    from .remotedesktop import RemoteDesktopWidget, isActiveXAvailable, controlProgId, disconnectReasonText, \
        isNormalDisconnect, CONTROL_PROGID, DEFAULT_CONTROL_VERSION, DEFAULT_RDP_PORT, DISCONNECT_REASONS, EVENTS, \
        SETTINGS_INTERFACES, RdpSettingsInterface, RdpControlSettings, RdpAdvancedSettings, RdpAdvancedSettings2, \
        RdpAdvancedSettings3, RdpAdvancedSettings4, RdpAdvancedSettings5, RdpAdvancedSettings6, RdpAdvancedSettings7, \
        RdpAdvancedSettings8, RdpSecuredSettings, RdpSecuredSettings2, RdpClientShell, RdpRemoteProgram, \
        RdpRemoteProgram2, RdpRemoteProgram3, RdpTransportSettings, RdpTransportSettings2, RdpTransportSettings3, \
        RdpTransportSettings4
    from .connectionbar import ConnectionBar, StatusDot, parseAddress, parseUserName
    from .mainwindow import RemoteConnector, createAppIcon
    from .main import main
except:
    from version import __version__, __author__, __email__, __license__
    from remotedesktop import RemoteDesktopWidget, isActiveXAvailable, controlProgId, disconnectReasonText, \
        isNormalDisconnect, CONTROL_PROGID, DEFAULT_CONTROL_VERSION, DEFAULT_RDP_PORT, DISCONNECT_REASONS, EVENTS, \
        SETTINGS_INTERFACES, RdpSettingsInterface, RdpControlSettings, RdpAdvancedSettings, RdpAdvancedSettings2, \
        RdpAdvancedSettings3, RdpAdvancedSettings4, RdpAdvancedSettings5, RdpAdvancedSettings6, RdpAdvancedSettings7, \
        RdpAdvancedSettings8, RdpSecuredSettings, RdpSecuredSettings2, RdpClientShell, RdpRemoteProgram, \
        RdpRemoteProgram2, RdpRemoteProgram3, RdpTransportSettings, RdpTransportSettings2, RdpTransportSettings3, \
        RdpTransportSettings4
    from connectionbar import ConnectionBar, StatusDot, parseAddress, parseUserName
    from mainwindow import RemoteConnector, createAppIcon
    from main import main

__all__ = ['__version__', 'RemoteDesktopWidget', 'isActiveXAvailable', 'controlProgId', 'disconnectReasonText',
           'isNormalDisconnect', 'CONTROL_PROGID', 'DEFAULT_CONTROL_VERSION', 'DEFAULT_RDP_PORT',
           'DISCONNECT_REASONS', 'EVENTS', 'SETTINGS_INTERFACES', 'RdpSettingsInterface', 'RdpControlSettings',
           'RdpAdvancedSettings', 'RdpAdvancedSettings2', 'RdpAdvancedSettings3', 'RdpAdvancedSettings4',
           'RdpAdvancedSettings5', 'RdpAdvancedSettings6', 'RdpAdvancedSettings7', 'RdpAdvancedSettings8',
           'RdpSecuredSettings', 'RdpSecuredSettings2', 'RdpClientShell', 'RdpRemoteProgram', 'RdpRemoteProgram2',
           'RdpRemoteProgram3', 'RdpTransportSettings', 'RdpTransportSettings2', 'RdpTransportSettings3',
           'RdpTransportSettings4', 'ConnectionBar', 'StatusDot', 'parseAddress', 'parseUserName', 'RemoteConnector',
           'createAppIcon', 'main']  # type: list[str]
