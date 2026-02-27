import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "views"

Window {
    id: mainWindow
    visible: true
    width: 1240
    height: 850
    title: "Entropy v0.42.4 (QML)"
    color: "#0a0f14"

    property string currentView: "Dashboard"

    // --- MAIN LAYOUT ---
    Item {
        anchors.fill: parent
        
        // --- CONTENT AREA ---
        StackLayout {
            id: mainStack
            anchors.fill: parent
            anchors.leftMargin: 90
            anchors.margins: 25
            currentIndex: {
                if (currentView === "Dashboard") return 0;
                if (currentView === "AI") return 1;
                if (currentView === "Sandbox") return 2;
                if (currentView === "Security") return 3;
                if (currentView === "Settings") return 4;
                return 0;
            }

            // Views with individual entry animations
            DashboardView {
                opacity: mainStack.currentIndex === 0 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }
                layer.enabled: true
            }
            AIView {
                opacity: mainStack.currentIndex === 1 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }
                layer.enabled: true
            }
            SandboxView {
                opacity: mainStack.currentIndex === 2 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }
                layer.enabled: true
            }
            SecurityView {
                opacity: mainStack.currentIndex === 3 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }
                layer.enabled: true
            }
            SettingsView {
                opacity: mainStack.currentIndex === 4 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }
                layer.enabled: true
            }
        }
    }

    // --- FLOATING DOCK ---
    FloatingDock {
        activeView: currentView
        onViewChanged: (view) => currentView = view
    }
}
