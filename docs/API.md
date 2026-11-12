# QAxRDP settings reference

Generated from the interface tables of `QAxRDP/remotedesktop/rdpsettings.py`. Every property is exposed as
a getter, a `@pyqtSlot` setter (unless read-only) and a `pyqtProperty`, so all of these work:

```python
rdp.advancedSettings.setSmartSizing(True)      # setter (slot)
rdp.advancedSettings.smartSizing = True          # pyqtProperty
rdp.advancedSettings.setProperty('smartSizing', True)
rdp.applySettings({'advancedSettings.smartSizing': True})
```

Access: **rw** read/write, **r** read-only, **w** write-only (the getter returns the last value set,
except for passwords which are never returned).

## Contents:

- [`RdpControlSettings`](#rdpcontrolsettings) - `rdp.controlSettings`
- [`RdpAdvancedSettings`](#rdpadvancedsettings) - `rdp.advancedSettings`
- [`RdpAdvancedSettings2`](#rdpadvancedsettings2) - `rdp.advancedSettings2`
- [`RdpAdvancedSettings3`](#rdpadvancedsettings3) - `rdp.advancedSettings3`
- [`RdpAdvancedSettings4`](#rdpadvancedsettings4) - `rdp.advancedSettings4`
- [`RdpAdvancedSettings5`](#rdpadvancedsettings5) - `rdp.advancedSettings5`
- [`RdpAdvancedSettings6`](#rdpadvancedsettings6) - `rdp.advancedSettings6`
- [`RdpAdvancedSettings7`](#rdpadvancedsettings7) - `rdp.advancedSettings7`
- [`RdpAdvancedSettings8`](#rdpadvancedsettings8) - `rdp.advancedSettings8`
- [`RdpSecuredSettings`](#rdpsecuredsettings) - `rdp.securedSettings`
- [`RdpSecuredSettings2`](#rdpsecuredsettings2) - `rdp.securedSettings2`
- [`RdpClientShell`](#rdpclientshell) - `rdp.clientShell`
- [`RdpRemoteProgram`](#rdpremoteprogram) - `rdp.remoteProgram`
- [`RdpRemoteProgram2`](#rdpremoteprogram2) - `rdp.remoteProgram2`
- [`RdpRemoteProgram3`](#rdpremoteprogram3) - `rdp.remoteProgram3`
- [`RdpTransportSettings`](#rdptransportsettings) - `rdp.transportSettings`
- [`RdpTransportSettings2`](#rdptransportsettings2) - `rdp.transportSettings2`
- [`RdpTransportSettings3`](#rdptransportsettings3) - `rdp.transportSettings3`
- [`RdpTransportSettings4`](#rdptransportsettings4) - `rdp.transportSettings4`

## RdpControlSettings:

Top level properties of the MsTscAx control (server, credentials, display and texts). COM interface `IMsRdpClient10`, ActiveX sub-object `(the control)`, reached with `rdp.controlSettings`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `server` | `getServer()` / `setServer()` | str | rw | `Server` | Name or IP address of the server to connect to. |
| `domain` | `getDomain()` / `setDomain()` | str | rw | `Domain` | Domain to which the current user logs on. |
| `userName` | `getUserName()` / `setUserName()` | str | rw | `UserName` | User name logon credential. |
| `colorDepth` | `getColorDepth()` / `setColorDepth()` | int | rw | `ColorDepth` | Color depth, in bits per pixel (8, 15, 16, 24 or 32). |
| `desktopWidth` | `getDesktopWidth()` / `setDesktopWidth()` | int | rw | `DesktopWidth` | Width, in pixels, of the initial remote desktop. |
| `desktopHeight` | `getDesktopHeight()` / `setDesktopHeight()` | int | rw | `DesktopHeight` | Height, in pixels, of the initial remote desktop. |
| `connectingText` | `getConnectingText()` / `setConnectingText()` | str | rw | `ConnectingText` | Text displayed centered in the control while connecting. |
| `connectedStatusText` | `getConnectedStatusText()` / `setConnectedStatusText()` | str | rw | `ConnectedStatusText` | Text displayed in the control once connected. |
| `disconnectedText` | `getDisconnectedText()` / `setDisconnectedText()` | str | rw | `DisconnectedText` | Text displayed centered in the control when disconnected. |
| `fullScreenTitle` | `getFullScreenTitle()` / `setFullScreenTitle()` | str | w | `FullScreenTitle` | Window title displayed in full-screen mode (write-only). |
| `fullScreen` | `isFullScreen()` / `setFullScreen()` | bool | rw | `FullScreen` | Full-screen state of the control. |
| `startConnected` | `getStartConnected()` / `setStartConnected()` | int | rw | `StartConnected` | Connect immediately upon startup (1) or not (0). |
| `securedSettingsEnabled` | `getSecuredSettingsEnabled()` | int | r | `SecuredSettingsEnabled` | Whether the secured settings interface is available (read-only). |
| `version` | `getVersion()` | str | r | `Version` | Version number of the control (read-only). |
| `cipherStrength` | `getCipherStrength()` | int | r | `CipherStrength` | Maximum encryption strength of the control (read-only). |
| `horizontalScrollBarVisible` | `getHorizontalScrollBarVisible()` | int | r | `HorizontalScrollBarVisible` | Whether the control displays a horizontal scroll bar (read-only). |
| `verticalScrollBarVisible` | `getVerticalScrollBarVisible()` | int | r | `VerticalScrollBarVisible` | Whether the control displays a vertical scroll bar (read-only). |
| `connected` | `getConnected()` | int | r | `Connected` | Connection state: 0 disconnected, 1 connected, 2 connecting (read-only). |
| `extendedDisconnectReason` | `getExtendedDisconnectReason()` | int | r | `ExtendedDisconnectReason` | Extended information about the last disconnection (read-only). |

## RdpAdvancedSettings:

Advanced settings of the control: bitmap caching, hot keys, redirection, timeouts, port... COM interface `IMsRdpClientAdvancedSettings`, ActiveX sub-object `AdvancedSettings`, reached with `rdp.advancedSettings`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `acceleratorPassthrough` | `isAcceleratorPassthrough()` / `setAcceleratorPassthrough()` | bool | rw | `AcceleratorPassthrough` | Specifies whether accelerator passthrough is enabled. |
| `allowBackgroundInput` | `getAllowBackgroundInput()` / `setAllowBackgroundInput()` | int | rw | `allowBackgroundInput` | Specifies whether background input mode is enabled. |
| `bitmapCacheSize` | `getBitmapCacheSize()` / `setBitmapCacheSize()` | int | rw | `BitmapCacheSize` | Size, in kilobytes, of the bitmap cache file used for 8 bpp bitmaps (1 to 32). |
| `bitmapPeristence` | `getBitmapPeristence()` / `setBitmapPeristence()` | int | rw | `BitmapPeristence` | Specifies whether bitmap caching is enabled (the misspelling is in the released version of the control). |
| `bitmapPersistence` | `getBitmapPersistence()` / `setBitmapPersistence()` | int | rw | `BitmapPersistence` | Specifies if persistent bitmap caching should be used. |
| `bitmapVirtualCache16BppSize` | `getBitmapVirtualCache16BppSize()` / `setBitmapVirtualCache16BppSize()` | int | rw | `BitmapVirtualCache16BppSize` | Size, in megabytes, of the persistent bitmap cache file for 15 and 16 bpp. |
| `bitmapVirtualCache24BppSize` | `getBitmapVirtualCache24BppSize()` / `setBitmapVirtualCache24BppSize()` | int | rw | `BitmapVirtualCache24BppSize` | Size, in megabytes, of the persistent bitmap cache file for 24 bpp. |
| `bitmapVirtualCacheSize` | `getBitmapVirtualCacheSize()` / `setBitmapVirtualCacheSize()` | int | rw | `BitmapVirtualCacheSize` | Size, in megabytes, of the persistent bitmap cache file for 8 bpp (1 to 32). |
| `brushSupportLevel` | `getBrushSupportLevel()` / `setBrushSupportLevel()` | int | rw | `brushSupportLevel` | Specifies the level of brush support. |
| `cachePersistenceActive` | `getCachePersistenceActive()` / `setCachePersistenceActive()` | int | rw | `CachePersistenceActive` | Specifies whether persistent bitmap caching should be used. |
| `clearTextPassword` | `getClearTextPassword()` / `setClearTextPassword()` | str | w | `ClearTextPassword` | Password used to connect (write-only; the getter never returns it). |
| `compress` | `getCompress()` / `setCompress()` | int | rw | `Compress` | Specifies whether compression is enabled. |
| `connectToServerConsole` | `isConnectToServerConsole()` / `setConnectToServerConsole()` | bool | rw | `ConnectToServerConsole` | This property is not supported by recent versions of the control (kept for completeness). |
| `connectWithEndpoint` | `getConnectWithEndpoint()` / `setConnectWithEndpoint()` | int | w | `ConnectWithEndpoint` | This property is not supported by recent versions of the control (kept for completeness). |
| `containerHandledFullScreen` | `getContainerHandledFullScreen()` / `setContainerHandledFullScreen()` | int | rw | `ContainerHandledFullScreen` | Specifies whether the container-handled full-screen mode is enabled. |
| `dedicatedTerminal` | `getDedicatedTerminal()` / `setDedicatedTerminal()` | int | rw | `DedicatedTerminal` | This property is not supported by recent versions of the control (kept for completeness). |
| `disableCtrlAltDel` | `getDisableCtrlAltDel()` / `setDisableCtrlAltDel()` | int | rw | `DisableCtrlAltDel` | Specifies if the initial explanatory screen in Winlogon should display. |
| `disableRdpdr` | `getDisableRdpdr()` / `setDisableRdpdr()` | int | rw | `DisableRdpdr` | Specifies whether printer and clipboard redirection is enabled. |
| `displayConnectionBar` | `isDisplayConnectionBar()` / `setDisplayConnectionBar()` | bool | rw | `DisplayConnectionBar` | Specifies whether to use the connection bar. |
| `doubleClickDetect` | `getDoubleClickDetect()` / `setDoubleClickDetect()` | int | rw | `DoubleClickDetect` | Specifies if the client identifies double-clicks for the server. |
| `enableMouse` | `getEnableMouse()` / `setEnableMouse()` | int | rw | `EnableMouse` | This property is not supported by recent versions of the control (kept for completeness). |
| `enableWindowsKey` | `getEnableWindowsKey()` / `setEnableWindowsKey()` | int | rw | `EnableWindowsKey` | Specifies if the Windows key can be used in the remote session. |
| `encryptionEnabled` | `getEncryptionEnabled()` / `setEncryptionEnabled()` | int | rw | `EncryptionEnabled` | Not supported: encryption cannot be disabled. |
| `grabFocusOnConnect` | `isGrabFocusOnConnect()` / `setGrabFocusOnConnect()` | bool | rw | `GrabFocusOnConnect` | Specifies if the client control should have the focus while connecting. |
| `hotKeyAltEsc` | `getHotKeyAltEsc()` / `setHotKeyAltEsc()` | int | rw | `HotKeyAltEsc` | Virtual-key added to ALT to replace ALT+ESC (default VK_INSERT). |
| `hotKeyAltShiftTab` | `getHotKeyAltShiftTab()` / `setHotKeyAltShiftTab()` | int | rw | `HotKeyAltShiftTab` | Virtual-key added to ALT to replace ALT+SHIFT+TAB (default VK_NEXT). |
| `hotKeyAltSpace` | `getHotKeyAltSpace()` / `setHotKeyAltSpace()` | int | rw | `HotKeyAltSpace` | Virtual-key added to ALT to replace ALT+SPACE (default VK_DELETE). |
| `hotKeyAltTab` | `getHotKeyAltTab()` / `setHotKeyAltTab()` | int | rw | `HotKeyAltTab` | Virtual-key added to ALT to replace ALT+TAB (default VK_PRIOR). |
| `hotKeyCtrlAltDel` | `getHotKeyCtrlAltDel()` / `setHotKeyCtrlAltDel()` | int | rw | `HotKeyCtrlAltDel` | Virtual-key added to CTRL+ALT to replace CTRL+ALT+DELETE (default VK_END). |
| `hotKeyCtrlEsc` | `getHotKeyCtrlEsc()` / `setHotKeyCtrlEsc()` | int | rw | `HotKeyCtrlEsc` | Virtual-key added to ALT to replace CTRL+ESC (default VK_HOME). |
| `hotKeyFullScreen` | `getHotKeyFullScreen()` / `setHotKeyFullScreen()` | int | rw | `HotKeyFullScreen` | Virtual-key added to CTRL+ALT to switch to full-screen mode (default VK_CANCEL). |
| `iconFile` | `getIconFile()` / `setIconFile()` | str | w | `IconFile` | File containing the icon displayed in full-screen mode (write-only). |
| `iconIndex` | `getIconIndex()` / `setIconIndex()` | int | rw | `IconIndex` | Index of the icon within the current icon file. |
| `inputEventsAtOnce` | `getInputEventsAtOnce()` / `setInputEventsAtOnce()` | int | rw | `InputEventsAtOnce` | This property is not supported by recent versions of the control (kept for completeness). |
| `keepAliveInterval` | `getKeepAliveInterval()` / `setKeepAliveInterval()` | int | rw | `keepAliveInterval` | Interval, in ms, of keep-alive messages (0 disables, minimum valid value is 10000). |
| `keyboardFunctionKey` | `getKeyboardFunctionKey()` / `setKeyboardFunctionKey()` | int | rw | `KeyboardFunctionKey` | Valid for Windows CE only. |
| `keyBoardLayoutStr` | `getKeyBoardLayoutStr()` / `setKeyBoardLayoutStr()` | str | w | `KeyBoardLayoutStr` | Active input locale identifier (keyboard layout) to use (write-only). |
| `keyboardSubType` | `getKeyboardSubType()` / `setKeyboardSubType()` | int | rw | `KeyboardSubType` | Specifies the keyboard subtype. |
| `keyboardType` | `getKeyboardType()` / `setKeyboardType()` | int | rw | `KeyboardType` | Specifies the keyboard type. |
| `loadBalanceInfo` | `getLoadBalanceInfo()` / `setLoadBalanceInfo()` | str | rw | `LoadBalanceInfo` | Load balancing cookie placed in the X.224 Connection Request packet. |
| `maxEventCount` | `getMaxEventCount()` / `setMaxEventCount()` | int | rw | `maxEventCount` | This property is not supported by recent versions of the control (kept for completeness). |
| `maximizeShell` | `getMaximizeShell()` / `setMaximizeShell()` | int | rw | `MaximizeShell` | Specifies if programs launched with StartProgram should be maximized. |
| `minInputSendInterval` | `getMinInputSendInterval()` / `setMinInputSendInterval()` | int | rw | `minInputSendInterval` | Minimum interval, in ms, between the sending of mouse events. |
| `minutesToIdleTimeout` | `getMinutesToIdleTimeout()` / `setMinutesToIdleTimeout()` | int | rw | `MinutesToIdleTimeout` | Maximum time, in minutes, to stay connected without user input (0 to 240). |
| `notifyTSPublicKey` | `isNotifyTSPublicKey()` / `setNotifyTSPublicKey()` | bool | rw | `NotifyTSPublicKey` | Specifies whether receivedTSPublicKey is emitted during connection. |
| `numBitmapCaches` | `getNumBitmapCaches()` / `setNumBitmapCaches()` | int | rw | `NumBitmapCaches` | This property is not supported by recent versions of the control (kept for completeness). |
| `orderDrawThreshold` | `getOrderDrawThreshold()` / `setOrderDrawThreshold()` | int | rw | `orderDrawThreshold` | This property is not supported by recent versions of the control (kept for completeness). |
| `overallConnectionTimeout` | `getOverallConnectionTimeout()` / `setOverallConnectionTimeout()` | int | rw | `overallConnectionTimeout` | Total time, in seconds, the control waits for a connection to complete (0 to 600). |
| `performanceFlags` | `getPerformanceFlags()` / `setPerformanceFlags()` | int | rw | `PerformanceFlags` | Set of features that can be set at the server to improve performance. |
| `persistCacheDirectory` | `getPersistCacheDirectory()` / `setPersistCacheDirectory()` | str | rw | `PersistCacheDirectory` | This property is not supported by recent versions of the control (kept for completeness). |
| `pinConnectionBar` | `isPinConnectionBar()` / `setPinConnectionBar()` | bool | rw | `PinConnectionBar` | State of the connection bar: True = pinned, False = auto-hide. |
| `pluginDlls` | `getPluginDlls()` / `setPluginDlls()` | str | w | `PluginDlls` | Names of virtual channel client DLLs to be loaded (write-only). |
| `rdpdrClipCleanTempDirString` | `getRdpdrClipCleanTempDirString()` / `setRdpdrClipCleanTempDirString()` | str | rw | `RdpdrClipCleanTempDirString` | This property is not supported by recent versions of the control (kept for completeness). |
| `rdpdrClipPasteInfoString` | `getRdpdrClipPasteInfoString()` / `setRdpdrClipPasteInfoString()` | str | rw | `RdpdrClipPasteInfoString` | This property is not supported by recent versions of the control (kept for completeness). |
| `rdpdrLocalPrintingDocName` | `getRdpdrLocalPrintingDocName()` / `setRdpdrLocalPrintingDocName()` | str | rw | `RdpdrLocalPrintingDocName` | This property is not supported by recent versions of the control (kept for completeness). |
| `rdpPort` | `getRdpPort()` / `setRdpPort()` | int | rw | `RDPPort` | Connection port (default 3389). |
| `redirectDrives` | `isRedirectDrives()` / `setRedirectDrives()` | bool | rw | `RedirectDrives` | Specifies if redirection of disk drives is allowed. |
| `redirectPorts` | `isRedirectPorts()` / `setRedirectPorts()` | bool | rw | `RedirectPorts` | Specifies if redirection of local ports (COM, LPT) is allowed. |
| `redirectPrinters` | `isRedirectPrinters()` / `setRedirectPrinters()` | bool | rw | `RedirectPrinters` | Specifies if redirection of printers is allowed. |
| `redirectSmartCards` | `isRedirectSmartCards()` / `setRedirectSmartCards()` | bool | rw | `RedirectSmartCards` | Specifies if redirection of smart cards is allowed. |
| `sasSequence` | `getSasSequence()` / `setSasSequence()` | int | rw | `SasSequence` | Secure access sequence (SAS) used to access the login screen. |
| `scaleBitmapCachesByBPP` | `getScaleBitmapCachesByBPP()` / `setScaleBitmapCachesByBPP()` | int | rw | `ScaleBitmapCachesByBPP` | This property is not supported by recent versions of the control (kept for completeness). |
| `shadowBitmap` | `getShadowBitmap()` / `setShadowBitmap()` | int | rw | `ShadowBitmap` | This property is not supported by recent versions of the control (kept for completeness). |
| `shutdownTimeout` | `getShutdownTimeout()` / `setShutdownTimeout()` | int | rw | `shutdownTimeout` | Time, in seconds, to wait for the server to answer a disconnection request (0 to 600). |
| `singleConnectionTimeout` | `getSingleConnectionTimeout()` / `setSingleConnectionTimeout()` | int | rw | `singleConnectionTimeout` | Maximum time, in seconds, to wait for a connection to one IP address (0 to 600). |
| `smartSizing` | `isSmartSizing()` / `setSmartSizing()` | bool | rw | `SmartSizing` | Scale the remote display to fit the client area of the control. |
| `smoothScroll` | `getSmoothScroll()` / `setSmoothScroll()` | int | rw | `SmoothScroll` | This property is not supported by recent versions of the control (kept for completeness). |
| `transportType` | `getTransportType()` / `setTransportType()` | int | rw | `TransportType` | Transport type used by the client (not used by the ActiveX control). |
| `winceFixedPalette` | `getWinceFixedPalette()` / `setWinceFixedPalette()` | int | rw | `WinceFixedPalette` | Valid for Windows CE only. |

## RdpAdvancedSettings2:

Automatic reconnection settings. COM interface `IMsRdpClientAdvancedSettings2`, ActiveX sub-object `AdvancedSettings2`, reached with `rdp.advancedSettings2`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `canAutoReconnect` | `getCanAutoReconnect()` | bool | r | `CanAutoReconnect` | Whether the control can reconnect automatically to the current session (read-only). |
| `enableAutoReconnect` | `isEnableAutoReconnect()` / `setEnableAutoReconnect()` | bool | rw | `EnableAutoReconnect` | Enable automatic reconnection in the event of a network disconnection. |
| `maxReconnectAttempts` | `getMaxReconnectAttempts()` / `setMaxReconnectAttempts()` | int | rw | `MaxReconnectAttempts` | Number of times to try to reconnect during automatic reconnection (0 to 200). |

## RdpAdvancedSettings3:

Connection bar buttons. COM interface `IMsRdpClientAdvancedSettings3`, ActiveX sub-object `AdvancedSettings3`, reached with `rdp.advancedSettings3`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `connectionBarShowMinimizeButton` | `isConnectionBarShowMinimizeButton()` / `setConnectionBarShowMinimizeButton()` | bool | rw | `ConnectionBarShowMinimizeButton` | Display the Minimize button on the connection bar. |
| `connectionBarShowRestoreButton` | `isConnectionBarShowRestoreButton()` / `setConnectionBarShowRestoreButton()` | bool | rw | `ConnectionBarShowRestoreButton` | Display the Restore button on the connection bar. |

## RdpAdvancedSettings4:

Server authentication level. COM interface `IMsRdpClientAdvancedSettings4`, ActiveX sub-object `AdvancedSettings4`, reached with `rdp.advancedSettings4`.

Enum `RdpAdvancedSettings4.AuthenticationLevel`: `NoAuthentication` = 0, `AuthenticationRequired` = 1, `AuthenticationWarn` = 2.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `authenticationLevel` | `getAuthenticationLevel()` / `setAuthenticationLevel()` | int | rw | `AuthenticationLevel` | Authentication level (see RdpAdvancedSettings4.AuthenticationLevel). |

## RdpAdvancedSettings5:

Audio, clipboard, devices and public mode. COM interface `IMsRdpClientAdvancedSettings5`, ActiveX sub-object `AdvancedSettings5`, reached with `rdp.advancedSettings5`.

Enum `RdpAdvancedSettings5.AudioRedirectionMode`: `RedirectToClient` = 0, `PlayOnServer` = 1, `DoNotPlay` = 2.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `audioRedirectionMode` | `getAudioRedirectionMode()` / `setAudioRedirectionMode()` | int | rw | `AudioRedirectionMode` | Audio redirection mode (see RdpAdvancedSettings5.AudioRedirectionMode). |
| `bitmapVirtualCache32BppSize` | `getBitmapVirtualCache32BppSize()` / `setBitmapVirtualCache32BppSize()` | int | rw | `BitmapVirtualCache32BppSize` | Virtual cache file size for 32 bpp bitmaps. |
| `connectionBarShowPinButton` | `isConnectionBarShowPinButton()` / `setConnectionBarShowPinButton()` | bool | rw | `ConnectionBarShowPinButton` | Display the pin button on the connection bar. |
| `publicMode` | `isPublicMode()` / `setPublicMode()` | bool | rw | `PublicMode` | Public mode prevents the client from caching user data to the local system. |
| `redirectClipboard` | `isRedirectClipboard()` / `setRedirectClipboard()` | bool | rw | `RedirectClipboard` | Clipboard redirection. |
| `redirectDevices` | `isRedirectDevices()` / `setRedirectDevices()` | bool | rw | `RedirectDevices` | Device redirection. |
| `redirectPOSDevices` | `isRedirectPOSDevices()` / `setRedirectPOSDevices()` | bool | rw | `RedirectPOSDevices` | Point of Service device redirection. |

## RdpAdvancedSettings6:

Authentication and focus settings. COM interface `IMsRdpClientAdvancedSettings6`, ActiveX sub-object `AdvancedSettings6`, reached with `rdp.advancedSettings6`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `authenticationServiceClass` | `getAuthenticationServiceClass()` / `setAuthenticationServiceClass()` | str | rw | `AuthenticationServiceClass` | Service principal name (SPN) used for authentication. |
| `authenticationType` | `getAuthenticationType()` | int | r | `AuthenticationType` | Type of authentication used for this connection (read-only). |
| `connectToAdministerServer` | `isConnectToAdministerServer()` / `setConnectToAdministerServer()` | bool | rw | `ConnectToAdministerServer` | Connect to the server for administrative purposes. |
| `enableCredSspSupport` | `isEnableCredSspSupport()` / `setEnableCredSspSupport()` | bool | rw | `EnableCredSspSupport` | Enable the Credential Security Service Provider (CredSSP / NLA). |
| `hotKeyFocusReleaseLeft` | `getHotKeyFocusReleaseLeft()` / `setHotKeyFocusReleaseLeft()` | int | rw | `HotKeyFocusReleaseLeft` | Virtual-key added to CTRL+ALT to replace CTRL+ALT+LEFT ARROW. |
| `hotKeyFocusReleaseRight` | `getHotKeyFocusReleaseRight()` / `setHotKeyFocusReleaseRight()` | int | rw | `HotKeyFocusReleaseRight` | Virtual-key added to CTRL+ALT to replace CTRL+ALT+RIGHT ARROW. |
| `pcb` | `getPcb()` / `setPcb()` | str | rw | `PCB` | Preconnection BLOB (PCB) sent to the server before connecting. |
| `relativeMouseMode` | `isRelativeMouseMode()` / `setRelativeMouseMode()` | bool | rw | `RelativeMouseMode` | True for relative mouse mode, False for absolute mode. |

## RdpAdvancedSettings7:

Audio capture, network type, SuperPan and video playback. COM interface `IMsRdpClientAdvancedSettings7`, ActiveX sub-object `AdvancedSettings7`, reached with `rdp.advancedSettings7`.

Enum `RdpAdvancedSettings7.AudioQualityMode`: `DynamicQuality` = 0, `MediumQuality` = 1, `HighQuality` = 2.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `audioCaptureRedirectionMode` | `isAudioCaptureRedirectionMode()` / `setAudioCaptureRedirectionMode()` | bool | rw | `AudioCaptureRedirectionMode` | Redirect the default audio input device to the remote session. |
| `audioQualityMode` | `getAudioQualityMode()` / `setAudioQualityMode()` | int | rw | `AudioQualityMode` | Audio quality mode (see RdpAdvancedSettings7.AudioQualityMode). |
| `enableSuperPan` | `isEnableSuperPan()` / `setEnableSuperPan()` | bool | rw | `EnableSuperPan` | Enable SuperPan. |
| `networkConnectionType` | `getNetworkConnectionType()` / `setNetworkConnectionType()` | int | rw | `NetworkConnectionType` | Network connection type. |
| `redirectDirectX` | `isRedirectDirectX()` / `setRedirectDirectX()` | bool | rw | `RedirectDirectX` | This property is not used. |
| `superPanAccelerationFactor` | `getSuperPanAccelerationFactor()` / `setSuperPanAccelerationFactor()` | int | rw | `SuperPanAccelerationFactor` | SuperPan acceleration factor. |
| `videoPlaybackMode` | `getVideoPlaybackMode()` / `setVideoPlaybackMode()` | int | rw | `VideoPlaybackMode` | Video playback mode. |

## RdpAdvancedSettings8:

Bandwidth detection. COM interface `IMsRdpClientAdvancedSettings8`, ActiveX sub-object `AdvancedSettings8`, reached with `rdp.advancedSettings8`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `bandwidthDetection` | `isBandwidthDetection()` / `setBandwidthDetection()` | bool | rw | `BandwidthDetection` | Specifies if bandwidth changes are automatically detected. |

## RdpSecuredSettings:

Start program, keyboard hook, audio and full-screen state. COM interface `IMsRdpClientSecuredSettings`, ActiveX sub-object `SecuredSettings`, reached with `rdp.securedSettings`.

Enum `RdpSecuredSettings.KeyboardHookMode`: `ApplyLocally` = 0, `ApplyRemotely` = 1, `ApplyInFullScreen` = 2.

Enum `RdpSecuredSettings.AudioRedirectionMode`: `RedirectToClient` = 0, `PlayOnServer` = 1, `DoNotPlay` = 2.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `audioRedirectionMode` | `getAudioRedirectionMode()` / `setAudioRedirectionMode()` | int | rw | `AudioRedirectionMode` | Redirect sounds or play them on the server (see RdpSecuredSettings.AudioRedirectionMode). |
| `fullScreen` | `getFullScreen()` / `setFullScreen()` | int | rw | `FullScreen` | Full-screen state of the client control. |
| `keyboardHookMode` | `getKeyboardHookMode()` / `setKeyboardHookMode()` | int | rw | `KeyboardHookMode` | Where Windows key combinations apply (see RdpSecuredSettings.KeyboardHookMode). |
| `startProgram` | `getStartProgram()` / `setStartProgram()` | str | rw | `StartProgram` | Program started on the remote server upon connection. |
| `workDir` | `getWorkDir()` / `setWorkDir()` | str | rw | `WorkDir` | Working directory of the start program. |

## RdpSecuredSettings2:

Preconnection BLOB. COM interface `IMsRdpClientSecuredSettings2`, ActiveX sub-object `SecuredSettings2`, reached with `rdp.securedSettings2`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `pcb` | `getPcb()` / `setPcb()` | str | rw | `PCB` | Preconnection BLOB (PCB) sent to the server before connecting. |

## RdpClientShell:

RDP file / RD Web Access launcher. COM interface `IMsRdpClientShell`, ActiveX sub-object `MsRdpClientShell`, reached with `rdp.clientShell`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `remoteProgramClientInstalled` | `isRemoteProgramClientInstalled()` | bool | r | `IsRemoteProgramClientInstalled` | Whether the client supports Windows Server 2008 R2 RemoteApp (read-only). |
| `publicMode` | `isPublicMode()` / `setPublicMode()` | bool | rw | `PublicMode` | Specifies whether public mode is enabled. |
| `rdpFileContents` | `getRdpFileContents()` / `setRdpFileContents()` | str | rw | `RdpFileContents` | RDP file content to launch from RD Web Access or another web portal. |

Methods:

- `getRdpProperty(name)`
- `setRdpProperty(name, value)`
- `launch()`
- `showTrustedSitesManagementDialog()`

## RdpRemoteProgram:

RemoteApp mode. COM interface `ITSRemoteProgram`, ActiveX sub-object `RemoteProgram`, reached with `rdp.remoteProgram`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `remoteProgramMode` | `isRemoteProgramMode()` / `setRemoteProgramMode()` | bool | rw | `RemoteProgramMode` | The RemoteApp mode. |

Methods:

- `serverStartProgram(executablePath, filePath='', workingDirectory='', expandEnvVarInWorkingDirectoryOnServer=False, arguments='', expandEnvVarInArgumentsOnServer=False)`

## RdpRemoteProgram2:

RemoteApp identification. COM interface `ITSRemoteProgram2`, ActiveX sub-object `RemoteProgram2`, reached with `rdp.remoteProgram2`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `remoteApplicationArgs` | `getRemoteApplicationArgs()` / `setRemoteApplicationArgs()` | str | w | `RemoteApplicationArgs` | Command-line arguments of the RemoteApp (write-only). |
| `remoteApplicationName` | `getRemoteApplicationName()` / `setRemoteApplicationName()` | str | w | `RemoteApplicationName` | Name of the RemoteApp (write-only). |
| `remoteApplicationProgram` | `getRemoteApplicationProgram()` / `setRemoteApplicationProgram()` | str | w | `RemoteApplicationProgram` | Path and file name of the RemoteApp program (write-only). |

## RdpRemoteProgram3:

Start a packaged app in the remote session. COM interface `ITSRemoteProgram3`, ActiveX sub-object `RemoteProgram3`, reached with `rdp.remoteProgram3`.

Methods:

- `serverStartApp(appUserModelId, arguments='', expandEnvVarInArgumentsOnServer=False)`

## RdpTransportSettings:

Remote Desktop Gateway settings. COM interface `IMsRdpClientTransportSettings`, ActiveX sub-object `TransportSettings`, reached with `rdp.transportSettings`.

Enum `RdpTransportSettings.GatewayUsageMethod`: `NoneDirect` = 0, `Direct` = 1, `Detect` = 2, `Default` = 3, `NoneDetect` = 4.

Enum `RdpTransportSettings.GatewayCredsSource`: `UserPassword` = 0, `SmartCard` = 1, `Any` = 4.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `gatewayCredsSource` | `getGatewayCredsSource()` / `setGatewayCredsSource()` | int | rw | `GatewayCredsSource` | RD Gateway authentication method (see RdpTransportSettings.GatewayCredsSource). |
| `gatewayDefaultUsageMethod` | `getGatewayDefaultUsageMethod()` | int | r | `GatewayDefaultUsageMethod` | Default RD Gateway usage method (read-only). |
| `gatewayHostname` | `getGatewayHostname()` / `setGatewayHostname()` | str | rw | `GatewayHostname` | Host name of the RD Gateway server. |
| `gatewayIsSupported` | `getGatewayIsSupported()` | int | r | `GatewayIsSupported` | Whether RD Gateway is supported (read-only). |
| `gatewayProfileUsageMethod` | `getGatewayProfileUsageMethod()` / `setGatewayProfileUsageMethod()` | int | rw | `GatewayProfileUsageMethod` | Whether to use default RD Gateway settings. |
| `gatewayUsageMethod` | `getGatewayUsageMethod()` / `setGatewayUsageMethod()` | int | rw | `GatewayUsageMethod` | When to use an RD Gateway server (see RdpTransportSettings.GatewayUsageMethod). |
| `gatewayUserSelectedCredsSource` | `getGatewayUserSelectedCredsSource()` / `setGatewayUserSelectedCredsSource()` | int | rw | `GatewayUserSelectedCredsSource` | User-specified RD Gateway credential source. |

## RdpTransportSettings2:

RD Gateway credentials and one-time password. COM interface `IMsRdpClientTransportSettings2`, ActiveX sub-object `TransportSettings2`, reached with `rdp.transportSettings2`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `gatewayCredSharing` | `getGatewayCredSharing()` / `setGatewayCredSharing()` | int | rw | `GatewayCredSharing` | Whether single sign-on for RD Gateway is enabled. |
| `gatewayDomain` | `getGatewayDomain()` / `setGatewayDomain()` | str | rw | `GatewayDomain` | Domain name used to connect to the RD Gateway server. |
| `gatewayEncryptedOtpCookie` | `getGatewayEncryptedOtpCookie()` / `setGatewayEncryptedOtpCookie()` | str | rw | `GatewayEncryptedOtpCookie` | The encrypted OTP cookie. |
| `gatewayEncryptedOtpCookieSize` | `getGatewayEncryptedOtpCookieSize()` / `setGatewayEncryptedOtpCookieSize()` | int | rw | `GatewayEncryptedOtpCookieSize` | Size, in bytes, of the encrypted OTP cookie. |
| `gatewayPassword` | `getGatewayPassword()` / `setGatewayPassword()` | str | w | `GatewayPassword` | Password used to connect to the RD Gateway server (write-only; the getter never returns it). |
| `gatewayPreAuthRequirement` | `getGatewayPreAuthRequirement()` / `setGatewayPreAuthRequirement()` | int | rw | `GatewayPreAuthRequirement` | Whether the RD Gateway one-time password (OTP) feature is enabled. |
| `gatewayPreAuthServerAddr` | `getGatewayPreAuthServerAddr()` / `setGatewayPreAuthServerAddr()` | str | rw | `GatewayPreAuthServerAddr` | Web address of the pre-authentication server. |
| `gatewaySupportUrl` | `getGatewaySupportUrl()` / `setGatewaySupportUrl()` | str | rw | `GatewaySupportUrl` | Web address of the RD Gateway technical support site. |
| `gatewayUsername` | `getGatewayUsername()` / `setGatewayUsername()` | str | rw | `GatewayUsername` | User name used to connect to the RD Gateway server. |

## RdpTransportSettings3:

RD Gateway cookie-based authentication. COM interface `IMsRdpClientTransportSettings3`, ActiveX sub-object `TransportSettings3`, reached with `rdp.transportSettings3`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `gatewayAuthCookieServerAddr` | `getGatewayAuthCookieServerAddr()` / `setGatewayAuthCookieServerAddr()` | str | rw | `GatewayAuthCookieServerAddr` | Server address for cookie-based authentication. |
| `gatewayAuthLoginPage` | `getGatewayAuthLoginPage()` / `setGatewayAuthLoginPage()` | str | rw | `GatewayAuthLoginPage` | Address of the login webpage used to authenticate a user. |
| `gatewayCredSourceCookie` | `getGatewayCredSourceCookie()` / `setGatewayCredSourceCookie()` | int | rw | `GatewayCredSourceCookie` | 1 if the credential source is cookie-based, 0 otherwise. |
| `gatewayEncryptedAuthCookie` | `getGatewayEncryptedAuthCookie()` / `setGatewayEncryptedAuthCookie()` | str | rw | `GatewayEncryptedAuthCookie` | The encrypted authentication cookie. |
| `gatewayEncryptedAuthCookieSize` | `getGatewayEncryptedAuthCookieSize()` / `setGatewayEncryptedAuthCookieSize()` | int | rw | `GatewayEncryptedAuthCookieSize` | Size, in characters, of GatewayEncryptedAuthCookie. |

## RdpTransportSettings4:

RD Gateway brokering. COM interface `IMsRdpClientTransportSettings4`, ActiveX sub-object `TransportSettings4`, reached with `rdp.transportSettings4`.

| Property | Getter / Setter | Type | Access | ActiveX name | Description |
|---|---|---|---|---|---|
| `gatewayBrokeringType` | `getGatewayBrokeringType()` / `setGatewayBrokeringType()` | int | rw | `GatewayBrokeringType` | The gateway brokering type. |
