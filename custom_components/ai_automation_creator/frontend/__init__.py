"""Frontend for AI Automation Creator."""
import os
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FRONTEND_SCRIPT_URL = "/ai_automation_creator_static/main.js"

async def async_register_frontend(hass: HomeAssistant):
    """Register the frontend module."""
    root_dir = Path(__file__).parent.parent
    module_dir = os.path.join(root_dir, "www")

    # Create www directory if it doesn't exist
    if not os.path.exists(module_dir):
        os.makedirs(module_dir, exist_ok=True)

    js_path = os.path.join(module_dir, "main.js")
    
    # Register the frontend script
    hass.http.register_static_path(
        FRONTEND_SCRIPT_URL, js_path, cache_headers=False
    )
    
    # Add the script to frontend
    add_extra_js_url(hass, FRONTEND_SCRIPT_URL) 