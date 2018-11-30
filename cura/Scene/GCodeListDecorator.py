from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from copy import deepcopy


class GCodeListDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._gcode_list = []

    def getGCodeList(self):
        return self._gcode_list

    def setGCodeList(self, list):
        self._gcode_list = list

    def __deepcopy__(self, memo):
        copy =  GCodeListDecorator()
        copy.setGCodeList(deepcopy(self._gcode_list, memo))
        return copy
