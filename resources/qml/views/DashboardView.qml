import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import "../components"

ScrollView {
    id: dashboard
    clip: true
    contentHeight: mainLayout.implicitHeight
    
    // Disable horizontal scroll
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    
    // Custom Vertical ScrollBar
    ScrollBar.vertical: StyledScrollBar {
        parent: dashboard
        x: dashboard.width - width - 4
        y: dashboard.topPadding
        height: dashboard.availableHeight
    }

    ColumnLayout {
        id: mainLayout
        width: dashboard.availableWidth - 40
        anchors.left: parent.left
        anchors.leftMargin: 20
        spacing: 30
        anchors.topMargin: 20
        anchors.bottomMargin: 20
        
        // --- HEADER ---
        RowLayout {
            spacing: 15
            Image {
                source: "../assets/logo.png"
                width: 36
                height: 36
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
            Text {
                text: mainVM.trans.title_dashboard
                color: "#e6edf3"
                font.pixelSize: 28
                font.bold: true
            }
        }
        
        // --- STATS CARDS ---
        RowLayout {
            spacing: 20
            Layout.fillWidth: true
            
            StatsCard { 
                title: mainVM.trans.lbl_cpu
                value: mainVM.cpu + "%"
                subtitle: mainVM.trans.sub_current_load
                accentColor: "#58a6ff"
                Layout.fillWidth: true 
            }
            StatsCard { 
                title: mainVM.trans.lbl_ram
                value: mainVM.ram + "%"
                subtitle: mainVM.trans.sub_current_usage
                accentColor: "#238636"
                Layout.fillWidth: true 
            }
            StatsCard { 
                title: mainVM.trans.lbl_pps
                value: mainVM.pps
                subtitle: mainVM.trans.sub_packets_sec
                accentColor: "#e3b341"
                Layout.fillWidth: true 
            }
            StatsCard { 
                title: mainVM.trans.lbl_risk
                value: mainVM.aiRiskScore + "%"
                subtitle: mainVM.trans.sub_eaii_score
                accentColor: mainVM.aiRiskScore > 40 ? "#ff4444" : "#238636"
                isAlert: mainVM.aiRiskScore > 40
                Layout.fillWidth: true 
            }
        }
        
        // --- GRAPHS SECTION 1 (CPU & RAM) ---
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 220
            spacing: 20
            
            // CPU Chart
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 8
                    
                    // Header with current value
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.chart_cpu_history; color: "#8b949e"; font.pixelSize: 12; font.bold: true }
                        Text { 
                            text: mainVM.cpu + "%"
                            color: "#58a6ff"
                            font.pixelSize: 20
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        Text { text: mainVM.trans.lbl_time_60s; color: "#6e7681"; font.pixelSize: 10 }
                    }
                    
                    // Graph
                    LiveGraph {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        dataPoints: mainVM.cpuHistory
                        lineColor: "#58a6ff"
                        fillColor: Qt.rgba(88/255, 166/255, 255/255, 0.15)
                    }
                    
                    // Min/Max stats
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "min: " + (mainVM.cpuHistory.length > 0 ? Math.min(...mainVM.cpuHistory).toFixed(0) : "—") + "%"; color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "avg: " + (mainVM.cpuHistory.length > 0 ? (mainVM.cpuHistory.reduce((a,b) => a+b, 0) / mainVM.cpuHistory.length).toFixed(0) : "—") + "%"; color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "max: " + (mainVM.cpuHistory.length > 0 ? Math.max(...mainVM.cpuHistory).toFixed(0) : "—") + "%"; color: "#6e7681"; font.pixelSize: 10 }
                    }
                }
            }
            
            // RAM Chart
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 8
                    
                    // Header with current value
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.chart_ram_history; color: "#8b949e"; font.pixelSize: 12; font.bold: true }
                        Text { 
                            text: mainVM.ram + "%"
                            color: "#238636"
                            font.pixelSize: 20
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        Text { text: mainVM.trans.lbl_time_60s; color: "#6e7681"; font.pixelSize: 10 }
                    }
                    
                    // Graph
                    LiveGraph {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        dataPoints: mainVM.ramHistory
                        lineColor: "#238636"
                        fillColor: Qt.rgba(35/255, 134/255, 54/255, 0.15)
                    }
                    
                    // Min/Max stats
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "min: " + (mainVM.ramHistory.length > 0 ? Math.min(...mainVM.ramHistory).toFixed(0) : "—") + "%"; color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "avg: " + (mainVM.ramHistory.length > 0 ? (mainVM.ramHistory.reduce((a,b) => a+b, 0) / mainVM.ramHistory.length).toFixed(0) : "—") + "%"; color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "max: " + (mainVM.ramHistory.length > 0 ? Math.max(...mainVM.ramHistory).toFixed(0) : "—") + "%"; color: "#6e7681"; font.pixelSize: 10 }
                    }
                }
            }
        }
        
        // --- GRAPHS SECTION 2 (PPS & JITTER) ---
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 220
            spacing: 20
            
            // PPS Chart
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 8
                    
                    // Header with current value
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.chart_pps_history; color: "#8b949e"; font.pixelSize: 12; font.bold: true }
                        Text { 
                            text: mainVM.pps
                            color: "#f0883e"
                            font.pixelSize: 20
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        Text { text: mainVM.trans.lbl_time_60s; color: "#6e7681"; font.pixelSize: 10 }
                    }
                    
                    // Graph
                    LiveGraph {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        dataPoints: mainVM.ppsHistory
                        lineColor: "#f0883e"
                        fillColor: Qt.rgba(240/255, 136/255, 62/255, 0.15)
                        maxValue: 2000
                    }
                    
                    // Min/Max stats
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "min: " + (mainVM.ppsHistory.length > 0 ? Math.min(...mainVM.ppsHistory).toFixed(0) : "—"); color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "avg: " + (mainVM.ppsHistory.length > 0 ? (mainVM.ppsHistory.reduce((a,b) => a+b, 0) / mainVM.ppsHistory.length).toFixed(0) : "—"); color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "max: " + (mainVM.ppsHistory.length > 0 ? Math.max(...mainVM.ppsHistory).toFixed(0) : "—"); color: "#6e7681"; font.pixelSize: 10 }
                    }
                }
            }

            // Jitter Chart
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 8
                    
                    // Header with current value
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.chart_jitter_history; color: "#8b949e"; font.pixelSize: 12; font.bold: true }
                        Text { 
                            text: mainVM.jitter + "ms"
                            color: "#a371f7"
                            font.pixelSize: 20
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        Text { text: mainVM.trans.lbl_time_60s; color: "#6e7681"; font.pixelSize: 10 }
                    }
                    
                    // Graph
                    LiveGraph {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        dataPoints: mainVM.jitterHistory
                        lineColor: "#a371f7"
                        fillColor: Qt.rgba(163/255, 113/255, 247/255, 0.15)
                        maxValue: 50
                    }
                    
                    // Min/Max stats
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "min: " + (mainVM.jitterHistory.length > 0 ? Math.min(...mainVM.jitterHistory).toFixed(1) : "—") + "ms"; color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "avg: " + (mainVM.jitterHistory.length > 0 ? (mainVM.jitterHistory.reduce((a,b) => a+b, 0) / mainVM.jitterHistory.length).toFixed(1) : "—") + "ms"; color: "#6e7681"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "max: " + (mainVM.jitterHistory.length > 0 ? Math.max(...mainVM.jitterHistory).toFixed(1) : "—") + "ms"; color: "#6e7681"; font.pixelSize: 10 }
                    }
                }
            }
        }

        // --- USER STATISTICS SECTION ---
        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 400
            spacing: 12
            
            Text {
                text: mainVM.trans.lbl_users
                color: "#e6edf3"
                font.pixelSize: 20
                font.bold: true
            }
            
            UserTable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                modelData: mainVM.usersData
            }
        }
    }
}
