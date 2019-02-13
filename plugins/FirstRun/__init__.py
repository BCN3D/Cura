from . import FirstRun

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {}

def register(app):
    return {
        "extension": FirstRun.FirstRun()
    }
