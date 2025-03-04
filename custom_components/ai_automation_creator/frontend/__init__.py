"""Frontend for AI Automation Creator."""
import os
from homeassistant.components.frontend import add_extra_js_url


async def async_register_frontend(hass):
    """Register the frontend module."""
    # Register the frontend module
    add_extra_js_url(
        hass, "/ai_automation_creator/frontend/main.js", es5=False
    ) 