# coding=utf-8
"""
Allows "python -m QAxRDP" to start the RDP Connector application.
"""
from os.path import dirname
from sys import path, exit

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .main import main
except:
    from main import main

exit(main())
