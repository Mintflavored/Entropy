
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import "../components"

ScrollView {
    id: securityView
    clip: true
    contentHeight: mainLayout.implicitHeight
    
    // Custom ScrollBar style
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical: StyledScrollBar {
        parent: securityView
        x: securityView.width - width - 4
        y: securityView.topPadding
        height: securityView.availableHeight
    }

    ColumnLayout {
        id: mainLayout
        width: securityView.availableWidth - 40
        anchors.left: parent.left
        anchors.leftMargin: 20
        spacing: 30
        anchors.topMargin: 20
        anchors.bottomMargin: 20
        
        // --- HEADER ---
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: mainVM.trans.title_security
                color: "#e6edf3"
                font.pixelSize: 28
                font.bold: true
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                width: 120; height: 32; radius: 16
                color: Qt.rgba(255, 255, 255, 0.05)
                border.color: mainVM.riskColor
                Text {
                    anchors.centerIn: parent
                    text: mainVM.riskLabel
                    color: mainVM.riskColor
                    font.bold: true; font.pixelSize: 12
                }
            }
        }
        
        // --- MAIN RISK RADAR ---
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 350
            color: Qt.rgba(22/255, 27/255, 34/255, 0.8)
            radius: 20
            border.color: "#30363d"
            
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20
                
                // Big Gauge Placeholder (Using text/circle for now)
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 200; height: 200; radius: 100
                    color: "transparent"
                    border.width: 15
                    border.color: mainVM.riskColor
                    opacity: 0.8
                    
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 5
                        
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: mainVM.riskScore + "%"
                            color: "white"
                            font.pixelSize: 48
                            font.bold: true
                        }
                        
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: mainVM.trans.lbl_entropy_index
                                color: "#8b949e"
                                font.pixelSize: 10
                                font.letterSpacing: 2
                                font.bold: true
                            }
                    }
                }
                
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: mainVM.trans.lbl_threat_level
                    color: "#8b949e"
                    font.pixelSize: 16
                }
            }
        }
        
        // --- SECURITY LOGS (PROBES) ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 15
            
            Text {
                text: mainVM.trans.title_invasion_logic
                color: "#e6edf3"
                font.pixelSize: 20
                font.bold: true
            }
            
            ListView {
                Layout.fillWidth: true
                Layout.preferredHeight: mainVM.probesData.length > 0 ? 300 : 100
                model: mainVM.probesData
                spacing: 12
                interactive: false // Inside ScrollView
                
                delegate: Rectangle {
                    width: ListView.view.width
                    height: 60
                    color: Qt.rgba(255, 68/255, 68/255, 0.05)
                    radius: 12
                    border.color: Qt.rgba(255, 68/255, 68/255, 0.2)
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        
                        Text {
                            text: mainVM.trans.log_bruteforce + modelData.ip
                            color: "#ff4444"
                            font.bold: true; font.pixelSize: 14
                            Layout.fillWidth: true
                        }
                        
                        Text {
                            text: modelData.attempts + " " + mainVM.trans.lbl_attempts
                            color: "#8b949e"
                        }
                        
                        Text {
                            text: modelData.seen
                            color: "#8b949e"
                            font.italic: true
                        }
                    }
                }
                
                Text {
                    anchors.centerIn: parent
                    visible: mainVM.probesData.length === 0
                    text: mainVM.trans.log_clean
                    color: "#238636"
                    font.pixelSize: 14
                }
            }
        }
    }
}
