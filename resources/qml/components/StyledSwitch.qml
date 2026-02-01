
import QtQuick 2.15
import QtQuick.Controls 2.15

Switch {
    id: control
    
    indicator: Rectangle {
        implicitWidth: 48
        implicitHeight: 26
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        radius: 13
        color: control.checked ? "#238636" : "#21262d"
        border.color: control.checked ? "#2ea043" : "#30363d"
        border.width: 1

        Rectangle {
            x: control.checked ? parent.width - width - 2 : 2
            y: 2
            width: 22
            height: 22
            radius: 11
            color: "white"
            
            Behavior on x {
                NumberAnimation { duration: 200; easing.type: Easing.OutBack }
            }
        }
        
        Behavior on color { ColorAnimation { duration: 200 } }
    }
}
