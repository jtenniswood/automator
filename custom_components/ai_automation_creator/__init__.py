"""The AI Automation Creator integration."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import openai
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONF_OPENAI_API_KEY, DOMAIN, CONF_MODEL, DEFAULT_MODEL
from .panel import async_setup_panel
from .frontend import async_register_frontend

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
                vol.Optional("sidebar_title", default="AI Automation"): cv.string,
                vol.Optional("sidebar_icon", default="mdi:robot"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_CREATE_AUTOMATION_SCHEMA = vol.Schema(
    {
        vol.Required("description"): cv.string,
    }
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration from configuration.yaml."""
    conf = config.get(DOMAIN, {})
    hass.data[DOMAIN] = conf
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AI Automation Creator from a config entry."""
    # Set up the OpenAI client
    openai.api_key = entry.data[CONF_OPENAI_API_KEY]
    
    # Register frontend resources
    await async_register_frontend(hass)
    
    # Set up panel
    await async_setup_panel(hass)
    
    # Store automation response for frontend
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["latest_automation"] = None
    
    async def create_automation(call: ServiceCall) -> None:
        """Create an automation based on natural language description."""
        description = call.data.get("description")
        if not description:
            raise ValueError("Description is required")

        # Get all available entities
        entity_registry = er.async_get(hass)
        entities = [
            {
                "entity_id": entity.entity_id,
                "name": entity.name or entity.entity_id,
                "domain": entity.domain,
                "device_class": entity.device_class,
            }
            for entity in entity_registry.entities.values()
        ]

        # Create prompt for OpenAI
        prompt = f"""Create a Home Assistant automation based on this description: {description}

Available entities:
{json.dumps(entities, indent=2)}

Analyze the request and available entities to create a robust automation. Use Home Assistant's automation YAML format.
Consider appropriate triggers, conditions, and actions.

Please provide the automation configuration in YAML format. The YAML should be valid and immediately usable in Home Assistant."""

        try:
            response = await hass.async_add_executor_job(
                lambda: openai.chat.completions.create(
                    model=hass.data[DOMAIN].get(CONF_MODEL, DEFAULT_MODEL),
                    messages=[
                        {"role": "system", "content": "You are a Home Assistant automation expert. Create valid YAML configurations for automations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
            )

            automation_yaml = response.choices[0].message.content
            
            # Clean up the YAML (remove markdown formatting if present)
            if "```yaml" in automation_yaml:
                automation_yaml = automation_yaml.split("```yaml")[1].split("```")[0].strip()
            elif "```" in automation_yaml:
                automation_yaml = automation_yaml.split("```")[1].split("```")[0].strip()
            
            # Store for frontend
            hass.data[DOMAIN]["latest_automation"] = automation_yaml
            
            # Save the automation to a file
            automation_path = f"{hass.config.config_dir}/automations.yaml"
            with open(automation_path, "a") as f:
                f.write(f"\n{automation_yaml}\n")

            # Reload automations
            await hass.services.async_call("automation", "reload")
            
            return {"success": True, "automation": automation_yaml}

        except Exception as err:
            _LOGGER.error("Error creating automation: %s", err)
            raise

    hass.services.async_register(
        DOMAIN, 
        "create_automation", 
        create_automation, 
        schema=SERVICE_CREATE_AUTOMATION_SCHEMA
    )
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, "create_automation")
    return True 