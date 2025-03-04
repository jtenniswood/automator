// Direct import of lit-element to avoid module loading issues
const LitElement = window.LitElement || Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class AiAutomationCreator extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      panel: { type: Object },
      userInput: { type: String },
      isProcessing: { type: Boolean },
      automationYaml: { type: String },
      automationCreated: { type: Boolean },
      errorMessage: { type: String },
    };
  }

  constructor() {
    super();
    this.userInput = "";
    this.isProcessing = false;
    this.automationYaml = "";
    this.automationCreated = false;
    this.errorMessage = null;
  }

  render() {
    return html`
      <ha-card>
        <div class="card-content">
          <h2>AI Automation Creator</h2>
          
          ${this.automationCreated ? 
            this.renderResult() : 
            this.renderForm()}
        </div>
      </ha-card>
    `;
  }

  renderForm() {
    return html`
      <p>
        Describe what you want your automation to do in natural language. Include devices, 
        triggers, conditions, and actions.
      </p>
      
      <div class="examples">
        <p><strong>Examples:</strong></p>
        <ul>
          <li>"Turn on living room lights when motion is detected in the hallway after sunset"</li>
          <li>"Set the thermostat to 72°F when someone arrives home"</li>
          <li>"Send a notification when the front door has been open for more than 5 minutes"</li>
        </ul>
      </div>

      <div class="input-container">
        <textarea
          id="userInput"
          .value=${this.userInput}
          @input=${(e) => this.userInput = e.target.value}
          placeholder="Describe your automation here..."
          rows="5"
        ></textarea>
      </div>

      <div class="button-container">
        <mwc-button
          raised
          ?disabled=${!this.userInput || this.isProcessing}
          @click=${this.generateAutomation}
        >
          ${this.isProcessing ? "Creating..." : "Create Automation"}
        </mwc-button>
      </div>

      ${this.errorMessage ? html`
        <div class="error-message">
          ${this.errorMessage}
        </div>
      ` : ''}
    `;
  }

  renderResult() {
    return html`
      <div class="success-container">
        <p class="success-message">
          <ha-icon icon="mdi:check-circle"></ha-icon>
          Automation created successfully!
        </p>
        
        <div class="yaml-container">
          <h3>Generated Automation:</h3>
          <pre>${this.automationYaml}</pre>
        </div>
        
        <div class="button-container">
          <mwc-button raised @click=${this.reset}>
            Create Another Automation
          </mwc-button>
        </div>
      </div>
    `;
  }

  generateAutomation() {
    if (!this.userInput.trim()) return;
    
    this.isProcessing = true;
    this.errorMessage = null;
    
    // Call service to create automation
    this.hass.callService("ai_automation_creator", "create_automation", {
      description: this.userInput,
    })
    .then(() => {
      // Now get the automation YAML
      return this.hass.callService("ai_automation_creator", "get_automation_yaml", {});
    })
    .then(() => {
      // Wait a brief moment to make sure the data is updated
      setTimeout(() => {
        // Try to get the latest automation from hass data
        if (this.hass.data && this.hass.data.ai_automation_creator && 
            this.hass.data.ai_automation_creator.latest_automation) {
          this.automationYaml = this.hass.data.ai_automation_creator.latest_automation;
        } else {
          // Fallback - show generic message
          this.automationYaml = "Automation created successfully. Check your Home Assistant automations list.";
        }
        
        this.isProcessing = false;
        this.automationCreated = true;
        this.requestUpdate();
      }, 500);
    })
    .catch((error) => {
      this.isProcessing = false;
      this.errorMessage = `Error: ${error.message || "Failed to create automation"}`;
      this.requestUpdate();
    });
  }

  reset() {
    this.userInput = "";
    this.automationYaml = "";
    this.automationCreated = false;
    this.errorMessage = null;
    this.requestUpdate();
  }

  static get styles() {
    return css`
      :host {
        display: block;
        padding: 16px;
      }
      
      ha-card {
        max-width: 800px;
        margin: 0 auto;
        padding: 16px;
      }
      
      .card-content {
        padding: 0;
      }
      
      h2 {
        margin-top: 0;
        margin-bottom: 16px;
        color: var(--primary-text-color);
      }
      
      p {
        color: var(--primary-text-color);
        margin-top: 0;
      }
      
      .examples {
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 16px 0;
      }
      
      .examples ul {
        margin: 8px 0 0 0;
        padding-left: 20px;
      }
      
      .examples li {
        margin-bottom: 8px;
      }
      
      .input-container {
        margin: 16px 0;
      }
      
      textarea {
        width: 100%;
        min-height: 120px;
        padding: 12px;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        background-color: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 16px;
        resize: vertical;
        box-sizing: border-box;
      }
      
      textarea:focus {
        outline: none;
        border-color: var(--primary-color);
      }
      
      .button-container {
        display: flex;
        justify-content: flex-end;
        margin: 16px 0;
      }
      
      .error-message {
        color: var(--error-color);
        padding: 12px;
        border-radius: 4px;
        background-color: rgba(var(--rgb-error), 0.1);
        margin-top: 16px;
      }
      
      .success-container {
        display: flex;
        flex-direction: column;
      }
      
      .success-message {
        display: flex;
        align-items: center;
        color: var(--success-color);
        font-size: 18px;
        font-weight: 500;
      }
      
      .success-message ha-icon {
        --mdc-icon-size: 24px;
        margin-right: 8px;
      }
      
      .yaml-container {
        background-color: var(--code-background-color, #f5f5f5);
        border-radius: 4px;
        padding: 16px;
        margin: 16px 0;
        overflow-x: auto;
      }
      
      .yaml-container h3 {
        margin-top: 0;
        margin-bottom: 8px;
      }
      
      pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: monospace;
      }
    `;
  }
}

customElements.define("ai-automation-creator", AiAutomationCreator);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ai-automation-creator",
  name: "AI Automation Creator",
  description: "Create automations using natural language with AI assistance.",
}); 