"""Config flow for AI Automation Creator integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_OPENAI_API_KEY

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Automation Creator."""

    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Accept any key without validation for now
            api_key = user_input[CONF_OPENAI_API_KEY]
            _LOGGER.info("Accepting OpenAI API key configuration without validation")
            
            # Create the entry
            return self.async_create_entry(
                title="AI Automation Creator",
                data=user_input,
            )
        
        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OPENAI_API_KEY): str,
                }
            ),
            errors=errors,
        )
    
    async def async_step_import(self, import_config: dict):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config) 