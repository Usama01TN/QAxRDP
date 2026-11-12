# coding=utf-8
"""
Tests of the Qt Designer integration: launcher helpers, widget descriptions, PyQt plugin and .ui round trip.
"""
from unittest import TestCase, main, skipUnless
from os.path import isfile, join, dirname
from importlib import import_module
from xml.etree import ElementTree
from os import pathsep, remove
from tempfile import mkstemp
from inspect import isclass
from sys import path

ROOT = dirname(__file__)  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

try:
    from .qtapp import application
except:
    from qtapp import application

application()
from QAxRDP.designer import pluginDirectory, packageRoot, designerEnvironment, environmentScript, launchDesigner, \
    findDesigner
from QAxRDP.designer.widgetinfo import WIDGETS, GROUP, INCLUDE_FILE
from QAxRDP import RemoteDesktopWidget, ConnectionBar, StatusDot
import ManyQt

IS_PYQT = (ManyQt.USED_API or '').startswith('pyqt')  # type: bool
UI_FORM = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Form</class>
 <widget class="QWidget" name="Form">
  <layout class="QVBoxLayout" name="layout">
   <item><widget class="RemoteDesktopWidget" name="rdp">
    <property name="server"><string>10.0.0.5</string></property>
    <property name="smartSizing"><bool>true</bool></property>
   </widget></item>
   <item><widget class="ConnectionBar" name="bar"/></item>
   <item><widget class="StatusDot" name="dot"><property name="state"><number>2</number></property></widget></item>
  </layout>
 </widget>
 <customwidgets>
  <customwidget><class>RemoteDesktopWidget</class><extends>QWidget</extends><header>QAxRDP</header></customwidget>
  <customwidget><class>ConnectionBar</class><extends>QFrame</extends><header>QAxRDP</header></customwidget>
  <customwidget><class>StatusDot</class><extends>QWidget</extends><header>QAxRDP</header></customwidget>
 </customwidgets>
</ui>
'''  # type: str


class LauncherTest(TestCase):
    """
    designer.py helpers (no Qt involved).
    """

    def test_plugin_directory(self):
        """
        :return:
        """
        self.assertTrue(isfile(join(pluginDirectory(), 'qaxrdpplugin.py')))
        self.assertTrue(isfile(join(pluginDirectory(), 'registerqaxrdp.py')))
        self.assertTrue(isfile(join(packageRoot(), 'QAxRDP', '__init__.py')))

    def test_environment(self):
        """
        :return:
        """
        env = designerEnvironment('pyside6',
                                  {'PYQTDESIGNERPATH': '/other', 'PYTHONPATH': '/lib'})  # type: dict[str, str]
        self.assertEqual(env['PYQTDESIGNERPATH'].split(pathsep), [pluginDirectory(), '/other'])
        self.assertEqual(env['PYSIDE_DESIGNER_PLUGINS'], pluginDirectory())
        self.assertEqual(env['PYTHONPATH'].split(pathsep), [packageRoot(), '/lib'])
        self.assertEqual(env['QT_API'], 'pyside6')
        self.assertIn(pluginDirectory(), environmentScript('pyqt5'))

    def test_missing_designer(self):
        """
        :return:
        """
        self.assertIsNone(findDesigner('no-such-binding'))
        self.assertRaises(RuntimeError, launchDesigner, (), 'no-such-binding')


class WidgetInfoTest(TestCase):
    """
    Widget descriptions shared by the plugins.
    """

    def test_widgets(self):
        """
        :return:
        """
        self.assertEqual([info.widgetClass for info in WIDGETS], [RemoteDesktopWidget, ConnectionBar, StatusDot])
        self.assertEqual((GROUP, INCLUDE_FILE), ('QAxRDP', 'QAxRDP'))
        for info in WIDGETS:
            widget = ElementTree.fromstring(info.domXml()).find('widget')
            self.assertEqual(widget.get('class'), info.name())
            self.assertEqual(widget.get('name'), info.objectName)
            self.assertTrue(isfile(info.iconFile), info.iconFile)
            self.assertFalse(info.icon().isNull())
            self.assertIsInstance(info.create(), info.widgetClass)

    def test_design_mode(self):
        """
        Designer instances never create the ActiveX control.
        :return:
        """
        rdp = WIDGETS[0].create()
        self.assertFalse(rdp.isAutoCreateControl())
        self.assertFalse(rdp.controlAvailable)
        self.assertEqual(rdp.errorString, '')
        self.assertTrue(RemoteDesktopWidget().isAutoCreateControl())

    def test_designable_properties(self):
        """
        Secrets and runtime state stay out of the property editor (and of .ui files).
        :return:
        """
        for cls in (RemoteDesktopWidget, ConnectionBar):
            mo = cls.staticMetaObject
            designable = dict((mo.property(i).name(), mo.property(i).isDesignable()) for i in range(mo.propertyCount()))
            self.assertFalse(designable['password'], cls.__name__)
        mo = RemoteDesktopWidget.staticMetaObject
        designable = dict((mo.property(i).name(), mo.property(i).isDesignable()) for i in range(mo.propertyCount()))
        for name in ('server', 'port', 'userName', 'smartSizing', 'accentColor'):
            self.assertTrue(designable[name], name)
        for name in ('advancedSettings', 'connectionState', 'autoCreateControl', 'errorString'):
            self.assertFalse(designable[name], name)


@skipUnless(IS_PYQT, 'PyQt Designer plugin (current binding: {})'.format(ManyQt.USED_API))
class PyQtPluginTest(TestCase):
    """
    qaxrdpplugin.py, loaded the way PyQt's Designer plugin loader does.
    """

    def setUp(self):
        """
        :return:
        """
        self.__m_default = RemoteDesktopWidget.DEFAULT_AUTO_CREATE_CONTROL  # type: bool

    def tearDown(self):
        """
        :return:
        """
        RemoteDesktopWidget.DEFAULT_AUTO_CREATE_CONTROL = self.__m_default

    def test_plugins(self):
        """
        :return:
        """
        from ManyQt.QtDesigner import QPyDesignerCustomWidgetPlugin
        from ManyQt.QtWidgets import QWidget
        module = import_module('QAxRDP.designer.qaxrdpplugin')
        plugins = [o for o in vars(module).values() if isclass(o) and issubclass(o, QPyDesignerCustomWidgetPlugin)
                   and o is not QPyDesignerCustomWidgetPlugin]
        self.assertEqual(sorted(p.__name__ for p in plugins),
                         ['ConnectionBarPlugin', 'RemoteDesktopWidgetPlugin', 'StatusDotPlugin'])
        parent = QWidget()  # type: QWidget
        for cls in plugins:
            plugin = cls()
            self.assertFalse(plugin.isInitialized())
            plugin.initialize(None)
            self.assertTrue(plugin.isInitialized())
            self.assertEqual(type(plugin.createWidget(parent)).__name__, plugin.name())
            self.assertEqual((plugin.group(), plugin.includeFile()), ('QAxRDP', 'QAxRDP'))
            self.assertFalse(plugin.icon().isNull())
            self.assertFalse(plugin.isContainer())
            self.assertIn(plugin.name(), plugin.domXml())
            self.assertTrue(plugin.toolTip() and plugin.whatsThis())
        self.assertFalse(RemoteDesktopWidget.DEFAULT_AUTO_CREATE_CONTROL)

    def test_ui_round_trip(self):
        """
        A form using the widgets loads with uic, setting their designable properties.
        :return:
        """
        uic = import_module('{}.uic'.format({'pyqt5': 'PyQt5', 'pyqt6': 'PyQt6', 'pyqt4': 'PyQt4'}[ManyQt.USED_API]))
        handle, fileName = mkstemp(suffix='.ui')
        with open(handle, 'w') as f:
            f.write(UI_FORM)
        try:
            form = uic.loadUi(fileName)
        finally:
            remove(fileName)
        self.assertEqual((form.rdp.server, form.rdp.smartSizing, form.dot.state), ('10.0.0.5', True, 2))
        self.assertIsInstance(form.bar, ConnectionBar)


if __name__ == '__main__':
    main()
