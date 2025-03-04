# AI Automation Creator for Home Assistant

Create Home Assistant automations with natural language using OpenAI.

## Overview

AI Automation Creator is a custom integration for Home Assistant that allows you to create automations using natural language descriptions. Simply describe what you want your automation to do, and the integration will generate the necessary YAML code and add it to your configuration.

## Features

- **Natural Language Interface**: Describe your automation in plain English
- **OpenAI Integration**: Uses OpenAI's language models to convert descriptions into YAML
- **Simple Installation**: Easy setup through Home Assistant's UI
- **YAML Generation**: Automatically generates valid automation YAML
- **Sidebar Panel**: Dedicated sidebar panel for a smooth user experience

## Installation

### HACS Installation (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Go to HACS → Integrations → "+" button
3. Search for "AI Automation Creator" and install it
4. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/ai_automation_creator` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

After installation, add the integration through the Home Assistant UI:

1. Go to Configuration → Integrations
2. Click "+ Add Integration"
3. Search for "AI Automation Creator"
4. Enter your OpenAI API key

### Configuration Options

- **OpenAI API Key**: Your OpenAI API key (required)
- **Model**: The OpenAI model to use (default: gpt-3.5-turbo)

## Usage

1. After installation, you'll see the "AI Automation Creator" icon in your sidebar
2. Click on it to open the interface
3. Enter a description of the automation you want to create
4. Click "Create Automation"
5. The integration will generate the automation YAML and add it to your automations.yaml file

### Example Descriptions

- "Turn on the living room lights when motion is detected in the hallway after sunset"
- "Set the thermostat to 72°F when someone arrives home"
- "Send a notification when the front door has been open for more than 5 minutes"

## Troubleshooting

- **Panel Not Appearing**: Make sure you've restarted Home Assistant after installation
- **API Key Errors**: Verify your OpenAI API key is valid and has sufficient credits
- **YAML Generation Errors**: Try using more specific descriptions or different phrasing

## Support

If you encounter issues or have suggestions:

- Open an issue on GitHub
- Join the Home Assistant community forum

## License

This project is licensed under the MIT License - see the LICENSE file for details.
