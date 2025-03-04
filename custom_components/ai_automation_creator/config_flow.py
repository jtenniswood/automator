"""Config flow for AI Automation Creator integration."""
import logging
from typing import Any, Dict, Optional

import openai
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_OPENAI_API_KEY, CONF_MODEL, DEFAULT_MODEL

_LOGGER = logging.getLogger(__name__)

async def validate_api_key(api_key: str) -> bool:
    """Test if the API key is valid."""
    try:
        openai.api_key = api_key
        # Make a simple API call to verify the key works
        models = await openai.models.list()
        return True
    except Exception as e:
        _LOGGER.error("Failed to validate OpenAI API key: %s", str(e))
        return False

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Automation Creator."""

    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                api_key = user_input[CONF_OPENAI_API_KEY]
                
                # Validate the API key
                is_valid = await validate_api_key(api_key)
                
                if is_valid:
                    # Create the entry
                    return self.async_create_entry(
                        title="AI Automation Creator",
                        data=user_input,
                    )
                else:
                    errors["base"] = "invalid_api_key"
            
            except Exception as e:
                _LOGGER.exception("Unexpected error during setup: %s", str(e))
                errors["base"] = "unknown"
        
        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OPENAI_API_KEY): str,
                    vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
                }
            ),
            errors=errors,
        )
    
    async def async_step_import(self, import_config: dict) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            # Update entry
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_MODEL, 
                default=self.config_entry.options.get(CONF_MODEL, DEFAULT_MODEL)
            ): str,
        }

        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(options)
        ) 