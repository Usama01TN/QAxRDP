# coding=utf-8
"""
Entry point of the RDP Connector application (also installed as the "qaxrdp" command).
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .mainwindow import RemoteConnector, APP_NAME, ORGANIZATION_NAME
    from .version import __version__
except:
    from mainwindow import RemoteConnector, APP_NAME, ORGANIZATION_NAME
    from version import __version__


def main(argv=None):
    """
    Starts the RDP Connector application.
    :param argv: (list[str | unicode | QString] | QStringList | None) Command line, sys.argv when None.
    :return: (int) Exit code.
    """
    from ManyQt.QtCore import Qt, qVersion
    from ManyQt.QtWidgets import QApplication
    from sys import argv as sysArgv

    if qVersion().startswith('5.') and hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    a = QApplication.instance() or QApplication(list(argv if argv is not None else sysArgv))  # type: QApplication
    a.setApplicationName(APP_NAME)
    a.setOrganizationName(ORGANIZATION_NAME)
    a.setApplicationVersion(__version__)
    w = RemoteConnector()  # type: RemoteConnector
    w.show()
    return (getattr(a, 'exec', None) or a.exec_)()  # exec_() is deprecated in Qt 6 bindings.


if __name__ == '__main__':
    from sys import exit

    exit(main())
