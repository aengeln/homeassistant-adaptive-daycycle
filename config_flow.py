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


_TIME_SELECTOR = selector.TimeSelector()
_WEATHER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="weather")
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
                ): _TIME_SELECTOR,
                vol.Required(
                    CONF_NIGHT_START,
                    default=DEFAULT_NIGHT_START,
                ): _TIME_SELECTOR,
                vol.Optional(CONF_WEATHER_ENTITY): _WEATHER_SELECTOR,
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

    async def async_step_init(self, user_input=None):
        """Manage the integration options."""

        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=user_input[CONF_NAME],
            )

            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_LATITUDE): float,
                vol.Required(CONF_LONGITUDE): float,
                vol.Required(CONF_EARLIEST_DAWN): _TIME_SELECTOR,
                vol.Required(CONF_NIGHT_START): _TIME_SELECTOR,
                vol.Optional(CONF_WEATHER_ENTITY): _WEATHER_SELECTOR,
            }
        )

        suggested = {
            CONF_NAME: self.config_entry.title,
            CONF_LATITUDE: current.get(CONF_LATITUDE, self.hass.config.latitude),
            CONF_LONGITUDE: current.get(CONF_LONGITUDE, self.hass.config.longitude),
            CONF_EARLIEST_DAWN: current.get(CONF_EARLIEST_DAWN, DEFAULT_EARLIEST_DAWN),
            CONF_NIGHT_START: current.get(CONF_NIGHT_START, DEFAULT_NIGHT_START),
            CONF_WEATHER_ENTITY: current.get(CONF_WEATHER_ENTITY),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
        )
