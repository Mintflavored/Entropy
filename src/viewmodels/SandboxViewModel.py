"""
Entropy AI Sandbox - ViewModel for QML UI
Мост между EAISAgent и QML-интерфейсом
"""

import json
import logging
from PySide6.QtCore import QObject, Signal, Property, Slot, QThread

logger = logging.getLogger("SandboxViewModel")


class SandboxWorker(QThread):
    """Фоновый поток для AI экспериментов"""
    
    progress_changed = Signal(int, int)
    status_changed = Signal(str)
    optimization_finished = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, agent, max_experiments=10):
        super().__init__()
        self.agent = agent
        self.max_experiments = max_experiments
    
    def run(self):
        try:
            # Подключаем callbacks для UI
            self.agent.set_callbacks(
                status_cb=lambda text: self.status_changed.emit(text),
                progress_cb=lambda cur, total: self.progress_changed.emit(cur, total)
            )
            
            result = self.agent.run_optimization(max_experiments=self.max_experiments)
            
            if result:
                recommendation = self.agent.get_recommendation()
                self.optimization_finished.emit(recommendation)
            else:
                self.error_occurred.emit("Оптимизация завершилась без результата")
            
        except Exception as e:
            logger.error(f"Sandbox worker error: {e}")
            self.error_occurred.emit(str(e))


class SandboxViewModel(QObject):
    """ViewModel для AI Sandbox UI"""
    
    statusChanged = Signal()
    progressChanged = Signal()
    resultsChanged = Signal()
    
    def __init__(self, ssh_manager=None, config_manager=None):
        super().__init__()
        
        self._ssh = ssh_manager
        self._cfg = config_manager
        self._is_running = False
        self._current_experiment = 0
        self._total_experiments = 0
        self._best_score = 0.0
        self._baseline_score = 0.0
        self._improvement = 0.0
        self._best_config = {}
        self._status_text = "Готово к запуску"
        self._error = ""
        self._ai_reasoning = ""
        
        self._agent = None
        self._worker = None
    
    def _get_agent(self):
        if self._agent is None:
            from ai.sandbox_agent import EAISAgent
            self._agent = EAISAgent(self._ssh, self._cfg)
        return self._agent
    
    # --- QML Properties ---
    
    @Property(bool, notify=statusChanged)
    def isRunning(self) -> bool:
        return self._is_running
    
    @Property(int, notify=progressChanged)
    def currentExperiment(self) -> int:
        return self._current_experiment
    
    @Property(int, notify=progressChanged)
    def totalExperiments(self) -> int:
        return self._total_experiments
    
    @Property(float, notify=resultsChanged)
    def bestScore(self) -> float:
        return self._best_score
    
    @Property(float, notify=resultsChanged)
    def baselineScore(self) -> float:
        return self._baseline_score
    
    @Property(float, notify=resultsChanged)
    def improvement(self) -> float:
        return self._improvement
    
    @Property(str, notify=resultsChanged)
    def bestConfigJson(self) -> str:
        return json.dumps(self._best_config, indent=2)
    
    @Property(str, notify=statusChanged)
    def statusText(self) -> str:
        return self._status_text
    
    @Property(str, notify=statusChanged)
    def error(self) -> str:
        return self._error
    
    @Property(float, notify=progressChanged)
    def progressPercent(self) -> float:
        if self._total_experiments == 0:
            return 0.0
        return (self._current_experiment / self._total_experiments) * 100
    
    @Property(str, notify=resultsChanged)
    def aiReasoning(self) -> str:
        return self._ai_reasoning
    
    # --- QML Slots ---
    
    @Slot()
    def startOptimization(self):
        """Запуск AI оптимизации"""
        if self._is_running:
            return
        
        # Проверяем что EAIS включён
        if self._cfg and not self._cfg.get("eais_enabled", False):
            self._error = "EAIS отключён. Включите в Настройках → Интерактивный AI Аналитик"
            self._status_text = "EAIS отключён"
            self.statusChanged.emit()
            return
        
        # Проверяем SSH
        if not self._ssh:
            self._error = "SSH не подключён"
            self.statusChanged.emit()
            return
        
        # Проверяем AI ключ
        if self._cfg and not self._cfg.ai_key:
            self._error = "API ключ не настроен"
            self.statusChanged.emit()
            return
        
        self._is_running = True
        self._error = ""
        self._status_text = "Инициализация EAIS..."
        self.statusChanged.emit()
        
        agent = self._get_agent()
        self._worker = SandboxWorker(agent, max_experiments=10)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.status_changed.connect(self._on_status)
        self._worker.optimization_finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
    
    @Slot()
    def stopOptimization(self):
        if self._agent:
            self._agent.stop()
        self._is_running = False
        self._status_text = "Остановлено пользователем"
        self._agent = None  # Сброс агента для пересоздания при следующем запуске
        self.statusChanged.emit()
    
    @Slot()
    def applyBestConfig(self):
        if not self._best_config:
            self._error = "Нет результатов для применения"
            self.statusChanged.emit()
            return
        logger.info(f"Applying best config: {self._best_config}")
        self._status_text = "Конфигурация готова к применению"
        self.statusChanged.emit()
    
    # --- Callbacks ---
    
    def _on_progress(self, current: int, total: int):
        self._current_experiment = current
        self._total_experiments = total
        self.progressChanged.emit()
    
    def _on_status(self, text: str):
        self._status_text = text
        self.statusChanged.emit()
    
    def _on_finished(self, recommendation: dict):
        self._is_running = False
        
        if "error" in recommendation:
            self._error = recommendation["error"]
        else:
            self._best_score = recommendation.get("score", 0)
            self._baseline_score = recommendation.get("baseline_score", 0) or 0
            self._improvement = recommendation.get("improvement_pct", 0)
            self._best_config = recommendation.get("config", {})
            self._ai_reasoning = recommendation.get("ai_reasoning", "")
            self._status_text = f"Готово! Улучшение: {self._improvement:.1f}%"
        
        self.statusChanged.emit()
        self.resultsChanged.emit()
        self._cleanup_worker()
    
    def _on_error(self, error: str):
        self._is_running = False
        self._error = error
        self._status_text = "Ошибка"
        self.statusChanged.emit()
        self._cleanup_worker()
    
    def _cleanup_worker(self):
        """Safely clean up worker thread"""
        if self._worker:
            self._worker.quit()
            self._worker.wait(3000)
            self._worker.deleteLater()
            self._worker = None
