# coding=utf-8
"""
Entry point of "qaxrdp-designer": starts Qt Designer with the QAxRDP widgets registered.
    qaxrdp-designer [--api pyqt5|pyqt6|pyside6] [form.ui ...]   start Qt Designer (falls back to --preview)
    qaxrdp-designer --preview                                   show the plugin preview window
    qaxrdp-designer --print-env                                 print the variables to register the plugins
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .designer import launchDesigner, environmentScript, selectApi
except:
    from designer import launchDesigner, environmentScript, selectApi


def main(argv=None):
    """
    :param argv: (list[str | unicode | QString] | QStringList | None) Arguments, sys.argv[1:] when None.
    :return: (int) Exit code.
    """
    from sys import argv as sysArgv, stderr
    from argparse import ArgumentParser
    from os import environ

    parser = ArgumentParser(
        prog='qaxrdp-designer', description='Qt Designer with the QAxRDP widgets.')  # type: ArgumentParser
    parser.add_argument('--api', choices=('pyqt5', 'pyqt6', 'pyside6', 'pyqt4'), help='Qt binding of Designer')
    parser.add_argument('--preview', action='store_true', help='show the plugin preview instead of Designer')
    parser.add_argument('--print-env', action='store_true', help='print the environment registering the plugins')
    parser.add_argument('files', nargs='*', help='.ui files to open')
    args = parser.parse_args(sysArgv[1:] if argv is None else argv)
    api = selectApi(args.api)  # type: str | None
    if args.print_env:
        print(environmentScript(api))
        return 0
    if not args.preview:
        try:
            return launchDesigner(args.files, api).wait()
        except RuntimeError as e:
            stderr.write('{}\nShowing the plugin preview instead.\n'.format(e))
    if api:
        environ['QT_API'] = api
    try:
        from .mainwindow import MainWindow
    except:
        from mainwindow import MainWindow
    from ManyQt.QtWidgets import QApplication

    a = QApplication.instance() or QApplication(list(sysArgv[:1]))  # type: QApplication
    w = MainWindow()  # type: MainWindow
    w.show()
    run = getattr(a, 'exec', None) or a.exec_
    return run()


if __name__ == '__main__':
    from sys import exit

    exit(main())
