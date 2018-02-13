from copy import deepcopy

from UM.Math.Vector import Vector
from UM.Operations.MirrorOperation import MirrorOperation
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode

from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.SetObjectExtruderOperation import SetObjectExtruderOperation

class DuplicatedNode(CuraSceneNode):

    def __init__(self, node, parent = None):
        super().__init__(parent)
        self.node = node
        self.setTransformation(node.getLocalTransformation())
        self.setMeshData(node.getMeshData())
        self.setVisible(deepcopy(node.isVisible()))
        self._selectable = False
        self._name = deepcopy(node.getName())
        for decorator in node.getDecorators():
            self.addDecorator(deepcopy(decorator))

        for child in node.getChildren():
            if type(child) == SceneNode:
                self.addChild(DuplicatedNode(child))
            else:
                self.addChild(deepcopy(child))

        node.calculateBoundingBoxMesh()
        self.node.transformationChanged.connect(self._onTransformationChanged)
        self.node.parentChanged.connect(self._someParentChanged)
        self.parentChanged.connect(self._someParentChanged)
        SetObjectExtruderOperation(self, ExtruderManager.getInstance().getExtruderStack(1).getId()).redo()

    def setSelectable(self, select: bool):
        self._selectable = False

    def update(self):
        if type(self.getParent()) == DuplicatedNode:
            self.setTransformation(self.node.getLocalTransformation())
            return
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        machine_width = Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value")
        self.setScale(self.node.getScale())
        node_pos = self.node.getPosition()
        self.setTransformation(self.node.getLocalTransformation())

        if print_mode == "mirror":
            MirrorOperation(self, Vector(-1, 1, 1)).redo()
            self.setPosition(Vector(-node_pos.x, node_pos.y, node_pos.z))
        elif print_mode == "duplication":
            self.setPosition(Vector(node_pos.x + (machine_width/2), node_pos.y, node_pos.z))
        else:
            return

        if node_pos.x > 0:
            self.node.setPosition(Vector(0, node_pos.y, node_pos.z))

    def _onTransformationChanged(self, node):
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode != "regular":
            self.update()

    def _someParentChanged(self, node=None):
        self.update()