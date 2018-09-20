// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Window 2.2
import QtQuick.Controls 1.2

import UM 1.1 as UM

UM.Dialog
{
    id: base;

    width: 400;
    minimumWidth: 400 * screenScaleFactor;
    height: 50;
    minimumHeight: 50 * screenScaleFactor;

    visible: true;
    modality: Qt.ApplicationModal;

    title: catalog.i18nc("@title:window","Update LCD files");

    Column
    {
        anchors.fill: parent;

        Label
        {
            anchors
            {
                left: parent.left;
                right: parent.right;
                verticalCenter: parent.verticalCenter;
            }

            text: catalog.i18nc("@label", "<a href='https://www.bcn3dtechnologies.com/wp-content/themes/BCN3D/pdfs/how-to-change-the-micro-sd-card-files-of-the-lcd-screen.pdf'>Click here</a> to view the step by step guide to update the LCD files.");
            onLinkActivated: Qt.openUrlExternally(link);
        }

        UM.I18nCatalog { id: catalog; name: "cura"; }
    }
}
