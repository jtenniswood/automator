"""Panel for AI Automation Creator."""
import voluptuous as vol
from homeassistant.components import panel_custom
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

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

async def async_setup_panel(hass):
    """Set up the AI Automation Creator panel."""
    config = hass.data.get(DOMAIN, {})
    
    sidebar_title = config.get("sidebar_title", "AI Automation")
    sidebar_icon = config.get("sidebar_icon", "mdi:robot")
    
    await hass.async_add_executor_job(
        hass.components.frontend.async_register_built_in_panel,
        "custom",
        sidebar_title,
        sidebar_icon,
        DOMAIN,
        {"_panel_custom": {"name": "ai-automation-creator", "embed_iframe": False}},
        require_admin=True,
    )
    
    hass.http.register_static_path(
        f"/ai_automation_creator/frontend/main.js",
        hass.config.path(f"custom_components/ai_automation_creator/frontend/main.js"),
        True,
    )
    
    return True 