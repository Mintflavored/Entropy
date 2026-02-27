import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Button {
    id: control
    property string symbol: ""
    property string label: ""
    property bool isActive: false
    
    // We don't use 'text' property directly to avoid confusion, or we bind it
    
    background: Rectangle {
        color: isActive ? Qt.rgba(88/255, 166/255, 255/255, 0.1) : "transparent"
        
        // Active Indicator Line
        Rectangle {
            width: 3
            height: parent.height
            color: isActive ? "#58a6ff" : "transparent"
            anchors.left: parent.left
        }
        
        // Hover effect
        Rectangle {
            anchors.fill: parent
            color: control.hovered && !isActive ? Qt.rgba(255, 255, 255, 0.05) : "transparent"
        }
    }
    
    contentItem: Text {
        text: control.symbol + "  " + control.label
        color: isActive ? "#e6edf3" : "#8b949e"
        font.pixelSize: 14
        font.bold: isActive
        verticalAlignment: Text.AlignVCenter
        leftPadding: 20
    }
    
    Layout.fillWidth: true
    Layout.preferredHeight: 50
    // Disable default text handling to avoid conflicts if needed, but overriding contentItem handles display.
}
