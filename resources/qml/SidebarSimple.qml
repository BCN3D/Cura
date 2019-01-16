// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.8
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.2 as Cura

Item
{
    id: base

    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    property Action configureSettings;
    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;
    property bool settingsEnabled: Cura.ExtruderManager.activeExtruderStackId || machineExtruderCount.properties.value == 1

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name: "cura" }

    ScrollView
    {
        visible: Cura.MachineManager.activeMachineName != "" // If no printers added then the view is invisible
        anchors.fill: parent
        style: UM.Theme.styles.scrollview
        flickableItem.flickableDirection: Flickable.VerticalFlick

        Rectangle
        {
            width: childrenRect.width
            height: childrenRect.height
            color: UM.Theme.getColor("sidebar")

            //
            // Infill
            //
            Item
            {
                id: infillCellLeft

                anchors.top: parent.top
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: parent.left

                width: Math.round(UM.Theme.getSize("sidebar").width * .45 - UM.Theme.getSize("sidebar_margin").width)

                Label
                {
                    id: infillLabel
                    text: catalog.i18nc("@label", "Infill")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")

                    anchors.top: parent.top
                    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height * 1.7)
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                }
            }

            Item
            {
                id: infillCellRight

                height: infillSlider.height + UM.Theme.getSize("sidebar_margin").height + enableGradualInfillCheckBox.visible * (enableGradualInfillCheckBox.height + UM.Theme.getSize("sidebar_margin").height)
                width: Math.round(UM.Theme.getSize("sidebar").width * .55)

                anchors.left: infillCellLeft.right
                anchors.top: infillCellLeft.top
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height

                Label {
                    id: selectedInfillRateText

                    //anchors.top: parent.top
                    anchors.left: infillSlider.left
                    anchors.leftMargin: Math.round((infillSlider.value / infillSlider.stepSize) * (infillSlider.width / (infillSlider.maximumValue / infillSlider.stepSize)) - 10 * screenScaleFactor)
                    anchors.right: parent.right

                    text: parseInt(infillDensity.properties.value) + "%"
                    horizontalAlignment: Text.AlignLeft

                    color: infillSlider.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                }

                // We use a binding to make sure that after manually setting infillSlider.value it is still bound to the property provider
                Binding {
                    target: infillSlider
                    property: "value"
                    value: parseInt(infillDensity.properties.value)
                }

                Slider
                {
                    id: infillSlider

                    anchors.top: selectedInfillRateText.bottom
                    anchors.left: parent.left
                    anchors.right: infillIcon.left
                    anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width

                    height: UM.Theme.getSize("sidebar_margin").height
                    width: parseInt(infillCellRight.width - UM.Theme.getSize("sidebar_margin").width - style.handleWidth)

                    minimumValue: 0
                    maximumValue: 100
                    stepSize: 1
                    tickmarksEnabled: true

                    // disable slider when gradual support is enabled
                    enabled: parseInt(infillSteps.properties.value) == 0

                    // set initial value from stack
                    value: parseInt(infillDensity.properties.value)

                    onValueChanged: {

                        // Don't round the value if it's already the same
                        if (parseInt(infillDensity.properties.value) == infillSlider.value) {
                            return
                        }

                        // Round the slider value to the nearest multiple of 10 (simulate step size of 10)
                        var roundedSliderValue = Math.round(infillSlider.value / 10) * 10

                        // Update the slider value to represent the rounded value
                        infillSlider.value = roundedSliderValue

                        // Explicitly cast to string to make sure the value passed to Python is an integer.
                        infillDensity.setPropertyValue("value", String(roundedSliderValue))
                    }

                    style: SliderStyle
                    {
                        groove: Rectangle {
                            id: groove
                            implicitWidth: 200 * screenScaleFactor
                            implicitHeight: 2 * screenScaleFactor
                            color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            radius: 1
                        }

                        handle: Item {
                            Rectangle {
                                id: handleButton
                                anchors.centerIn: parent
                                color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                                implicitWidth: 10 * screenScaleFactor
                                implicitHeight: 10 * screenScaleFactor
                                radius: 10 * screenScaleFactor
                            }
                        }

                        tickmarks: Repeater {
                            id: repeater
                            model: control.maximumValue / control.stepSize + 1

                            // check if a tick should be shown based on it's index and wether the infill density is a multiple of 10 (slider step size)
                            function shouldShowTick (index) {
                                if (index % 10 == 0) {
                                    return true
                                }
                                return false
                            }

                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                                width: 1 * screenScaleFactor
                                height: 6 * screenScaleFactor
                                y: 0
                                x: Math.round(styleData.handleWidth / 2 + index * ((repeater.width - styleData.handleWidth) / (repeater.count-1)))
                                visible: shouldShowTick(index)
                            }
                        }
                    }
                }

                Rectangle
                {
                    id: infillIcon

                    width: Math.round((parent.width / 5) - (UM.Theme.getSize("sidebar_margin").width))
                    height: width

                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height / 2)

                    // we loop over all density icons and only show the one that has the current density and steps
                    Repeater
                    {
                        id: infillIconList
                        model: infillModel
                        anchors.fill: parent

                        function activeIndex () {
                            for (var i = 0; i < infillModel.count; i++) {
                                var density = Math.round(infillDensity.properties.value)
                                var steps = Math.round(infillSteps.properties.value)
                                var infillModelItem = infillModel.get(i)

                                if (infillModelItem != "undefined"
                                    && density >= infillModelItem.percentageMin
                                    && density <= infillModelItem.percentageMax
                                    && steps >= infillModelItem.stepsMin
                                    && steps <= infillModelItem.stepsMax
                                ){
                                    return i
                                }
                            }
                            return -1
                        }

                        Rectangle
                        {
                            anchors.fill: parent
                            visible: infillIconList.activeIndex() == index

                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("quality_slider_unavailable")

                            UM.RecolorImage {
                                anchors.fill: parent
                                anchors.margins: 2 * screenScaleFactor
                                sourceSize.width: width
                                sourceSize.height: width
                                source: UM.Theme.getIcon(model.icon)
                                color: UM.Theme.getColor("quality_slider_unavailable")
                            }
                        }
                    }
                }

                //  Gradual Support Infill Checkbox
                CheckBox {
                    id: enableGradualInfillCheckBox
                    property alias _hovered: enableGradualInfillMouseArea.containsMouse

                    anchors.top: infillSlider.bottom
                    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height / 2) // closer to slider since it belongs to the same category
                    anchors.left: infillCellRight.left

                    style: UM.Theme.styles.checkbox
                    enabled: base.settingsEnabled
                    visible: infillSteps.properties.enabled == "True"
                    checked: parseInt(infillSteps.properties.value) > 0

                    MouseArea {
                        id: enableGradualInfillMouseArea

                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: true

                        property var previousInfillDensity: parseInt(infillDensity.properties.value)

                        onClicked: {
                            // Set to 90% only when enabling gradual infill
                            if (parseInt(infillSteps.properties.value) == 0) {
                                previousInfillDensity = parseInt(infillDensity.properties.value)
                                infillDensity.setPropertyValue("value", String(90))
                            } else {
                                infillDensity.setPropertyValue("value", String(previousInfillDensity))
                            }

                            infillSteps.setPropertyValue("value", (parseInt(infillSteps.properties.value) == 0) ? 5 : 0)
                        }

                        onEntered: {
                            base.showTooltip(enableGradualInfillCheckBox, Qt.point(-infillCellRight.x, 0),
                                catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top."))
                        }

                        onExited: {
                            base.hideTooltip()
                        }
                    }

                    Label {
                        id: gradualInfillLabel
                        anchors.left: enableGradualInfillCheckBox.right
                        anchors.leftMargin: Math.round(UM.Theme.getSize("sidebar_margin").width / 2)
                        text: catalog.i18nc("@label", "Enable gradual")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    }
                }

                //  Infill list model for mapping icon
                ListModel
                {
                    id: infillModel
                    Component.onCompleted:
                    {
                        infillModel.append({
                            percentageMin: -1,
                            percentageMax: 0,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "hollow"
                        })
                        infillModel.append({
                            percentageMin: 0,
                            percentageMax: 40,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "sparse"
                        })
                        infillModel.append({
                            percentageMin: 40,
                            percentageMax: 89,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "dense"
                        })
                        infillModel.append({
                            percentageMin: 90,
                            percentageMax: 9999999999,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "solid"
                        })
                        infillModel.append({
                            percentageMin: 0,
                            percentageMax: 9999999999,
                            stepsMin: 1,
                            stepsMax: 9999999999,
                            icon: "gradual"
                        })
                    }
                }
            }

            //
            //  Enable support
            //
            Label
            {
                id: enableSupportLabel
                visible: enableSupportCheckBox.visible

                anchors.top: infillCellRight.bottom
                anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height * 1.5)
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.right: infillCellLeft.right
                anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.verticalCenter: enableSupportCheckBox.verticalCenter

                text: catalog.i18nc("@label", "Generate Support");
                font: UM.Theme.getFont("default");
                color: UM.Theme.getColor("text");
                elide: Text.ElideRight
            }

            CheckBox
            {
                id: enableSupportCheckBox
                property alias _hovered: enableSupportMouseArea.containsMouse

                anchors.top: enableSupportLabel.top
                anchors.left: infillCellRight.left

                style: UM.Theme.styles.checkbox;
                enabled: base.settingsEnabled

                visible: supportEnabled.properties.enabled == "True"
                checked: supportEnabled.properties.value == "True";

                MouseArea
                {
                    id: enableSupportMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: true
                    onClicked:
                    {
                        // The value is a string "True" or "False"
                        supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True");
                    }
                    onEntered:
                    {
                        base.showTooltip(enableSupportCheckBox, Qt.point(-enableSupportCheckBox.x, 0),
                            catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }
            }

            Label
            {
                id: supportExtruderLabel
                visible: supportExtruderCombobox.visible
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.right: infillCellLeft.right
                anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.verticalCenter: supportExtruderCombobox.verticalCenter
                text: catalog.i18nc("@label", "Support Extruder");
                font: UM.Theme.getFont("default");
                color: UM.Theme.getColor("text");
                elide: Text.ElideRight
            }

            ComboBox
            {
                id: supportExtruderCombobox
                visible: enableSupportCheckBox.visible && (supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)
                model: extruderModel

                property string color_override: ""  // for manually setting values
                property string color:  // is evaluated automatically, but the first time is before extruderModel being filled
                {
                    var current_extruder = extruderModel.get(currentIndex);
                    color_override = "";
                    if (current_extruder === undefined) return ""
                    return (current_extruder.color) ? current_extruder.color : "";
                }

                textRole: "text"  // this solves that the combobox isn't populated in the first time Cura is started

                anchors.top: enableSupportCheckBox.bottom
                anchors.topMargin: ((supportEnabled.properties.value === "True") && (machineExtruderCount.properties.value > 1)) ? UM.Theme.getSize("sidebar_margin").height : 0
                anchors.left: infillCellRight.left

                width: Math.round(UM.Theme.getSize("sidebar").width * .55)
                height: ((supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)) ? UM.Theme.getSize("setting_control").height : 0

                Behavior on height { NumberAnimation { duration: 100 } }

                style: UM.Theme.styles.combobox_color
                enabled: base.settingsEnabled
                property alias _hovered: supportExtruderMouseArea.containsMouse

                currentIndex: supportExtruderNr.properties !== null ? parseFloat(supportExtruderNr.properties.value) : 0
                onActivated:
                {
                    // Send the extruder nr as a string.
                    supportExtruderNr.setPropertyValue("value", String(index));
                }
                MouseArea
                {
                    id: supportExtruderMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: base.settingsEnabled
                    acceptedButtons: Qt.NoButton
                    onEntered:
                    {
                        base.showTooltip(supportExtruderCombobox, Qt.point(-supportExtruderCombobox.x, 0),
                            catalog.i18nc("@label", "Select which extruder to use for support. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }

                function updateCurrentColor()
                {
                    var current_extruder = extruderModel.get(currentIndex);
                    if (current_extruder !== undefined) {
                        supportExtruderCombobox.color_override = current_extruder.color;
                    }
                }

            }

            Label
            {
                id: adhesionHelperLabel
                visible: adhesionCheckBox.visible

                text: catalog.i18nc("@label", "Build Plate Adhesion")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                elide: Text.ElideRight

                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("sidebar_margin").width
                    right: infillCellLeft.right
                    rightMargin: UM.Theme.getSize("sidebar_margin").width
                    verticalCenter: adhesionCheckBox.verticalCenter
                }
            }

            CheckBox
            {
                id: adhesionCheckBox
                property alias _hovered: adhesionMouseArea.containsMouse

                anchors.top: enableSupportCheckBox.visible ? supportExtruderCombobox.bottom : infillCellRight.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: infillCellRight.left

                //: Setting enable printing build-plate adhesion helper checkbox
                style: UM.Theme.styles.checkbox;
                enabled: base.settingsEnabled

                visible: platformAdhesionType.properties.enabled == "True"
                checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"

                MouseArea
                {
                    id: adhesionMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: base.settingsEnabled
                    onClicked:
                    {
                        var adhesionType = "skirt";
                        if(!parent.checked)
                        {
                            // Remove the "user" setting to see if the rest of the stack prescribes a brim or a raft
                            platformAdhesionType.removeFromContainer(0);
                            adhesionType = platformAdhesionType.properties.value;
                            if(adhesionType == "skirt" || adhesionType == "none")
                            {
                                // If the rest of the stack doesn't prescribe an adhesion-type, default to a brim
                                adhesionType = "brim";
                            }
                        }
                        platformAdhesionType.setPropertyValue("value", adhesionType);
                    }
                    onEntered:
                    {
                        base.showTooltip(adhesionCheckBox, Qt.point(-adhesionCheckBox.x, 0),
                            catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }
            }

            ListModel
            {
                id: extruderModel
                Component.onCompleted: populateExtruderModel()
            }

            //: Model used to populate the extrudelModel
            Cura.ExtrudersModel
            {
                id: extruders
                onModelChanged: populateExtruderModel()
            }

            UM.SettingPropertyProvider
            {
                id: infillExtruderNumber
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_extruder_nr"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: infillDensity
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_sparse_density"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: infillSteps
                containerStackId: Cura.MachineManager.activeStackId
                key: "gradual_infill_steps"
                watchedProperties: ["value", "enabled"]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: platformAdhesionType
                containerStackId: Cura.MachineManager.activeMachineId
                key: "adhesion_type"
                watchedProperties: [ "value", "enabled" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: supportEnabled
                containerStackId: Cura.MachineManager.activeMachineId
                key: "support_enable"
                watchedProperties: [ "value", "enabled", "description" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: machineExtruderCount
                containerStackId: Cura.MachineManager.activeMachineId
                key: "machine_extruder_count"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: supportExtruderNr
                containerStackId: Cura.MachineManager.activeMachineId
                key: "support_extruder_nr"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }
        }
    }

    function populateExtruderModel()
    {
        extruderModel.clear();
        for(var extruderNumber = 0; extruderNumber < extruders.rowCount() ; extruderNumber++)
        {
            extruderModel.append({
                text: extruders.getItem(extruderNumber).name,
                color: extruders.getItem(extruderNumber).color
            })
        }
        supportExtruderCombobox.updateCurrentColor();
    }
}
