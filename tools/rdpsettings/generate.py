# -*- coding: utf-8 -*-
"""
Renders QAxRDP/remotedesktop/rdpsettings.py and docs/API.md from spec.py (+ header.py.tpl).
Usage (from anywhere):
    python tools/rdpsettings/generate.py [<package_dir> <api_md>]
Edit spec.py (properties, types, ranges, descriptions), header.py.tpl (helpers and base class) or the EXTRA
methods below, then run this script instead of editing rdpsettings.py by hand.
"""
from os.path import join, dirname, abspath
from sys import argv, path
from textwrap import wrap

path.insert(0, dirname(abspath(__file__)))
from spec import INTERFACES, P, I, S, B  # noqa

ROOT = dirname(dirname(dirname(abspath(__file__))))
OUT_PKG = argv[1] if len(argv) > 2 else join(ROOT, 'QAxRDP', 'remotedesktop')
OUT_DOC = argv[2] if len(argv) > 2 else join(ROOT, 'docs', 'API.md')

CONTROL = ('', 'ControlSettings', 'IMsRdpClient10',
           'Top level properties of the MsTscAx control (server, credentials, display and texts).', [], [
               P('Server', S, desc='Name or IP address of the server to connect to.'),
               P('Domain', S, desc='Domain to which the current user logs on.'),
               P('UserName', S, desc='User name logon credential.'),
               P('ColorDepth', I, default=32, desc='Color depth, in bits per pixel (8, 15, 16, 24 or 32).'),
               P('DesktopWidth', I, rng=(0, 8192), desc='Width, in pixels, of the initial remote desktop.'),
               P('DesktopHeight', I, rng=(0, 8192), desc='Height, in pixels, of the initial remote desktop.'),
               P('ConnectingText', S, desc='Text displayed centered in the control while connecting.'),
               P('ConnectedStatusText', S, desc='Text displayed in the control once connected.'),
               P('DisconnectedText', S, desc='Text displayed centered in the control when disconnected.'),
               P('FullScreenTitle', S, acc='w', desc='Window title displayed in full-screen mode (write-only).'),
               P('FullScreen', B, desc='Full-screen state of the control.'),
               P('StartConnected', I, desc='Connect immediately upon startup (1) or not (0).'),
               P('SecuredSettingsEnabled', I, acc='r',
                 desc='Whether the secured settings interface is available (read-only).'),
               P('Version', S, acc='r', desc='Version number of the control (read-only).'),
               P('CipherStrength', I, acc='r', desc='Maximum encryption strength of the control (read-only).'),
               P('HorizontalScrollBarVisible', I, acc='r',
                 desc='Whether the control displays a horizontal scroll bar (read-only).'),
               P('VerticalScrollBarVisible', I, acc='r',
                 desc='Whether the control displays a vertical scroll bar (read-only).'),
               P('Connected', I, acc='r', desc='Connection state: 0 disconnected, 1 connected, 2 connecting '
                                               '(read-only).'),
               P('ExtendedDisconnectReason', I, acc='r',
                 desc='Extended information about the last disconnection (read-only).'),
           ])

ALL = [CONTROL] + INTERFACES


def pyName(ax):
    """camelCase python name of an ActiveX property."""
    if ax.startswith('Is') and ax[2].isupper():
        ax = ax[2:]
    i = 0
    while i < len(ax) and ax[i].isupper():
        i += 1
    if i == 0:
        return ax
    if i == len(ax):
        return ax.lower()
    if i == 1:
        return ax[0].lower() + ax[1:]
    return ax[:i - 1].lower() + ax[i - 1:]


def accessors(p):
    name = pyName(p['ax'])
    cap = name[0].upper() + name[1:]
    if p['py'] == B and not p['ax'].startswith('Can'):
        getter = 'is' + cap
    else:
        getter = 'get' + cap
    return name, getter, 'set' + cap


def className(key):
    return 'Rdp' + key


PYTYPE_DOC = {B: 'bool', I: 'int', S: 'str | unicode'}
PROP_TYPE = {B: 'bool', I: 'int', S: 'str'}


def doc(lines, indent):
    pad = ' ' * indent
    out = [pad + '"""']
    for l in lines:
        out.append((pad + l) if l else '')
    out.append(pad + '"""')
    return '\n'.join(out)


def wrapped(text, indent, width=112):
    return wrap(text, width - indent) or ['']


def render_property(p):
    name, getter, setter = accessors(p)
    py, ax, axt, acc = p['py'], p['ax'], p['axt'], p['acc']
    lines = []
    desc = wrapped(p['desc'].replace('(see ', '(see Rdp'), 8)
    default = repr(p['default'])
    # Getter.
    lines.append('    def {}(self):'.format(getter))
    lines.append(doc(desc + ['ActiveX property: {}.'.format(ax), ':return: {}'.format(PYTYPE_DOC[py])], 8))
    if p['secret']:
        lines.append("        return ''")
    else:
        conv = {B: 'bool', I: 'int', S: 'toText'}[py]
        lines.append("        return {}(self._read('{}', {}))".format(conv, ax, default))
    lines.append('')
    if acc != 'r':
        # Setter.
        if py == B:
            lines += ['    @pyqtSlot(bool)', '    @pyqtSlot(int)']
        elif py == I:
            lines += ['    @pyqtSlot(int)']
        else:
            lines += ["    @pyqtSlot('QString')\n    @pyqtSlot(str)"]
        lines.append('    def {}(self, {}):'.format(setter, name))
        lines.append(doc([':param {}: {}'.format(name, PYTYPE_DOC[py]),
                          ':return: bool, True if the control accepted the value.'], 8))
        if py == B:
            lines.append('        {0} = bool({0})  # type: bool'.format(name))
        elif py == I:
            if p['rng']:
                lo, hi = p['rng']
                lines.append('        {0} = clamp(int({0}), {1}, {2})  # type: int'.format(name, lo, hi))
            else:
                lines.append('        {0} = int({0})  # type: int'.format(name))
        else:
            lines.append('        {0} = toText({0})  # type: str'.format(name))
        if ax == 'ColorDepth':
            lines.append('        {0} = min(COLOR_DEPTHS, key=lambda d: abs(d - {0}))  # type: int'.format(name))
        lines.append("        return self._write('{}', {}, '{}'{})".format(
            ax, name, axt, ', secret=True' if p['secret'] else ''))
        lines.append('')
    return '\n'.join(lines), name, getter, (setter if acc != 'r' else None), py


EXTRA = {
    'MsRdpClientShell': '''
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
''',
    'RemoteProgram': '''
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
''',
    'RemoteProgram3': '''
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
''',
}


def render_class(iface):
    key, clsKey, com, summary, enums, props = iface
    cls = className(clsKey)
    out = []
    out.append('class {}(RdpSettingsInterface):'.format(cls))
    title = 'the control itself' if not key else 'the "{}" sub-object'.format(key)
    out.append(doc(wrapped('{} ({}, {}).'.format(summary.rstrip('.'), com, title), 4), 4))
    out.append("    INTERFACE = '{}'  # type: str".format(key))
    out.append("    COM_INTERFACE = '{}'  # type: str".format(com))
    for ename, members in enums:
        out.append('')
        out.append('    class {}(IntEnum):'.format(ename))
        out.append(doc(['{} enumeration class.'.format(ename)], 8))
        for m, v in members:
            out.append('        {} = {}  # type: int'.format(m, v))
    if enums:
        out.append('')
        for ename, members in enums:
            for m, v in members:
                out.append('    {0} = {1}.{0}  # type: int'.format(m, ename))
    out.append('')
    out.append('    # ---------- Properties table (python name, ActiveX name, ActiveX type, access) ----------')
    out.append('    PROPERTIES = (')
    rendered = []
    for p in props:
        name, getter, setter = accessors(p)
        out.append("        ('{}', '{}', '{}', '{}'),".format(name, p['ax'], p['axt'], p['acc']))
        rendered.append(render_property(p))
    out.append('    )  # type: tuple[tuple[str, str, str, str]]')
    out.append('')
    out.append('    # ---------- Public API ----------')
    for code, *_ in rendered:
        out.append(code)
    if key in EXTRA or clsKey in EXTRA:
        out.append('    # ---------- Methods ----------')
        out.append(EXTRA.get(key or clsKey, '').strip('\n'))
        out.append('')
    if rendered:
        out.append('    # ---------- Properties ----------')
        for code, name, getter, setter, py in rendered:
            head = '    {} = pyqtProperty({}, fget={}'.format(name, PROP_TYPE[py], getter)
            tail = (', fset={})'.format(setter) if setter else ')') + '  # type: pyqtProperty'
            if len(head + tail) <= 120:
                out.append(head + tail)
            else:
                out.append(head + ',')
                out.append(' ' * (head.index('(') + 1) + tail.lstrip(', '))
    while out and out[-1] == '':
        out.pop()
    return cls, '\n'.join(out)


HEADER = open(join(dirname(abspath(__file__)), 'header.py.tpl'), encoding='utf-8').read()

classes = []
bodies = []
for iface in ALL:
    cls, body = render_class(iface)
    classes.append((iface[0], cls))
    bodies.append(body)

ifaceMap = '\n'.join("    ('{}', {}),".format(k, c) for k, c in classes if k)
src = HEADER.replace('{{CLASSES}}', '\n\n\n'.join(bodies))
src = src.replace('{{INTERFACE_MAP}}', ifaceMap)
src = src.replace('{{ALL}}', ',\n           '.join("'{}'".format(c) for _, c in classes))
with open(join(OUT_PKG, 'rdpsettings.py'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(src.rstrip() + '\n')

# ---------- docs/API.md ----------
md = ['# QAxRDP settings reference', '',
      'Generated from the interface tables of `QAxRDP/remotedesktop/rdpsettings.py`. Every property is exposed as',
      'a getter, a `@pyqtSlot` setter (unless read-only) and a `pyqtProperty`, so all of these work:', '',
      '```python', "rdp.advancedSettings.setSmartSizing(True)      # setter (slot)",
      "rdp.advancedSettings.smartSizing = True          # pyqtProperty",
      "rdp.advancedSettings.setProperty('smartSizing', True)",
      "rdp.applySettings({'advancedSettings.smartSizing': True})", '```', '',
      'Access: **rw** read/write, **r** read-only, **w** write-only (the getter returns the last value set,',
      'except for passwords which are never returned).', '']
md.append('## Contents')
md.append('')
for iface in ALL:
    key, clsKey, com = iface[0], iface[1], iface[2]
    attr = pyName(clsKey)
    md.append('- [`{}`](#{}) - `rdp.{}`'.format(className(clsKey), className(clsKey).lower(), attr))
md.append('')
for iface in ALL:
    key, clsKey, com, summary, enums, props = iface
    cls = className(clsKey)
    attr = pyName(clsKey)
    md.append('## {}'.format(cls))
    md.append('')
    md.append('{} COM interface `{}`, ActiveX sub-object `{}`, reached with `rdp.{}`.'.format(
        summary, com, key or '(the control)', attr))
    md.append('')
    for ename, members in enums:
        md.append('Enum `{}.{}`: {}.'.format(cls, ename, ', '.join('`{}` = {}'.format(m, v) for m, v in members)))
        md.append('')
    if props:
        md.append('| Property | Getter / Setter | Type | Access | ActiveX name | Description |')
        md.append('|---|---|---|---|---|---|')
        for p in props:
            name, getter, setter = accessors(p)
            acc = p['acc']
            gs = '`{}()`'.format(getter) + (' / `{}()`'.format(setter) if acc != 'r' else '')
            md.append('| `{}` | {} | {} | {} | `{}` | {} |'.format(name, gs, PROP_TYPE[p['py']], acc, p['ax'],
                                                                  p['desc'].replace('|', '/').replace('(see ', '(see Rdp')))
        md.append('')
    extra = EXTRA.get(key or clsKey)
    if extra:
        md.append('Methods:')
        md.append('')
        sig = None
        for line in extra.splitlines():
            line = line.strip()
            if line.startswith('def '):
                sig = line[4:]
            elif sig is not None:
                sig += ' ' + line
            if sig is not None and sig.endswith('):'):
                md.append('- `{}`'.format(sig.rstrip(':').replace('self, ', '').replace('(self)', '()')))
                sig = None
        md.append('')
with open(OUT_DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(md).rstrip() + '\n')
print('generated', len(classes), 'classes')
