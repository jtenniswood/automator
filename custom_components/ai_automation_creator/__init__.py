"""The AI Automation Creator integration."""
import logging
import os
import yaml
import voluptuous as vol
import openai
import asyncio
import concurrent.futures
import re
import datetime
import time

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.components.persistent_notification import create as create_notification, ATTR_MESSAGE, DOMAIN as NOTIFICATION_DOMAIN

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
            You are a Home Assistant automation expert. Create a valid Home Assistant automation based on this description.
            
            IMPORTANT REQUIREMENTS:
            1. Return ONLY the YAML for the automation, no explanations or markdown.
            2. Do NOT include an 'id' field - I will add this automatically.
            3. Include appropriate triggers, conditions, and actions based on the request.
            4. Use proper yaml formatting with correct indentation.
            5. Include an 'alias' that is human-readable.
            6. Include a descriptive 'description' field explaining what the automation does.
            
            Example format (do not include the id):
            ```
            alias: Turn on lights at sunset
            description: Turns on the living room lights automatically when the sun sets
            trigger:
              - platform: sun
                event: sunset
            condition: []
            action:
              - service: light.turn_on
                target:
                  entity_id: light.living_room
            mode: single
            ```
            """
            
            try:
                # Make the OpenAI API call in the simplest way possible
                def call_openai():
                    return openai.chat.completions.create(
                        model=DEFAULT_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Create automation: {description}"}
                        ],
                        temperature=0.2,
                    )
                
                # Use concurrent.futures to run the OpenAI call in a thread pool
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    response = await asyncio.get_event_loop().run_in_executor(
                        executor, call_openai
                    )
                
                automation_yaml = response.choices[0].message.content.strip()
                automation_yaml = automation_yaml.replace("```yaml", "").replace("```", "").strip()
                
                # Check if it's valid YAML
                automation_data = yaml.safe_load(automation_yaml)
                
                # Generate a 13-digit numerical ID
                automation_id = str(int(time.time() * 1000))  # Current time in milliseconds as a 13-digit number
                
                # Add the ID to the automation data
                if "id" in automation_data:
                    _LOGGER.info("Automation already had an ID, replacing with: %s", automation_id)
                
                automation_data["id"] = automation_id
                
                # Regenerate the YAML for a single automation
                single_automation_yaml = yaml.dump(automation_data, default_flow_style=False)
                
                # Store for frontend access
                hass.data[DOMAIN]["latest_automation"] = single_automation_yaml
                
                try:
                    # Use the Home Assistant automation API to create the automation
                    # This makes it appear immediately in the UI without requiring a reload
                    _LOGGER.info("Creating automation with ID %s via API", automation_id)
                    
                    # First, check if the automation entity registry is available
                    from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
                    from homeassistant.components.automation import DOMAIN as AUTOMATION_DOMAIN
                    
                    # Create the automation using the automation.create service
                    service_data = {
                        "id": automation_id,
                        **automation_data  # Include all the generated automation data
                    }
                    
                    await hass.services.async_call(
                        AUTOMATION_DOMAIN,
                        "create",
                        service_data,
                        blocking=True
                    )
                    
                    _LOGGER.info("Automation created successfully via API")
                    
                    # Also save to the automations.yaml file for persistence
                    # This is optional but ensures the automation persists across restarts
                    automations_path = os.path.join(hass.config.path(), "automations.yaml")
                    
                    # Check if file exists and has content
                    if os.path.exists(automations_path) and os.path.getsize(automations_path) > 0:
                        # Read existing automations
                        with open(automations_path, "r") as f:
                            content = f.read().strip()
                            
                        # Prepare the properly indented automation entry
                        # First line starts with '- ' and the rest is indented by 2 spaces
                        indent_level = 2
                        lines = single_automation_yaml.strip().split('\n')
                        
                        # Format the first line with a dash
                        formatted_lines = [f"- {lines[0]}"]
                        
                        # Format the rest of the lines with proper indentation
                        for line in lines[1:]:
                            formatted_lines.append(' ' * indent_level + line)
                        
                        indented_automation = '\n'.join(formatted_lines)
                        
                        # Append to file
                        with open(automations_path, "a") as f:
                            f.write("\n\n# AI Generated Automation\n")
                            f.write(indented_automation)
                    else:
                        # Create new automations file with header and first automation
                        with open(automations_path, "w") as f:
                            f.write("# Automations created by AI Automation Creator\n\n")
                            
                            # Format with leading dash
                            lines = single_automation_yaml.strip().split('\n')
                            formatted_lines = [f"- {lines[0]}"]
                            
                            # Indent the rest by 2 spaces
                            for line in lines[1:]:
                                formatted_lines.append('  ' + line)
                            
                            indented_automation = '\n'.join(formatted_lines)
                            f.write(indented_automation)
                    
                    _LOGGER.info("Automation also saved to %s", automations_path)
                    
                    # Send a notification with a clickable link to the automation
                    notification_message = f"""
Successfully created automation from: {description}
<br><br>
<a href='/config/automation/edit/{automation_id}' target='_blank'>Click here to view or edit the automation</a>
"""
                    # Use the service call to ensure HTML rendering works
                    await hass.services.async_call(
                        NOTIFICATION_DOMAIN,
                        "create",
                        {
                            "title": "AI Automation Creator Success",
                            "message": notification_message,
                            "notification_id": "ai_automation_creator_success",
                        },
                        blocking=True
                    )
                    
                except Exception as e:
                    _LOGGER.error("Error creating automation via API, falling back to file creation: %s", str(e))
                    
                    # If API creation fails, fall back to file-based creation and trigger a reload
                    try:
                        # Save to file with proper formatting for the automations.yaml file
                        automations_path = os.path.join(hass.config.path(), "automations.yaml")
                        
                        # Check if file exists and has content
                        if os.path.exists(automations_path) and os.path.getsize(automations_path) > 0:
                            # Read existing automations
                            with open(automations_path, "r") as f:
                                content = f.read().strip()
                                
                            # Prepare the properly indented automation entry
                            # First line starts with '- ' and the rest is indented by 2 spaces
                            indent_level = 2
                            lines = single_automation_yaml.strip().split('\n')
                            
                            # Format the first line with a dash
                            formatted_lines = [f"- {lines[0]}"]
                            
                            # Format the rest of the lines with proper indentation
                            for line in lines[1:]:
                                formatted_lines.append(' ' * indent_level + line)
                            
                            indented_automation = '\n'.join(formatted_lines)
                            
                            # Append to file
                            with open(automations_path, "a") as f:
                                f.write("\n\n# AI Generated Automation\n")
                                f.write(indented_automation)
                        else:
                            # Create new automations file with header and first automation
                            with open(automations_path, "w") as f:
                                f.write("# Automations created by AI Automation Creator\n\n")
                                
                                # Format with leading dash
                                lines = single_automation_yaml.strip().split('\n')
                                formatted_lines = [f"- {lines[0]}"]
                                
                                # Indent the rest by 2 spaces
                                for line in lines[1:]:
                                    formatted_lines.append('  ' + line)
                                
                                indented_automation = '\n'.join(formatted_lines)
                                f.write(indented_automation)
                        
                        _LOGGER.info("Automation saved to %s, triggering reload", automations_path)
                        
                        # Trigger an automation reload
                        await hass.services.async_call(
                            AUTOMATION_DOMAIN,
                            "reload",
                            {},
                            blocking=True
                        )
                        
                        # Provide a notification with a link after file-based creation
                        notification_message = f"""
Successfully created automation from: {description}
<br><br>
<a href='/config/automation/edit/{automation_id}' target='_blank'>Click here to view or edit the automation</a>
"""
                        # Use the service call to ensure HTML rendering works
                        await hass.services.async_call(
                            NOTIFICATION_DOMAIN,
                            "create",
                            {
                                "title": "AI Automation Creator Success",
                                "message": notification_message,
                                "notification_id": "ai_automation_creator_success",
                            },
                            blocking=True
                        )
                        
                    except Exception as file_error:
                        _LOGGER.error("Error saving automation to file: %s", str(file_error))
                        # Use the service call for error notification too
                        await hass.services.async_call(
                            NOTIFICATION_DOMAIN,
                            "create",
                            {
                                "title": "AI Automation Creator Error",
                                "message": f"Error saving to automations.yaml: {str(file_error)}",
                                "notification_id": "ai_automation_creator_file_error",
                            },
                            blocking=True
                        )
                
                return {"yaml": single_automation_yaml, "id": automation_id}
                
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