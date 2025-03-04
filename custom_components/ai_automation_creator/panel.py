"""Panel setup for AI Automation Creator."""
import logging
import os
import voluptuous as vol
from homeassistant.components.frontend import async_register_built_in_panel

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ai_automation_creator"
PANEL_URL = "/ai-automation-creator"
PANEL_TITLE = "AI Automation Creator"
PANEL_ICON = "mdi:robot"

async def async_setup_panel(hass):
    """Set up the AI Automation Creator panel."""
    try:
        # Register the panel
        async_register_built_in_panel(
            hass,
            component_name=DOMAIN,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            frontend_url_path="ai-automation-creator",
            require_admin=False,
            config={},
        )
        
        # Tell the frontend to load the custom card element
        hass.http.register_static_path(
            f"/ai_automation_creator_panel",
            os.path.join(os.path.dirname(__file__), "www"),
        )
        
        hass.components.frontend.async_register_extra_js_url(
            hass, 
            "/local/ai_automation_creator.js"
        )
        
        _LOGGER.info("AI Automation Creator panel registered successfully")
        return True
    except Exception as e:
        _LOGGER.error("Failed to register panel: %s", str(e))
        return False 