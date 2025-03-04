/**
 * AI Automation Creator
 * Custom panel for creating Home Assistant automations with natural language
 */

// This ensures the Home Assistant connection is properly established
const hassConnection = document.querySelector('home-assistant');

class AiAutomationCreator extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.userInput = "";
    this.isProcessing = false;
    this.automationYaml = "";
    this.automationCreated = false;
    this.errorMessage = null;
    this._hass = null;
    
    // Try to get Home Assistant connection
    if (hassConnection) {
      hassConnection.addEventListener('hass-connect', (ev) => {
        this._hass = ev.detail.hass;
        this.render();
      });
    }
    
    // For standalone loading
    window.addEventListener('connection-status', (ev) => {
      if (ev.detail === 'connected') {
        // Get Home Assistant object from parent
        if (window.parent.document.querySelector('home-assistant')) {
          this._hass = window.parent.document.querySelector('home-assistant').hass;
          this.render();
        }
      }
    });
  }

  setConfig(config) {
    // Not used but required by HA
  }

  set hass(hass) {
    // Store hass object
    this._hass = hass;
    
    // Initial render if not done yet
    if (!this._hasRendered) {
      this._hasRendered = true;
      this.render();
    }
  }
  
  render() {
    if (!this._hass) {
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            font-family: var(--paper-font-body1_-_font-family);
            padding: 16px;
          }
        </style>
        <div>
          <h2>Loading Home Assistant connection...</h2>
          <p>If this message persists, please refresh the page.</p>
        </div>
      `;
      return;
    }
    
    // Prepare the content based on state
    let content = this.automationCreated ? this.renderResult() : this.renderForm();
    
    // Apply styles and content
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--paper-font-body1_-_font-family);
          padding: 16px;
        }
        .card {
          background-color: var(--card-background-color);
          border-radius: 8px;
          box-shadow: var(--ha-card-box-shadow);
          padding: 16px;
          max-width: 800px;
          margin: 0 auto;
        }
        h1 {
          font-size: 24px;
          margin-top: 0;
          margin-bottom: 16px;
          color: var(--primary-text-color);
        }
        p {
          margin-top: 0;
          margin-bottom: 12px;
          color: var(--secondary-text-color);
        }
        .examples {
          background-color: var(--secondary-background-color);
          border-radius: 8px;
          padding: 12px;
          margin: 12px 0;
        }
        textarea {
          width: 100%;
          min-height: 100px;
          padding: 8px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          margin: 8px 0 16px 0;
          background-color: var(--card-background-color);
          color: var(--primary-text-color);
        }
        button {
          background-color: var(--primary-color);
          color: var(--text-primary-color);
          border: none;
          border-radius: 4px;
          padding: 8px 16px;
          font-size: 14px;
          cursor: pointer;
          margin-right: 8px;
        }
        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .success {
          color: var(--success-color);
          margin: 16px 0;
        }
        .error {
          color: var(--error-color);
          margin: 16px 0;
        }
        .yaml-container {
          background-color: var(--code-background-color);
          padding: 16px;
          border-radius: 4px;
          overflow-x: auto;
          margin: 16px 0;
          position: relative;
        }
        pre {
          margin: 0;
          white-space: pre-wrap;
          font-family: monospace;
          overflow-x: auto;
          color: var(--primary-text-color);
          line-height: 1.4;
          /* Ensure YAML formatting is preserved */
          tab-size: 2;
        }
        #yaml-output {
          max-height: 400px;
          overflow-y: auto;
          padding: 8px 0;
          border-radius: 4px;
        }
        .button-container {
          display: flex;
          justify-content: flex-end;
        }
        .copy-button {
          position: absolute;
          top: 16px;
          right: 16px;
          background-color: var(--secondary-background-color);
          color: var(--primary-text-color);
          font-size: 12px;
          padding: 4px 8px;
        }
        .info-text {
          font-style: italic;
          margin-top: 0;
          font-size: 14px;
        }
        h3 {
          margin-top: 0;
          margin-bottom: 16px;
          padding-right: 60px; /* Make space for the copy button */
        }
      </style>
      <div class="card">
        <h1>AI Automation Creator</h1>
        ${content}
      </div>
    `;
    
    // Add event listeners
    if (!this.automationCreated) {
      const textarea = this.shadowRoot.querySelector('textarea');
      const button = this.shadowRoot.querySelector('button');
      
      if (textarea) {
        textarea.addEventListener('input', (e) => {
          this.userInput = e.target.value;
          if (button) {
            button.disabled = !this.userInput.trim();
          }
        });
      }
      
      if (button) {
        button.addEventListener('click', () => this.generateAutomation());
      }
    } else {
      const resetButton = this.shadowRoot.querySelector('button');
      if (resetButton) {
        resetButton.addEventListener('click', () => this.reset());
      }
      
      // Add copy button functionality
      const copyButton = this.shadowRoot.querySelector('#copy-yaml');
      if (copyButton) {
        copyButton.addEventListener('click', () => {
          const yamlText = this.shadowRoot.querySelector('#yaml-output').textContent;
          navigator.clipboard.writeText(yamlText).then(() => {
            copyButton.textContent = "Copied!";
            setTimeout(() => {
              copyButton.textContent = "Copy YAML";
            }, 2000);
          });
        });
      }
    }
  }
  
  renderForm() {
    return `
      <p>Describe what you want your automation to do in natural language. Include devices, triggers, conditions, and actions.</p>
      
      <div class="examples">
        <p><strong>Examples:</strong></p>
        <ul>
          <li>"Turn on living room lights when motion is detected in the hallway after sunset"</li>
          <li>"Set the thermostat to 72°F when someone arrives home"</li>
          <li>"Send a notification when the front door has been open for more than 5 minutes"</li>
        </ul>
      </div>
      
      <textarea placeholder="Describe your automation here...">${this.userInput}</textarea>
      
      <div class="button-container">
        <button ${this.isProcessing || !this.userInput ? 'disabled' : ''}>
          ${this.isProcessing ? 'Creating...' : 'Create Automation'}
        </button>
      </div>
      
      ${this.errorMessage ? `<div class="error">${this.errorMessage}</div>` : ''}
    `;
  }
  
  renderResult() {
    return `
      <div class="success">
        <p><strong>✓ Automation created successfully!</strong></p>
      </div>
      
      <div class="yaml-container">
        <h3>Generated Automation YAML:</h3>
        <pre id="yaml-output">${this.automationYaml}</pre>
        <button id="copy-yaml" class="copy-button">Copy YAML</button>
      </div>
      
      <p class="info-text">This automation has been automatically added to your automations.yaml file.</p>
      
      <div class="button-container">
        <button>Create Another Automation</button>
      </div>
    `;
  }
  
  generateAutomation() {
    if (!this.userInput.trim() || this.isProcessing) return;
    
    this.isProcessing = true;
    this.errorMessage = null;
    this.render();
    
    // Call service to create automation
    this._hass.callService("ai_automation_creator", "create_automation", {
      description: this.userInput,
    })
    .then(() => {
      // Wait a moment to ensure the service processes the request
      return new Promise(resolve => {
        setTimeout(() => {
          resolve();
        }, 2000); // Longer wait to ensure processing completes
      });
    })
    .then(() => {
      // Now call the service to get the YAML
      return this._hass.callService("ai_automation_creator", "get_automation_yaml", {});
    })
    .then((result) => {
      // Check if we can get the result directly
      if (result && result.yaml) {
        this.automationYaml = result.yaml;
        this.isProcessing = false;
        this.automationCreated = true;
        this.render();
        return;
      }
      
      // If direct result isn't available, try to get it from hass data
      return new Promise(resolve => {
        setTimeout(() => {
          try {
            // Check for success notification to confirm
            const notifications = this._hass.states;
            let automationCreated = false;
            
            Object.keys(notifications).forEach(key => {
              if (key.includes('persistent_notification.ai_automation_creator_success')) {
                automationCreated = true;
              }
            });
            
            // Try to get the automation from the get_automation_yaml service again
            this._hass.callService("ai_automation_creator", "get_automation_yaml", {})
              .then(result => {
                if (result && result.yaml) {
                  this.automationYaml = result.yaml;
                } else if (automationCreated) {
                  // If we can confirm it was created but don't have the YAML, show a message
                  this.automationYaml = "Automation was created successfully and added to your automations.yaml file.";
                } else {
                  // Fallback message if we can't find confirmation or YAML
                  this.automationYaml = "Automation has been processed. Please check your automations.yaml file.";
                }
                
                this.isProcessing = false;
                this.automationCreated = true;
                this.render();
                resolve();
              })
              .catch(error => {
                this.handleError(error);
                resolve();
              });
          } catch (error) {
            this.handleError(error);
            resolve();
          }
        }, 1000);
      });
    })
    .catch((error) => {
      this.handleError(error);
    });
  }
  
  handleError(error) {
    this.isProcessing = false;
    this.errorMessage = `Error: ${error.message || "Failed to create automation"}`;
    this.render();
  }
  
  reset() {
    this.userInput = "";
    this.automationYaml = "";
    this.automationCreated = false;
    this.errorMessage = null;
    this.render();
  }
}

// Register the element
customElements.define('ai-automation-creator', AiAutomationCreator);

// Tell Home Assistant this can be used as a custom card
window.customCards = window.customCards || [];
window.customCards.push({
  type: "ai-automation-creator",
  name: "AI Automation Creator",
  description: "Create automations using natural language"
}); 