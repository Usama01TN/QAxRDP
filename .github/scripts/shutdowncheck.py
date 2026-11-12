# -*- coding: utf-8 -*-
"""
Application shutdown check used by .github/workflows/release.yml: shows a RemoteDesktopWidget (with the real
ActiveX control on Windows), quits through the event loop like an application, then lets the interpreter exit
normally. The process exit code must be 0: anything else means the control is not released cleanly at exit.
    python -X faulthandler .github/scripts/shutdowncheck.py
"""
from sys import argv, exit, path, stdout
from os.path import abspath, dirname

ROOT = dirname(dirname(dirname(abspath(__file__))))  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

from ManyQt.QtWidgets import QApplication
from ManyQt.QtCore import QTimer
from QAxRDP import RemoteDesktopWidget, isActiveXAvailable


def main():
    """
    :return: (int) Exit code of the event loop.
    """
    app = QApplication(argv)  # type: QApplication
    rdp = RemoteDesktopWidget(server='qaxrdp.invalid', userName='probe')  # type: RemoteDesktopWidget
    rdp.resize(640, 480)
    rdp.show()
    print('ActiveX available: {} | control: {}'.format(
        isActiveXAvailable(), rdp.getActiveControlName() or rdp.getErrorString()))
    QTimer.singleShot(1500, app.quit)
    code = (getattr(app, 'exec', None) or app.exec_)()  # type: int
    print('Event loop returned {} | control released by aboutToQuit: {}'.format(code, not rdp.isControlAvailable()))
    stdout.flush()
    return code


if __name__ == '__main__':
    exit(main())
