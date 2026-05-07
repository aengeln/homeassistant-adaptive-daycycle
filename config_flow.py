"""Config flow for Adaptive Day Cycle."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_EARLIEST_DAWN,
    CONF_NIGHT_START,
    CONF_WEATHER_ENTITY,
    DEFAULT_EARLIEST_DAWN,
    DEFAULT_NAME,
    DEFAULT_NIGHT_START,
    DOMAIN,
)


class AdaptiveDayCycleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Adaptive Day Cycle."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): float,
                vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): float,
                vol.Required(
                    CONF_EARLIEST_DAWN,
                    default=DEFAULT_EARLIEST_DAWN,
                ): str,
                vol.Required(
                    CONF_NIGHT_START,
                    default=DEFAULT_NIGHT_START,
                ): str,
                vol.Optional(
                    CONF_WEATHER_ENTITY,
                    default="weather.forecast_home",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="weather",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""

        return AdaptiveDayCycleOptionsFlow(config_entry)


class AdaptiveDayCycleOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Adaptive Day Cycle."""

    def __init__(self, config_entry):
        """Initialize options flow."""

        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the integration options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE,
                    default=self.config_entry.data.get(
                        CONF_LATITUDE,
                        self.hass.config.latitude,
                    ),
                ): float,
                vol.Required(
                    CONF_LONGITUDE,
                    default=self.config_entry.data.get(
                        CONF_LONGITUDE,
                        self.hass.config.longitude,
                    ),
                ): float,
                vol.Required(
                    CONF_EARLIEST_DAWN,
                    default=self.config_entry.data.get(
                        CONF_EARLIEST_DAWN,
                        DEFAULT_EARLIEST_DAWN,
                    ),
                ): str,
                vol.Required(
                    CONF_NIGHT_START,
                    default=self.config_entry.data.get(
                        CONF_NIGHT_START,
                        DEFAULT_NIGHT_START,
                    ),
                ): str,
                vol.Optional(
                    CONF_WEATHER_ENTITY,
                    default=self.config_entry.data.get(
                        CONF_WEATHER_ENTITY,
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="weather",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )