"""
Entropy - SSH Connection Manager
Maintains persistent SSH connection with auto-reconnect and keepalive
"""

import paramiko
import os
import logging
import socket
import threading
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SSHConnectionManager:
    """
    Manages a persistent SSH connection with:
    - Auto-reconnect on failure
    - Keepalive packets every 30 seconds
    - Thread-safe operations
    """
    
    def __init__(self, config_manager):
        self.cfg = config_manager
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._lock = threading.Lock()
        self._connected = False
        self._last_server_key = None  # Для отслеживания смены сервера
        
    @property
    def _server_key(self) -> str:
        """Уникальный ключ сервера для определения смены"""
        return f"{self.cfg.get('ip')}:{self.cfg.get('port')}"
    
    def _should_reconnect(self) -> bool:
        """Проверяем нужно ли переподключение"""
        if not self._connected or not self._client:
            return True
        if self._server_key != self._last_server_key:
            logger.info("Server changed, reconnecting...")
            return True
        # Проверяем живое ли соединение
        try:
            transport = self._client.get_transport()
            if transport is None or not transport.is_active():
                return True
        except Exception:
            return True
        return False
    
    def connect(self) -> bool:
        """Подключиться к серверу (или использовать существующее соединение)"""
        with self._lock:
            if not self._should_reconnect():
                return True
            
            # Закрываем старое соединение если есть
            self._close_internal()
            
            try:
                ip = self.cfg.get("ip")
                port = self.cfg.get("port")
                user = self.cfg.get("user")
                key_path = self.cfg.get("key_path")
                
                logger.info(f"SSH: Подключение к {ip}:{port}...")
                
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if not key_path or not os.path.exists(key_path):
                    raise FileNotFoundError(f"SSH ключ не найден: {key_path}")
                
                self._client.connect(
                    hostname=ip,
                    port=port,
                    username=user,
                    key_filename=key_path,
                    timeout=15,
                    banner_timeout=30
                )
                
                # Настраиваем keepalive
                transport = self._client.get_transport()
                if transport:
                    transport.set_keepalive(30)  # Keepalive каждые 30 сек
                
                self._connected = True
                self._last_server_key = self._server_key
                logger.info("SSH: Соединение установлено (persistent)")
                return True
                
            except Exception as e:
                logger.error(f"SSH: Ошибка подключения: {e}")
                self._connected = False
                self._client = None
                return False
    
    def exec_command(self, command: str, timeout: int = 10) -> Tuple[bool, str]:
        """Выполнить команду на сервере (thread-safe, без блокировки других команд)"""
        # Throttling: предотвращает слишком быструю отправку команд от 3-х пулов
        time.sleep(0.1)
        
        if not self.connect():
            return False, "Connection failed"
        
        with self._lock:
            client = self._client
            
        if not client:
            return False, "Client not available"
            
        try:
            # exec_command открывает новый channel. Это потокобезопасно.
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            return True, output if output else error
        except (TimeoutError, socket.timeout):
            # Таймаут команды — соединение живо, просто команда долгая
            logger.warning(f"SSH timeout [{command[:60]}] (timeout={timeout}s)")
            return False, f"Command timed out after {timeout}s"
        except Exception as e:
            # Реальная ошибка канала, но не обязательно всего соединения
            logger.error(f"SSH exec error [{command[:60]}]: {type(e).__name__}: {e}")
            return False, str(e)
    
    def get_sftp(self) -> Optional[paramiko.SFTPClient]:
        """Получить общий SFTP клиент (переиспользуемый)"""
        if not self.connect():
            return None
        
        with self._lock:
            client = self._client
            
        if not client:
            return None
            
        # Защищаем создание sftp также локом, чтобы не насоздавать лишних
        with self._lock:
            if self._sftp:
                try:
                    # Проверяем живо ли SFTP
                    self._sftp.stat('.')
                    return self._sftp
                except Exception:
                    self._sftp = None
            
            try:
                self._sftp = client.open_sftp()
                return self._sftp
            except Exception as e:
                logger.error(f"SFTP open error: {type(e).__name__}: {e}")
                return None
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Скачать файл через SFTP (использует разделяемую сессию)"""
        sftp = self.get_sftp()
        if not sftp:
            return False
        
        try:
            sftp.get(remote_path, local_path)
            # ВАЖНО: больше не делаем sftp.close(), т.к. сессия переиспользуется
            return True
        except Exception as e:
            logger.error(f"SFTP download error: {e}")
            with self._lock:
                self._sftp = None  # Сбросим битую сессию
            return False
    
    def _close_internal(self):
        """Внутреннее закрытие соединения (без lock)"""
        if self._sftp:
            try:
                self._sftp.close()
            except:
                pass
            self._sftp = None
        
        if self._client:
            try:
                self._client.close()
            except:
                pass
            self._client = None
        
        self._connected = False
    
    def close(self):
        """Закрыть соединение"""
        with self._lock:
            self._close_internal()
            logger.info("SSH: Соединение закрыто")
    
    def is_connected(self) -> bool:
        """Проверить активно ли соединение"""
        return self._connected and self._client is not None
