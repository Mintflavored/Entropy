
import QtQuick 2.15
import QtQuick.Controls 2.15

ScrollBar {
    id: control
    
    readonly property color colorNormal: Qt.rgba(88/255, 166/255, 255/255, 0.3)
    readonly property color colorHover: "#58a6ff"
    readonly property color colorPressed: "#388bfd"

    active: parent.activeFocus || parent.hovered || hovered || pressed
    orientation: Qt.Vertical
    policy: ScrollBar.AsNeeded
    
    contentItem: Rectangle {
        implicitWidth: 6
        implicitHeight: 100
        radius: 3
        color: control.pressed ? control.colorPressed : (control.hovered ? control.colorHover : control.colorNormal)
        opacity: control.active ? 1.0 : 0.0
        
        Behavior on opacity { NumberAnimation { duration: 200 } }
        Behavior on color { ColorAnimation { duration: 150 } }
    }
    
    background: Rectangle {
        implicitWidth: 6
        color: "transparent"
    }
}
