
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Item {
    id: root
    
    // Config
    property string activeView: "Dashboard"
    signal viewChanged(string view)
    
    // Logic
    readonly property int collapsedWidth: 64
    readonly property int expandedWidth: 220
    
    width: hoverHandler.hovered ? expandedWidth : collapsedWidth
    height: parent.height * 0.8
    anchors.left: parent.left
    anchors.leftMargin: 20
    anchors.verticalCenter: parent.verticalCenter
    z: 100

    // MODERN HOVER DETECTION (Doesn't block children)
    HoverHandler {
        id: hoverHandler
    }

    Rectangle {
        id: dock
        anchors.fill: parent
        color: hoverHandler.hovered ? Qt.rgba(22/255, 27/255, 34/255, 0.92) : Qt.rgba(22/255, 27/255, 34/255, 0.65)
        radius: 16
        border.color: Qt.rgba(255, 255, 255, 0.15)
        border.width: 1
        clip: true 
        
        Behavior on color { ColorAnimation { duration: 250 } }

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 20
            
            // LOGO
            Item {
                width: parent.width
                height: 50
                Image {
                    anchors.centerIn: parent
                    source: "../../assets/logo.png"
                    width: 40
                    height: 40
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }
            
            // NAV ITEMS
            Repeater {
                model: [
                    { id: "Dashboard", icon: "▤", label: mainVM.trans.nav_dashboard },
                    { id: "AI", icon: "✧", label: mainVM.trans.nav_ai },
                    { id: "Security", icon: "⬢", label: mainVM.trans.nav_security },
                    { id: "Settings", icon: "⚙", label: mainVM.trans.nav_settings }
                ]
                
                delegate: Item {
                    width: dock.width - 24
                    height: 44
                    
                    Rectangle {
                        anchors.fill: parent
                        radius: 12
                        color: activeView === modelData.id ? "#388bfd" : 
                               (itemHandler.hovered ? Qt.rgba(255, 255, 255, 0.08) : "transparent")
                        
                        Behavior on color { ColorAnimation { duration: 150 } }

                        Row {
                            anchors.fill: parent
                            spacing: 15
                            
                            Item {
                                width: 40
                                height: 44
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    font.pixelSize: 22
                                    color: "white"
                                    // Ensure standard geometry for symbols
                                    font.family: "Segoe UI Symbol"
                                    opacity: activeView === modelData.id ? 1.0 : 0.7
                                }
                            }
                            
                            Text {
                                text: modelData.label
                                color: "white"
                                height: parent.height
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 14
                                opacity: root.width > 150 ? 1.0 : 0.0
                                visible: opacity > 0.01
                                font.bold: activeView === modelData.id
                                Behavior on opacity { NumberAnimation { duration: 150 } }
                            }
                        }
                        
                        // Handler for item-specific hover and click
                        HoverHandler { id: itemHandler }
                        TapHandler {
                            onTapped: root.viewChanged(modelData.id)
                        }
                    }
                }
            }
        }
    }
    
    Behavior on width {
        NumberAnimation { duration: 350; easing.type: Easing.OutQuart }
    }
}
