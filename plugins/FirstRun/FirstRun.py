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
            Preferences.getInstance().setValue("cura/first_run", False)
            global_stack = Application.getInstance().getGlobalContainerStack()
            if global_stack.getBottom().getId() == "bcn3dsigmaxr19":
                message = Message("Now the default hotends size is 0.4. You can check it in the printer screeen.", title="New default hotends")
                message.show()