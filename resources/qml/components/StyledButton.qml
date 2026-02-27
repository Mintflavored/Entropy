
import QtQuick 2.15
import QtQuick.Controls 2.15

Button {
    id: control
    
    property color colorDefault: "#238636"
    property color colorHover: "#2ea043"
    property color colorPressed: "#26933d"
    property color textColor: "white"
    
    contentItem: Text {
        text: control.text
        font: control.font
        opacity: enabled ? 1.0 : 0.3
        color: control.textColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 100
        implicitHeight: 40
        opacity: enabled ? 1 : 0.3
        color: control.down ? control.colorPressed : (control.hovered ? control.colorHover : control.colorDefault)
        radius: 8
        border.color: "transparent"
        
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
