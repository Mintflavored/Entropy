
import QtQuick 2.15
import QtQuick.Controls 2.15

TextField {
    id: control
    
    color: "white"
    font.pixelSize: 14
    placeholderTextColor: "#8b949e"
    
    background: Rectangle {
        implicitWidth: 200
        implicitHeight: 40
        color: "#0d1117"
        radius: 8
        border.color: control.activeFocus ? "#388bfd" : "#30363d"
        border.width: control.activeFocus ? 2 : 1
        
        Behavior on border.color { ColorAnimation { duration: 150 } }
        Behavior on border.width { NumberAnimation { duration: 100 } }
    }
}
