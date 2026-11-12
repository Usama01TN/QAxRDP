# Changelog

## 2.1.0 - 2026-11-11

### Added:

- Qt Designer plugins (`QAxRDP/designer`): `RemoteDesktopWidget`, `ConnectionBar` and `StatusDot` in a "QAxRDP"
  widget box section, with icons, tooltips and default sizes.
    - `qaxrdpplugin.py` for PyQt5 / PyQt6 / PyQt4 (`PYQTDESIGNERPATH`), `registerqaxrdp.py` for PySide6
      (`PYSIDE_DESIGNER_PLUGINS`), both reading the same widget descriptions (`widgetinfo.py`).
    - `qaxrdp-designer` command: finds a Qt Designer for the binding (`pyside6-designer`, `pyqt5-tools designer`,
      `pyqt6-tools designer`, `designer`) and starts it with the plugins registered; `--preview` shows the plugins
      without Designer; `--print-env` prints the variables for another Designer or Qt Creator.
    - Forms use the header `QAxRDP`: `pyuic5`, `pyside6-uic`, `uic.loadUi` and `QUiLoader` were tested with them.
    - The PySide6 script adds the site-packages of `VIRTUAL_ENV`, which Designer's embedded Python can miss.
- `RemoteDesktopWidget.autoCreateControl` option and `DEFAULT_AUTO_CREATE_CONTROL`: Designer shows a placeholder
  instead of starting the RDP control.
- Logo, banner (PNG and font independent SVG), application icon and Designer icons, drawn by
  `tools/branding/makebranding.py`; the application window uses the logo.
- `[designer]` install extra (PySide6, which ships a Designer able to load Python plugins).
- Tests of the Designer integration; the whole suite also runs on PySide6 (`QT_API=pyside6`).
- Release workflow (`.github/workflows/release.yml`): checks the version and this changelog, runs the tests (PyQt5 on
  Python 3.10 / 3.12 / 3.13, PySide6, and Windows with the ActiveX control), builds and checks the distributions, then
  publishes them on PyPI and in the GitHub release `v<version>` (forced: an existing release and tag are recreated).
- PyPI project links (source, issues, releases, changelog), and README links and images made absolute for PyPI when
  built by the workflow.

### Changed:

- Settings objects, password and runtime state properties are no longer designable, so they are not shown in
  Designer's property editor nor saved in `.ui` files (the password is never written to a form).
- `exec()` is used instead of the deprecated `exec_()` when the binding provides it (no warning with PySide6).
- Banner: only the word mark and the tag line are kept.
- License declared as the SPDX expression `GPL-3.0-only` instead of a license classifier (deprecated by setuptools).
- The wheel is tagged `py3` (setuptools deprecated universal wheels); Python 2 installs from the sdist.

## 2.0.0 - 2026-11-11:

Complete rewrite on Qt logic and ManyQt. The API changed: see "Migrating from QAxRDP 1.x" in the README.

### Changed:

- Qt imports go through ManyQt instead of PyQt5: PyQt4, PyQt5, PyQt6, PySide, PySide2 and PySide6 are supported.
- `QAxRemoteDesktop(QAxWidget)` became `RemoteDesktopWidget(QWidget)`, which hosts the `QAxWidget` in a layout.
- ActiveX events are re-emitted as typed signals (`connected`, `disconnected(int)`...) instead of overridable
  `onXxx` methods; any signal can be given to the constructor as a callable keyword argument.
- Dual-purpose methods (`Server(value)` to set, `Server()` to get) became getters, `@pyqtSlot` setters and
  `pyqtProperty` declarations.
- The nested settings classes became QObjects (`RdpAdvancedSettings`, `RdpSecuredSettings`...) reached through
  read-only properties (`rdp.advancedSettings`...). `MsRdpClientShell` is now `RdpClientShell` / `rdp.clientShell`.
- `parseArguments()` became `applySettings()`: python names, ActiveX names and `interface.property` keys,
  case-insensitive, returns the keys it could not apply.
- `Connect()` / `Disconnect()` became `connectToServer()` / `disconnectFromServer()` (`disconnect` is reserved by
  QObject). `version(n)` became the `controlVersion` property.
- The demo became a package with an application window (`RemoteConnector`), a reusable `ConnectionBar` and the
  `qaxrdp` command / `python -m QAxRDP`.

### Added:

- Validation of values (port, timeouts, cache sizes, color depth, enumerated settings).
- Write-only ActiveX properties fall back to the `SetXxx(type)` slots QAxBase generates for put-only COM
  properties when they are not in the control's meta-object.
- Cache of settings: they can be set before the control exists, are reapplied when the control is recreated and
  remain readable without ActiveX.
- Painted placeholder and full API on platforms without ActiveX; `isActiveXAvailable()`, `errorString`.
- Automatic fallback to older registered control versions.
- Control methods from `IMsRdpClient10`: `reconnect()`, `requestClose()`, `getErrorDescription()`,
  `getStatusText()`, `sendRemoteAction()`, `syncSessionDisplaySettings()`, `updateSessionDisplaySettings()`,
  `virtualChannelOptions()` / `setVirtualChannelOptions()`; `connectedStatusText`, `extendedDisconnectReason`.
- Built-in table of disconnect reasons, `isNormalDisconnect()`.
- Enumerations: connection state, extended disconnect reasons, remote session actions, authentication level,
  audio redirection and quality, keyboard hook mode, RD Gateway usage method and credentials source.
- `connectionState` property with its `connectionStateChanged` notify signal.
- `ConnectionBar` (password masked, address and logon name parsing, state handling) and `StatusDot`.
- Packaging (`setup.py`, `pyproject.toml`), unit tests, settings reference (`docs/API.md`) and its generator.

### Fixed:

- The demo split the domain and user name from the address field instead of the user field.
- `SecuredSettings2.PCB` read and wrote `AdvancedSettings8.BandwidthDetection`.
- `AdvancedSettings5.BandwidthDetection` used an empty property name (the property belongs to `AdvancedSettings8`
  and was removed from `AdvancedSettings5`).
- `version(n)` used `rstrip('.11')`, which strips characters rather than a suffix and could corrupt the ProgID.
- `SaveScreenshot()` passed the file suffix with its dot (`'.png'`) as image format.
- `DesktopWidth()` returned the value only when setting it.
- `GatewayPassword` was typed as an integer.
- `ColorDepth()` required an argument, so the color depth could not be read.
- `parseArguments()` matched names with `lstrip('set')`, which strips the characters s, e and t: `server`,
  `smartSizing`, `startProgram`... never matched (`'server'.lstrip('set')` is `'rver'`).
- Wrong descriptions of `AcceleratorPassthrough` and `brushSupportLevel`.
- `parseArguments` listed `SecuredSettings` twice; `connectAllSignals()` was called twice by the demo.
- The demo showed the password in clear text and positioned widgets manually in `resizeEvent`.

## 1.x - 2022-2023:

- `QAxRemoteDesktop`, a `QAxWidget` subclass for `MsTscAx.MsTscAx.11` written for ManyQt, and the `RemoteConnector`
  demo.
