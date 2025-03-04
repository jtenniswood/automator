import { LitElement, html, css } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class AiAutomationCreator extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      userInput: { type: String },
      isProcessing: { type: Boolean },
      automationYaml: { type: String },
      automationCreated: { type: Boolean },
      resultMessage: { type: String },
    };
  }

  constructor() {
    super();
    this.userInput = "";
    this.isProcessing = false;
    this.automationYaml = "";
    this.automationCreated = false;
    this.resultMessage = "";
  }

  render() {
    if (!this.hass) {
      return html`<p>Loading...</p>`;
    }
    
    return html`
      <div class="card-container">
        <ha-card header="AI Automation Creator">
          <div class="card-content">
            ${this.automationCreated ? this.renderResult() : this.renderPrompt()}
          </div>
        </ha-card>
      </div>
    `;
  }

  renderPrompt() {
    return html`
      <div class="automation-creator">
        <div class="prompt-container">
          <h3>Describe the automation you want to create</h3>
          <p>
            Describe what you want your automation to do in natural language. Include any devices, 
            triggers, conditions, and actions that should be part of your automation.
          </p>
          
          <div class="examples">
            <p class="examples-header">Examples:</p>
            <ul>
              <li>"Turn on the living room lights when motion is detected in the hallway, but only if it's after sunset"</li>
              <li>"Set the thermostat to 72°F when someone arrives home"</li>
              <li>"Send a notification when the front door has been open for more than 5 minutes"</li>
            </ul>
          </div>

          <div class="input-container">
            <div class="input-row">
              <textarea
                id="userInputField"
                class="user-input"
                .value=${this.userInput}
                @input=${(e) => (this.userInput = e.target.value)}
                placeholder="Describe your automation here..."
                rows="5"
              ></textarea>
            </div>
            
            <div class="button-row">
              <mwc-button 
                raised 
                ?disabled=${!this.userInput}
                @click=${this.createAutomation}
              >
                Create Automation
              </mwc-button>
            </div>
          </div>
        </div>

        ${this.isProcessing
          ? html`
              <div class="processing">
                <div class="processing-spinner"></div>
                <div class="processing-text">Creating your automation...</div>
              </div>
            `
          : ''}
      </div>
    `;
  }

  renderResult() {
    return html`
      <div class="result">
        <div class="success-message">
          <ha-icon icon="mdi:check-circle" class="success-icon"></ha-icon>
          <div>${this.resultMessage}</div>
        </div>

        <div class="yaml-preview">
          <h3>Automation YAML</h3>
          <pre>${this.automationYaml}</pre>
        </div>

        <div class="buttons">
          <mwc-button raised @click=${this.startOver}>Create Another</mwc-button>
        </div>
      </div>
    `;
  }

  createAutomation() {
    if (!this.userInput.trim()) return;
    
    this.isProcessing = true;
    
    // Call the service to create automation
    this.hass.callService("ai_automation_creator", "create_automation", {
      description: this.userInput.trim(),
    }).then(
      (result) => {
        // Success
        this.resultMessage = "Automation created successfully! You can find it in your automations.yaml file or in the automation editor.";
        this.isProcessing = false;
        this.automationCreated = true;
        
        // Get the latest automation 
        if (this.hass.states["persistent_notification.ai_automation_creator_success"]) {
          // We have a notification with the automation
          this.automationYaml = this.hass.data?.ai_automation_creator?.latest_automation || 
                               "Automation created successfully. The YAML is available in your Home Assistant automations.yaml file.";
        } else {
          // Try to get it from the hass data
          this.automationYaml = this.hass.data?.ai_automation_creator?.latest_automation || 
                               "Automation created successfully. The YAML is available in your Home Assistant automations.yaml file.";
        }
      },
      (error) => {
        // Error
        this.resultMessage = `Error creating automation: ${error.message || "Unknown error"}`;
        this.isProcessing = false;
        this.automationCreated = true;
        this.automationYaml = "Failed to create automation. Please try again with a more detailed description.";
      }
    );
    
    // Force update
    this.requestUpdate();
  }

  startOver() {
    this.userInput = "";
    this.automationYaml = "";
    this.automationCreated = false;
    this.resultMessage = "";
    
    // Force update
    this.requestUpdate();
  }

  static get styles() {
    return css`
      :host {
        display: block;
        padding: 16px;
      }
      
      .card-container {
        max-width: 800px;
        margin: 0 auto;
      }
      
      ha-card {
        width: 100%;
        margin-bottom: 16px;
      }
      
      .card-content {
        padding: 16px;
      }
      
      .automation-creator {
        display: flex;
        flex-direction: column;
      }
      
      .prompt-container {
        margin-bottom: 24px;
      }
      
      .prompt-container h3 {
        margin-top: 0;
        margin-bottom: 8px;
        color: var(--primary-text-color);
      }
      
      .prompt-container p {
        margin-top: 0;
        margin-bottom: 16px;
        color: var(--secondary-text-color);
      }
      
      .examples {
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 24px;
      }
      
      .examples-header {
        font-weight: 500;
        margin-top: 0;
        margin-bottom: 8px;
      }
      
      .examples ul {
        margin: 0;
        padding-left: 24px;
      }
      
      .examples li {
        margin-bottom: 8px;
        font-style: italic;
      }
      
      .examples li:last-child {
        margin-bottom: 0;
      }
      
      .input-container {
        display: flex;
        flex-direction: column;
        margin-bottom: 16px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        overflow: hidden;
      }
      
      .input-row {
        display: flex;
        width: 100%;
      }
      
      .user-input {
        width: 100%;
        min-height: 60px;
        padding: 12px;
        border: none;
        background-color: var(--card-background-color, #fff);
        color: var(--primary-text-color);
        font-size: 16px;
        resize: vertical;
      }
      
      .user-input:focus {
        outline: none;
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      
      .button-row {
        display: flex;
        justify-content: flex-end;
        padding: 8px;
        background-color: var(--secondary-background-color);
      }
      
      .processing {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 24px;
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        margin-top: 16px;
      }
      
      .processing-spinner {
        width: 32px;
        height: 32px;
        margin-bottom: 16px;
        border: 3px solid var(--divider-color);
        border-top: 3px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1.5s linear infinite;
      }
      
      .processing-text {
        font-style: italic;
        color: var(--secondary-text-color);
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      .result {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      
      .success-message {
        display: flex;
        align-items: center;
        margin-bottom: 24px;
        color: var(--success-color, #4CAF50);
        font-size: 18px;
      }
      
      .success-icon {
        margin-right: 8px;
        --mdc-icon-size: 24px;
      }
      
      .yaml-preview {
        width: 100%;
        background-color: var(--code-background-color, #f5f5f5);
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        overflow-x: auto;
      }
      
      .yaml-preview h3 {
        margin-top: 0;
        margin-bottom: 16px;
      }
      
      pre {
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: monospace;
        font-size: 14px;
      }
      
      .buttons {
        display: flex;
        gap: 8px;
      }
      
      @media (max-width: 600px) {
        .card-content {
          padding: 12px;
        }
      }
    `;
  }

  connectedCallback() {
    super.connectedCallback();
  }
  
  // This is called when panel is first created
  setConfig(config) {
    // Nothing to configure
  }
}

customElements.define("ai-automation-creator", AiAutomationCreator);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ai-automation-creator",
  name: "AI Automation Creator",
  description: "Create automations using natural language with AI assistance.",
}); 