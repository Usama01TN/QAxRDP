# -*- coding: utf-8 -*-
"""
Description of the QAxRDP widgets for Qt Designer, shared by the PyQt plugin (qaxrdpplugin.py), the PySide6
registration script (registerqaxrdp.py) and the plugin preview (mainwindow.py). Binding neutral: it does not need
the QtDesigner module.
"""
from ManyQt.QtGui import QIcon
from os.path import dirname, join, abspath
from xml.sax.saxutils import escape
from sys import path

_ROOT = dirname(dirname(dirname(abspath(__file__))))  # type: str
if _ROOT not in path:
    path.insert(0, _ROOT)

try:
    from .QAxRDP import RemoteDesktopWidget, ConnectionBar, StatusDot
except:  # Source tree not installed: Designer imports this file directly from QAxRDP/designer.
    from QAxRDP import RemoteDesktopWidget, ConnectionBar, StatusDot

GROUP = 'QAxRDP'  # type: str  # Widget box section.
INCLUDE_FILE = 'QAxRDP'  # type: str  # Module imported by the code generated from .ui files (pyuic, pyside-uic).
IMAGES_DIR = join(dirname(abspath(__file__)), 'images')  # type: str


class WidgetInfo(object):
    """
    Everything Qt Designer needs to know about one widget class.
    """

    def __init__(self, widgetClass, objectName, displayName, toolTip, whatsThis, iconFile, width=200, height=100,
                 container=False, createKwargs=None):
        """
        :param widgetClass: (type) QWidget subclass exported by the QAxRDP package.
        :param objectName: (str | unicode | QString) Default object name of new instances.
        :param displayName: (str | unicode | QString) Name shown in the widget box.
        :param toolTip: str | unicode | QString
        :param whatsThis: str | unicode | QString
        :param iconFile: (str | unicode | QString) File name in designer/images.
        :param width: (int) Default width in px.
        :param height: (int) Default height in px.
        :param container: (bool) Whether children can be dropped into the widget.
        :param createKwargs: (dict | None) Options passed when Designer creates an instance.
        """
        self.widgetClass = widgetClass  # type: type
        self.objectName = objectName  # type: str
        self.displayName = displayName  # type: str
        self.toolTip = toolTip  # type: str
        self.whatsThis = whatsThis  # type: str
        self.iconFile = join(IMAGES_DIR, iconFile)  # type: str
        self.width = int(width)  # type: int
        self.height = int(height)  # type: int
        self.container = bool(container)  # type: bool
        self.createKwargs = dict(createKwargs or {})  # type: dict

    def name(self):
        """
        :return: (str | unicode | QString) Class name, as written in .ui files.
        """
        return self.widgetClass.__name__

    def icon(self):
        """
        :return: QIcon
        """
        return QIcon(self.iconFile)

    def create(self, parent=None):
        """
        Creates an instance the way Qt Designer does (design mode options applied).
        :param parent: QWidget | None
        :return: QWidget
        """
        return self.widgetClass(parent, **self.createKwargs)

    def domXml(self):
        """
        :return: (str | unicode | QString) Default XML of a new instance in a form.
        """
        return ('<ui language="c++" displayname="{display}">\n'
                ' <widget class="{cls}" name="{name}">\n'
                '  <property name="geometry">\n'
                '   <rect><x>0</x><y>0</y><width>{w}</width><height>{h}</height></rect>\n'
                '  </property>\n'
                '  <property name="toolTip"><string>{tip}</string></property>\n'
                '  <property name="whatsThis"><string>{what}</string></property>\n'
                ' </widget>\n'
                '</ui>\n').format(display=escape(self.displayName, {'"': '&quot;'}), cls=self.name(),
                                  name=self.objectName, w=self.width, h=self.height, tip=escape(self.toolTip),
                                  what=escape(self.whatsThis))


WIDGETS = (
    WidgetInfo(RemoteDesktopWidget, 'remoteDesktopWidget', 'Remote Desktop',
               'Microsoft Remote Desktop (RDP) client control',
               'Hosts the Microsoft RDP client ActiveX control (MsTscAx). Set server, port, userName and the other '
               'properties here; the password and the advanced settings are set in code. The ActiveX control is '
               'created when the form runs (Windows only).',
               'remotedesktopwidget.png', 480, 320, False, {'autoCreateControl': False}),
    WidgetInfo(ConnectionBar, 'connectionBar', 'Connection Bar',
               'RDP connection bar: address, logon name, password, Connect and Disconnect',
               'Emits connectRequested(host, port, domain, user, password) with the parsed fields and '
               'disconnectRequested(). Drive its state with setState().',
               'connectionbar.png', 760, 40),
    WidgetInfo(StatusDot, 'statusDot', 'Status Dot',
               'Connection status indicator (pulses while connecting)',
               'Round indicator: grey disconnected, amber connecting, green connected, red error.',
               'statusdot.png', 20, 20),
)  # type: tuple[WidgetInfo]
