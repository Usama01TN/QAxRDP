# coding=utf-8
"""
Shared QApplication for the tests (offscreen platform except on Windows, where ActiveX needs a real desktop).
"""
from os.path import dirname, abspath
from os import environ, name
from atexit import register
from sys import path

ROOT = dirname(dirname(abspath(__file__)))  # type: str
if ROOT not in path:
    path.insert(0, ROOT)
if name != 'nt':
    environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
_APPLICATION = []  # type: list[QApplication]  # Keeps the application alive for the whole test run.


def application():
    """
    :return: QApplication
    """
    from ManyQt.QtWidgets import QApplication
    if not _APPLICATION:
        _APPLICATION.append(QApplication.instance() or QApplication(['qaxrdp-tests']))
        register(cleanup)
    return _APPLICATION[0]


def cleanup():
    """
    Safety net for "python -m unittest": the tests never run QApplication.exec(), so aboutToQuit is never emitted;
    release the ActiveX controls still alive while the QApplication exists. Widgets are deliberately not deleted
    here: destroying the remaining native windows in bulk at interpreter exit crashed on Windows (access violation).
    Tests delete their widgets with deleteNow(), and "python -m tests" ends the process right after the run.
    :return:
    """
    if not _APPLICATION:
        return
    try:
        from QAxRDP import RemoteDesktopWidget
    except:
        return
    # Select the widgets before releasing anything: releasing a control destroys its internal native widgets.
    widgets = [w for w in _APPLICATION[0].allWidgets() if isinstance(w, RemoteDesktopWidget)]  # type: list
    for widget in widgets:
        widget.releaseControl()


def deleteNow(obj):
    """
    Deletes a QObject now, through the event loop like deleteLater() in an application.
    :param obj: QObject
    :return: (bool) True if the object was destroyed.
    """
    from ManyQt.QtCore import QCoreApplication, QEvent
    destroyed = []  # type: list[bool]
    obj.destroyed.connect(lambda *args: destroyed.append(True))
    obj.deleteLater()
    processEvents(0)
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    return bool(destroyed)


def processEvents(ms=0):
    """
    Runs the event loop for ms milliseconds.
    :param ms: int
    :return:
    """
    from ManyQt.QtCore import QEventLoop, QTimer
    loop = QEventLoop()  # type: QEventLoop
    QTimer.singleShot(ms, loop.quit)
    (getattr(loop, 'exec', None) or loop.exec_)()
