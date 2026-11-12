# coding=utf-8
"""
Tests of the settings interfaces without a hosting control (cache behavior, validation, metaobject).
"""
from unittest import TestCase, main
from os.path import dirname
from sys import path

ROOT = dirname(__file__)  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

try:
    from .qtapp import application
except:
    from qtapp import application

application()
from QAxRDP import SETTINGS_INTERFACES, RdpAdvancedSettings, RdpControlSettings, RdpTransportSettings2


def sampleValue(axType, current):
    """
    :param axType: str | unicode | QString
    :param current: any
    :return: any, a value different from current.
    """
    if axType == 'bool':
        return not current
    if axType == 'QString':
        return u'value-{}'.format(len(current))
    return current + 1


class InterfacesTest(TestCase):
    """
    Generic tests run on every interface.
    """

    def test_meta_object(self):
        """
        Every PROPERTIES entry is a Qt property, in the same order.
        :return:
        """
        for _, cls in SETTINGS_INTERFACES:
            obj = cls()
            mo = obj.metaObject()
            names = [mo.property(i).name() for i in range(mo.propertyOffset(), mo.propertyCount())]
            self.assertEqual(names, obj.propertyNames(), cls.__name__)
            self.assertFalse(obj.isAvailable())

    def test_round_trip(self):
        """
        Writable properties keep the value set (write-only ones too, passwords excepted).
        :return:
        """
        for _, cls in SETTINGS_INTERFACES:
            obj = cls()
            for name, axName, axType, access in obj.PROPERTIES:
                if access == 'r':
                    self.assertFalse(obj.setProperty(name, 1), '{}.{}'.format(cls.__name__, name))
                    continue
                value = 16 if name == 'colorDepth' else sampleValue(axType, obj.property(name))  # Valid depth.
                self.assertTrue(obj.setProperty(name, value), '{}.{}'.format(cls.__name__, name))
                if 'Password' in axName:
                    self.assertEqual(obj.property(name), '')
                else:
                    self.assertEqual(obj.property(name), value, '{}.{}'.format(cls.__name__, name))


class ValidationTest(TestCase):
    """
    Ranges, color depths, secrets and signals.
    """

    def test_clamping(self):
        """
        :return:
        """
        settings = RdpAdvancedSettings()  # type: RdpAdvancedSettings
        settings.setRdpPort(70000)
        self.assertEqual(settings.getRdpPort(), 65535)
        settings.setBitmapCacheSize(0)
        self.assertEqual(settings.getBitmapCacheSize(), 1)
        settings.overallConnectionTimeout = 9999
        self.assertEqual(settings.overallConnectionTimeout, 600)
        control = RdpControlSettings()  # type: RdpControlSettings
        control.setColorDepth(23)
        self.assertEqual(control.getColorDepth(), 24)

    def test_secrets(self):
        """
        :return:
        """
        emitted = []
        settings = RdpTransportSettings2(
            settingChanged=lambda name, value: emitted.append((name, value)))  # type: RdpTransportSettings2
        settings.setGatewayPassword('secret')
        settings.setGatewayUsername('bob')
        self.assertEqual(settings.getGatewayPassword(), '')
        self.assertEqual(settings.values(), {'GatewayUsername': 'bob'})
        self.assertEqual(emitted, [('GatewayPassword', ''), ('GatewayUsername', 'bob')])

    def test_find_property(self):
        """
        :return:
        """
        settings = RdpAdvancedSettings()  # type: RdpAdvancedSettings
        self.assertEqual(settings.findProperty('SMARTSIZING'), 'smartSizing')
        self.assertEqual(settings.findProperty('RDPPort'), 'rdpPort')
        self.assertIsNone(settings.findProperty('nothing'))
        self.assertEqual(settings.reapply(), 0)


if __name__ == '__main__':
    main()
