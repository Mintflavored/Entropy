
import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import "../components"

ScrollView {
    id: settingsView
    contentHeight: mainLayout.implicitHeight
    clip: true
    
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical: StyledScrollBar {
        parent: settingsView
        x: settingsView.width - width - 4
        y: settingsView.topPadding
        height: settingsView.availableHeight
    }

    ColumnLayout {
        id: mainLayout
        width: settingsView.availableWidth - 80
        anchors.left: parent.left
        anchors.leftMargin: 40
        spacing: 30
        anchors.topMargin: 20
        anchors.bottomMargin: 40
        
        Text {
            text: mainVM.trans.title_settings
            color: "#e6edf3"
            font.pixelSize: 28
            font.bold: true
        }

        // --- GENERAL SETTINGS ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 15
            
            Text { text: mainVM.trans.sec_general; color: "#8b949e"; font.pixelSize: 14; font.bold: true }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    Text { text: mainVM.trans.lbl_lang_selection; color: "white"; font.bold: true; font.pixelSize: 16 }
                    Item { Layout.fillWidth: true }
                    StyledComboBox {
                        id: langCombo
                        model: ["ru", "en"]
                        currentIndex: mainVM.language === "ru" ? 0 : 1
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 120
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    RowLayout {
                        Text { text: mainVM.trans.lbl_sync_interval; color: "white"; font.bold: true; font.pixelSize: 16 }
                        Item { Layout.fillWidth: true }
                        Text { text: (syncSlider.value / 1000).toFixed(1) + " s"; color: "#58a6ff"; font.bold: true }
                    }
                    StyledSlider {
                        id: syncSlider
                        Layout.fillWidth: true
                        from: 2000; to: 30000; stepSize: 1000
                        value: mainVM.syncInterval
                    }
                }
            }
        }
        
        // --- INTERACTIVE AI (ANALYSIS TOOL) ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 15
            
            Text { text: mainVM.trans.sec_interactive_ai; color: "#8b949e"; font.pixelSize: 14; font.bold: true }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 380
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 25
                    spacing: 20
                    
                    // Provider
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.lbl_ai_provider; color: "white"; font.pixelSize: 14 }
                        StyledComboBox {
                            id: aiProviderCombo
                            Layout.fillWidth: true
                            model: ["openai_compatible", "gemini", "anthropic", "local_ollama"]
                            currentIndex: model.indexOf(mainVM.aiProvider) !== -1 ? model.indexOf(mainVM.aiProvider) : 0
                        }
                    }
                    
                    // Model & Base URL
                    RowLayout {
                        spacing: 20
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: mainVM.trans.lbl_model_name; color: "white"; font.pixelSize: 14 }
                            StyledTextField {
                                id: aiModelField
                                Layout.fillWidth: true
                                text: mainVM.aiModel
                                placeholderText: "gpt-4o"
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: mainVM.trans.lbl_base_url; color: "white"; font.pixelSize: 14 }
                            StyledTextField {
                                id: aiUrlField
                                Layout.fillWidth: true
                                text: mainVM.aiBaseUrl
                                placeholderText: "https://api..."
                            }
                        }
                    }
                    
                    // API Key
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.lbl_api_key; color: "white"; font.pixelSize: 14 }
                        StyledTextField {
                            id: aiKeyField
                            Layout.fillWidth: true
                            text: mainVM.aiApiKey
                            echoMode: TextInput.Password
                            placeholderText: "Enter your secret key"
                        }
                    }
                }
            }
        }

        // --- EAII (SMART SECURITY) ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 15
            
            Text { text: mainVM.trans.sec_background_ai; color: "#8b949e"; font.pixelSize: 14; font.bold: true }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 480
                color: Qt.rgba(22/255, 27/255, 34/255, 0.5)
                radius: 12
                border.color: "#30363d"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 25
                    spacing: 20
                    
                    RowLayout {
                            ColumnLayout {
                                Text { text: mainVM.trans.lbl_enable_ai; color: "white"; font.bold: true; font.pixelSize: 16 }
                                Text { text: mainVM.trans.lbl_ai_desc; color: "#8b949e"; font.pixelSize: 13 }
                            }
                        Item { Layout.fillWidth: true }
                        StyledSwitch { id: eaiiSwitch; checked: mainVM.eaiiEnabled }
                    }
                    
                    // EAII Interval Slider
                    RowLayout {
                        Text { text: mainVM.trans.lbl_eaii_interval; color: "white"; font.pixelSize: 14 }
                        Item { Layout.fillWidth: true }
                        Text { text: eaiiIntervalSlider.value + " " + mainVM.trans.lbl_minutes; color: "#58a6ff"; font.bold: true }
                    }
                    StyledSlider {
                        id: eaiiIntervalSlider
                        Layout.fillWidth: true
                        from: 1; to: 30; stepSize: 1
                        value: mainVM.eaiiInterval
                    }
                    
                    Rectangle { Layout.fillWidth: true; height: 1; color: "#30363d" }
                    
                    // Provider
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.lbl_ai_provider; color: "white"; font.pixelSize: 14 }
                        StyledComboBox {
                            id: providerCombo
                            Layout.fillWidth: true
                            model: ["openai_compatible", "gemini", "anthropic", "local_ollama"]
                            currentIndex: model.indexOf(mainVM.eaiiProvider) !== -1 ? model.indexOf(mainVM.eaiiProvider) : 0
                        }
                    }
                    
                    // Model & Base URL
                    RowLayout {
                        spacing: 20
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: mainVM.trans.lbl_model_name; color: "white"; font.pixelSize: 14 }
                            StyledTextField {
                                id: modelField
                                Layout.fillWidth: true
                                text: mainVM.eaiiModel
                                placeholderText: "gpt-4o-mini"
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: mainVM.trans.lbl_base_url; color: "white"; font.pixelSize: 14 }
                            StyledTextField {
                                id: urlField
                                Layout.fillWidth: true
                                text: mainVM.eaiiBaseUrl
                                placeholderText: "https://api..."
                            }
                        }
                    }
                    
                    // API Key
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: mainVM.trans.lbl_api_key; color: "white"; font.pixelSize: 14 }
                        StyledTextField {
                            id: keyField
                            Layout.fillWidth: true
                            text: mainVM.eaiiApiKey
                            echoMode: TextInput.Password
                            placeholderText: "Enter your secret key"
                        }
                    }
                }
            }
        }
        
        StyledButton {
            text: mainVM.trans.btn_apply_all
            Layout.alignment: Qt.AlignRight
            Layout.preferredWidth: 250
            Layout.preferredHeight: 45
            
            onClicked: {
                mainVM.applySettings(
                    eaiiSwitch.checked, 
                    syncSlider.value,
                    eaiiIntervalSlider.value,
                    langCombo.currentText,
                    providerCombo.currentText,
                    modelField.text,
                    urlField.text,
                    keyField.text,
                    aiProviderCombo.currentText,
                    aiModelField.text,
                    aiUrlField.text,
                    aiKeyField.text
                )
            }
        }
    }
}
