# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import math

from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtGui import QDesktopServices
from UM.FlameProfiler import pyqtSlot

from UM.Event import CallFunctionEvent
from UM.Application import Application
from UM.Math.Vector import Vector
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.SetTransformOperation import SetTransformOperation
from UM.Operations.TranslateOperation import TranslateOperation

from cura.Operations.RemoveNodesOperation import RemoveNodesOperation
from cura.Operations.SetParentOperation import SetParentOperation
from cura.MultiplyObjectsJob import MultiplyObjectsJob
from cura.Settings.SetObjectExtruderOperation import SetObjectExtruderOperation
from cura.Settings.ExtruderManager import ExtruderManager
from cura.PrintModeManager import PrintModeManager

from cura.Operations.SetBuildPlateNumberOperation import SetBuildPlateNumberOperation

from UM.Logger import Logger


class CuraActions(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot()
    def openDocumentation(self):
        # Starting a web browser from a signal handler connected to a menu will crash on windows.
        # So instead, defer the call to the next run of the event loop, since that does work.
        # Note that weirdly enough, only signal handlers that open a web browser fail like that.
        event = CallFunctionEvent(self._openUrl, [QUrl("http://www.bcn3dtechnologies.com/wp-content/themes/BCN3D/pdfs/BCN3D_Technologies_BCN3D_Cura_User_Manual.pdf")], {})
        Application.getInstance().functionEvent(event)

    @pyqtSlot()
    def openBugReportPage(self):
        event = CallFunctionEvent(self._openUrl, [QUrl("http://github.com/BCN3D/Cura/issues")], {})
        Application.getInstance().functionEvent(event)

    ##  Reset camera position and direction to default
    @pyqtSlot()
    def homeCamera(self) -> None:
        scene = Application.getInstance().getController().getScene()
        camera = scene.getActiveCamera()
        camera.setPosition(Vector(-80, 250, 700))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))

    ##  Center all objects in the selection
    @pyqtSlot()
    def centerSelection(self) -> None:
        operation = GroupedOperation()
        for node in Selection.getAllSelectedObjects():
            current_node = node
            while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
                current_node = current_node.getParent()

            vector = current_node._position
            print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
            if print_mode_enabled:
                print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
                if print_mode != "regular":
                    machine_width = Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value")
                    center = -machine_width / 4
                    if print_mode == "mirror":
                        machine_head_with_fans_polygon = Application.getInstance().getGlobalContainerStack().getProperty(
                            "machine_head_with_fans_polygon", "value")
                        machine_head_size = math.fabs( machine_head_with_fans_polygon[0][0] - machine_head_with_fans_polygon[2][0])
                        center -= machine_head_size / 4
                    vector = Vector(current_node._position.x - center, current_node._position.y, current_node._position.z)

            center_operation = TranslateOperation(current_node, -vector)
            operation.addOperation(center_operation)
            # node.setPosition(vector)
        operation.push()

    ##  Multiply all objects in the selection
    #
    #   \param count The number of times to multiply the selection.
    @pyqtSlot(int)
    def multiplySelection(self, count: int) -> None:
        job = MultiplyObjectsJob(Selection.getAllSelectedObjects(), count, min_offset = 4)
        job.start()

    ##  Delete all selected objects.
    @pyqtSlot()
    def deleteSelection(self) -> None:
        if not Application.getInstance().getController().getToolsEnabled():
            return

        removed_group_nodes = []
        op = GroupedOperation()
        nodes = Selection.getAllSelectedObjects()
        for node in nodes:
            print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
            if print_mode_enabled:
                node_dup = PrintModeManager.getInstance().getDuplicatedNode(node)
                op.addOperation(RemoveNodesOperation(node_dup))
            else:
                op.addOperation(RemoveSceneNodeOperation(node))
            group_node = node.getParent()
            if group_node and group_node.callDecoration("isGroup") and group_node not in removed_group_nodes:
                remaining_nodes_in_group = list(set(group_node.getChildren()) - set(nodes))
                if len(remaining_nodes_in_group) == 1:
                    removed_group_nodes.append(group_node)
                    op.addOperation(SetParentOperation(remaining_nodes_in_group[0], group_node.getParent()))
                    op.addOperation(RemoveSceneNodeOperation(group_node))

            # Reset the print information
            Application.getInstance().getController().getScene().sceneChanged.emit(node)

        op.push()

    ##  Set the extruder that should be used to print the selection.
    #
    #   \param extruder_id The ID of the extruder stack to use for the selected objects.
    @pyqtSlot(str)
    def setExtruderForSelection(self, extruder_id: str) -> None:
        operation = GroupedOperation()

        nodes_to_change = []
        for node in Selection.getAllSelectedObjects():
            # Do not change any nodes that already have the right extruder set.
            if node.callDecoration("getActiveExtruder") == extruder_id:
                continue

            # If the node is a group, apply the active extruder to all children of the group.
            if node.callDecoration("isGroup"):
                for grouped_node in BreadthFirstIterator(node):
                    if grouped_node.callDecoration("getActiveExtruder") == extruder_id:
                        continue

                    if grouped_node.callDecoration("isGroup"):
                        continue

                    nodes_to_change.append(grouped_node)
                continue

            nodes_to_change.append(node)

        if not nodes_to_change:
            # If there are no changes to make, we still need to reset the selected extruders.
            # This is a workaround for checked menu items being deselected while still being
            # selected.
            ExtruderManager.getInstance().resetSelectedObjectExtruders()
            return

        for node in nodes_to_change:
            operation.addOperation(SetObjectExtruderOperation(node, extruder_id))
        operation.push()

    @pyqtSlot(int)
    def setBuildPlateForSelection(self, build_plate_nr: int) -> None:
        Logger.log("d", "Setting build plate number... %d" % build_plate_nr)
        operation = GroupedOperation()

        root = Application.getInstance().getController().getScene().getRoot()

        nodes_to_change = []
        for node in Selection.getAllSelectedObjects():
            parent_node = node  # Find the parent node to change instead
            while parent_node.getParent() != root:
                parent_node = parent_node.getParent()

            for single_node in BreadthFirstIterator(parent_node):
                nodes_to_change.append(single_node)

        if not nodes_to_change:
            Logger.log("d", "Nothing to change.")
            return

        for node in nodes_to_change:
            operation.addOperation(SetBuildPlateNumberOperation(node, build_plate_nr))
        operation.push()

        Selection.clear()

    def _openUrl(self, url):
        QDesktopServices.openUrl(url)
