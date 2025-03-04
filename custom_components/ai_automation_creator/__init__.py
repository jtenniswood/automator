"""The AI Automation Creator integration."""
import os
import logging
from pathlib import Path

import voluptuous as vol
import openai

from homeassistant.core import HomeAssistant, callback, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.components.persistent_notification import create as create_notification

from .const import DOMAIN, CONF_OPENAI_API_KEY, CONF_MODEL, DEFAULT_MODEL
from .panel import async_setup_panel
from .frontend import async_register_frontend

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
    _LOGGER.info("Setting up AI Automation Creator integration")
    
    # Create www directory for static assets if it doesn't exist
    www_dir = hass.config.path("www")
    if not os.path.exists(www_dir):
        os.makedirs(www_dir, exist_ok=True)
        _LOGGER.info("Created www directory for static assets")
    
    if DOMAIN not in config:
        # Create www and copy assets as a backup even if config not provided
        await async_register_frontend(hass)
        return True
    
    conf = config[DOMAIN]
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        "config": conf,
        "latest_automation": None
    }
    
    # Set the OpenAI API key if provided in the config
    if CONF_OPENAI_API_KEY in conf:
        api_key = conf[CONF_OPENAI_API_KEY]
        openai.api_key = api_key
        _LOGGER.info("OpenAI API key configured from YAML")
    else:
        _LOGGER.warning("No OpenAI API key provided in configuration")
    
    # Set up services
    await async_setup_services(hass)
    
    # Register frontend resources
    frontend_success = await async_register_frontend(hass)
    if not frontend_success:
        _LOGGER.error("Failed to register frontend resources")
        create_notification(
            hass,
            "Failed to register frontend resources. The AI Automation Creator UI may not display correctly.",
            title="AI Automation Creator Error",
            notification_id="ai_automation_creator_frontend_error",
        )
    
    # Set up panel
    panel_success = await async_setup_panel(hass)
    if not panel_success:
        _LOGGER.error("Failed to register sidebar panel")
        create_notification(
            hass,
            "Failed to register sidebar panel. You may not see the AI Automation Creator in the sidebar.",
            title="AI Automation Creator Error",
            notification_id="ai_automation_creator_panel_error",
        )
    
    # Handle imports from configuration.yaml
    if hass.config_entries.async_entries(DOMAIN):
        return True
        
    # Create a config entry
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data=conf
        )
    )
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].update({
        "config_entry": entry.data,
        "latest_automation": None
    })
    
    # Set OpenAI API key
    if CONF_OPENAI_API_KEY in entry.data:
        api_key = entry.data[CONF_OPENAI_API_KEY]
        openai.api_key = api_key
        _LOGGER.info("OpenAI API key configured from config entry")
        
        # Validate the API key to make sure it works
        try:
            # Using a simple synchronous call wrapped in async executor
            from functools import partial
            from homeassistant.helpers.executor import async_call_executor
            
            # Create a partial function for the synchronous call
            sync_func = partial(openai.models.list)
            
            # Execute the function in the executor
            await async_call_executor(sync_func)
            _LOGGER.info("OpenAI API key validation successful")
        except Exception as e:
            _LOGGER.error("OpenAI API key validation failed: %s", str(e))
            create_notification(
                hass,
                f"OpenAI API key validation failed: {str(e)}. Check your API key and try again.",
                title="AI Automation Creator Error",
                notification_id="ai_automation_creator_api_key_error",
            )
    else:
        _LOGGER.error("No OpenAI API key provided in the config entry")
        create_notification(
            hass,
            "No OpenAI API key provided. Please reconfigure the integration.",
            title="AI Automation Creator Error",
            notification_id="ai_automation_creator_missing_key_error",
        )
    
    # Make sure services are set up
    await async_setup_services(hass)
    
    # Register frontend components after config entry is set up
    await async_register_frontend(hass)
    
    # Set up panel
    await async_setup_panel(hass)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove the config entry data
    if DOMAIN in hass.data and "config_entry" in hass.data[DOMAIN]:
        del hass.data[DOMAIN]["config_entry"]
    
    return True

# Register services
async def async_setup_services(hass: HomeAssistant):
    """Set up services for AI Automation Creator."""
    
    # Initialize data structure if not already done
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("latest_automation", None)
    
    @callback
    def update_frontend_data(yaml_content):
        """Update the frontend data with the latest automation YAML."""
        _LOGGER.debug("Updating frontend data with latest automation YAML")
        if yaml_content and yaml_content.strip():
            # Store the YAML content for retrieval by the frontend
            hass.data[DOMAIN]["latest_automation"] = yaml_content.strip()
            _LOGGER.info("Stored %d characters of YAML for frontend access", len(yaml_content))
        else:
            _LOGGER.warning("Attempted to store empty YAML content")
    
    async def create_automation(call: ServiceCall) -> None:
        """Create an automation based on natural language description."""
        description = call.data.get("description")
        if not description:
            _LOGGER.error("No description provided for automation creation")
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
        
        # Log the API key being used (masked for security)
        masked_key = f"{openai.api_key[:5]}...{openai.api_key[-4:]}" if len(openai.api_key) > 10 else "[Invalid Key]"
        _LOGGER.debug("Using OpenAI API key: %s", masked_key)
        
        try:
            _LOGGER.info("Creating automation from description: %s", description)
            
            # Create automation YAML using OpenAI
            try:
                # Create a system prompt that guides the model to generate valid YAML directly
                system_prompt = """
                You are an expert Home Assistant automation creator. 
                Your task is to create a valid automation for Home Assistant based on the user's description.
                
                IMPORTANT: DO NOT ASK ANY QUESTIONS. Generate the best possible automation with the information provided.
                
                Return ONLY the YAML for the automation, without any markdown formatting, explanations, or code blocks.
                Do not include any questions, suggestions, or comments - ONLY the YAML content.
                
                The YAML should be valid and ready to be copied directly into an automations.yaml file.
                
                Format your response as a single automation with the following structure:
                - id: unique_id_for_automation
                  alias: Descriptive Name
                  description: Optional longer description
                  trigger:
                    # trigger configuration
                  condition:
                    # condition configuration (if needed)
                  action:
                    # action configuration
                """
                
                # Run the OpenAI API call in an executor to avoid blocking
                from functools import partial
                from homeassistant.helpers.executor import async_call_executor
                
                # Log the API call attempt with the API key (masked)
                masked_key = f"{openai.api_key[:5]}...{openai.api_key[-4:]}" if openai.api_key and len(openai.api_key) > 10 else "Invalid Key"
                _LOGGER.debug("Calling OpenAI API with key %s and model %s", masked_key, DEFAULT_MODEL)
                
                # Create a partial function for the synchronous OpenAI call
                sync_func = partial(
                    openai.chat.completions.create,
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Create a Home Assistant automation for: {description}"}
                    ],
                    temperature=0.2,
                )
                
                # Execute the function in the executor
                response = await async_call_executor(sync_func)
                
                # Log success
                _LOGGER.info("Successfully received response from OpenAI API")
                
                automation_yaml = response.choices[0].message.content.strip()
                
                # Clean up the response to ensure it's pure YAML
                automation_yaml = automation_yaml.replace("```yaml", "").replace("```", "").strip()
                
                # Validate the YAML
                import yaml
                yaml.safe_load(automation_yaml)
                
            except Exception as e:
                _LOGGER.error("Error generating YAML: %s", str(e))
                create_notification(
                    hass,
                    f"Error generating automation YAML: {str(e)}",
                    title="AI Automation Creator Error",
                    notification_id="ai_automation_creator_generation_error",
                )
                return
            
            if not automation_yaml:
                _LOGGER.error("Failed to generate automation YAML")
                create_notification(
                    hass,
                    "Failed to generate automation YAML. Please try a different description.",
                    title="AI Automation Creator Error",
                    notification_id="ai_automation_creator_generation_error",
                )
                return
            
            # Store for frontend access
            update_frontend_data(automation_yaml)
            
            # Save the automation to automations.yaml
            try:
                automations_path = os.path.join(hass.config.path(), "automations.yaml")
                
                # Create the file if it doesn't exist
                if not os.path.exists(automations_path):
                    with open(automations_path, "w") as f:
                        f.write("# Automations created by AI Automation Creator\n\n")
                
                # Append the new automation
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
            except Exception as e:
                _LOGGER.error("Error saving automation to file: %s", str(e))
                create_notification(
                    hass,
                    f"Error saving automation to file: {str(e)}",
                    title="AI Automation Creator Error",
                    notification_id="ai_automation_creator_file_error",
                )
                
        except Exception as e:
            _LOGGER.error("Error creating automation: %s", str(e))
            create_notification(
                hass,
                f"Error creating automation: {str(e)}",
                title="AI Automation Creator Error",
                notification_id="ai_automation_creator_error",
            )
    
    async def get_automation_yaml(call):
        """Get the last created automation YAML."""
        yaml_content = hass.data[DOMAIN].get("latest_automation", "")
        _LOGGER.debug("Returning YAML content of length: %d", len(yaml_content) if yaml_content else 0)
        
        # Ensure we're returning a valid response that the frontend can access
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
    
    _LOGGER.info("AI Automation Creator services are ready")
    return True 