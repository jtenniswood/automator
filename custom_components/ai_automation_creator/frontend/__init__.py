"""Frontend for AI Automation Creator."""
import os
import logging
import shutil
from pathlib import Path

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_register_frontend(hass: HomeAssistant):
    """Register the frontend module."""
    # Get paths
    root_dir = Path(__file__).parent.parent
    src_js_path = root_dir / "www" / "main.js"
    
    # Path to www directory
    www_dir = hass.config.path("www")
    if not os.path.exists(www_dir):
        os.makedirs(www_dir, exist_ok=True)
        
    # Destination file
    dest_js_path = os.path.join(www_dir, "ai_automation_creator.js")
    
    try:
        # Check if source file exists
        if not os.path.exists(src_js_path):
            _LOGGER.error("Source JS file not found: %s", src_js_path)
            return False
        
        # Copy the file
        shutil.copy2(str(src_js_path), dest_js_path)
        _LOGGER.info("Successfully copied JS file to %s", dest_js_path)
        
        return True
    except Exception as ex:
        _LOGGER.error("Error registering frontend: %s", ex)
        return False 