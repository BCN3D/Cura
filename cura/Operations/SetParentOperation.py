# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Operations import Operation
from UM.Math.Vector import Vector

from cura.Scene.DuplicatedNode import DuplicatedNode
from cura.PrintModeManager import PrintModeManager

##  An operation that parents a scene node to another scene node.

class SetParentOperation(Operation.Operation):
    ##  Initialises this SetParentOperation.
    #
    #   \param node The node which will be reparented.
    #   \param parent_node The node which will be the parent.
    def __init__(self, node, parent_node):
        super().__init__()
        self._node = node
        self._parent = parent_node
        self._old_parent = node.getParent() # To restore the previous parent in case of an undo.
        self._scene_root = Application.getInstance().getController().getScene().getRoot()
        self._print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
        self._is_duplicated_node = type(node) == DuplicatedNode

    ##  Undoes the set-parent operation, restoring the old parent.
    def undo(self):
        if self._print_mode_enabled and self._is_duplicated_node:
            self._fixAndSetParent(self._old_parent)
            if type(self._parent) == DuplicatedNode:
                if self._parent in PrintModeManager.getInstance().getDuplicatedNodes():
                    PrintModeManager.getInstance().deleteDuplicatedNode(self._parent, False)
            elif type(self._old_parent) == DuplicatedNode:
                if self._old_parent not in PrintModeManager.getInstance().getDuplicatedNodes():
                    PrintModeManager.getInstance().addDuplicatedNode(self._old_parent)

        else:
            self._set_parent(self._old_parent)

    ##  Re-applies the set-parent operation.
    def redo(self):
        if self._print_mode_enabled and self._is_duplicated_node:
            self._fixAndSetParent(self._parent)
            if type(self._parent) == DuplicatedNode:
                if self._parent not in PrintModeManager.getInstance().getDuplicatedNodes():
                    PrintModeManager.getInstance().addDuplicatedNode(self._parent)
            elif type(self._old_parent) == DuplicatedNode:
                if self._old_parent in PrintModeManager.getInstance().getDuplicatedNodes():
                    PrintModeManager.getInstance().deleteDuplicatedNode(self._old_parent, False)

        else:
            self._set_parent(self._parent)

    def _fixAndSetParent(self, parent):
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode == "regular" and parent == self._scene_root:
            self._set_parent(None)
        elif print_mode != "regular" and parent is None:
            self._set_parent(self._scene_root)
        else:
            self._set_parent(parent)

    ##  Sets the parent of the node while applying transformations to the world-transform of the node stays the same.
    #
    #   \param new_parent The new parent. Note: this argument can be None, which would hide the node from the scene.
    def _set_parent(self, new_parent):
        if new_parent:
            current_parent = self._node.getParent()
            if current_parent:
                # Special casing for groups that have been removed.
                # In that case we want to put them back where they belong before checking the depth difference.
                # If we don't, we always get 0.
                old_parent = new_parent.callDecoration("getOldParent")
                if old_parent:
                    new_parent.callDecoration("getNode").setParent(old_parent)

                # Based on the depth difference, we need to do something different.
                depth_difference = current_parent.getDepth() - new_parent.getDepth()
                child_transformation = self._node.getLocalTransformation()
                if depth_difference > 0:
                    parent_transformation = current_parent.getLocalTransformation()
                    # A node in the chain was removed, so we need to squash the parent info into all the nodes, so positions remain the same.
                    self._node.setTransformation(parent_transformation.multiply(child_transformation))
                else:
                    # A node is inserted into the chain, so use the inverse of the parent to set the transformation of it's children.
                    parent_transformation = new_parent.getLocalTransformation()
                    result = parent_transformation.getInverse().multiply(child_transformation, copy = True)
                    self._node.setTransformation(result)

        self._node.setParent(new_parent)

    ##  Returns a programmer-readable representation of this operation.
    #
    #   \return A programmer-readable representation of this operation.
    def __repr__(self):
        return "SetParentOperation(node = {0}, parent_node={1})".format(self._node, self._parent)
