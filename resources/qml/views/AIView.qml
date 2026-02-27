
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import "../components"

ScrollView {
    id: aiView
    clip: true
    contentHeight: mainLayout.implicitHeight
    
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical: StyledScrollBar {
        parent: aiView
        x: aiView.width - width - 4
        y: aiView.topPadding
        height: aiView.availableHeight
    }

    ColumnLayout {
        id: mainLayout
        width: aiView.availableWidth - 40
        anchors.left: parent.left
        anchors.leftMargin: 20
        spacing: 20
        anchors.topMargin: 20
        anchors.bottomMargin: 20
        
        // Header
        Text {
            text: mainVM.trans.title_ai_intelligence
            color: "#e6edf3"
            font.pixelSize: 28
            font.bold: true
        }
        
        // 1. EAII STATUS CARD (Background)
        Text { text: mainVM.trans.sec_eaii_status; color: "#8b949e"; font.pixelSize: 14; font.bold: true }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            color: Qt.rgba(22/255, 27/255, 34/255, 0.8)
            radius: 16
            border.color: mainVM.isEaiiAnalyzing ? "#58a6ff" : (mainVM.aiRiskScore > 40 ? "#ff4444" : "#30363d")
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 25
                
                // Risk Meter
                Rectangle {
                    width: 70; height: 70
                    radius: 35
                    color: "transparent"
                    border.width: 4
                    border.color: mainVM.aiRiskScore > 40 ? "#ff4444" : "#238636"
                    
                    Text {
                        anchors.centerIn: parent
                        text: mainVM.isEaiiAnalyzing ? "..." : mainVM.aiRiskScore + "%"
                        color: "white"
                        font.pixelSize: 18
                        font.bold: true
                    }
                }
                
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: mainVM.isEaiiAnalyzing ? mainVM.trans.ai_status_analyzing : mainVM.trans.ai_status_idle
                        color: "#e6edf3"
                        font.pixelSize: 16
                        font.bold: true
                    }
                    Text {
                        text: mainVM.aiExplanation
                        color: "#8b949e"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 4
                        elide: Text.ElideRight
                    }
                }
            }
        }
        
        // 2. DEEP DIAGNOSTIC CARD (Interactive)
        Text { text: mainVM.trans.sec_deep_diagnostic; color: "#8b949e"; font.pixelSize: 14; font.bold: true }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 350
            color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
            radius: 12
            border.color: mainVM.isInteractiveAnalyzing ? "#388bfd" : "#30363d"
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                
                Flickable {
                    id: reportFlick
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentHeight: diagnosticText.height
                    clip: true
                    
                    Text {
                        id: diagnosticText
                        width: reportFlick.width
                        text: mainVM.isInteractiveAnalyzing ? mainVM.trans.ai_interactive_analyzing : mainVM.aiInteractiveResult
                        color: mainVM.isInteractiveAnalyzing ? "#58a6ff" : "#c9d1d9"
                        font.pixelSize: 15
                        wrapMode: Text.WordWrap
                        lineHeight: 1.5
                        
                        // Micro-animation for thinking state
                        opacity: mainVM.isInteractiveAnalyzing ? 0.7 : 1.0
                        Behavior on opacity { NumberAnimation { duration: 500 } }
                    }
                    
                    ScrollBar.vertical: StyledScrollBar {}
                }
            }
        }
        
        StyledButton {
            text: mainVM.trans.btn_ai_scan
            Layout.alignment: Qt.AlignRight
            enabled: !mainVM.isInteractiveAnalyzing
            colorDefault: "#388bfd"
            onClicked: {
                mainVM.startManualScan()
            }
        }
    }
}
