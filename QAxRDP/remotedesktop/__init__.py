# coding=utf-8
"""
remotedesktop package: RemoteDesktopWidget and the MsTscAx settings interfaces.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .remotedesktop import RemoteDesktopWidget, isActiveXAvailable, controlProgId, disconnectReasonText, \
        isNormalDisconnect, CONTROL_PROGID, DEFAULT_CONTROL_VERSION, DEFAULT_RDP_PORT, DISCONNECT_REASONS, EVENTS, \
        SETTINGS_INTERFACES
    from .rdpsettings import RdpSettingsInterface, RdpControlSettings, RdpAdvancedSettings, RdpAdvancedSettings2, \
        RdpAdvancedSettings3, RdpAdvancedSettings4, RdpAdvancedSettings5, RdpAdvancedSettings6, RdpAdvancedSettings7, \
        RdpAdvancedSettings8, RdpSecuredSettings, RdpSecuredSettings2, RdpClientShell, RdpRemoteProgram, \
        RdpRemoteProgram2, RdpRemoteProgram3, RdpTransportSettings, RdpTransportSettings2, RdpTransportSettings3, \
        RdpTransportSettings4
except:
    from remotedesktop import RemoteDesktopWidget, isActiveXAvailable, controlProgId, disconnectReasonText, \
        isNormalDisconnect, CONTROL_PROGID, DEFAULT_CONTROL_VERSION, DEFAULT_RDP_PORT, DISCONNECT_REASONS, EVENTS, \
        SETTINGS_INTERFACES
    from rdpsettings import RdpSettingsInterface, RdpControlSettings, RdpAdvancedSettings, RdpAdvancedSettings2, \
        RdpAdvancedSettings3, RdpAdvancedSettings4, RdpAdvancedSettings5, RdpAdvancedSettings6, RdpAdvancedSettings7, \
        RdpAdvancedSettings8, RdpSecuredSettings, RdpSecuredSettings2, RdpClientShell, RdpRemoteProgram, \
        RdpRemoteProgram2, RdpRemoteProgram3, RdpTransportSettings, RdpTransportSettings2, RdpTransportSettings3, \
        RdpTransportSettings4

__all__ = ['RemoteDesktopWidget', 'isActiveXAvailable', 'controlProgId', 'disconnectReasonText',
           'isNormalDisconnect', 'CONTROL_PROGID', 'DEFAULT_CONTROL_VERSION', 'DEFAULT_RDP_PORT',
           'DISCONNECT_REASONS', 'EVENTS', 'SETTINGS_INTERFACES', 'RdpSettingsInterface', 'RdpControlSettings',
           'RdpAdvancedSettings', 'RdpAdvancedSettings2', 'RdpAdvancedSettings3', 'RdpAdvancedSettings4',
           'RdpAdvancedSettings5', 'RdpAdvancedSettings6', 'RdpAdvancedSettings7', 'RdpAdvancedSettings8',
           'RdpSecuredSettings', 'RdpSecuredSettings2', 'RdpClientShell', 'RdpRemoteProgram', 'RdpRemoteProgram2',
           'RdpRemoteProgram3', 'RdpTransportSettings', 'RdpTransportSettings2', 'RdpTransportSettings3',
           'RdpTransportSettings4']  # type: list[str]
