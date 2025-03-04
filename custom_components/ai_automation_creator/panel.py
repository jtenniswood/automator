"""Panel for AI Automation Creator."""
import voluptuous as vol
import logging
from homeassistant.components import panel_custom
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
    
    try:
        # Register the panel
        await hass.components.frontend.async_register_built_in_panel(
            component_name="custom",
            sidebar_title=sidebar_title,
            sidebar_icon=sidebar_icon,
            frontend_url_path=DOMAIN,
            config={
                "_panel_custom": {
                    "name": "ai-automation-creator",
                    "module_url": FRONTEND_SCRIPT_URL,
                    "embed_iframe": False,
                }
            },
            require_admin=True,
        )
    except Exception as ex:
        _LOGGER.error("Could not register panel %s", ex)
        return False
    
    return True 