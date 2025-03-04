"""Panel for AI Automation Creator."""
import voluptuous as vol
import logging
import os
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .frontend import FRONTEND_SCRIPT_URL

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("sidebar_title", default="AI Automation"): cv.string,
                vol.Optional("sidebar_icon", default="mdi:robot"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup_panel(hass: HomeAssistant):
    """Set up the AI Automation Creator panel."""
    config = hass.data.get(DOMAIN, {})
    
    sidebar_title = config.get("sidebar_title", "AI Automation")
    sidebar_icon = config.get("sidebar_icon", "mdi:robot")
    
    root_path = Path(__file__).parent
    www_path = root_path / "www"
    
    # Make sure the www directory exists
    if not os.path.exists(www_path):
        _LOGGER.warning("www directory doesn't exist, creating it")
        os.makedirs(www_path, exist_ok=True)
    
    # Make sure main.js exists
    js_path = www_path / "main.js"
    if not os.path.exists(js_path):
        _LOGGER.error("main.js doesn't exist at %s", js_path)
        return False
    
    _LOGGER.info("Setting up AI Automation Creator panel with script at %s", FRONTEND_SCRIPT_URL)
    
    try:
        # Register the panel
        await async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=sidebar_title,
            sidebar_icon=sidebar_icon,
            frontend_url_path=DOMAIN,
            config={
                "_panel_custom": {
                    "name": "ai-automation-creator",
                    "module_url": FRONTEND_SCRIPT_URL,
                    "embed_iframe": False,
                    "trust_external": True,
                    "allow_all_scripts": True
                }
            },
            require_admin=True,
        )
        
        _LOGGER.info("Successfully registered AI Automation Creator panel")
        return True
    except Exception as ex:
        _LOGGER.error("Could not register panel: %s", ex)
        return False 