# coding=utf-8
"""
connectionbar package: ConnectionBar, StatusDot and the address / logon name parsers.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .connectionbar import ConnectionBar, StatusDot, parseAddress, parseUserName
except:
    from connectionbar import ConnectionBar, StatusDot, parseAddress, parseUserName

__all__ = ['ConnectionBar', 'StatusDot', 'parseAddress', 'parseUserName']  # type: list[str]
