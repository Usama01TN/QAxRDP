# coding=utf-8
"""
designer package: Qt Designer plugins of the QAxRDP widgets.

    - qaxrdpplugin.py: plugin module for PyQt (PYQTDESIGNERPATH).
    - registerqaxrdp.py: registration script for PySide6 (PYSIDE_DESIGNER_PLUGINS).
    - designer.py: launcher (qaxrdp-designer) and environment helpers, without any Qt import.
    - widgetinfo.py: binding neutral description of the widgets.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .designer import pluginDirectory, packageRoot, selectApi, findDesigner, designerEnvironment, \
        environmentScript, launchDesigner, DESIGNER_APIS
except:
    from designer import pluginDirectory, packageRoot, selectApi, findDesigner, designerEnvironment, \
        environmentScript, launchDesigner, DESIGNER_APIS

__all__ = ['pluginDirectory', 'packageRoot', 'selectApi', 'findDesigner', 'designerEnvironment',
           'environmentScript', 'launchDesigner', 'DESIGNER_APIS']  # type: list[str]
