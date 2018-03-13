// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1
import QtQuick.Dialogs 1.2 // For filedialog

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.MachineAction
{
    property var connectedPrinter: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
    anchors.fill: parent;
    Item
    {
        id: upgradeFirmwareMachineAction
        anchors.fill: parent;
        UM.I18nCatalog { id: catalog; name:"cura"}

        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Upgrade Firmware")
            wrapMode: Text.WordWrap
            font.pointSize: 18
        }
        Label
        {
            id: pageDescription
            anchors.top: pageTitle.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "Firmware is the piece of software running directly on your 3D printer. This firmware controls the step motors, regulates the temperature and ultimately makes your printer work.")
        }

        Label
        {
            id: upgradeText1
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "The firmware shipping with new printers works, but new versions tend to have more features and improvements.");
        }

        Label
        {
            id: currentVersion
            anchors.top: upgradeText1.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            visible: connectedPrinter != null && connectedPrinter.connectionState == 2
            text: connectedPrinter != null ? catalog.i18nc("@label", "Current Version") + ": " + connectedPrinter.firmwareVersion : ""
        }
        Label
        {
            id: latestVersion
            anchors.top: currentVersion.bottom
            width: parent.width
            visible: connectedPrinter != null && connectedPrinter.connectionState == 2
            text: connectedPrinter != null ? catalog.i18nc("@label", "Latest Version") + ": " + connectedPrinter.firmwareLatestVersion : ""
        }
        Label
        {
            id: releaseNotes
            anchors.top: latestVersion.bottom
            width: parent.width
            visible: connectedPrinter != null && connectedPrinter.connectionState == 2
            text: catalog.i18nc("@label", "<a href='" + manager.getReleaseNotesUrl() + "'>View all release notes</a>")
            onLinkActivated: Qt.openUrlExternally(link)
        }

        Row
        {
            id: buttonsRow
            anchors.top: currentVersion.visible ? releaseNotes.bottom : upgradeText1.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            width: childrenRect.width
            spacing: UM.Theme.getSize("default_margin").width
            Button
            {
                id: autoUpgradeButton
                text: catalog.i18nc("@action:button", "Automatically upgrade Firmware");
                enabled: connectedPrinter != null && connectedPrinter.connectionState == 2;
                onClicked:
                {
                    Cura.USBPrinterManager.updateAllFirmware("")
                }
            }
            Button
            {
                id: manualUpgradeButton
                text: catalog.i18nc("@action:button", "Upload custom Firmware");
                enabled: connectedPrinter != null && connectedPrinter.connectionState == 2;
                onClicked:
                {
                    customFirmwareDialog.open()
                }
            }
        }
        Label
        {
            id: noPrinterWarning
            anchors.top: buttonsRow.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            text: catalog.i18nc("@label", "Connect the printer to upgrade firmware");
            visible: connectedPrinter == null;
        }
        Label
        {
            id: printerConnectionState
            anchors.top: buttonsRow.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            visible: connectedPrinter != null;
            text:
            {
                switch (connectedPrinter.connectionState)
                {
                    case 1:
                        return "Connecting printer"
                    default:
                        return ""
                }
            }
        }

        FileDialog
        {
            id: customFirmwareDialog
            title: catalog.i18nc("@title:window", "Select custom firmware")
            nameFilters:  "Firmware image files (*.hex)"
            selectExisting: true
            onAccepted: Cura.USBPrinterManager.updateAllFirmware(fileUrl)
        }
    }
}