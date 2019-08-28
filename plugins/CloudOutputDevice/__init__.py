from . import CloudOutputDevicePlugin

from UM.i18n import i18nCatalog
catalog = i18nCatalog("uranium")

def getMetaData():
    return {
    }

def register(app):
    return {
        "output_device": CloudOutputDevicePlugin.CloudOutputDevicePlugin()
    }
