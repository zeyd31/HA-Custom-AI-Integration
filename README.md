# Custom LLM Conversation Agent for Home Assistant

A versatile Home Assistant integration that connects any OpenAI-compatible LLM API endpoint as a conversation agent, enabling intelligent voice and text interactions with your smart home.

## Features

- 🤖 **Universal LLM Support**: Works with any OpenAI-compatible API (Ollama, Mistral, OpenAI, Claude, etc.)
- 🏠 **Smart Home Context**: Automatically includes information about your devices and entities
- 🌐 **Multi-Language Support**: Configurable for any language (German, English, French, etc.)
- 🗣️ **Voice Assistant Integration**: Works with Home Assistant's voice assistant pipeline
- 💬 **Dashboard Integration**: Add conversation cards to your dashboard
- 🔧 **Fully Configurable**: Customize API endpoint, model, tokens, temperature, and more
- 📱 **Conversation History**: Maintains context across multiple interactions
- 🔐 **Secure**: API keys stored securely in Home Assistant

## Requirements

- Home Assistant 2023.5 or later
- Access to any OpenAI-compatible LLM API endpoint
- Valid API key for your chosen LLM service

## Installation

### Method 1: Manual Installation

1. **Download the integration**:
   - Copy the `custom_llm_conversation` folder to your `custom_components` directory
   - Your structure should look like: `/config/custom_components/custom_llm_conversation/`

2. **Required files**:
   ```
   custom_components/custom_llm_conversation/
   ├── __init__.py
   ├── conversation.py
   ├── config_flow.py
   └── manifest.json
   ```

3. **Restart Home Assistant**

### Method 2: HACS (if published)

1. Open HACS
2. Search for "Custom LLM Conversation Agent"
3. Install and restart Home Assistant

## Configuration

### UI Configuration

1. **Add Integration**:
   - Go to **Settings** → **Devices & Services**
   - Click **"+ Add Integration"**
   - Search for **"Custom LLM Conversation"**

2. **Configure Settings**:
   - **Name**: Display name for your assistant (e.g., "My LLM Assistant")
   - **API Key**: Your LLM service API key
   - **Base URL**: API endpoint URL (see examples below)
   - **Model**: Model name (depends on your service)
   - **Max Tokens**: Maximum response length (default: 300)
   - **Temperature**: Response creativity (0-2, default: 0.7)

## Usage

### Voice Assistant Setup

1. **Create Voice Assistant**:
   - Go to **Settings** → **Voice assistants**
   - Click **"Add Assistant"**
   - Select **"Custom LLM Conversation"** as conversation agent
   - Configure language and speech settings

2. **Set as Default** (optional):
   - Click three dots next to your assistant
   - Select **"Make Default"**

### Dashboard Integration

Add a conversation card to your dashboard:

```yaml
type: conversation
title: "LLM Assistant"
conversation_agent: conversation.custom_llm_conversation_[ID]
```

### Developer Tools Testing

Test the conversation agent directly:

```yaml
service: conversation.process
data:
  text: "How many lights do I have?"
  agent_id: conversation.custom_llm_conversation_[ID]
```

## Supported LLM Providers

This integration works with any OpenAI-compatible API endpoint:

### Ollama (Local)
- **Base URL**: `http://localhost:11434/api` or `https://your-ollama-server.com/api`
- **Models**: `mistral:7b`, `llama2`, `codellama`, etc.
- **API Key**: Usually not required (use any placeholder)

### Mistral AI
- **Base URL**: `https://api.mistral.ai/v1`
- **Models**: `mistral-tiny`, `mistral-small`, `mistral-medium`
- **API Key**: Your Mistral API key

### OpenAI
- **Base URL**: `https://api.openai.com/v1`
- **Models**: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`
- **API Key**: Your OpenAI API key

### Local LM Studio
- **Base URL**: `http://localhost:1234/v1`
- **Models**: Any model loaded in LM Studio
- **API Key**: Usually `lm-studio` (placeholder)

### Anthropic Claude (via OpenAI-compatible proxy)
- **Base URL**: Depends on proxy service
- **Models**: `claude-3-sonnet`, `claude-3-haiku`
- **API Key**: Your Anthropic API key

### Custom/Self-hosted
- **Base URL**: Your custom endpoint URL
- **Models**: Whatever your service supports
- **API Key**: Your service's API key

## Configuration Examples

### Ollama Setup (Local Mistral)
```yaml
Name: Local Mistral
API Key: not-required
Base URL: http://localhost:11434/api
Model: mistral:7b
Max Tokens: 500
Temperature: 0.1
```

### OpenAI GPT-4
```yaml
Name: GPT-4 Assistant
API Key: sk-your-openai-api-key
Base URL: https://api.openai.com/v1
Model: gpt-4-turbo
Max Tokens: 300
Temperature: 0.7
```

### Mistral Cloud API
```yaml
Name: Mistral Cloud
API Key: your-mistral-api-key
Base URL: https://api.mistral.ai/v1
Model: mistral-small
Max Tokens: 400
Temperature: 0.5
```

### LM Studio (Local)
```yaml
Name: LM Studio Local
API Key: lm-studio
Base URL: http://localhost:1234/v1
Model: your-loaded-model-name
Max Tokens: 600
Temperature: 0.2
```

## Smart Home Context

The integration automatically provides context about your Home Assistant setup:

- **Device counts** by domain (lights, switches, sensors, etc.)
- **Available entities** and their current states
- **System information** relevant to user queries

This enables intelligent responses like:
- "You have 12 lights in your system, 3 are currently on"
- "Your motion sensor in the living room is currently active"
- "You have 5 automation rules configured"

## Automation Integration

Use in automations for dynamic responses:

```yaml
automation:
  - alias: "Ask about lights when motion detected"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_living_room
        to: "on"
    action:
      - service: conversation.process
        data:
          text: "What lights are on in the living room?"
          agent_id: conversation.custom_llm_conversation_12345
      - service: notify.mobile_app
        data:
          message: "{{ states.conversation.last_response.state }}"
```

## Troubleshooting

### Integration Not Loading
- Check Home Assistant logs for errors
- Verify all required files are present
- Ensure Home Assistant version compatibility (2023.5+)

### Conversation Agent Not Appearing
- Restart Home Assistant completely  
- Check **Developer Tools** → **States** for conversation entities
- Verify integration shows as "Loaded" in Devices & Services

### API Connection Issues
- Test API endpoint manually with curl:
  ```bash
  curl -X POST "YOUR_BASE_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    -d '{"model": "YOUR_MODEL", "messages": [{"role": "user", "content": "Hello"}]}'
  ```
- Verify API key and base URL are correct
- Check network connectivity from Home Assistant
- Ensure the API endpoint supports OpenAI-compatible format

### No Responses
- Check logs for API errors  
- Verify model name is correct for your service
- Test with simpler queries first
- Check if API has rate limits or usage restrictions
- Verify API key has sufficient permissions

### Model-Specific Issues
- **Ollama**: Ensure model is downloaded (`ollama pull mistral:7b`)
- **OpenAI**: Check API key permissions and billing status
- **Local models**: Verify model is loaded and server is running
- **Custom endpoints**: Confirm endpoint follows OpenAI API format

## Development

### File Structure
```
custom_components/custom_llm_conversation/
├── __init__.py          # Integration setup and platform loading
├── conversation.py      # Conversation agent implementation  
├── config_flow.py       # UI configuration flow
└── manifest.json        # Integration metadata and requirements
```

### Key Components
- **ConversationEntity**: Main conversation processing and API communication
- **ConfigFlow**: UI configuration interface for API settings
- **Home Assistant Context**: Automatic device information gathering and formatting
- **API Handler**: Generic OpenAI-compatible API client

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the [Home Assistant Community Forum](https://community.home-assistant.io/)
- Report bugs via GitHub Issues
- Check logs in **Settings** → **System** → **Logs**

## Changelog

### v1.0.0
- Initial release
- Basic conversation agent functionality
- German language optimization
- Smart home context integration
- UI configuration support
