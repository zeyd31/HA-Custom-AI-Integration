"""Config flow for the Conversation Agent."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

DOMAIN = "custom_conversation_agent"

DEFAULT_NAME = "AI Assistant"
DEFAULT_API_KEY = "aa-123456789"
DEFAULT_BASE_URL = "https://ollama.your-endpoint.com/api"
DEFAULT_MODEL = "mistral:7b"
DEFAULT_MAX_TOKENS = 300
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SYSTEM_PROMPT = ""  


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LLM Conversation Agent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Persist the entry
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=DEFAULT_NAME): str,
                    vol.Required("api_key", default=DEFAULT_API_KEY): str,
                    vol.Required("base_url", default=DEFAULT_BASE_URL): str,
                    vol.Required("model", default=DEFAULT_MODEL): str,
                    vol.Optional("max_tokens", default=DEFAULT_MAX_TOKENS): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=4000)
                    ),
                    vol.Optional("temperature", default=DEFAULT_TEMPERATURE): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=2)
                    ),
                    vol.Optional(
                        "system_prompt", default=DEFAULT_SYSTEM_PROMPT
                    ): str,  # NEW
                }
            ),
            errors=errors,
        )

    # ---------- enable “Configure” button later ----------
    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for an existing entry."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit stored options."""
        if user_input is not None:
            # Save changes
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "system_prompt",
                    default=self.entry.options.get(
                        "system_prompt",
                        self.entry.data.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
                    ),
                ): str,
                vol.Optional(
                    "max_tokens",
                    default=self.entry.options.get(
                        "max_tokens", self.entry.data.get("max_tokens", DEFAULT_MAX_TOKENS)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=4000)),
                vol.Optional(
                    "temperature",
                    default=self.entry.options.get(
                        "temperature",
                        self.entry.data.get("temperature", DEFAULT_TEMPERATURE),
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=2)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
