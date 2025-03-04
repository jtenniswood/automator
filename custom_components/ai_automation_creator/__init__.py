"""The AI Automation Creator integration."""
import logging
import os
import yaml
import voluptuous as vol
import openai

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.components.persistent_notification import create as create_notification

from .const import DOMAIN, CONF_OPENAI_API_KEY, DEFAULT_MODEL

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_OPENAI_API_KEY): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up this integration using YAML."""
    if DOMAIN not in config:
        return True
    
    conf = config[DOMAIN]
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        "config": conf,
        "latest_automation": None
    }
    
    # Set the OpenAI API key
    if CONF_OPENAI_API_KEY in conf:
        openai.api_key = conf[CONF_OPENAI_API_KEY]
        _LOGGER.info("OpenAI API key configured from YAML")
    
    # Set up services
    await setup_services(hass)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        "config_entry": entry.data,
        "latest_automation": None
    }
    
    # Set OpenAI API key
    if CONF_OPENAI_API_KEY in entry.data:
        openai.api_key = entry.data[CONF_OPENAI_API_KEY]
        _LOGGER.info("OpenAI API key configured from config entry")
    
    # Set up services
    await setup_services(hass)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True

async def setup_services(hass: HomeAssistant):
    """Set up services for the integration."""
    async def create_automation(call: ServiceCall) -> None:
        """Create an automation based on natural language description."""
        description = call.data.get("description")
        if not description:
            _LOGGER.error("No description provided")
            return
        
        if not openai.api_key:
            _LOGGER.error("OpenAI API key not configured")
            create_notification(
                hass,
                "OpenAI API key not configured. Please set up the integration properly.",
                title="AI Automation Creator Error",
                notification_id="ai_automation_creator_api_error",
            )
            return
        
        try:
            _LOGGER.info("Creating automation from description: %s", description)
            
            # Simple system prompt
            system_prompt = """
            Create a valid Home Assistant automation based on this description.
            Return ONLY the YAML for the automation, no explanations or markdown.
            """
            
            try:
                # Make the OpenAI API call in the simplest way possible
                from homeassistant.helpers.executor import async_call_executor
                import functools
                
                def call_openai():
                    return openai.chat.completions.create(
                        model=DEFAULT_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Create automation: {description}"}
                        ],
                        temperature=0.2,
                    )
                
                response = await async_call_executor(functools.partial(call_openai))
                
                automation_yaml = response.choices[0].message.content.strip()
                automation_yaml = automation_yaml.replace("```yaml", "").replace("```", "").strip()
                
                # Check if it's valid YAML
                yaml.safe_load(automation_yaml)
                
                # Store for frontend access
                hass.data[DOMAIN]["latest_automation"] = automation_yaml
                
                # Save to file
                automations_path = os.path.join(hass.config.path(), "automations.yaml")
                
                if not os.path.exists(automations_path):
                    with open(automations_path, "w") as f:
                        f.write("# Automations created by AI Automation Creator\n\n")
                
                with open(automations_path, "a") as f:
                    f.write("\n# AI Generated Automation\n")
                    f.write(automation_yaml)
                    f.write("\n")
                
                _LOGGER.info("Automation saved to %s", automations_path)
                
                create_notification(
                    hass,
                    f"Successfully created automation from: {description}",
                    title="AI Automation Creator Success",
                    notification_id="ai_automation_creator_success",
                )
                
                return {"yaml": automation_yaml}
                
            except Exception as e:
                _LOGGER.error("Error generating YAML: %s", str(e))
                create_notification(
                    hass,
                    f"Error: {str(e)}",
                    title="AI Automation Creator Error",
                    notification_id="ai_automation_creator_error",
                )
                return {"error": str(e)}
                
        except Exception as e:
            _LOGGER.error("Error in automation creation: %s", str(e))
            create_notification(
                hass,
                f"Error: {str(e)}",
                title="AI Automation Creator Error",
                notification_id="ai_automation_creator_error",
            )
            return {"error": str(e)}
    
    async def get_automation_yaml(call):
        """Get the last created automation YAML."""
        yaml_content = hass.data[DOMAIN].get("latest_automation", "")
        return {"yaml": yaml_content}
    
    # Register services
    hass.services.async_register(
        DOMAIN, 
        "create_automation", 
        create_automation
    )
    
    hass.services.async_register(
        DOMAIN, 
        "get_automation_yaml", 
        get_automation_yaml
    )
    
    _LOGGER.info("AI Automation Creator services registered")
    return True 