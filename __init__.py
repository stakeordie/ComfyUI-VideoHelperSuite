from .videohelpersuite.nodes import NODE_CLASS_MAPPINGS as BASE_NODE_CLASS_MAPPINGS
from .videohelpersuite.nodes import NODE_DISPLAY_NAME_MAPPINGS as BASE_NODE_DISPLAY_NAME_MAPPINGS
from .videohelpersuite.emprops_nodes import EmProps_VideoCombine
import folder_paths
from .videohelpersuite.server import server
from .videohelpersuite import documentation

WEB_DIRECTORY = "./web"

# Merge base nodes with EmProps nodes
NODE_CLASS_MAPPINGS = {
    **BASE_NODE_CLASS_MAPPINGS,
    "EmProps_VideoCombine": EmProps_VideoCombine
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **BASE_NODE_DISPLAY_NAME_MAPPINGS,
    "EmProps_VideoCombine": "EmProps Video Combine 🎥🅴🅿"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
documentation.format_descriptions(NODE_CLASS_MAPPINGS)
