"""File type management for the discord-image-cleaner.

Supports selecting which file types are archived.
"""

import os
from typing import Tuple

# All supported file types, organized by category
SUPPORTED_TYPES = {
    "images": {
        "extensions": (".png", ".jpg", ".jpeg", ".webp"),
        "description": "Common image formats",
    },
}

# Flatten for quick lookup
ALL_EXTENSIONS = tuple(
    ext for category in SUPPORTED_TYPES.values() for ext in category["extensions"]
)


class FileTypeManager:
    """Manages which file types are archived.
    
    Use the MANAGED_EXTENSIONS tuple for checking allowed file types.
    Configure via MANAGED_FILE_TYPES environment variable.
    """

    @staticmethod
    def get_managed_extensions() -> Tuple[str, ...]:
        """Return tuple of file extensions to manage.
        
        Reads MANAGED_FILE_TYPES env var (comma-separated category names).
        Defaults to all available types if not set.
        
        Example:
            MANAGED_FILE_TYPES=images
        
        Returns:
            Tuple of lowercase extensions (e.g., ('.png', '.jpg'))
        """
        managed_types = os.getenv("MANAGED_FILE_TYPES", "").strip().lower()

        if not managed_types:
            # Default: include all types
            return ALL_EXTENSIONS

        # Parse comma-separated categories
        requested = [t.strip() for t in managed_types.split(",") if t.strip()]
        extensions = []

        for req in requested:
            if req not in SUPPORTED_TYPES:
                raise ValueError(
                    f"Unknown file type category: {req}. "
                    f"Available: {', '.join(SUPPORTED_TYPES.keys())}"
                )
            extensions.extend(SUPPORTED_TYPES[req]["extensions"])

        return tuple(extensions)

    @staticmethod
    def list_available_types() -> None:
        """Print all available file type categories."""
        print("Available file type categories:")
        for category, info in SUPPORTED_TYPES.items():
            exts = ", ".join(info["extensions"])
            print(f"  {category:12} - {info['description']}: {exts}")


# Load on module import
MANAGED_EXTENSIONS = FileTypeManager.get_managed_extensions()
