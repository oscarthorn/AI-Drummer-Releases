import QtQuick 2.8
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3


Rectangle{
    id: rectangle
    width: 650
    height: columnLayout.implicitHeight + 30
    color: "#3a3a3a"
    radius: 20

    Column {
        id: columnLayout
        spacing: 20
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.top: parent.top
        anchors.rightMargin: 10
        anchors.leftMargin: 10
        anchors.bottomMargin: 10
        anchors.topMargin: 10

        Row {
            spacing: 10

            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: "Add condition:"
                font.pixelSize: 16
                font.italic: true
                color: "white"
            }

            RoundButton {
                id: roundButton
                width: 30
                height: 30
                text: "+"
                wheelEnabled: false
                spacing: 6
                leftPadding: 6
                transformOrigin: Item.Center
                onClicked: { api.add_condition()}
            }

            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: "Add before:"
                font.pixelSize: 16
                font.italic: true
                color: "white"
            }

            RoundButton {
                id: roundButton1
                width: 30
                height: 30
                text: "("
                wheelEnabled: false
                leftPadding: 6
                transformOrigin: Item.Center
                spacing: 6
                onClicked:{ api.add_open_parentheses_before() }
            }

            RoundButton {
                id: roundButton2
                width: 30
                height: 30
                text: "~"
                wheelEnabled: false
                leftPadding: 6
                transformOrigin: Item.Center
                spacing: 6
                onClicked:{ api.add_not_before() }
            }

            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: "Add parentheses after:"
                font.pixelSize: 16
                font.italic: true
                color: "white"
            }

            RoundButton {
                id: roundButton3
                width: 30
                height: 30
                text: "("
                wheelEnabled: false
                leftPadding: 6
                transformOrigin: Item.Center
                spacing: 6
                onClicked:{ api.add_open_parentheses() }
            }

            RoundButton {
                id: roundButton4
                width: 30
                height: 30
                text: ")"
                wheelEnabled: false
                leftPadding: 6
                transformOrigin: Item.Center
                spacing: 6
                onClicked:{ api.add_close_parentheses() }
            }

            RoundButton {
                id: roundButton5
                width: 30
                height: 30
                text: "~"
                wheelEnabled: false
                leftPadding: 6
                transformOrigin: Item.Center
                spacing: 6
                onClicked:{ api.add_not() }
            }
        }

        Row {
            id: row2
            width: parent.width
            Layout.leftMargin: 10

            ListView {
                id: listView
                x: 0
                y: 0
                width: parent.width
                Layout.fillWidth: true
                height: contentHeight
                spacing: 10
                delegate: Loader{
                    width: parent.width
                    property int modelIndex: index
                    property QtObject modelData: model
                    sourceComponent: switch(NameRole){
                        case 'condition':
                            return condition
                            break;
                        case 'start_condition':
                            return start_condition
                            break;
                        case 'consequent':
                            return consequent
                            break;
                        case 'open_parentheses':
                            return open_parentheses
                            break;
                        case 'close_parentheses':
                            return close_parentheses
                            break;
                        case 'not':
                            return not
                            break;
                    }
                }
                model: rule_model
            }
        }
    }
    Component {
        id: consequent
        Row {
            id: row1
            width: parent.width
            spacing: 10

            Text {
                id: element1
                color: "#f7f7f7"
                text: qsTr("THEN")
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 20
            }

            ComboBox {
                id: cons
                width: 120
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.ConsRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.ConsRole
                onCurrentIndexChanged: {
                    modelData.ConsRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setConsRoleSel
                }
            }

            Text {
                id: element3
                color: "#ffffff"
                text: qsTr("IS")
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 20
            }

            ComboBox {
                id: cons_term
                width: 120
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.ConsTermRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.ConsTermRole
                onCurrentIndexChanged: {
                    modelData.TermRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setTermRoleSel
                }
            }
        }
    }
    Component {
        id: start_condition
        Row {
            id: row
            width: 480
            spacing: 10

            Text {
                id: element
                color: "#ffffff"
                text: qsTr("IF")
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 20
            }

            ComboBox {
                id: ante
                width: 120
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.AnteRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.AnteRole
                onCurrentIndexChanged: {
                    modelData.AnteRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setAnteRoleSel
                }
            }

            ComboBox {
                id: rel
                width: 80
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.ModifierRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.ModifierRole
                onCurrentIndexChanged: {
                    modelData.ModifierRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setModifierRoleSel
                }
            }

            ComboBox {
                id: ante_term
                width: 120
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.AnteTermRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.AnteTermRole
                onCurrentIndexChanged: {
                    modelData.TermRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setTermRoleSel
                }
            }
        }
    }

    Component {
        id: condition
        Row {
            spacing: 10
            ComboBox {
                width: 80
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.AndOrRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.AndOrRole
                onCurrentIndexChanged: {
                    modelData.AndOrRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setAndOrRoleSel
                }
            }

            ComboBox {
                width: 120
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.AnteRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.AnteRole
                onCurrentIndexChanged: {
                    modelData.AnteRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setAnteRoleSel
                }
            }

            ComboBox {
                width: 80
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.ModifierRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.ModifierRole
                onCurrentIndexChanged: {
                    modelData.ModifierRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setModifierRoleSel
                }
            }

            ComboBox {
                width: 120
                height: 25
                popup.width: 200
                popup.height: 40 *(modelData.AnteTermRole.length)
                anchors.verticalCenter: parent.verticalCenter
                model: modelData.AnteTermRole
                onCurrentIndexChanged: {
                    modelData.TermRoleSel = currentIndex
                }
                onModelChanged: {
                    currentIndex = modelData.setTermRoleSel
                }
            }

            ToolSeparator {
                rightPadding: 12
                leftPadding: 12
            }

            RoundButton {
                width: 30
                height: 30
                text: "-"
                wheelEnabled: false
                spacing: 6
                leftPadding: 6
                transformOrigin: Item.Center
                onClicked:{
                    rule_model.removeRow(modelIndex)
                }
            }
        }
    }
    Component{
        id: open_parentheses
        Row {
            RowLayout {
                width: parent.width- 50
                height: 35
                Canvas {
                    contextType: qsTr("")
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();

                        var centreX = width / 2;
                        var centreY = height *16.6;

                        ctx.beginPath();
                        ctx.fillStyle = "black";
                        ctx.arc(centreX, centreY, width, 0, Math.PI, true);
                        ctx.stroke()
                    }
                }
            }
            ToolSeparator {
                    rightPadding: 12
                    leftPadding: 12
            }

            RoundButton {
                width: 30
                height: 30
                text: "-"
                wheelEnabled: false
                spacing: 6
                leftPadding: 6
                transformOrigin: Item.Center
                onClicked:{
                    rule_model.removeRow(modelIndex)
                }
            }
        }
    }
    Component{
        id: close_parentheses
        Row {
            RowLayout {
                width: parent.width- 50
                height: 35
                Canvas {
                    contextType: qsTr("")
                    Layout.fillWidth: true;
                    Layout.fillHeight: true;
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();

                        var centreX = width / 2;
                        var centreY = -height*15.6;

                        ctx.beginPath();
                        ctx.fillStyle = "black";
                        ctx.arc(centreX, centreY, width, 0, Math.PI, false);
                        ctx.stroke()

                    }
                }

            }
            ToolSeparator {
                    rightPadding: 12
                    leftPadding: 12
            }

            RoundButton {
                width: 30
                height: 30
                text: "-"
                wheelEnabled: false
                spacing: 6
                leftPadding: 6
                transformOrigin: Item.Center
                onClicked:{
                    rule_model.removeRow(modelIndex)
                }
            }
        }
    }
    Component{
        id: not
        Row {
            RowLayout {
                width: parent.width- 50
                height: 35
                Text {
                    id: element
                    color: "#ffffff"
                    text: qsTr("NOT")
                    anchors.verticalCenter: parent.verticalCenter
                    font.pixelSize: 20
                }
            }
            ToolSeparator {
                    rightPadding: 12
                    leftPadding: 12
            }

            RoundButton {
                width: 30
                height: 30
                text: "-"
                wheelEnabled: false
                spacing: 6
                leftPadding: 6
                transformOrigin: Item.Center
                onClicked:{
                    rule_model.removeRow(modelIndex)
                }
            }
        }
    }
}




/*##^##
Designer {
    D{i:3;anchors_width:480}D{i:2;anchors_width:100}
}
##^##*/
