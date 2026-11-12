# -*- coding: utf-8 -*-
"""
Qt Designer plugin for PySide6: registers RemoteDesktopWidget, ConnectionBar and StatusDot in the "QAxRDP" section
of the widget box.
PySide6's Designer runs every "register*.py" script found in the directories of the PYSIDE_DESIGNER_PLUGINS
environment variable. Use "qaxrdp-designer --api pyside6" to start pyside6-designer with this directory registered.
Designer executes this script with separate globals and locals, so module level imports are not visible inside
functions: each function imports what it uses (do not move these imports to the module level).
"""


def addVirtualEnvSitePackages():
    """
    Designer's embedded Python does not always see the packages of the virtual environment it was started from
    (it replaces PYTHONPATH and may ignore VIRTUAL_ENV): add its site-packages so PySide6, ManyQt and QAxRDP
    can be imported.
    :return:
    """
    from sys import path, platform, version_info
    from os.path import join, isdir
    from site import addsitedir
    from os import environ

    venv = environ.get('VIRTUAL_ENV', '')  # type: str
    if not venv:
        return
    if platform.startswith('win'):
        sitePackages = join(venv, 'Lib', 'site-packages')  # type: str
    else:
        sitePackages = join(venv, 'lib', 'python{}.{}'.format(*version_info[:2]), 'site-packages')  # type: str
    if isdir(sitePackages) and sitePackages not in path:
        addsitedir(sitePackages)


def registerWidgets():
    """
    Registers every QAxRDP widget in Qt Designer.
    :return:
    """
    from os import environ

    environ['QT_API'] = 'pyside6'  # Inside pyside6-designer, ManyQt must use PySide6 whatever else is installed.
    from ManyQt.QtDesigner import QPyDesignerCustomWidgetCollection
    try:
        from .widgetinfo import WIDGETS, GROUP, INCLUDE_FILE
    except:
        from widgetinfo import WIDGETS, GROUP, INCLUDE_FILE  # The plugin directory is on sys.path in Designer.
    for info in WIDGETS:
        if hasattr(info.widgetClass, 'DEFAULT_AUTO_CREATE_CONTROL'):
            info.widgetClass.DEFAULT_AUTO_CREATE_CONTROL = False  # No live RDP control inside Designer.
        QPyDesignerCustomWidgetCollection.registerCustomWidget(
            info.widgetClass, xml=info.domXml(), tool_tip=info.toolTip, group=GROUP, module=INCLUDE_FILE,
            container=info.container, icon=info.iconFile)


addVirtualEnvSitePackages()
registerWidgets()
