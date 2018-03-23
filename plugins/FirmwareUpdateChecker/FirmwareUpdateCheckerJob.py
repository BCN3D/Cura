# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger
from UM.Job import Job

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


##  This job checks if there is an update available on the provided URL.
class FirmwareUpdateCheckerJob(Job):
    def __init__(self, container = None, silent = False):
        super().__init__()
        self._container = container
        self.silent = silent

    def run(self):
        firmware_version = Application.getInstance().getFirmwareVersion()
        latest_firmware_version = Application.getInstance().getLatestFirmwareVersion()

        if firmware_version is None or latest_firmware_version is None:
            Logger.log("i", "Can not check for updates. Current or latest firmware version not known.")
            return

        if firmware_version < latest_firmware_version:
            machine_name = self._container.definition.getName()
            message = Message(
                i18n_catalog.i18nc("@info Don't translate {machine_name}, since it gets replaced by a printer name!",
                                   "New features are available for your {machine_name}! It is recommended to update the firmware on your printer.\n"
                                   "Go to Preferences->Printers to update the firmware.").format(machine_name=machine_name),
                title=i18n_catalog.i18nc("@info:title The %s gets replaced with the printer name.",
                                         "New %s firmware available") % machine_name)
            message.show()