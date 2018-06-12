import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: printModeCell
    anchors.top: settingsModeSelection.bottom
    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 2
    anchors.left: parent.left
    anchors.right: parent.right
    height: childrenRect.height
    enabled: printModes.visible

    UM.I18nCatalog{id: catalog; name:"cura"}

    Text
    {
        id: printModeLabel
        text: catalog.i18nc("@label", printMode.properties.label)
        font: UM.Theme.getFont("default");
        color: UM.Theme.getColor("text");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
    }

    ComboBox
    {
        id: printModeComboBox
        model: printModeModel
        width: base.width * 0.55
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
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
