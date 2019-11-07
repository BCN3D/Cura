from UM.Application import Application
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM import Util

from cura.Bcn3DApi.AuthApiService import AuthApiService

from .CloudOutputDevice import CloudOutputDevice

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


##  Implements an OutputDevicePlugin that provides a single instance of CloudOutputDevice
class CloudOutputDevicePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._global_stack = None
        self._supports_cloud_connection = False
        self._is_logged_in = False

    def start(self):
        AuthApiService.getInstance().authStateChanged.connect(self._authStateChanged)
        Application.getInstance().globalContainerStackChanged.connect(self._globalStackChanged)

    def stop(self):
        self.getOutputDeviceManager().removeOutputDevice("cloud")

    def _authStateChanged(self, logged_in):
        self._is_logged_in = logged_in
        if self._is_logged_in and self._supports_cloud_connection:
            self.getOutputDeviceManager().addOutputDevice(CloudOutputDevice())
        else:
            self.stop()

    def _globalStackChanged(self):
        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._supports_cloud_connection = Util.parseBool(self._global_stack.getMetaDataEntry("is_network_machine"))

            if self._supports_cloud_connection and self._is_logged_in:
                self.getOutputDeviceManager().addOutputDevice(CloudOutputDevice())
            else:
                self.stop()
