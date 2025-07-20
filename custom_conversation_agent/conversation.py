"""Conversation support for LLM AI assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Literal

import requests

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

_LOGGER = logging.getLogger(__name__)

DOMAIN = "custom_conversation_agent"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = MistralConversationEntity(config_entry)
    async_add_entities([agent])


class MistralConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """LLM Conversation Agent Entity."""
    
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = entry
        self.history: dict[str, list[dict]] = {}
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="AI Assistant",
            model="Mistral",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        
        # Get configuration from config entry
        self._entry_name = entry.data.get("name", "AI Assistant")
        self.api_key = entry.data.get("api_key", "")
        self.base_url = entry.data.get("base_url", "")
        self.model = entry.data.get("model", "")
        self.max_tokens = entry.data.get("max_tokens", 300)
        self.temperature = entry.data.get("temperature", 0.7)
        self.extra_system_prompt: str = (
            entry.options.get("system_prompt")
            or entry.data.get("system_prompt", "")
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._entry_name
    
    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        self.entry.async_on_unload(
            self.entry.add_update_listener(self._async_entry_update_listener)
        )

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        user_id = user_input.context.user_id or "default"
        conversation_id = user_input.conversation_id or ulid.ulid()
        
        if user_id not in self.history:
            self.history[user_id] = []
        
        # Get Home Assistant context
        ha_context = await self._get_ha_context()
        
        # Build system prompt with HA context
        system_prompt = f"""Du bist ein intelligenter Hausautomatisierungs-Assistent für Home Assistant.

Aktuelle Informationen über das Smart Home:
{ha_context}

Deine Aufgaben:
- Beantworte Fragen über Smart-Home-Geräte und deren Status
- Gib hilfreiche Informationen über verfügbare Funktionen
- Erkläre Home Assistant Konzepte verständlich
- Hilf bei der Nutzung und Automatisierung

Antworte immer freundlich, präzise und hilfsbereit. Passe deine Sprache an die Sprache des Nutzers an."""
        base_prompt = """Du bist ein intelligenter Hausautomatisierungs-Assistent ..."""
        system_prompt = f"{base_prompt}\n\n{self.extra_system_prompt}".strip()
        
        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limited)
        for msg in self.history[user_id][-10:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_input.text})
        
        try:
            # Call LLM API
            response_text = await self._call_mistral_api(messages)
            
            # Update history
            self.history[user_id].append({"role": "user", "content": user_input.text})
            self.history[user_id].append({"role": "assistant", "content": response_text})
            
            # Keep only last 20 messages to avoid context length issues
            if len(self.history[user_id]) > 20:
                self.history[user_id] = self.history[user_id][-20:]
            
            # Create response
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(response_text)
            
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=conversation_id,
            )
            
        except Exception as e:
            _LOGGER.error("Error calling LLM API: %s", e)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(
                "Entschuldigung, ich hatte einen Fehler beim Verarbeiten deiner Anfrage. "
                "Bitte versuche es später noch einmal."
            )
            
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=conversation_id,
            )

    async def _get_ha_context(self) -> str:
        """Get relevant Home Assistant context."""
        try:
            all_states = self.hass.states.async_all()
            
            # Count devices by domain
            device_counts = {}
            active_devices = {"lights_on": 0, "switches_on": 0}
            
            for state in all_states:
                domain = state.domain
                device_counts[domain] = device_counts.get(domain, 0) + 1
                
                # Count active devices
                if domain == "light" and state.state == "on":
                    active_devices["lights_on"] += 1
                elif domain == "switch" and state.state == "on":
                    active_devices["switches_on"] += 1
            
            # Build context string
            context_parts = [
                f"Geräte-Übersicht:",
                f"- Lichter: {device_counts.get('light', 0)} (davon {active_devices['lights_on']} an)",
                f"- Schalter: {device_counts.get('switch', 0)} (davon {active_devices['switches_on']} an)",
                f"- Sensoren: {device_counts.get('sensor', 0)}",
                f"- Binärsensoren: {device_counts.get('binary_sensor', 0)}",
                f"- Klimageräte: {device_counts.get('climate', 0)}",
                f"- Cover/Jalousien: {device_counts.get('cover', 0)}",
                f"- Mediaplayer: {device_counts.get('media_player', 0)}",
                f"- Kameras: {device_counts.get('camera', 0)}",
                f"- Szenen: {device_counts.get('scene', 0)}",
                f"- Automatisierungen: {device_counts.get('automation', 0)}",
                f"- Skripte: {device_counts.get('script', 0)}",
                f"- Personen: {device_counts.get('person', 0)}",
                f"- Zonen: {device_counts.get('zone', 0)}",
                f"\nGesamt: {len(all_states)} Entitäten"
            ]
            
            return "\n".join(context_parts)
        except Exception as e:
            _LOGGER.error("Error getting HA context: %s", e)
            return "Fehler beim Abrufen der Geräteinformationen."

    async def _call_mistral_api(self, messages: list[dict]) -> str:
        """Call LLM API asynchronously."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def make_request():
            return requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
        
        try:
            response = await loop.run_in_executor(None, make_request)
            response.raise_for_status()
            
            data = response.json()
            
            if 'choices' in data and data['choices']:
                return data['choices'][0]['message']['content'].strip()
            else:
                _LOGGER.error("Unexpected API response format: %s", data)
                return "Entschuldigung, ich konnte keine gültige Antwort generieren."
                
        except requests.exceptions.Timeout:
            _LOGGER.error("LLM API timeout")
            return "Die Anfrage hat zu lange gedauert. Bitte versuche es erneut."
        except requests.exceptions.RequestException as e:
            _LOGGER.error("LLM API request error: %s", e)
            return f"Fehler bei der API-Anfrage: {str(e)}"
        except Exception as e:
            _LOGGER.error("Unexpected error calling LLM API: %s", e)
            return "Ein unerwarteter Fehler ist aufgetreten."

    async def _async_entry_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle options update."""
        # Reload as we update device info + entity name + supported features
        await hass.config_entries.async_reload(entry.entry_id)
