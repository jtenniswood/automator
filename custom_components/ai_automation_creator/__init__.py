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

from homeassistant.core import HomeAssistant, ServiceCall, State
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
            5. Include an 'alias' that is VERY BRIEF and SUCCINCT (5 words or less).
            6. Include a descriptive 'description' field explaining what the automation does.
            7. Ensure all triggers have unique IDs that match their purpose or title.
            8. IMPORTANT: ONLY use entities that ACTUALLY EXIST in the system.
            9. If a trigger has an alias, use that alias (converted to snake_case) as its ID.
            
            Example format (do not include the id):
            ```
            alias: Lights On at Sunset
            description: Turns on the living room lights automatically when the sun sets
            trigger:
              - platform: sun
                event: sunset
                id: sunset_trigger
                alias: Sunset Trigger
            condition: []
            action:
              - service: light.turn_on
                target:
                  entity_id: light.living_room
            mode: single
            ```
            """
            
            try:
                # Get a list of existing entities in the system for validation
                existing_entities = []
                entity_info = []
                
                for state in hass.states.async_all():
                    entity_id = state.entity_id
                    existing_entities.append(entity_id)
                    
                    # Get entity friendly name and add to entity info
                    friendly_name = state.attributes.get("friendly_name", entity_id)
                    entity_data = {
                        "entity_id": entity_id,
                        "name": friendly_name,
                        "state": state.state
                    }
                    
                    # Add domain-specific attributes that might be helpful
                    if entity_id.startswith("light."):
                        entity_data["type"] = "light"
                    elif entity_id.startswith("switch."):
                        entity_data["type"] = "switch"
                    elif entity_id.startswith("sensor."):
                        entity_data["type"] = "sensor"
                        entity_data["unit"] = state.attributes.get("unit_of_measurement", "")
                    
                    entity_info.append(entity_data)
                
                _LOGGER.info(f"Found {len(existing_entities)} entities in Home Assistant")
                
                # Add entity information to the user prompt
                user_prompt = f"""Create automation: {description}
                
                Available entities (use ONLY these entities in your automation):
                {yaml.dump(entity_info[:50], default_flow_style=False)}
                
                {'' if len(entity_info) <= 50 else f'... and {len(entity_info) - 50} more entities'}
                """
                
                def call_openai():
                    return openai.chat.completions.create(
                        model=DEFAULT_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
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
                
                # Add the "automator" tag
                if "tags" in automation_data:
                    if "automator" not in automation_data["tags"]:
                        automation_data["tags"].append("automator")
                else:
                    automation_data["tags"] = ["automator"]
                
                # Validate and enhance the automation data
                try:
                    await enhance_automation(hass, automation_data)
                except Exception as enhance_error:
                    _LOGGER.error("Error enhancing automation: %s", str(enhance_error))
                
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

async def enhance_automation(hass, automation_data):
    """Enhance automation data with device information and validate entities."""
    _LOGGER.info("Enhancing automation data...")
    
    # Ensure all triggers have IDs
    if "trigger" in automation_data:
        for i, trigger in enumerate(automation_data["trigger"]):
            if "id" not in trigger:
                # Generate an ID based on the trigger alias or type/platform
                trigger_id = None
                
                # Use the trigger alias if available
                if "alias" in trigger:
                    trigger_id = re.sub(r'[^a-z0-9_]', '_', trigger["alias"].lower())
                    trigger_id = re.sub(r'_+', '_', trigger_id).strip('_')
                    if trigger_id:
                        trigger_id = f"{trigger_id}_trigger"
                
                # Fall back to trigger type if no alias or invalid alias
                if not trigger_id:
                    trigger_type = trigger.get("platform", "")
                    if not trigger_type and "type" in trigger:
                        trigger_type = trigger["type"]
                    if not trigger_type:
                        trigger_type = "trigger"
                    
                    trigger_id = f"{trigger_type}_{i+1}_trigger"
                
                trigger["id"] = trigger_id
                _LOGGER.info(f"Added ID '{trigger_id}' to trigger")
    
    # Find target devices and entities to get icon and area information
    target_entities = set()
    target_devices = set()
    
    # Extract entities from the automation
    extract_entities_from_dict(automation_data, target_entities, target_devices)
    
    # Validate entities exist in Home Assistant
    invalid_entities = []
    for entity_id in target_entities:
        state = hass.states.get(entity_id)
        if state is None:
            _LOGGER.warning(f"Entity '{entity_id}' does not exist in Home Assistant")
            invalid_entities.append(entity_id)
    
    if invalid_entities:
        warning_msg = f"The following entities do not exist: {', '.join(invalid_entities)}"
        _LOGGER.warning(warning_msg)
        automation_data["description"] = f"{automation_data.get('description', '')} WARNING: {warning_msg}"
    
    # Find primary entity for icon and area
    primary_entity = None
    
    # Prioritize entities in actions that actually exist in HA
    if "action" in automation_data:
        for candidate in find_entities_in_actions(automation_data["action"]):
            if hass.states.get(candidate) is not None:
                primary_entity = candidate
                break
    
    # If no valid entity found in actions, try triggers
    if not primary_entity and "trigger" in automation_data:
        for candidate in find_entities_in_triggers(automation_data["trigger"]):
            if hass.states.get(candidate) is not None:
                primary_entity = candidate
                break
    
    # If we found a primary entity, get its icon and area
    if primary_entity:
        state = hass.states.get(primary_entity)
        if state and hasattr(state, 'attributes'):
            # Get icon from entity
            if "icon" in state.attributes and "icon" not in automation_data:
                automation_data["icon"] = state.attributes["icon"]
                _LOGGER.info(f"Using icon '{state.attributes['icon']}' from entity '{primary_entity}'")
            
            try:
                # Get area from entity
                from homeassistant.helpers import area_registry as ar
                from homeassistant.helpers import device_registry as dr
                from homeassistant.helpers import entity_registry as er
                
                entity_reg = er.async_get(hass)
                entity_entry = entity_reg.async_get(primary_entity)
                
                if entity_entry and entity_entry.device_id:
                    device_reg = dr.async_get(hass)
                    device_entry = device_reg.async_get(entity_entry.device_id)
                    
                    if device_entry and device_entry.area_id:
                        area_reg = ar.async_get(hass)
                        area_entry = area_reg.async_get_area(device_entry.area_id)
                        
                        if area_entry:
                            # Store the area ID
                            automation_data["area_id"] = device_entry.area_id
                            _LOGGER.info(f"Using area ID '{device_entry.area_id}' from entity '{primary_entity}'")
            except Exception as area_error:
                _LOGGER.error(f"Error getting area for entity {primary_entity}: {str(area_error)}")

def extract_entities_from_dict(data, entity_set, device_set):
    """Recursively extract entity_ids and device_ids from a dictionary."""
    if not isinstance(data, dict):
        return
    
    # Check for entity_id
    if "entity_id" in data:
        entity_id = data["entity_id"]
        if isinstance(entity_id, str):
            entity_set.add(entity_id)
        elif isinstance(entity_id, list):
            for eid in entity_id:
                if isinstance(eid, str):
                    entity_set.add(eid)
    
    # Check for device_id
    if "device_id" in data:
        device_id = data["device_id"]
        if isinstance(device_id, str):
            device_set.add(device_id)
    
    # Recurse through all dictionary values
    for key, value in data.items():
        if isinstance(value, dict):
            extract_entities_from_dict(value, entity_set, device_set)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    extract_entities_from_dict(item, entity_set, device_set)

def find_entities_in_actions(actions):
    """Find all entities in the automation actions and return as a list."""
    entities = []
    
    for action in actions:
        if isinstance(action, dict):
            # Direct entity in the action
            if "entity_id" in action:
                entity_id = action["entity_id"]
                if isinstance(entity_id, str):
                    entities.append(entity_id)
                elif isinstance(entity_id, list):
                    entities.extend([e for e in entity_id if isinstance(e, str)])
            
            # Entity in target
            if "target" in action and isinstance(action["target"], dict) and "entity_id" in action["target"]:
                entity_id = action["target"]["entity_id"]
                if isinstance(entity_id, str):
                    entities.append(entity_id)
                elif isinstance(entity_id, list):
                    entities.extend([e for e in entity_id if isinstance(e, str)])
            
            # Recursively check nested dictionaries
            for key, value in action.items():
                if isinstance(value, dict):
                    entities.extend(find_entities_in_dict(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            entities.extend(find_entities_in_dict(item))
    
    return entities

def find_entities_in_triggers(triggers):
    """Find all entities in the automation triggers and return as a list."""
    entities = []
    
    for trigger in triggers:
        if isinstance(trigger, dict) and "entity_id" in trigger:
            entity_id = trigger["entity_id"]
            if isinstance(entity_id, str):
                entities.append(entity_id)
            elif isinstance(entity_id, list):
                entities.extend([e for e in entity_id if isinstance(e, str)])
    
    return entities

def find_entities_in_dict(data):
    """Find all entity_ids in a dictionary and return as a list."""
    entities = []
    if not isinstance(data, dict):
        return entities
    
    # Check for entity_id
    if "entity_id" in data:
        entity_id = data["entity_id"]
        if isinstance(entity_id, str):
            entities.append(entity_id)
        elif isinstance(entity_id, list):
            entities.extend([e for e in entity_id if isinstance(e, str)])
    
    # Recurse through all dictionary values
    for key, value in data.items():
        if isinstance(value, dict):
            entities.extend(find_entities_in_dict(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    entities.extend(find_entities_in_dict(item))
    
    return entities 