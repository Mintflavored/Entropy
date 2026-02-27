
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Item {
    id: root
    
    property var modelData: []
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 12
        
        // --- TABLE HEADER ---
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: "#161b22"
            radius: 8
            border.color: "#30363d"
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10
                
                Text { text: mainVM.trans.tbl_user_id; color: "#8b949e"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
                Text { text: mainVM.trans.tbl_ip_address; color: "#8b949e"; font.pixelSize: 12; font.bold: true; Layout.preferredWidth: 120 }
                Text { text: mainVM.trans.tbl_traffic_total; color: "#8b949e"; font.pixelSize: 12; font.bold: true; Layout.preferredWidth: 100 }
            }
        }
        
        // --- USER LIST ---
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.modelData
            spacing: 8
            clip: true
            
            delegate: Rectangle {
                width: ListView.view.width
                height: 50
                color: itemHover.hovered ? Qt.rgba(255, 255, 255, 0.05) : Qt.rgba(255, 255, 255, 0.02)
                radius: 10
                border.color: itemHover.hovered ? "#388bfd" : "#30363d"
                border.width: itemHover.hovered ? 1.5 : 1
                
                Behavior on border.color { ColorAnimation { duration: 150 } }
                Behavior on color { ColorAnimation { duration: 150 } }

                HoverHandler { id: itemHover }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 10
                    
                    Text {
                        text: modelData.user
                        color: "white"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    
                    Text {
                        text: modelData.ip
                        color: "#8b949e"
                        font.pixelSize: 13
                        Layout.preferredWidth: 120
                    }
                    
                    Rectangle {
                        Layout.preferredWidth: 100
                        height: 28
                        radius: 6
                        color: Qt.rgba(56/255, 139/255, 253/255, 0.1)
                        border.color: Qt.rgba(56/255, 139/255, 253/255, 0.3)
                        
                        Text {
                            anchors.centerIn: parent
                            text: modelData.traffic
                            color: "#58a6ff"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }
            }
            
            ScrollBar.vertical: StyledScrollBar { }
        }
    }
}
