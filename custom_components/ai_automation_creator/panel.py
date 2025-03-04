"""Panel setup for AI Automation Creator."""
import logging
import os
from pathlib import Path
import voluptuous as vol
from homeassistant.components.frontend import async_register_built_in_panel

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ai_automation_creator"
PANEL_URL = "/ai-automation-creator"
PANEL_TITLE = "AI Automation Creator"
PANEL_ICON = "mdi:robot"

async def async_setup_panel(hass):
    """Set up the AI Automation Creator panel."""
    try:
        # Register the panel with the correct panel_custom configuration
        async_register_built_in_panel(
            hass,
            "iframe",
            PANEL_TITLE,
            PANEL_ICON,
            "ai-automation-creator",
            {"url": "/local/ai_automation_creator.html"},
            require_admin=False,
        )
        
        # Register static path for serving the www directory
        hass.http.register_static_path(
            "/ai_automation_creator_static",
            os.path.join(os.path.dirname(__file__), "www"),
        )
        
        # Create the HTML wrapper file if it doesn't exist
        www_dir = hass.config.path("www")
        html_path = os.path.join(www_dir, "ai_automation_creator.html")
        
        if not os.path.exists(html_path):
            with open(html_path, "w") as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Automation Creator</title>
    <script type="module" src="/local/ai_automation_creator.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: var(--paper-font-body1_-_font-family);
            background-color: var(--primary-background-color);
            color: var(--primary-text-color);
            height: 100vh;
        }
        ai-automation-creator {
            display: block;
            height: 100%;
        }
    </style>
</head>
<body>
    <ai-automation-creator></ai-automation-creator>
</body>
</html>
                """)
            _LOGGER.info("Created HTML wrapper at %s", html_path)
        
        _LOGGER.info("AI Automation Creator panel registered successfully")
        return True
    except Exception as e:
        _LOGGER.error("Failed to register panel: %s", str(e))
        return False 