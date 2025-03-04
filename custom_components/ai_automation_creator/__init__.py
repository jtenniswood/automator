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
import copy

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
            
            # System prompt
            system_prompt = """
            You are a Home Assistant automation expert. Create a valid Home Assistant automation based on this description.
            
            IMPORTANT REQUIREMENTS:
            1. Return ONLY the YAML for the automation, no explanations or markdown.
            2. Do NOT include an 'id' field - I will add this automatically.
            3. Use the following structure for your automation:
               - Each trigger MUST have an ID that describes what it is (e.g., "motion_detected", "time_based_trigger")
               - Use "triggers" (plural) instead of "trigger" for all automations, even with a single trigger
               - Use "actions" (plural) instead of "action"
               - Structure the automation with a 'choose' element in the actions section
               - Within 'choose', use trigger-based conditions to check which trigger fired
               - Place the actual action sequence within the appropriate 'choose' condition
            
            4. Include an 'alias' that is human-readable.
            5. Include a descriptive 'description' field explaining what the automation does.
            
            Example format (do not include the automation id):
            ```
            alias: Turn on lights when motion detected
            description: Turns on the living room lights when motion is detected or at sunset
            triggers:
              - id: motion_detected
                platform: state
                entity_id: binary_sensor.living_room_motion
                to: 'on'
              - id: sunset_trigger
                platform: sun
                event: sunset
            conditions: []
            actions:
              - choose:
                - conditions:
                    - condition: trigger
                      id: motion_detected
                  sequence:
                    - service: light.turn_on
                      target:
                        entity_id: light.living_room
                      data:
                        brightness_pct: 100
                - conditions:
                    - condition: trigger
                      id: sunset_trigger
                  sequence:
                    - service: light.turn_on
                      target:
                        entity_id: light.living_room
                      data:
                        brightness_pct: 50
            mode: single
            ```
            
            Even for simple automations with a single trigger, use this structure for consistency.
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
                
                # Ensure the automation has the correct structure
                automation_data = ensure_automation_structure(automation_data, _LOGGER)
                
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
                        
                    except Exception as file_error:
                        _LOGGER.error("Error saving automation to file: %s", str(file_error))
                        create_notification(
                            hass,
                            f"Error saving to automations.yaml: {str(file_error)}",
                            title="AI Automation Creator Error",
                            notification_id="ai_automation_creator_file_error",
                        )
                
                create_notification(
                    hass,
                    f"Successfully created automation from: {description}",
                    title="AI Automation Creator Success",
                    notification_id="ai_automation_creator_success",
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

def ensure_automation_structure(automation_data, logger):
    """
    Ensure the automation has the required structure with trigger IDs and choose elements.
    If not, transform it to match the required structure.
    """
    modified_data = copy.deepcopy(automation_data)
    
    # Check if we need to rename 'trigger' to 'triggers'
    if 'trigger' in modified_data and 'triggers' not in modified_data:
        logger.info("Converting 'trigger' to 'triggers'")
        modified_data['triggers'] = modified_data.pop('trigger')
    
    # Check if we need to rename 'action' to 'actions'
    if 'action' in modified_data and 'actions' not in modified_data:
        logger.info("Converting 'action' to 'actions'")
        modified_data['actions'] = modified_data.pop('action')
    
    # Ensure triggers have IDs
    if 'triggers' in modified_data and isinstance(modified_data['triggers'], list):
        for i, trigger in enumerate(modified_data['triggers']):
            if 'id' not in trigger:
                # Generate a default ID based on the platform or type
                platform = trigger.get('platform', '')
                trigger_type = trigger.get('type', '')
                entity_id = trigger.get('entity_id', '')
                
                # Try to create a meaningful ID
                if entity_id:
                    # Extract the entity name from entity_id
                    entity_name = entity_id.split('.')[-1] if '.' in entity_id else entity_id
                    default_id = f"{platform or trigger_type}_{entity_name}".lower()
                else:
                    default_id = f"{platform or trigger_type}_{i+1}".lower()
                
                # Clean the ID
                default_id = re.sub(r'[^a-z0-9_]', '_', default_id)
                default_id = re.sub(r'_+', '_', default_id)  # Replace multiple underscores
                
                logger.info(f"Adding ID '{default_id}' to trigger #{i+1}")
                trigger['id'] = default_id
    
    # If we don't have a 'choose' structure in actions, create it
    if 'actions' in modified_data and isinstance(modified_data['actions'], list):
        has_choose = False
        
        # Check if any action is already a 'choose' element
        for action in modified_data['actions']:
            if isinstance(action, dict) and 'choose' in action:
                has_choose = True
                break
        
        if not has_choose:
            logger.info("Restructuring actions to use 'choose' pattern")
            original_actions = modified_data['actions']
            
            # Create new actions with choose structure
            new_actions = []
            
            # Get trigger IDs
            trigger_ids = []
            if 'triggers' in modified_data and isinstance(modified_data['triggers'], list):
                for trigger in modified_data['triggers']:
                    if 'id' in trigger:
                        trigger_ids.append(trigger['id'])
            
            if trigger_ids:
                # Create a 'choose' action that uses the trigger IDs
                choose_action = {
                    'choose': []
                }
                
                # Add a condition and sequence for each trigger
                for trigger_id in trigger_ids:
                    condition_block = {
                        'conditions': [
                            {
                                'condition': 'trigger',
                                'id': trigger_id
                            }
                        ],
                        'sequence': original_actions
                    }
                    choose_action['choose'].append(condition_block)
                
                new_actions.append(choose_action)
                modified_data['actions'] = new_actions
            else:
                # If no trigger IDs, keep original actions but note the issue
                logger.warning("Cannot create 'choose' structure: no trigger IDs found")
    
    # Return the modified automation data
    return modified_data 