
import QtQuick 2.15
import QtQuick.Controls 2.15

ComboBox {
    id: control
    
    delegate: ItemDelegate {
        width: control.width
        contentItem: Text {
            text: modelData
            color: "white"
            font: control.font
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: hovered ? "#1f6feb" : "#161b22"
        }
        highlighted: control.highlightedIndex === index
    }

    indicator: Canvas {
        id: canvas
        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        width: 12
        height: 8
        contextType: "2d"

        onPaint: {
            context.reset();
            context.moveTo(0, 0);
            context.lineTo(width, 0);
            context.lineTo(width / 2, height);
            context.closePath();
            context.fillStyle = control.pressed ? "#58a6ff" : "white";
            context.fill();
        }

        Connections {
            target: control
            function onPressedChanged() { canvas.requestPaint(); }
        }
    }

    contentItem: Text {
        leftPadding: 12
        rightPadding: control.indicator.width + control.spacing
        text: control.displayText
        font: control.font
        color: "white"
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 120
        implicitHeight: 40
        color: "#0d1117"
        border.color: control.activeFocus ? "#388bfd" : "#30363d"
        border.width: control.visualFocus ? 2 : 1
        radius: 8
    }

    popup: Popup {
        y: control.height + 4
        width: control.width
        implicitHeight: contentItem.implicitHeight
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: "#161b22"
            border.color: "#30363d"
            radius: 8
        }
    }
}
