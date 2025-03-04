import yaml
import time
import os

# Sample automation YAML (without ID)
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

def format_automation_for_file(automation_yaml):
    """Format automation YAML for automations.yaml file."""
    try:
        # Parse the YAML
        automation_data = yaml.safe_load(automation_yaml)
        
        # Generate a 13-digit numerical ID
        automation_id = str(int(time.time() * 1000))  # Current time in milliseconds as a 13-digit number
        print(f"Generated ID: {automation_id} (Length: {len(automation_id)})")
        
        # Add the ID to the automation
        automation_data["id"] = automation_id
        
        # Convert back to YAML
        single_automation_yaml = yaml.dump(automation_data, default_flow_style=False)
        
        # Format for automations.yaml (with leading dash and indentation)
        lines = single_automation_yaml.strip().split('\n')
        formatted_lines = [f"- {lines[0]}"]
        
        # Indent the rest by 2 spaces
        for line in lines[1:]:
            formatted_lines.append('  ' + line)
        
        indented_automation = '\n'.join(formatted_lines)
        
        return indented_automation
    except Exception as e:
        print(f"Error formatting automation: {e}")
        return None

# Create a test automations.yaml file
def create_test_file(formatted_yaml):
    """Create a test automations.yaml file with the formatted automation."""
    test_file_path = "test_call/test_automations.yaml"
    
    with open(test_file_path, "w") as f:
        f.write("# Test Automations File\n\n")
        f.write(formatted_yaml)
        
    print(f"Test file created: {test_file_path}")
    return test_file_path

# Append a second automation to the file
def append_automation(file_path, formatted_yaml):
    """Append another automation to the file."""
    with open(file_path, "a") as f:
        f.write("\n\n# Another automation\n")
        f.write(formatted_yaml)
    
    print(f"Appended second automation to file: {file_path}")

# Test the functions
print("Original automation YAML (without ID):")
print(sample_automation)
print("\n" + "-"*50 + "\n")

# Format the first automation
formatted_automation_1 = format_automation_for_file(sample_automation)
print("Formatted automation YAML (with 13-digit ID, ready for automations.yaml):")
print(formatted_automation_1)

# Create test file with the first automation
test_file = create_test_file(formatted_automation_1)

# Simulate a delay before adding a second automation
print("\nWaiting 1 second before adding second automation...\n")
time.sleep(1)

# Format and append a second automation (same content, but will get a new ID)
formatted_automation_2 = format_automation_for_file(sample_automation)
append_automation(test_file, formatted_automation_2)

print("\n" + "-"*50 + "\n")
print("Final test file content:")
with open(test_file, "r") as f:
    print(f.read())

print("\nNote: Each automation has a unique 13-digit numerical ID based on the current timestamp.") 