from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Message import Message
from UM.Application import Application


class FirstRun(Extension):

    def __init__(self, parent = None):
        super().__init__()
        Preferences.getInstance().addPreference("cura/first_run", True)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)


    def _onGlobalStackChanged(self):
        if Preferences.getInstance().getValue("cura/first_run"):
            global_stack = Application.getInstance().getGlobalContainerStack()
            if global_stack.getBottom().getId() == "bcn3dsigmaxr19":
                Preferences.getInstance().setValue("cura/first_run", False)
                message = Message("Latest Sigmax R19 printers come with 0.4mm nozzles installed. Make sure to select the correct hotend when preparing the print file.", title="Sigmax default hotends")
                message.show()