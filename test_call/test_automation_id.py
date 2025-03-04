import yaml
import re
import datetime
import sys
import os

# Sample automation YAML that might be missing an ID
sample_automation = """
alias: Turn on lights at sunset
description: Turns on the living room lights when the sun sets
trigger:
  - platform: sun
    event: sunset
    offset: '+00:00:00'
condition: []
action:
  - service: light.turn_on
    data: {}
    target:
      entity_id: light.living_room
mode: single
"""

# Description that would be used to generate an ID
description = "Turn on lights at sunset"

def ensure_automation_has_id(automation_yaml, description):
    """Ensure the automation has an ID, generating one if needed."""
    try:
        # Parse the YAML
        automation_data = yaml.safe_load(automation_yaml)
        
        # Check if it already has an ID
        if "id" in automation_data:
            print(f"Automation already has ID: {automation_data['id']}")
            return automation_yaml
        
        print("No ID found in automation, generating one...")
        
        # Generate an ID based on the description
        base_id = re.sub(r'[^a-z0-9]', '_', description.lower())
        base_id = re.sub(r'_+', '_', base_id)  # Replace multiple underscores with a single one
        base_id = base_id.strip('_')[:40]  # Limit length and trim underscores at ends
        
        # Add a timestamp to ensure uniqueness
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        automation_id = f"ai_automation_{base_id}_{timestamp}"
        
        # Add the ID to the automation
        automation_data["id"] = automation_id
        
        # Regenerate the YAML
        updated_yaml = yaml.dump(automation_data, default_flow_style=False)
        
        print(f"Generated ID: {automation_id}")
        return updated_yaml
        
    except Exception as e:
        print(f"Error processing automation YAML: {e}")
        return automation_yaml

# Test the function
print("Original automation YAML:")
print(sample_automation)
print("\n" + "-"*50 + "\n")

updated_yaml = ensure_automation_has_id(sample_automation, description)

print("Updated automation YAML:")
print(updated_yaml)

# Now test with a sample that already has an ID
sample_with_id = """
id: existing_automation_id
alias: Turn on lights at sunset
description: Turns on the living room lights when the sun sets
trigger:
  - platform: sun
    event: sunset
    offset: '+00:00:00'
condition: []
action:
  - service: light.turn_on
    data: {}
    target:
      entity_id: light.living_room
mode: single
"""

print("\n" + "-"*50 + "\n")
print("Testing with automation that already has an ID:")
updated_yaml_2 = ensure_automation_has_id(sample_with_id, description)
print("Updated automation YAML (should keep existing ID):")
print(updated_yaml_2) 