import yaml
import copy
import re
import time
import sys
import os

# Function from the integration to test
def ensure_automation_structure(automation_data, logger=None):
    """
    Ensure the automation has the required structure with trigger IDs and choose elements.
    If not, transform it to match the required structure.
    """
    # Simple logger if none provided
    class SimpleLogger:
        def info(self, msg):
            print(f"INFO: {msg}")
        def warning(self, msg):
            print(f"WARNING: {msg}")
        def error(self, msg):
            print(f"ERROR: {msg}")
    
    if logger is None:
        logger = SimpleLogger()
    
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

# Test case 1: Basic automation with trigger and action (no IDs, no choose)
test_1 = {
    'alias': 'Turn on lights at sunset',
    'description': 'Turns on the living room lights automatically when the sun sets',
    'trigger': [
        {
            'platform': 'sun',
            'event': 'sunset',
            'offset': '+00:00:00'
        }
    ],
    'condition': [],
    'action': [
        {
            'service': 'light.turn_on',
            'data': {},
            'target': {
                'entity_id': 'light.living_room'
            }
        }
    ],
    'mode': 'single'
}

# Test case 2: Multiple triggers without IDs
test_2 = {
    'alias': 'Turn on lights',
    'description': 'Turns on lights based on motion or time',
    'trigger': [
        {
            'platform': 'state',
            'entity_id': 'binary_sensor.motion',
            'to': 'on'
        },
        {
            'platform': 'time',
            'at': '17:00:00'
        }
    ],
    'condition': [],
    'action': [
        {
            'service': 'light.turn_on',
            'target': {
                'entity_id': 'light.living_room'
            }
        }
    ],
    'mode': 'single'
}

# Test case 3: Already properly formatted
test_3 = {
    'alias': 'Properly formatted automation',
    'description': 'This automation already has the correct structure',
    'triggers': [
        {
            'id': 'motion_detected',
            'platform': 'state',
            'entity_id': 'binary_sensor.motion',
            'to': 'on'
        }
    ],
    'conditions': [],
    'actions': [
        {
            'choose': [
                {
                    'conditions': [
                        {
                            'condition': 'trigger',
                            'id': 'motion_detected'
                        }
                    ],
                    'sequence': [
                        {
                            'service': 'light.turn_on',
                            'target': {
                                'entity_id': 'light.living_room'
                            }
                        }
                    ]
                }
            ]
        }
    ],
    'mode': 'single'
}

# Run tests
test_cases = [
    ('Basic automation (trigger, no IDs)', test_1),
    ('Multiple triggers without IDs', test_2),
    ('Already properly formatted', test_3)
]

for test_name, test_data in test_cases:
    print(f"\n\n{'='*80}\nTEST: {test_name}\n{'='*80}")
    
    print("\nOriginal automation:")
    print(yaml.dump(test_data, default_flow_style=False))
    
    # Apply structure validation
    corrected_data = ensure_automation_structure(test_data)
    
    print("\nCorrected automation:")
    print(yaml.dump(corrected_data, default_flow_style=False))
    
    # Verify key structural elements
    print("\nVerification:")
    
    # Check for 'triggers' (plural)
    if 'triggers' in corrected_data:
        print("✅ Has 'triggers' (plural)")
    else:
        print("❌ Missing 'triggers' (plural)")
    
    # Check for trigger IDs
    has_trigger_ids = True
    for trigger in corrected_data.get('triggers', []):
        if 'id' not in trigger:
            has_trigger_ids = False
            break
    
    if has_trigger_ids:
        print("✅ All triggers have IDs")
    else:
        print("❌ Some triggers are missing IDs")
    
    # Check for 'actions' (plural)
    if 'actions' in corrected_data:
        print("✅ Has 'actions' (plural)")
    else:
        print("❌ Missing 'actions' (plural)")
    
    # Check for 'choose' structure
    has_choose = False
    for action in corrected_data.get('actions', []):
        if isinstance(action, dict) and 'choose' in action:
            has_choose = True
            break
    
    if has_choose:
        print("✅ Has 'choose' structure in actions")
    else:
        print("❌ Missing 'choose' structure in actions") 