
import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    property string title: "TITLE"
    property string value: "0"
    property string subtitle: ""  // e.g. "packets/sec" or "last 60s"
    property color accentColor: "#ffffff"
    property bool isAlert: false
    
    Layout.preferredHeight: 130
    radius: 10
    color: Qt.rgba(22/255, 27/255, 34/255, 0.8)
    border.color: isAlert ? accentColor : Qt.rgba(48/255, 54/255, 61/255, 0.5)
    
    ColumnLayout {
        anchors.centerIn: parent
        spacing: 4
        
        Text {
            text: title
            color: "#8b949e"
            font.pixelSize: 11
            font.bold: true
            font.letterSpacing: 1
            Layout.alignment: Qt.AlignHCenter
        }
        
        Text {
            text: value
            color: accentColor
            font.pixelSize: 34
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }
        
        Text {
            text: subtitle
            color: "#6e7681"
            font.pixelSize: 11
            visible: subtitle !== ""
            Layout.alignment: Qt.AlignHCenter
        }
    }
    
    // Alert Animation
    SequentialAnimation on color {
        running: isAlert
        loops: Animation.Infinite
        ColorAnimation { to: Qt.rgba(accentColor.r, accentColor.g, accentColor.b, 0.2); duration: 800 }
        ColorAnimation { to: Qt.rgba(22/255, 27/255, 34/255, 0.8); duration: 800 }
    }
}
