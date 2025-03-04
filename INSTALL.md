# Installation

## HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Navigate to HACS → Integrations → Click the three dots in the upper right corner → Custom repositories.
3. Add this repository URL (`https://github.com/yourusername/ai-automation-creator`) and select "Integration" as the category.
4. Click "ADD".
5. Search for "AI Automation Creator" and install it.
6. Restart Home Assistant.
7. Go to Settings → Devices & Services → Add Integration, and search for "AI Automation Creator".
8. Follow the configuration steps.

## Manual Installation

If you prefer to install manually:

1. Download the latest release from GitHub.
2. Extract the contents to your Home Assistant config folder under `custom_components/ai_automation_creator`.
3. Restart Home Assistant.
4. Go to Settings → Devices & Services → Add Integration, and search for "AI Automation Creator".
5. Follow the configuration steps.

# Requirements

- Home Assistant 2023.8.0 or later
- An OpenAI API key with access to GPT-4 models
- HACS for easy installation (recommended) 