from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty

from UM.Application import Application
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.MachineAction import MachineAction

catalog = i18nCatalog("cura")

##  Upgrade the firmware of a machine by USB with this action.
class UpgradeFirmwareMachineAction(MachineAction):
    def __init__(self):
        super().__init__("UpgradeFirmware", catalog.i18nc("@action", "Upgrade Firmware"))
        self._qml_url = "UpgradeFirmwareMachineAction.qml"
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions if they support USB connection
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtSlot(result=str)
    def getReleaseNotesUrl(self):
        machine_id = Application.getInstance().getGlobalContainerStack().getBottom().getId()
        if machine_id == "bcn3dsigma":
            return "https://github.com/BCN3D/BCN3DSigma-Firmware/releases"
        elif machine_id == "bcn3dsigmax":
            return "https://github.com/BCN3D/BCN3DSigmax-Firmware/releases"
        else:
            return ""
