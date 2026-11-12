# -*- coding: utf-8 -*-
"""
Qt Designer plugin for PyQt (PyQt5, PyQt6, PyQt4): adds RemoteDesktopWidget, ConnectionBar and StatusDot to the
"QAxRDP" section of the widget box.
PyQt's Designer plugin loader imports every "*plugin.py" module found in the directories of the PYQTDESIGNERPATH
environment variable and instantiates its QPyDesignerCustomWidgetPlugin subclasses. Use "qaxrdp-designer" to start
Qt Designer with this directory registered, or set PYQTDESIGNERPATH to it yourself.
"""
from sys import path, modules
from os.path import dirname
from os import environ

# Designer already loaded its PyQt: make ManyQt use the same binding, whatever else is installed.
for _module, _api in (('PyQt6', 'pyqt6'), ('PyQt5', 'pyqt5'), ('PyQt4', 'pyqt4')):
    if _module in modules:
        environ['QT_API'] = _api
        break

from ManyQt.QtDesigner import QPyDesignerCustomWidgetPlugin

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .widgetinfo import WIDGETS, GROUP, INCLUDE_FILE
except:
    from widgetinfo import WIDGETS, GROUP, INCLUDE_FILE


class _WidgetPlugin(QPyDesignerCustomWidgetPlugin):
    """
    Base plugin: the INFO class attribute (a WidgetInfo) of each subclass describes the widget.
    """
    INFO = None  # type: WidgetInfo

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        # Not super(_WidgetPlugin, self): the name _WidgetPlugin is deleted at the end of this module (so that
        # PyQt's loader does not instantiate the base class) and would raise NameError here.
        QPyDesignerCustomWidgetPlugin.__init__(self, *args, **kwargs)
        self.__m_initialized = False  # type: bool

    def initialize(self, core):
        """
        :param core: QDesignerFormEditorInterface
        :return:
        """
        if not self.__m_initialized:
            # No live RDP control inside Designer, also for widgets it creates outside createWidget().
            if hasattr(self.INFO.widgetClass, 'DEFAULT_AUTO_CREATE_CONTROL'):
                self.INFO.widgetClass.DEFAULT_AUTO_CREATE_CONTROL = False
            self.__m_initialized = True  # type: bool

    def isInitialized(self):
        """
        :return: bool
        """
        return self.__m_initialized

    def createWidget(self, parent):
        """
        :param parent: QWidget
        :return: QWidget
        """
        return self.INFO.create(parent)

    def name(self):
        """
        :return: str | unicode | QString
        """
        return self.INFO.name()

    def group(self):
        """
        :return: str | unicode | QString
        """
        return GROUP

    def icon(self):
        """
        :return: QIcon
        """
        return self.INFO.icon()

    def toolTip(self):
        """
        :return: str | unicode | QString
        """
        return self.INFO.toolTip

    def whatsThis(self):
        """
        :return: str | unicode | QString
        """
        return self.INFO.whatsThis

    def isContainer(self):
        """
        :return: bool
        """
        return self.INFO.container

    def domXml(self):
        """
        :return: str | unicode | QString
        """
        return self.INFO.domXml()

    def includeFile(self):
        """
        :return: (str | unicode | QString) pyuic writes "from QAxRDP import <class>".
        """
        return INCLUDE_FILE


def _pluginClass(info):
    """
    :param info: WidgetInfo
    :return: (type) A _WidgetPlugin subclass named <class>Plugin.
    """
    return type('{}Plugin'.format(info.name()), (_WidgetPlugin,), {
        'INFO': info, '__doc__': 'Qt Designer plugin of {}.'.format(info.name())})


RemoteDesktopWidgetPlugin = _pluginClass(WIDGETS[0])  # type: type
ConnectionBarPlugin = _pluginClass(WIDGETS[1])  # type: type
StatusDotPlugin = _pluginClass(WIDGETS[2])  # type: type
# The loader instantiates every QPyDesignerCustomWidgetPlugin subclass of this namespace: hide the base class.
del _WidgetPlugin

__all__ = ['RemoteDesktopWidgetPlugin', 'ConnectionBarPlugin', 'StatusDotPlugin']  # type: list[str]
