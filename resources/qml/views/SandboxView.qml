import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import "../components"

ScrollView {
    id: sandboxView
    contentHeight: mainLayout.implicitHeight
    clip: true
    
    // Null-safe properties
    readonly property bool vmReady: typeof sandboxVM !== "undefined" && sandboxVM !== null
    readonly property bool isRunning: vmReady ? sandboxVM.isRunning : false
    readonly property real bestScore: vmReady ? sandboxVM.bestScore : 0
    readonly property real baselineScore: vmReady ? sandboxVM.baselineScore : 0
    readonly property real improvement: vmReady ? sandboxVM.improvement : 0
    readonly property real progressPercent: vmReady ? sandboxVM.progressPercent : 0
    readonly property int currentExp: vmReady ? sandboxVM.currentExperiment : 0
    readonly property int totalExp: vmReady ? sandboxVM.totalExperiments : 0
    readonly property string statusText: vmReady ? sandboxVM.statusText : "Загрузка..."
    readonly property string errorText: vmReady ? sandboxVM.error : ""
    readonly property string configJson: vmReady ? sandboxVM.bestConfigJson : "{}"
    
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical: StyledScrollBar {
        parent: sandboxView
        x: sandboxView.width - width - 4
        y: sandboxView.topPadding
        height: sandboxView.availableHeight
    }

    ColumnLayout {
        id: mainLayout
        width: sandboxView.availableWidth - 80
        anchors.left: parent.left
        anchors.leftMargin: 40
        spacing: 25
        anchors.topMargin: 20
        anchors.bottomMargin: 40
        
        // Header
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: mainVM.trans.title_sandbox_view
                color: "#e6edf3"
                font.pixelSize: 28
                font.bold: true
            }
            
            Item { Layout.fillWidth: true }
            
            // Status indicator
            Rectangle {
                width: 12; height: 12
                radius: 6
                color: sandboxView.isRunning ? "#f0883e" : 
                       sandboxView.bestScore > 0 ? "#3fb950" : "#8b949e"
                
                SequentialAnimation on opacity {
                    running: sandboxView.isRunning
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.3; duration: 500 }
                    NumberAnimation { to: 1.0; duration: 500 }
                }
            }
            
            Text {
                text: sandboxView.statusText
                color: "#8b949e"
                font.pixelSize: 14
            }
        }
        
        // Description
        Text {
            text: mainVM.trans.eais_desc
            color: "#8b949e"
            font.pixelSize: 13
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }

        // Progress Section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: progressColumn.implicitHeight + 50
            color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
            radius: 12
            border.color: sandboxView.isRunning ? "#f0883e" : "#30363d"
            
            ColumnLayout {
                id: progressColumn
                anchors.fill: parent
                anchors.margins: 25
                spacing: 15
                
                RowLayout {
                    Text { 
                        text: mainVM.trans.eais_progress 
                        color: "white" 
                        font.bold: true 
                        font.pixelSize: 16 
                    }
                    Item { Layout.fillWidth: true }
                    Text { 
                        text: sandboxView.currentExp + " / " + sandboxView.totalExp
                        color: "#58a6ff" 
                        font.bold: true 
                    }
                }
                
                // Progress bar
                Rectangle {
                    Layout.fillWidth: true
                    height: 8
                    radius: 4
                    color: "#21262d"
                    
                    Rectangle {
                        width: parent.width * (sandboxView.progressPercent / 100)
                        height: parent.height
                        radius: 4
                        color: "#238636"
                        
                        Behavior on width { NumberAnimation { duration: 300 } }
                    }
                }
                
                // Control buttons
                RowLayout {
                    spacing: 15
                    
                    StyledButton {
                        text: sandboxView.isRunning ? mainVM.trans.btn_stop : mainVM.trans.btn_start_opt
                        Layout.preferredWidth: 220
                        Layout.preferredHeight: 40
                        enabled: sandboxView.vmReady
                        
                        onClicked: {
                            if (sandboxView.vmReady) {
                                if (sandboxView.isRunning) {
                                    sandboxVM.stopOptimization()
                                } else {
                                    sandboxVM.startOptimization()
                                }
                            }
                        }
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    Text {
                        text: sandboxView.errorText
                        color: "#f85149"
                        font.pixelSize: 12
                        visible: sandboxView.errorText !== ""
                    }
                }
            }
        }

        // Results Section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: resultsColumn.implicitHeight + 50
            color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
            radius: 12
            border.color: sandboxView.improvement > 0 ? "#238636" : "#30363d"
            visible: sandboxView.bestScore > 0
            
            ColumnLayout {
                id: resultsColumn
                anchors.fill: parent
                anchors.margins: 25
                spacing: 20
                
                Text { 
                    text: mainVM.trans.title_best_result 
                    color: "white" 
                    font.bold: true 
                    font.pixelSize: 16 
                }
                
                // Score comparison
                RowLayout {
                    spacing: 30
                    
                    ColumnLayout {
                        Text { text: mainVM.trans.lbl_baseline; color: "#8b949e"; font.pixelSize: 12 }
                        Text { 
                            text: sandboxView.baselineScore.toFixed(1) 
                            color: "#8b949e" 
                            font.pixelSize: 28 
                            font.bold: true 
                        }
                    }
                    
                    Text { 
                        text: "→" 
                        color: "#3fb950" 
                        font.pixelSize: 24 
                    }
                    
                    ColumnLayout {
                        Text { text: mainVM.trans.lbl_optimized; color: "#8b949e"; font.pixelSize: 12 }
                        Text { 
                            text: sandboxView.bestScore.toFixed(1) 
                            color: "#3fb950" 
                            font.pixelSize: 28 
                            font.bold: true 
                        }
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    // Improvement badge
                    Rectangle {
                        width: 120
                        height: 50
                        radius: 8
                        color: sandboxView.improvement > 0 ? Qt.rgba(35/255, 134/255, 54/255, 0.3) : Qt.rgba(255,255,255,0.1)
                        border.color: sandboxView.improvement > 0 ? "#3fb950" : "#8b949e"
                        
                        Text {
                            anchors.centerIn: parent
                            text: (sandboxView.improvement > 0 ? "+" : "") + sandboxView.improvement.toFixed(1) + "%"
                            color: sandboxView.improvement > 0 ? "#3fb950" : "#8b949e"
                            font.pixelSize: 20
                            font.bold: true
                        }
                    }
                }
                
                Rectangle { Layout.fillWidth: true; height: 1; color: "#30363d" }
                
                // Best config
                Text { text: mainVM.trans.lbl_rec_config; color: "#8b949e"; font.pixelSize: 13 }
                
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: configText.implicitHeight + 20
                    color: "#0d1117"
                    radius: 6
                    border.color: "#30363d"
                    
                    Text {
                        id: configText
                        anchors.fill: parent
                        anchors.margins: 10
                        text: sandboxView.configJson
                        color: "#7ee787"
                        font.family: "Consolas"
                        font.pixelSize: 12
                        wrapMode: Text.Wrap
                    }
                }
                
                // Apply button
                RowLayout {
                    Item { Layout.fillWidth: true }
                    
                    StyledButton {
                        text: mainVM.trans.btn_apply_prod
                        Layout.preferredWidth: 220
                        Layout.preferredHeight: 40
                        enabled: sandboxView.improvement > 0 && !sandboxView.isRunning && sandboxView.vmReady
                        
                        onClicked: {
                            applyConfirmDialog.open()
                        }
                    }
                }
            }
        }
        
        // Info section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: infoColumn.implicitHeight + 40
            color: Qt.rgba(22/255, 27/255, 34/255, 0.3)
            radius: 12
            border.color: "#30363d"
            
            ColumnLayout {
                id: infoColumn
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10
                
                Text { 
                    text: mainVM.trans.title_how_it_works 
                    color: "#8b949e" 
                    font.bold: true 
                    font.pixelSize: 14 
                }
                
                Text {
                    text: mainVM.trans.desc_how_it_works
                    color: "#6e7681"
                    font.pixelSize: 12
                    lineHeight: 1.4
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
        }
    }
    
    // Confirmation dialog
    Dialog {
        id: applyConfirmDialog
        title: mainVM.trans.dialog_apply_title
        modal: true
        x: (sandboxView.width - width) / 2
        y: (sandboxView.height - height) / 2
        width: 400
        
        contentItem: Text {
            text: mainVM.trans.dialog_apply_desc
            color: "#e6edf3"
            font.pixelSize: 14
        }
        
        standardButtons: Dialog.Ok | Dialog.Cancel
        
        onAccepted: {
            if (sandboxView.vmReady) {
                sandboxVM.applyBestConfig()
            }
        }
        
        background: Rectangle {
            color: "#161b22"
            radius: 12
            border.color: "#30363d"
        }
    }
}
