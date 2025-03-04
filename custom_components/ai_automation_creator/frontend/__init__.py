"""Frontend for AI Automation Creator."""
import os
import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FRONTEND_SCRIPT_URL = "/ai_automation_creator_static/main.js"

async def async_register_frontend(hass: HomeAssistant):
    """Register the frontend module."""
    root_dir = Path(__file__).parent.parent
    module_dir = root_dir / "www"
    
    # Create www directory if it doesn't exist
    if not os.path.exists(module_dir):
        os.makedirs(module_dir, exist_ok=True)
        _LOGGER.info("Created www directory at %s", module_dir)

    js_path = module_dir / "main.js"
    
    if not os.path.exists(js_path):
        _LOGGER.error("Frontend file not found: %s", js_path)
        # This is a critical error, we should inform the user
        hass.components.persistent_notification.create(
            "The AI Automation Creator frontend file is missing. Please reinstall the integration.",
            title="AI Automation Creator Error",
            notification_id="ai_automation_creator_error",
        )
        return False
    
    # Register the frontend script
    try:
        hass.http.register_static_path(
            FRONTEND_SCRIPT_URL, str(js_path), cache_headers=False
        )
        _LOGGER.info("Registered static path: %s -> %s", FRONTEND_SCRIPT_URL, js_path)
        
        # Add the script to frontend
        add_extra_js_url(hass, FRONTEND_SCRIPT_URL)
        _LOGGER.info("Added JS URL: %s", FRONTEND_SCRIPT_URL)
        
        return True
    except Exception as ex:
        _LOGGER.error("Error registering frontend: %s", ex)
        return False 