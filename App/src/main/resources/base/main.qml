import QtQuick.Window 2.12
import QtQuick.Controls 2.5
import QtQuick.Controls.Material 2.0
import QtQuick.Dialogs 1.3
import QtQuick 2.8
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

Window {
    id: window
    visible: true
    width: 980
    height: 700
    title: qsTr("AI Drummer")

    MessageDialog {
        id: messageDialog
        text: ""
        onAccepted: {
            messageDialog.close();
        }
    }

    Dialog {
        id: load_dialog
        title: "Choose a rule"
        contentItem: Column {
            padding: 20
            Row {
                ListView {
                    id: list
                    model: api.ruleModel.rulesList
                    highlight: Rectangle { color: "#dae5e8"; radius: 5; }
                    focus: true
                    implicitWidth: 600
                    implicitHeight: 400
                    onCurrentIndexChanged: api.ruleModel.rulesListSelection = currentIndex
                    delegate: Item {
                        width: parent.width
                        height: 20
                        Row{
                            Text { text: api.ruleModel.rulesList[index]; width: 160 }
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: list.currentIndex = index
                        }
                    }
                }
            }
            Row {
                spacing: 10
                Button {
                    id: load_button
                    width: 120
                    height: 30
                    text: qsTr("Load")
                    onClicked: {
                        api.ruleModel.load_rule();
                        load_dialog.close()
                    }
                }
                Button {
                    id: delete_button
                    width: 120
                    height: 30
                    text: qsTr("Delete")
                    onClicked: api.ruleModel.delete_rule()
                }
                Button {
                    id: cancel_button
                    width: 120
                    height: 30
                    text: qsTr("Cancel")
                    onClicked: load_dialog.close()
                }
            }
        }

    }

    Rectangle {
        id: rectangle1
        width: 980
        color: "#191919"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.top: parent.top
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        clip: true
        rotation: 0

        ColumnLayout {
            y: 16
            height: 579
            anchors.right: parent.right
            anchors.rightMargin: 156
            anchors.left: parent.horizontalCenter
            anchors.leftMargin: -466
            visible: true

            RowLayout {
                id: buttonsRow
                Button{
                    text: "New Rule"
                    onClicked:{
                        api.add_rule()
                        ruleLoader.visible = true;
                    }
                }

                Button {
                    text: "Save Rule"
                    onClicked:{
                        var data = api.ruleModel.save_rule()
                        messageDialog.text = data['message']
                        messageDialog.open()
                    }
                }

                Button {
                    text: "Load Rule"
                    onClicked:{
                        api.ruleModel.reset()
                        api.ruleModel.read_rules()
                        load_dialog.open()
                    }
                }

                CheckBox {
                    id: checkBox
                    width: 120
                    height: 30
                    text: "<font color=\"white\">Use Custom Rules</font>"
                    checked: false
                    onCheckStateChanged: {api.useCustomRules = checkState}
                }
            }

            Item {
                id: listView
                clip: true
                Layout.fillWidth: true
                Layout.fillHeight: true
                ScrollView {
                    anchors.fill: parent
                    Loader {
                        id: ruleLoader
                        property QtObject rule_model: api.ruleModel
                        visible: false
                        source: 'Rule.qml'
                    }
                }

            }
        }


        Rectangle {
            id: rectangle
            x: 711
            width: 400
            height: 200
            color: "#3a3a3a"
            anchors.top: parent.top
            anchors.topMargin: -33
            anchors.right: parent.right
            anchors.rightMargin: -131
            rotation: 45
            clip: true
            Material.theme: Material.Dark
            Material.accent: Material.DeepOrange
        }

        RoundButton {
            id: playButton
            x: 356
            y: 632
            width: 100
            text: "Play"
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 28
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: 70
            onClicked: { api.play()}
        }

        RoundButton {
            id: stopButton
            x: 500
            y: 632
            width: 100
            text: "Stop"
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: -70
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 28
            onClicked: { api.stop()}
        }

        ComboBox {
            id: in_port
            visible: location.local
            x: 214
            y: 637
            width: 120
            height: 30
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: 176
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 33
            model: api.midiIn
            onCurrentIndexChanged: api.setMidiInSelection(currentIndex)
            displayText: "Midi In"
            popup.width: width*2
        }

        ComboBox {
            id: out_port
            visible: location.local
            x: 68
            y: 637
            width: 120
            height: 30
            anchors.bottomMargin: 33
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: 302
            anchors.bottom: parent.bottom
            model: api.midiOut
            onCurrentIndexChanged: api.setMidiOutSelection(currentIndex)
            displayText: "Midi Out"
            popup.width: width*2
        }

        ComboBox {
            id: play_type
            x: 566
            y: 637
            width: 120
            height: 30
            displayText: "Play Type"
            anchors.rightMargin: -196
            anchors.bottomMargin: 33
            anchors.bottom: parent.bottom
            model: api.playType
            onCurrentIndexChanged: api.setPlayTypeSelection(currentIndex)
            anchors.right: parent.horizontalCenter
            popup.width: width*2
        }

        ComboBox {
            id: instrument_port
            visible: location.local
            x: 692
            y: 637
            width: 120
            height: 30
            displayText: "Instrument"
            anchors.rightMargin: -322
            anchors.bottomMargin: 33
            anchors.bottom: parent.bottom
            anchors.right: parent.horizontalCenter
            model: api.instrument
            onCurrentIndexChanged: api.setInstrumentSelection(currentIndex)
            popup.width: width*2
        }

        ComboBox {
            id: play_piano
            x: 692
            y: 601
            width: 120
            height: 30
            displayText: "Play Piano"
            anchors.rightMargin: -322
            anchors.bottomMargin: 69
            anchors.bottom: parent.bottom
            anchors.right: parent.horizontalCenter
            model: api.playInstrument
            onCurrentIndexChanged: api.setPlayInstrumentSelection(currentIndex)
            popup.width: width*2
        }
        Button {
            id: button
            x: 566
            y: 601
            width: 120
            height: 30
            text: qsTr("MIDI File")
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: -196
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 69
            onClicked: midi_file.open()

        }
        FileDialog{
            id: midi_file
            folder: shortcuts.home
            onAccepted: api.set_MidiFile(fileUrl)

        }

        ComboBox {
            id: location
            x: 68
            y: 601
            width: 120
            height: 30
            anchors.right: parent.horizontalCenter
            displayText: "Location"
            anchors.bottomMargin: 69
            anchors.rightMargin: 302
            anchors.bottom: parent.bottom
            model: api.location
            property bool local: true
            property bool remote: false
            onCurrentIndexChanged: {
                api.setLocationSelection(currentIndex);
                if (currentIndex == 0){
                    local = true;
                    remote = false;
                }
                else {
                    local = false;
                    remote = true;
                }
            }
            popup.width: width*2
        }

        TextField {
            id: ip
            visible: location.remote
            x: 194
            y: 601
            width: 120
            height: 30
            text: api.ipText
            onTextChanged: api.ipText = text
            font.pointSize: 11
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: 176
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 69
            placeholderText: "Remote IP"
        }

        ComboBox {
            id: style
            visible: location.remote
            x: 818
            y: 637
            width: 120
            height: 30
            anchors.bottom: parent.bottom
            anchors.right: parent.horizontalCenter
            displayText: "Style"
            anchors.rightMargin: -448
            anchors.bottomMargin: 33
            model: api.style
            onCurrentIndexChanged: api.setStyleSelection(currentIndex)
            popup.width: width*2
        }

    }
    Connections {
        target: api
    }
}
/*##^##
Designer {
    D{i:2;anchors_height:579;anchors_width:800;anchors_x:33;anchors_y:16}D{i:1;anchors_width:980}
}
##^##*/
