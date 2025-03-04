import { LitElement, html, css } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class AiAutomationCreator extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      conversation: { type: Array },
      userInput: { type: String },
      isProcessing: { type: Boolean },
      automationYaml: { type: String },
      automationCreated: { type: Boolean },
      currentStep: { type: Number },
      automationSteps: { type: Array },
    };
  }

  constructor() {
    super();
    this.conversation = [];
    this.userInput = "";
    this.isProcessing = false;
    this.automationYaml = "";
    this.automationCreated = false;
    this.currentStep = 0;
    this.automationSteps = [
      { question: "What would you like this automation to do? (Describe in natural language)", answer: "" },
      { question: "When should this automation trigger? (Time, event, condition, etc.)", answer: "" },
      { question: "Which devices or entities should be involved?", answer: "" },
      { question: "Are there any conditions that should be met before the automation runs?", answer: "" },
      { question: "Is there anything else I should know about this automation?", answer: "" },
    ];
  }

  render() {
    if (!this.hass) {
      return html`<p>Loading...</p>`;
    }
    
    return html`
      <div class="card-container">
        <ha-card header="AI Automation Creator">
          <div class="card-content">
            ${this.automationCreated ? this.renderResult() : this.renderConversation()}
          </div>
        </ha-card>
      </div>
    `;
  }

  renderConversation() {
    return html`
      <div class="conversation">
        <div class="messages">
          ${this.conversation.map(
            (message) => html`
              <div class="message ${message.sender}">
                <div class="content">${message.content}</div>
              </div>
            `
          )}
        </div>

        ${this.isProcessing
          ? html`<div class="processing">Processing your request...</div>`
          : html`
              <div class="current-question">
                <h3>${this.automationSteps[this.currentStep].question}</h3>
              </div>
              
              <div class="input-container">
                <div class="input-row">
                  <textarea
                    id="userInputField"
                    class="user-input"
                    .value=${this.userInput}
                    @input=${(e) => (this.userInput = e.target.value)}
                    placeholder="Type your answer here..."
                    rows="3"
                  ></textarea>
                </div>
                
                <div class="button-row">
                  <mwc-button 
                    raised 
                    ?disabled=${!this.userInput}
                    @click=${this.handleSend}
                  >
                    Send
                  </mwc-button>
                </div>
              </div>
            `}

        ${this.currentStep >= this.automationSteps.length
          ? html`
              <div class="create-button-container">
                <mwc-button
                  raised
                  @click=${this.createAutomation}
                  ?disabled=${this.isProcessing}
                  class="create-button"
                >
                  Create Automation
                </mwc-button>
              </div>
            `
          : ""}
      </div>
    `;
  }

  renderResult() {
    return html`
      <div class="result">
        <div class="success-message">
          <ha-icon icon="mdi:check-circle" class="success-icon"></ha-icon>
          <div>Automation created successfully!</div>
        </div>

        <div class="yaml-preview">
          <pre>${this.automationYaml}</pre>
        </div>

        <div class="buttons">
          <mwc-button raised @click=${this.startOver}>Create Another</mwc-button>
        </div>
      </div>
    `;
  }

  handleSend() {
    if (!this.userInput.trim()) return;

    // Add user message to conversation
    this.conversation = [
      ...this.conversation,
      { sender: "user", content: this.userInput },
    ];

    // Save answer to current step
    this.automationSteps[this.currentStep].answer = this.userInput;
    
    // Clear input
    this.userInput = "";
    
    // Move to next step
    if (this.currentStep < this.automationSteps.length - 1) {
      this.currentStep++;
      
      // Add assistant question to conversation
      this.conversation = [
        ...this.conversation,
        { sender: "assistant", content: this.automationSteps[this.currentStep].question },
      ];
    } else {
      this.currentStep = this.automationSteps.length;
    }
    
    // Force update to reflect changes
    this.requestUpdate();
  }

  createAutomation() {
    this.isProcessing = true;
    
    // Prepare the description by combining all answers
    let fullDescription = "";
    this.automationSteps.forEach(step => {
      fullDescription += `${step.question}\n${step.answer}\n\n`;
    });
    
    // Call the service to create automation
    this.hass.callService("ai_automation_creator", "create_automation", {
      description: fullDescription,
    }).then(
      (result) => {
        // Get the result from backend (the created automation YAML)
        this.conversation = [
          ...this.conversation,
          { 
            sender: "assistant", 
            content: "I've created your automation! You can find it in your automations.yaml file or in the automation editor." 
          },
        ];
        this.automationCreated = true;
        this.isProcessing = false;
        
        // Get the latest automation from Home Assistant
        this.hass.callApi("GET", "config/automation/config/0").then(
          (automation) => {
            this.automationYaml = JSON.stringify(automation, null, 2);
          }
        ).catch(error => {
          this.automationYaml = "Automation created successfully, but couldn't retrieve the YAML.";
          console.error("Failed to retrieve automation:", error);
        });
      },
      (error) => {
        this.conversation = [
          ...this.conversation,
          { 
            sender: "assistant", 
            content: "Sorry, there was an error creating your automation: " + error.message 
          },
        ];
        this.isProcessing = false;
      }
    );
  }

  startOver() {
    this.conversation = [];
    this.userInput = "";
    this.automationYaml = "";
    this.automationCreated = false;
    this.currentStep = 0;
    this.automationSteps.forEach(step => step.answer = "");
    
    // Add first question to conversation
    this.conversation = [
      { sender: "assistant", content: this.automationSteps[0].question },
    ];
    
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
      
      .conversation {
        display: flex;
        flex-direction: column;
        height: 100%;
      }
      
      .messages {
        margin-bottom: 24px;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        padding: 16px;
        background-color: var(--card-background-color, #fff);
      }
      
      .message {
        margin-bottom: 12px;
        padding: 10px 14px;
        border-radius: 8px;
        max-width: 80%;
        word-break: break-word;
      }
      
      .message.user {
        background-color: var(--primary-color);
        color: var(--text-primary-color, white);
        align-self: flex-end;
        margin-left: auto;
      }
      
      .message.assistant {
        background-color: var(--secondary-background-color);
        color: var(--primary-text-color);
        align-self: flex-start;
      }
      
      .current-question {
        margin-bottom: 16px;
      }
      
      .current-question h3 {
        margin: 0;
        font-size: 18px;
        color: var(--primary-text-color);
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
        padding: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-style: italic;
        color: var(--secondary-text-color);
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        margin-bottom: 16px;
      }
      
      .create-button-container {
        display: flex;
        justify-content: center;
        margin-top: 16px;
      }
      
      .create-button {
        --mdc-theme-primary: var(--success-color, #4CAF50);
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
        .message {
          max-width: 95%;
        }
      }
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    
    // Start the conversation with the first question
    if (this.conversation.length === 0) {
      this.conversation = [
        { sender: "assistant", content: this.automationSteps[0].question },
      ];
    }
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