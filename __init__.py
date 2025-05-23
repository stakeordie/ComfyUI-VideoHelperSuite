import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .videohelpersuite.nodes import NODE_CLASS_MAPPINGS
from .videohelpersuite.nodes import NODE_DISPLAY_NAME_MAPPINGS
import folder_paths
from .videohelpersuite.server import server
from .videohelpersuite import documentation

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
documentation.format_descriptions(NODE_CLASS_MAPPINGS)
