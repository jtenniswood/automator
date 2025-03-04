"""Services for AI Automation Creator."""
import logging
import os
import yaml
import openai

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.components.persistent_notification import create as create_notification

from .const import DOMAIN, CONF_OPENAI_API_KEY, DEFAULT_MODEL

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant):
    """Set up services for AI Automation Creator."""
    
    # Get configuration
    config = hass.data.get(DOMAIN, {})
    config_entry = config.get("config_entry", {})
    
    # Initialize data structure if not already done
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("latest_automation", None)
    
    # Set OpenAI API key if available
    api_key = None
    if "config_entry" in config and CONF_OPENAI_API_KEY in config_entry:
        api_key = config_entry[CONF_OPENAI_API_KEY]
    elif "config" in config and CONF_OPENAI_API_KEY in config["config"]:
        api_key = config["config"][CONF_OPENAI_API_KEY]
    
    if api_key:
        openai.api_key = api_key
    
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
        
        try:
            _LOGGER.info("Creating automation from description: %s", description)
            
            # Directly generate the automation YAML
            automation_yaml = await generate_automation_yaml(description)
            
            if not automation_yaml:
                _LOGGER.error("Failed to generate automation YAML")
                create_notification(
                    hass,
                    "Failed to generate automation YAML. Please try a different description.",
                    title="AI Automation Creator Error",
                    notification_id="ai_automation_creator_generation_error",
                )
                return
            
            # Store for frontend access immediately
            update_frontend_data(automation_yaml)
            
            # Save the automation to a file
            save_success = await save_automation_to_file(hass, automation_yaml)
            
            if save_success:
                _LOGGER.info("Automation created and saved successfully")
                create_notification(
                    hass,
                    f"Successfully created automation from: {description}",
                    title="AI Automation Creator Success",
                    notification_id="ai_automation_creator_success",
                )
            else:
                _LOGGER.warning("Automation generated but not saved to file")
                create_notification(
                    hass,
                    "Automation was generated but could not be saved to file. Check the logs for details.",
                    title="AI Automation Creator Warning",
                    notification_id="ai_automation_creator_warning",
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
        _LOGGER.debug("Returning YAML content: %s", yaml_content)
        
        # Ensure we're returning a valid response that can be accessed by the frontend
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

async def generate_automation_yaml(description):
    """Generate automation YAML from description using OpenAI."""
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
        
        response = openai.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a Home Assistant automation for: {description}"}
            ],
            temperature=0.2,
        )
        
        yaml_content = response.choices[0].message.content.strip()
        
        # Clean up the response to ensure it's pure YAML
        yaml_content = yaml_content.replace("```yaml", "").replace("```", "").strip()
        
        # Validate the YAML to ensure it's parseable
        try:
            yaml.safe_load(yaml_content)
            _LOGGER.info("Successfully generated and validated YAML")
        except yaml.YAMLError as e:
            _LOGGER.error("Invalid YAML generated: %s", str(e))
            return None
        
        return yaml_content
    
    except Exception as e:
        _LOGGER.error("Error generating automation YAML: %s", str(e))
        return None

async def save_automation_to_file(hass, yaml_content):
    """Save the automation YAML to the automations.yaml file."""
    try:
        automations_path = os.path.join(hass.config.path(), "automations.yaml")
        
        # Create the file if it doesn't exist
        if not os.path.exists(automations_path):
            with open(automations_path, "w") as f:
                f.write("# Automations created by AI Automation Creator\n\n")
        
        # Append the new automation
        with open(automations_path, "a") as f:
            f.write("\n# AI Generated Automation\n")
            f.write(yaml_content)
            f.write("\n")
        
        _LOGGER.info("Automation saved to %s", automations_path)
        return True
    
    except Exception as e:
        _LOGGER.error("Error saving automation to file: %s", str(e))
        return False 