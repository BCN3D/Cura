# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Logger import Logger
from UM.i18n import i18nCatalog

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob

i18n_catalog = i18nCatalog("cura")


## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class FirmwareUpdateChecker(Extension):

    def __init__(self):
        super().__init__()

        # Listen to a Signal that indicates a change in the list of printers, just if the user has enabled the
        # 'check for updates' option
        Preferences.getInstance().addPreference("info/automatic_update_check", True)

        self._view = None

        self._global_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        Application.getInstance().firmwareChanged.connect(self._onFirmwareChanged)

        self._onGlobalStackChanged()

    def _onGlobalStackChanged(self):
        self._global_stack = Application.getInstance().getGlobalContainerStack()

    def _onFirmwareChanged(self):
        if self._global_stack and Preferences.getInstance().getValue("info/automatic_update_check"):
            self.checkFirmwareVersion(self._global_stack, True)

    def checkFirmwareVersion(self, container = None, silent = False):
        job = FirmwareUpdateCheckerJob(container = container, silent = silent)
        job.start()
