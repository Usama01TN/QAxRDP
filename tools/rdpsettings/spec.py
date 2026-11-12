# -*- coding: utf-8 -*-
"""
Spec of the MsTscAx sub-interfaces ported from the original QAxRDP.py (descriptions from Microsoft docs).
Each property: (axName, pyType, axType, access, default, (lo, hi) | None, secret, description)
pyType: bool | int | str ; axType: bool | int | uint | QString ; access: rw | r | w
"""
B, I, S = 'bool', 'int', 'str'


def P(ax, py, axt=None, acc='rw', default=None, rng=None, secret=False, desc=''):
    if axt is None:
        axt = {'bool': 'bool', 'int': 'int', 'str': 'QString'}[py]
    if default is None:
        default = {'bool': False, 'int': 0, 'str': ''}[py]
    return dict(ax=ax, py=py, axt=axt, acc=acc, default=default, rng=rng, secret=secret, desc=desc)


NOT_SUPPORTED = 'This property is not supported by recent versions of the control (kept for completeness).'

INTERFACES = [
    ('AdvancedSettings', 'AdvancedSettings', 'IMsRdpClientAdvancedSettings',
     'Advanced settings of the control: bitmap caching, hot keys, redirection, timeouts, port...', [], [
         P('AcceleratorPassthrough', B, desc='Specifies whether accelerator passthrough is enabled.'),
         P('allowBackgroundInput', I, desc='Specifies whether background input mode is enabled.'),
         P('BitmapCacheSize', I, default=1, rng=(1, 32),
           desc='Size, in kilobytes, of the bitmap cache file used for 8 bpp bitmaps (1 to 32).'),
         P('BitmapPeristence', I, desc='Specifies whether bitmap caching is enabled (the misspelling is in the '
                                       'released version of the control).'),
         P('BitmapPersistence', I, desc='Specifies if persistent bitmap caching should be used.'),
         P('BitmapVirtualCache16BppSize', I, desc='Size, in megabytes, of the persistent bitmap cache file for '
                                                  '15 and 16 bpp.'),
         P('BitmapVirtualCache24BppSize', I, desc='Size, in megabytes, of the persistent bitmap cache file for '
                                                  '24 bpp.'),
         P('BitmapVirtualCacheSize', I, default=1, rng=(1, 32),
           desc='Size, in megabytes, of the persistent bitmap cache file for 8 bpp (1 to 32).'),
         P('brushSupportLevel', I, desc='Specifies the level of brush support.'),
         P('CachePersistenceActive', I, desc='Specifies whether persistent bitmap caching should be used.'),
         P('ClearTextPassword', S, acc='w', secret=True,
           desc='Password used to connect (write-only; the getter never returns it).'),
         P('Compress', I, desc='Specifies whether compression is enabled.'),
         P('ConnectToServerConsole', B, desc=NOT_SUPPORTED),
         P('ConnectWithEndpoint', I, acc='w', desc=NOT_SUPPORTED),
         P('ContainerHandledFullScreen', I, desc='Specifies whether the container-handled full-screen mode is '
                                                 'enabled.'),
         P('DedicatedTerminal', I, desc=NOT_SUPPORTED),
         P('DisableCtrlAltDel', I, desc='Specifies if the initial explanatory screen in Winlogon should display.'),
         P('DisableRdpdr', I, desc='Specifies whether printer and clipboard redirection is enabled.'),
         P('DisplayConnectionBar', B, default=True, desc='Specifies whether to use the connection bar.'),
         P('DoubleClickDetect', I, desc='Specifies if the client identifies double-clicks for the server.'),
         P('EnableMouse', I, desc=NOT_SUPPORTED),
         P('EnableWindowsKey', I, desc='Specifies if the Windows key can be used in the remote session.'),
         P('EncryptionEnabled', I, desc='Not supported: encryption cannot be disabled.'),
         P('GrabFocusOnConnect', B, default=True,
           desc='Specifies if the client control should have the focus while connecting.'),
         P('HotKeyAltEsc', I, default=0x2D, desc='Virtual-key added to ALT to replace ALT+ESC (default VK_INSERT).'),
         P('HotKeyAltShiftTab', I, default=0x22,
           desc='Virtual-key added to ALT to replace ALT+SHIFT+TAB (default VK_NEXT).'),
         P('HotKeyAltSpace', I, default=0x2E,
           desc='Virtual-key added to ALT to replace ALT+SPACE (default VK_DELETE).'),
         P('HotKeyAltTab', I, default=0x21, desc='Virtual-key added to ALT to replace ALT+TAB (default VK_PRIOR).'),
         P('HotKeyCtrlAltDel', I, default=0x23,
           desc='Virtual-key added to CTRL+ALT to replace CTRL+ALT+DELETE (default VK_END).'),
         P('HotKeyCtrlEsc', I, default=0x24, desc='Virtual-key added to ALT to replace CTRL+ESC (default VK_HOME).'),
         P('HotKeyFullScreen', I, default=0x03,
           desc='Virtual-key added to CTRL+ALT to switch to full-screen mode (default VK_CANCEL).'),
         P('IconFile', S, acc='w', desc='File containing the icon displayed in full-screen mode (write-only).'),
         P('IconIndex', I, desc='Index of the icon within the current icon file.'),
         P('InputEventsAtOnce', I, desc=NOT_SUPPORTED),
         P('keepAliveInterval', I, rng=(0, None),
           desc='Interval, in ms, of keep-alive messages (0 disables, minimum valid value is 10000).'),
         P('KeyboardFunctionKey', I, desc='Valid for Windows CE only.'),
         P('KeyBoardLayoutStr', S, acc='w', desc='Active input locale identifier (keyboard layout) to use '
                                                 '(write-only).'),
         P('KeyboardSubType', I, desc='Specifies the keyboard subtype.'),
         P('KeyboardType', I, desc='Specifies the keyboard type.'),
         P('LoadBalanceInfo', S, desc='Load balancing cookie placed in the X.224 Connection Request packet.'),
         P('maxEventCount', I, desc=NOT_SUPPORTED),
         P('MaximizeShell', I, desc='Specifies if programs launched with StartProgram should be maximized.'),
         P('minInputSendInterval', I, desc='Minimum interval, in ms, between the sending of mouse events.'),
         P('MinutesToIdleTimeout', I, rng=(0, 240),
           desc='Maximum time, in minutes, to stay connected without user input (0 to 240).'),
         P('NotifyTSPublicKey', B, desc='Specifies whether receivedTSPublicKey is emitted during connection.'),
         P('NumBitmapCaches', I, desc=NOT_SUPPORTED),
         P('orderDrawThreshold', I, desc=NOT_SUPPORTED),
         P('overallConnectionTimeout', I, default=120, rng=(0, 600),
           desc='Total time, in seconds, the control waits for a connection to complete (0 to 600).'),
         P('PerformanceFlags', I, desc='Set of features that can be set at the server to improve performance.'),
         P('PersistCacheDirectory', S, desc=NOT_SUPPORTED),
         P('PinConnectionBar', B, desc='State of the connection bar: True = pinned, False = auto-hide.'),
         P('PluginDlls', S, acc='w', desc='Names of virtual channel client DLLs to be loaded (write-only).'),
         P('RdpdrClipCleanTempDirString', S, desc=NOT_SUPPORTED),
         P('RdpdrClipPasteInfoString', S, desc=NOT_SUPPORTED),
         P('RdpdrLocalPrintingDocName', S, desc=NOT_SUPPORTED),
         P('RDPPort', I, default=3389, rng=(1, 65535), desc='Connection port (default 3389).'),
         P('RedirectDrives', B, desc='Specifies if redirection of disk drives is allowed.'),
         P('RedirectPorts', B, desc='Specifies if redirection of local ports (COM, LPT) is allowed.'),
         P('RedirectPrinters', B, desc='Specifies if redirection of printers is allowed.'),
         P('RedirectSmartCards', B, desc='Specifies if redirection of smart cards is allowed.'),
         P('SasSequence', I, desc='Secure access sequence (SAS) used to access the login screen.'),
         P('ScaleBitmapCachesByBPP', I, desc=NOT_SUPPORTED),
         P('ShadowBitmap', I, desc=NOT_SUPPORTED),
         P('shutdownTimeout', I, default=10, rng=(0, 600),
           desc='Time, in seconds, to wait for the server to answer a disconnection request (0 to 600).'),
         P('singleConnectionTimeout', I, rng=(0, 600),
           desc='Maximum time, in seconds, to wait for a connection to one IP address (0 to 600).'),
         P('SmartSizing', B, desc='Scale the remote display to fit the client area of the control.'),
         P('SmoothScroll', I, desc=NOT_SUPPORTED),
         P('TransportType', I, desc='Transport type used by the client (not used by the ActiveX control).'),
         P('WinceFixedPalette', I, desc='Valid for Windows CE only.'),
     ]),
    ('AdvancedSettings2', 'AdvancedSettings2', 'IMsRdpClientAdvancedSettings2', 'Automatic reconnection settings.',
     [], [
         P('CanAutoReconnect', B, acc='r', desc='Whether the control can reconnect automatically to the current '
                                                'session (read-only).'),
         P('EnableAutoReconnect', B, default=True,
           desc='Enable automatic reconnection in the event of a network disconnection.'),
         P('MaxReconnectAttempts', I, default=20, rng=(0, 200),
           desc='Number of times to try to reconnect during automatic reconnection (0 to 200).'),
     ]),
    ('AdvancedSettings3', 'AdvancedSettings3', 'IMsRdpClientAdvancedSettings3', 'Connection bar buttons.', [], [
        P('ConnectionBarShowMinimizeButton', B, default=True,
          desc='Display the Minimize button on the connection bar.'),
        P('ConnectionBarShowRestoreButton', B, default=True, desc='Display the Restore button on the connection bar.'),
    ]),
    ('AdvancedSettings4', 'AdvancedSettings4', 'IMsRdpClientAdvancedSettings4', 'Server authentication level.',
     [('AuthenticationLevel', [('NoAuthentication', 0), ('AuthenticationRequired', 1), ('AuthenticationWarn', 2)])],
     [
         P('AuthenticationLevel', I, rng=(0, 2),
           desc='Authentication level (see AdvancedSettings4.AuthenticationLevel).'),
     ]),
    ('AdvancedSettings5', 'AdvancedSettings5', 'IMsRdpClientAdvancedSettings5', 'Audio, clipboard, devices and '
                                                                                'public mode.',
     [('AudioRedirectionMode', [('RedirectToClient', 0), ('PlayOnServer', 1), ('DoNotPlay', 2)])], [
         P('AudioRedirectionMode', I, rng=(0, 2),
           desc='Audio redirection mode (see AdvancedSettings5.AudioRedirectionMode).'),
         P('BitmapVirtualCache32BppSize', I, desc='Virtual cache file size for 32 bpp bitmaps.'),
         P('ConnectionBarShowPinButton', B, default=True, desc='Display the pin button on the connection bar.'),
         P('PublicMode', B, desc='Public mode prevents the client from caching user data to the local system.'),
         P('RedirectClipboard', B, desc='Clipboard redirection.'),
         P('RedirectDevices', B, desc='Device redirection.'),
         P('RedirectPOSDevices', B, desc='Point of Service device redirection.'),
     ]),
    ('AdvancedSettings6', 'AdvancedSettings6', 'IMsRdpClientAdvancedSettings6', 'Authentication and focus settings.',
     [], [
         P('AuthenticationServiceClass', S, desc='Service principal name (SPN) used for authentication.'),
         P('AuthenticationType', I, acc='r', desc='Type of authentication used for this connection (read-only).'),
         P('ConnectToAdministerServer', B, desc='Connect to the server for administrative purposes.'),
         P('EnableCredSspSupport', B, desc='Enable the Credential Security Service Provider (CredSSP / NLA).'),
         P('HotKeyFocusReleaseLeft', I, desc='Virtual-key added to CTRL+ALT to replace CTRL+ALT+LEFT ARROW.'),
         P('HotKeyFocusReleaseRight', I, desc='Virtual-key added to CTRL+ALT to replace CTRL+ALT+RIGHT ARROW.'),
         P('PCB', S, desc='Preconnection BLOB (PCB) sent to the server before connecting.'),
         P('RelativeMouseMode', B, desc='True for relative mouse mode, False for absolute mode.'),
     ]),
    ('AdvancedSettings7', 'AdvancedSettings7', 'IMsRdpClientAdvancedSettings7', 'Audio capture, network type, '
                                                                                'SuperPan and video playback.',
     [('AudioQualityMode', [('DynamicQuality', 0), ('MediumQuality', 1), ('HighQuality', 2)])], [
         P('AudioCaptureRedirectionMode', B, desc='Redirect the default audio input device to the remote session.'),
         P('AudioQualityMode', I, rng=(0, 2), desc='Audio quality mode (see AdvancedSettings7.AudioQualityMode).'),
         P('EnableSuperPan', B, desc='Enable SuperPan.'),
         P('NetworkConnectionType', I, 'uint', desc='Network connection type.'),
         P('RedirectDirectX', B, desc='This property is not used.'),
         P('SuperPanAccelerationFactor', I, 'uint', desc='SuperPan acceleration factor.'),
         P('VideoPlaybackMode', I, 'uint', desc='Video playback mode.'),
     ]),
    ('AdvancedSettings8', 'AdvancedSettings8', 'IMsRdpClientAdvancedSettings8', 'Bandwidth detection.', [], [
        P('BandwidthDetection', B, desc='Specifies if bandwidth changes are automatically detected.'),
    ]),
    ('SecuredSettings', 'SecuredSettings', 'IMsRdpClientSecuredSettings', 'Start program, keyboard hook, audio and '
                                                                          'full-screen state.',
     [('KeyboardHookMode', [('ApplyLocally', 0), ('ApplyRemotely', 1), ('ApplyInFullScreen', 2)]),
      ('AudioRedirectionMode', [('RedirectToClient', 0), ('PlayOnServer', 1), ('DoNotPlay', 2)])], [
         P('AudioRedirectionMode', I, rng=(0, 2),
           desc='Redirect sounds or play them on the server (see SecuredSettings.AudioRedirectionMode).'),
         P('FullScreen', I, desc='Full-screen state of the client control.'),
         P('KeyboardHookMode', I, rng=(0, 2),
           desc='Where Windows key combinations apply (see SecuredSettings.KeyboardHookMode).'),
         P('StartProgram', S, desc='Program started on the remote server upon connection.'),
         P('WorkDir', S, desc='Working directory of the start program.'),
     ]),
    ('SecuredSettings2', 'SecuredSettings2', 'IMsRdpClientSecuredSettings2', 'Preconnection BLOB.', [], [
        P('PCB', S, desc='Preconnection BLOB (PCB) sent to the server before connecting.'),
    ]),
    ('MsRdpClientShell', 'ClientShell', 'IMsRdpClientShell', 'RDP file / RD Web Access launcher.', [], [
        P('IsRemoteProgramClientInstalled', B, acc='r',
          desc='Whether the client supports Windows Server 2008 R2 RemoteApp (read-only).'),
        P('PublicMode', B, desc='Specifies whether public mode is enabled.'),
        P('RdpFileContents', S, desc='RDP file content to launch from RD Web Access or another web portal.'),
    ]),
    ('RemoteProgram', 'RemoteProgram', 'ITSRemoteProgram', 'RemoteApp mode.', [], [
        P('RemoteProgramMode', B, desc='The RemoteApp mode.'),
    ]),
    ('RemoteProgram2', 'RemoteProgram2', 'ITSRemoteProgram2', 'RemoteApp identification.', [], [
        P('RemoteApplicationArgs', S, acc='w', desc='Command-line arguments of the RemoteApp (write-only).'),
        P('RemoteApplicationName', S, acc='w', desc='Name of the RemoteApp (write-only).'),
        P('RemoteApplicationProgram', S, acc='w', desc='Path and file name of the RemoteApp program (write-only).'),
    ]),
    ('RemoteProgram3', 'RemoteProgram3', 'ITSRemoteProgram3', 'Start a packaged app in the remote session.', [], []),
    ('TransportSettings', 'TransportSettings', 'IMsRdpClientTransportSettings', 'Remote Desktop Gateway settings.',
     [('GatewayUsageMethod', [('NoneDirect', 0), ('Direct', 1), ('Detect', 2), ('Default', 3), ('NoneDetect', 4)]),
      ('GatewayCredsSource', [('UserPassword', 0), ('SmartCard', 1), ('Any', 4)])], [
         P('GatewayCredsSource', I, 'uint', desc='RD Gateway authentication method '
                                                 '(see TransportSettings.GatewayCredsSource).'),
         P('GatewayDefaultUsageMethod', I, 'uint', acc='r', desc='Default RD Gateway usage method (read-only).'),
         P('GatewayHostname', S, desc='Host name of the RD Gateway server.'),
         P('GatewayIsSupported', I, acc='r', desc='Whether RD Gateway is supported (read-only).'),
         P('GatewayProfileUsageMethod', I, 'uint', desc='Whether to use default RD Gateway settings.'),
         P('GatewayUsageMethod', I, 'uint', desc='When to use an RD Gateway server '
                                                 '(see TransportSettings.GatewayUsageMethod).'),
         P('GatewayUserSelectedCredsSource', I, 'uint', desc='User-specified RD Gateway credential source.'),
     ]),
    ('TransportSettings2', 'TransportSettings2', 'IMsRdpClientTransportSettings2', 'RD Gateway credentials and '
                                                                                   'one-time password.', [], [
         P('GatewayCredSharing', I, 'uint', desc='Whether single sign-on for RD Gateway is enabled.'),
         P('GatewayDomain', S, desc='Domain name used to connect to the RD Gateway server.'),
         P('GatewayEncryptedOtpCookie', S, desc='The encrypted OTP cookie.'),
         P('GatewayEncryptedOtpCookieSize', I, 'uint', desc='Size, in bytes, of the encrypted OTP cookie.'),
         P('GatewayPassword', S, acc='w', secret=True,
           desc='Password used to connect to the RD Gateway server (write-only; the getter never returns it).'),
         P('GatewayPreAuthRequirement', I, desc='Whether the RD Gateway one-time password (OTP) feature is enabled.'),
         P('GatewayPreAuthServerAddr', S, desc='Web address of the pre-authentication server.'),
         P('GatewaySupportUrl', S, desc='Web address of the RD Gateway technical support site.'),
         P('GatewayUsername', S, desc='User name used to connect to the RD Gateway server.'),
     ]),
    ('TransportSettings3', 'TransportSettings3', 'IMsRdpClientTransportSettings3', 'RD Gateway cookie-based '
                                                                                   'authentication.', [], [
         P('GatewayAuthCookieServerAddr', S, desc='Server address for cookie-based authentication.'),
         P('GatewayAuthLoginPage', S, desc='Address of the login webpage used to authenticate a user.'),
         P('GatewayCredSourceCookie', I, 'uint', desc='1 if the credential source is cookie-based, 0 otherwise.'),
         P('GatewayEncryptedAuthCookie', S, desc='The encrypted authentication cookie.'),
         P('GatewayEncryptedAuthCookieSize', I, 'uint', desc='Size, in characters, of GatewayEncryptedAuthCookie.'),
     ]),
    ('TransportSettings4', 'TransportSettings4', 'IMsRdpClientTransportSettings4', 'RD Gateway brokering.', [], [
        P('GatewayBrokeringType', I, 'uint', desc='The gateway brokering type.'),
    ]),
]
