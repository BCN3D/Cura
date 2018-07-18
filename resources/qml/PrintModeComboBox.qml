import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: printModeCell

    property bool showInfoIcon: Cura.MachineManager.activeMachineId == "Sigma"

    anchors.top: settingsModeSelection.bottom
    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 2
    anchors.left: parent.left
    anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
    anchors.right: parent.right
    height: childrenRect.height
    visible: printModes.visible

    UM.I18nCatalog{id: catalog; name:"cura"}

    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    Label
    {
        id: printModeLabel
        text: catalog.i18nc("@label", printMode.properties.label)
        font: UM.Theme.getFont("default");
        color: UM.Theme.getColor("text");
        verticalAlignment: Text.AlignVCenter
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
    }

    MouseArea {
        property color color: UM.Theme.getColor("setting_control_button");
        property color hoverColor: UM.Theme.getColor("setting_control_button_hover");

        height: Math.round(parent.height / 2)
        width: height
        anchors.left: printModeLabel.right
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin_thin").width
        anchors.verticalCenter: parent.verticalCenter
        hoverEnabled: true
        visible: printModeCell.showInfoIcon;

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
            printModeCell.showTooltip(printModeCell, Qt.point(-UM.Theme.getSize("sidebar_margin").width, infoIcon.height/2), catalog.i18nc("@label", "Mirror and Duplication Print Modes are only compatible for Sigma if the firmware version loaded is 1.3.0 or later.\n\n Check your printer's firmware version via the LCD touchscreen. Select Info icon at the upper right corner of the Main Menu and then, select 'Unit Information'"))
        }

        onExited:
        {
            printModeCell.hideTooltip();
        }
    }

    ComboBox
    {
        id: printModeComboBox
        model: printModeModel
        width: Math.round(base.width * 0.55)
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
        anchors.verticalCenter: parent.verticalCenter
        currentIndex: printModes.visible ? printModes.activeIndex : -1
        onActivated: printModes.changeProperty(printModeModel.get(index).text)
        style: UM.Theme.styles.combobox
    }

    ListModel
    {
        id: printModeModel
        Component.onCompleted: populatePrintModeModel()
    }

    Cura.PrintModesModel
    {
        id: printModes
        onPrintModeChanged: updateIndex()
        onPrinterChanged: updateValues()
    }

    function updateValues() {
        printModes.update();
        printModeCell.visible = printModes.visible;
        printModeCell.enabled = printModes.visible;
        populatePrintModeModel();
        updateIndex();
    }

    function updateIndex() {
        printModeComboBox.currentIndex = printModes.activeIndex;
    }

    function populatePrintModeModel() {
        printModeModel.clear();
        if (printModes.visible) {
            for (var i in printModes.printModes) {
                printModeModel.append({
                    text: printModes.printModes[i],
                })
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: printMode

        containerStackId: Cura.MachineManager.activeMachineId
        key: "print_mode"
        watchedProperties: [ "label" ]
        storeIndex: 0
    }
}
