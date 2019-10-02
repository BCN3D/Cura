from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from .CloudOutputDevice import CloudOutputDevice

from cura.Authentication.AuthenticationService import AuthenticationService

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


##  Implements an OutputDevicePlugin that provides a single instance of CloudOutputDevice
class CloudOutputDevicePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()

    def start(self):
        AuthenticationService.getInstance().onAuthStateChanged.connect(self._authStateChanged)

    def stop(self):
        self.getOutputDeviceManager().removeOutputDevice("cloud")

    def _authStateChanged(self, logged_in):
        if logged_in:
            self.getOutputDeviceManager().addOutputDevice(CloudOutputDevice())
        else:
            self.stop()
