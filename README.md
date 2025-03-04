# AI Automation Creator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

This custom integration allows you to create Home Assistant automations using natural language descriptions powered by OpenAI's GPT-4.

## Features

- Create automations using natural language descriptions
- Automatically detects available entities in your Home Assistant instance
- Generates valid YAML configurations for automations
- Easy to use service call interface
- **Interactive UI with guided automation creation** - NEW!
- **Sidebar menu access for quick access** - NEW!

## Installation

### HACS Installation (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=yourusername&repository=ai-automation-creator&category=integration)

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Navigate to HACS → Integrations → Click the three dots in the upper right corner → Custom repositories.
3. Add this repository URL and select "Integration" as the category.
4. Click "ADD".
5. Search for "AI Automation Creator" and install it.
6. Restart Home Assistant.
7. Go to Settings → Devices & Services → Add Integration, and search for "AI Automation Creator".
8. Follow the configuration steps.

For detailed instructions, see [INSTALL.md](INSTALL.md).

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "AI Automation Creator"
4. Enter your OpenAI API key
5. Complete the setup

## Usage

You can create automations in three ways:

### 1. Using the Interactive UI (Recommended)

1. Click on the "AI Automation" icon in the sidebar menu
2. Follow the guided conversation to describe your automation needs
3. The AI will ask you specific questions to understand what you want
4. Review the generated automation and click "Create Automation"
5. Your automation is now available in Home Assistant!

### 2. Using the Service Call

You can call the service directly from Home Assistant:

```yaml
service: ai_automation_creator.create_automation
data:
  description: "Turn on the living room lights when motion is detected in the hallway"
```

### 3. Using the Developer Tools

1. Go to Developer Tools → Services
2. Select `ai_automation_creator.create_automation`
3. Enter your automation description in the `description` field
4. Click "Call Service"

## Example Descriptions

Here are some example descriptions you can use:

- "Turn off all lights when no motion is detected for 30 minutes"
- "Set the thermostat to 72°F when someone arrives home"
- "Turn on the porch light at sunset and off at sunrise"
- "Send a notification when the garage door has been open for more than 10 minutes"

## Requirements

- Home Assistant 2023.8 or later
- OpenAI API key
- HACS installed

## Container Support

This integration is fully compatible with Home Assistant running in a container. The integration operates entirely within the Home Assistant environment and doesn't require any external system access.

## Support

If you encounter any issues or have questions, please open an issue in the GitHub repository.

## License

MIT License 