
import QtQuick 2.15

Item {
    id: root
    
    property color lineColor: "#58a6ff"
    property color fillColor: Qt.rgba(88/255, 166/255, 255/255, 0.1)
    property var dataPoints: []
    property int maxPoints: 60
    property real maxValue: 100
    
    onDataPointsChanged: canvas.requestPaint()
    
    Canvas {
        id: canvas
        anchors.fill: parent
        renderTarget: Canvas.FramebufferObject
        renderStrategy: Canvas.Threaded
        
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            
            if (dataPoints.length < 2) return;
            
            var stepX = width / (maxPoints - 1);
            
            // --- DRAW GRADIENT FILL ---
            ctx.beginPath();
            ctx.moveTo(0, height);
            for (var i = 0; i < dataPoints.length; i++) {
                var x = i * stepX;
                var y = height - (dataPoints[i] / maxValue * height);
                ctx.lineTo(x, y);
            }
            ctx.lineTo((dataPoints.length - 1) * stepX, height);
            ctx.closePath();
            
            var grad = ctx.createLinearGradient(0, 0, 0, height);
            grad.addColorStop(0, root.fillColor);
            grad.addColorStop(1, "transparent");
            ctx.fillStyle = grad;
            ctx.fill();
            
            // --- DRAW LINE ---
            ctx.beginPath();
            ctx.strokeStyle = root.lineColor;
            ctx.lineWidth = 2;
            ctx.lineJoin = "round";
            
            for (var j = 0; j < dataPoints.length; j++) {
                var lx = j * stepX;
                var ly = height - (dataPoints[j] / maxValue * height);
                if (j === 0) ctx.moveTo(lx, ly);
                else ctx.lineTo(lx, ly);
            }
            ctx.stroke();
            
            // --- DRAW GLOW (Shadow) ---
            // Simple canvas shadow can be slow, but let's try a faint duplicate line
            ctx.globalAlpha = 0.3;
            ctx.lineWidth = 4;
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }
    }
}
