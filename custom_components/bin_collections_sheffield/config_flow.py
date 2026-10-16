import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_UPRN, DOMAIN
from .coordinator import SheffieldBinsApiError, async_fetch_collections


class SheffieldBinsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors = {}

        if user_input is not None:
            uprn = user_input[CONF_UPRN].strip()

            if not uprn.isdigit():
                errors[CONF_UPRN] = "invalid_uprn"
            else:
                await self.async_set_unique_id(uprn)
                self._abort_if_unique_id_configured()

                try:
                    collections = await async_fetch_collections(
                        async_get_clientsession(self.hass), uprn
                    )
                except SheffieldBinsApiError:
                    errors["base"] = "cannot_connect"
                else:
                    if not collections:
                        errors[CONF_UPRN] = "no_collections"
                    else:
                        return self.async_create_entry(
                            title=f"Sheffield Bins {uprn}",
                            data={CONF_UPRN: uprn},
                        )

        schema = vol.Schema(
            {
                vol.Required(CONF_UPRN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
