import logging
import sys
import threading
from typing import Optional

class SingletonLogger:
    """
    A thread-safe Singleton Logger for the Agentic RAG system.
    """
    _instance: Optional['SingletonLogger'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SingletonLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Configure the base logger
        self.logger = logging.getLogger("AgenticRAG")
        self.logger.setLevel(logging.INFO)

        # Standard output handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(console_handler)

        self._initialized = True

    def get_logger(self) -> logging.Logger:
        return self.logger

# Global access point
logger = SingletonLogger().get_logger()
