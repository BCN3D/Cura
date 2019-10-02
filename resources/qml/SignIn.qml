import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.3 as UM
import Cura 1.0 as Cura

Item {

    anchors.verticalCenter: parent.verticalCenter

    Button {
        id: signInButton

        visible: !Cura.AuthenticationService.isLoggedIn
        anchors.verticalCenter: parent.verticalCenter
        width: 80

        style: ButtonStyle {
            background: Rectangle {
                color: control.hovered ? UM.Theme.getColor("primary_hover") : "transparent"
                border.color: "white"
                border.width: 1
            }
            label: Text {
                color: "white"
                text: "Sign In"
                horizontalAlignment: Text.AlignHCenter
            }
        }

        onClicked: signInDialog.open()

    }

    ToolButton {
        id: userButton

        visible: Cura.AuthenticationService.isLoggedIn
        anchors.verticalCenter: parent.verticalCenter

        text: Cura.AuthenticationService.email

        style: ButtonStyle {
            background: Rectangle {
                color: {
                    if(control.pressed) {
                        return UM.Theme.getColor("sidebar_header_active");
                    }
                    else if(control.hovered) {
                        return UM.Theme.getColor("sidebar_header_hover");
                    }
                    else {
                        return UM.Theme.getColor("topbar_background_color");
                    }
                }
                Behavior on color { ColorAnimation { duration: 50; } }
            }
            label: Label {
                id: label
                color: UM.Theme.getColor("sidebar_header_text_active")
                text: control.text;
                elide: Text.ElideRight;
                anchors.left: parent.left;
                anchors.leftMargin: UM.Theme.getSize("default_margin").width / 2
                anchors.right: downArrow.left;
                anchors.rightMargin: control.rightMargin;
                anchors.verticalCenter: parent.verticalCenter;
                font: UM.Theme.getFont("default_bold")
            }
        }

        menu: Menu {
            id: userMenu
            MenuItem {
                text: "Logout"
                onTriggered: signInDialog.signOut()
            }
        }
    }

    UM.Dialog {
        id: signInDialog

        title: "Sign in"

        minimumWidth: 250 * screenScaleFactor
        minimumHeight: 200 * screenScaleFactor
        width: minimumWidth
        height: minimumHeight
        visible: false
        closeOnAccept: false

        onClosing: this.resetForm()

        onRejected: this.resetForm()

        ColumnLayout {
            id: formLayout

            anchors.fill: parent
            anchors.margins: 10

            Item {
                height: 30
                Layout.fillWidth: true

                TextField {
                    id: email

                    width: parent.width
                    placeholderText: "Email"
                    onEditingFinished: {
                        if (text != "") emailError.visible = false
                        else emailError.visible = true
                    }
                }
                Label {
                    id: emailError

                    anchors.top: email.bottom
                    text: "Email is required"
                    color: "red"
                    visible: false
                }
            }

            Item {
                height: 30
                Layout.fillWidth: true

                TextField {
                    id: password

                    width: parent.width
                    placeholderText: "Password"
                    echoMode: TextInput.Password
                    onEditingFinished: {
                        if (text != "") passwordError.visible = false
                        else passwordError.visible = true
                    }
                }
                Label {
                    id: passwordError

                    anchors.top: password.bottom
                    text: "Password is required"
                    color: "red"
                    visible: false
                }
            }

            ColumnLayout {
                Layout.fillWidth: true

                Button {
                    id: submitButton

                    Layout.fillWidth: true
                    text: "Sign in"
                    enabled: email.text != "" && password.text != ""
                    onClicked: signInDialog.signIn()
                }

                Label {
                    text: "<a href='https://www.bcn3dtechnologies.com' title='Register'>Register</a>"
                    onLinkActivated: Qt.openUrlExternally(link)

                    MouseArea {
                        hoverEnabled: true
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        cursorShape: containsMouse ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }
                }
            }
        }

        function signIn() {
            var success = Cura.AuthenticationService.signIn(email.text, password.text)
            if (success) {
                signInButton.visible = false
                userButton.visible = true
                this.resetForm()
                this.close()
            }
        }

        function signOut() {
            var success = Cura.AuthenticationService.signOut()
            if (success) {
                signInButton.visible = true
                userButton.visible = false
            }
        }

        function resetForm() {
            // lose focus from the text inputs to prevend editingFinished signal to emit when opening the dialog
            submitButton.forceActiveFocus()

            email.text = ""
            password.text = ""

            emailError.visible = false
            passwordError.visible = false
        }
    }
}
