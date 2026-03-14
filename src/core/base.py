from abc import ABC, abstractmethod
from typing import Dict, Any
from src.core.logger import logger

class BaseComponent(ABC):
    """
    Abstract base class for all components in the Agentic RAG system.
    Ensures a consistent interface across extraction, processing, indexing, and generation.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the component.
        
        Args:
            name (str): Unique identifier for the component instance.
            config (Dict[str, Any]): Configuration settings for the component.
        """
        self.name = name
        self.config = config
        self.status = "initialized"
        logger.info(f"Component '{self.name}' initialized with config: {self.config}")

    @abstractmethod
    def run(self) -> Any:
        """
        Main execution logic for the component. 
        Must be implemented by subclasses.
        """
        pass

    def get_status(self) -> str:
        """
        Returns the current status of the component.
        """
        return self.status

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the component's state.
         useful for serialization or tracking.
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "status": self.status,
            "config": self.config
        }
