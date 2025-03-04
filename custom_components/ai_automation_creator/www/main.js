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
    return html`
      <ha-card header="AI Automation Creator">
        <div class="card-content">
          ${this.automationCreated ? this.renderResult() : this.renderConversation()}
        </div>
      </ha-card>
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
          ? html`<div class="processing">Processing...</div>`
          : html`
              <div class="current-question">
                ${this.automationSteps[this.currentStep].question}
              </div>
              <div class="input-row">
                <ha-textarea
                  .value=${this.userInput}
                  @input=${(e) => (this.userInput = e.target.value)}
                  placeholder="Type your answer here..."
                  autogrow
                ></ha-textarea>
                <ha-icon-button
                  .disabled=${!this.userInput}
                  @click=${this.handleSend}
                  path="M2,21L23,12L2,3V10L17,12L2,14V21Z"
                ></ha-icon-button>
              </div>
            `}

        ${this.currentStep >= this.automationSteps.length
          ? html`
              <ha-button
                @click=${this.createAutomation}
                .disabled=${this.isProcessing}
                class="create-button"
              >
                Create Automation
              </ha-button>
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
          <ha-button @click=${this.startOver}>Create Another</ha-button>
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
        );
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
  }

  static get styles() {
    return css`
      ha-card {
        max-width: 800px;
        margin: 0 auto;
        padding: 16px;
      }
      
      .conversation {
        display: flex;
        flex-direction: column;
        height: 100%;
      }
      
      .messages {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 16px;
      }
      
      .message {
        margin-bottom: 8px;
        padding: 8px 12px;
        border-radius: 8px;
        max-width: 80%;
      }
      
      .message.user {
        background-color: var(--primary-color);
        color: white;
        align-self: flex-end;
        margin-left: auto;
      }
      
      .message.assistant {
        background-color: var(--secondary-background-color);
        color: var(--primary-text-color);
        align-self: flex-start;
      }
      
      .current-question {
        margin-bottom: 8px;
        font-weight: 500;
      }
      
      .input-row {
        display: flex;
        align-items: flex-end;
      }
      
      ha-textarea {
        flex: 1;
        min-height: 56px;
      }
      
      .processing {
        padding: 16px;
        display: flex;
        justify-content: center;
        font-style: italic;
      }
      
      .create-button {
        margin-top: 16px;
        align-self: center;
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
        color: var(--success-color);
        font-size: 18px;
      }
      
      .success-icon {
        margin-right: 8px;
        --mdc-icon-size: 24px;
      }
      
      .yaml-preview {
        width: 100%;
        background-color: var(--code-background-color, #f0f0f0);
        padding: 16px;
        border-radius: 4px;
        margin-bottom: 24px;
        overflow-x: auto;
      }
      
      pre {
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
      
      .buttons {
        display: flex;
        gap: 8px;
      }
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    // Start the conversation with the first question
    this.conversation = [
      { sender: "assistant", content: this.automationSteps[0].question },
    ];
  }
}

customElements.define("ai-automation-creator", AiAutomationCreator);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ai-automation-creator",
  name: "AI Automation Creator",
  description: "Create automations using natural language with AI assistance.",
}); 