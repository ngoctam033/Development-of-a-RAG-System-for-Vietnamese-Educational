import os

class MinIOPathManager:
    """
    Manages object paths and directory structure in MinIO.
    """
    
    DIR_STRUCTURE = {
        "raw": "raw/",
        "intermediate": "intermediate/",
        "processed": "processed/"
    }

    @staticmethod
    def get_path(category: str, filename: str) -> str:
        """
        Returns the full object path for a given category and filename.
        
        Args:
            category: The directory category ('raw', 'intermediate', 'processed').
            filename: The name of the file (including extension if needed).
            
        Returns:
            The full string path in MinIO.
        """
        prefix = MinIOPathManager.DIR_STRUCTURE.get(category.lower())
        if not prefix:
            raise ValueError(f"Invalid category: {category}. Must be one of {list(MinIOPathManager.DIR_STRUCTURE.keys())}")
            
        # Ensure filename doesn't start with a slash to avoid double slashes
        filename = filename.lstrip('/')
        return f"{prefix}{filename}"

    @staticmethod
    def validate_category(category: str) -> bool:
        """Checks if a category is defined in the directory structure."""
        return category.lower() in MinIOPathManager.DIR_STRUCTURE
