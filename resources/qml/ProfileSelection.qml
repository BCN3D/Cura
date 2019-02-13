// Copyright (c) 2017 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.8
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import "Menus"

Item
    {
        id: globalProfileRow
        height: UM.Theme.getSize("sidebar_setup").height
        visible: !sidebar.monitoringPrint && !sidebar.hideSettings

        anchors
        {
            top: parent.top
            left: parent.left
            leftMargin: Math.round(UM.Theme.getSize("sidebar_margin").width)
            right: parent.right
            rightMargin: Math.round(UM.Theme.getSize("sidebar_margin").width)
        }

        Label
        {
            id: globalProfileLabel
            text: catalog.i18nc("@label","Profile:");
            width: Math.round(parent.width * 0.45 - UM.Theme.getSize("sidebar_margin").width - 2)
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            verticalAlignment: Text.AlignVCenter
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }

        MouseArea {
            property color color: UM.Theme.getColor("setting_control_button");
            property color hoverColor: UM.Theme.getColor("setting_control_button_hover");

            height: Math.round(parent.height / 2)
            width: height
            anchors.right: globalProfileSelection.left
            anchors.rightMargin: UM.Theme.getSize("sidebar_margin_thin").width
            anchors.verticalCenter: parent.verticalCenter
            hoverEnabled: true
            visible: !Cura.MachineManager.sameNozzleExtruders

            UM.RecolorImage {
                id: infoIcon;

                anchors.fill: parent;
                sourceSize.width: width
                sourceSize.height: width
                source: UM.Theme.getIcon("notice")

                color: parent.containsMouse ? parent.hoverColor : parent.color;
            }

            onEntered:
            {
                base.showTooltip(globalProfileRow, Qt.point(-UM.Theme.getSize("sidebar_margin").width, infoIcon.height/2), catalog.i18nc("@label", "Since there are different hotends on the left and right extruder, only profiles with common layer heights are available. If you want to print with just one extruder, please select the same hotend on both extruders."))
            }

            onExited:
            {
                base.hideTooltip();
            }
        }

        ToolButton
        {
            id: globalProfileSelection

            text: generateActiveQualityText()
            enabled: !header.currentExtruderVisible || header.currentExtruderIndex > -1
            width: Math.round(parent.width * 0.55)
            height: UM.Theme.getSize("setting_control").height
            anchors.left: globalProfileLabel.right
            anchors.right: parent.right
            tooltip: Cura.MachineManager.activeQualityName
            style: UM.Theme.styles.sidebar_header_button
            activeFocusOnPress: true
            menu: ProfileMenu { }

            function generateActiveQualityText () {
                var result = Cura.MachineManager.activeQualityName;

                if (Cura.MachineManager.isActiveQualitySupported) {
                    if (Cura.MachineManager.activeQualityLayerHeight > 0) {
                        result += " <font color=\"" + UM.Theme.getColor("text_detail") + "\">"
                        result += " - "
                        result += Cura.MachineManager.activeQualityLayerHeight + "mm"
                        result += "</font>"
                    }
                }

                return result
            }

            UM.SimpleButton
            {
                id: customisedSettings

                visible: Cura.MachineManager.hasUserSettings
                height: Math.round(parent.height * 0.6)
                width: Math.round(parent.height * 0.6)

                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: Math.round(UM.Theme.getSize("setting_preferences_button_margin").width - UM.Theme.getSize("sidebar_margin").width)

                color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
                iconSource: UM.Theme.getIcon("star");

                onClicked:
                {
                    forceActiveFocus();
                    Cura.Actions.manageProfiles.trigger()
                }
                onEntered:
                {
                    var content = catalog.i18nc("@tooltip","Some setting/override values are different from the values stored in the profile.\n\nClick to open the profile manager.")
                    base.showTooltip(globalProfileRow, Qt.point(-UM.Theme.getSize("sidebar_margin").width, 0),  content)
                }
                onExited: base.hideTooltip()
            }
        }
    }