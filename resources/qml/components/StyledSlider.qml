
import QtQuick 2.15
import QtQuick.Controls 2.15

Slider {
    id: control
    
    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: 200
        implicitHeight: 4
        width: control.availableWidth
        height: implicitHeight
        radius: 2
        color: "#21262d"

        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            color: "#58a6ff"
            radius: 2
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: 16
        implicitHeight: 16
        radius: 8
        color: control.pressed ? "#58a6ff" : (control.hovered ? "white" : "#e6edf3")
        border.color: "#388bfd"
        border.width: control.pressed ? 4 : 0
        
        Behavior on border.width { NumberAnimation { duration: 100 } }
        Behavior on color { ColorAnimation { duration: 100 } }
    }
}
