"""Button platform for the Denon AVR integration.

Momentary actions that do not map to a stateful entity. Currently the manual
graphic-EQ helper on the EQ sub-device: copy the reference (Audyssey / flat)
curve into the manual equaliser as a starting point. Only created when the
receiver advertises a graphic EQ this profile can drive.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DenonAvrConfigEntry, DenonAvrCoordinator
from .entity import DenonAvrEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonAvrConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the graphic-EQ action buttons when the receiver supports them."""

    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = [
        DenonAvrActionButton(coordinator, action_id, data)
        for action_id, data in coordinator.device.profile.actions.items()
    ]
    if coordinator.device.graphic_eq.supported:
        entities.append(DenonAvrEqApply(coordinator))
        entities.append(DenonAvrEqCurveCopy(coordinator))
        entities.append(DenonAvrEqSetDefaults(coordinator))
    async_add_entities(entities)

class DenonAvrActionButton(DenonAvrEntity, ButtonEntity):
    """A stateless action button backed by a profile action command."""

    def __init__(
        self, coordinator: DenonAvrCoordinator, action_id: str, data: dict
    ) -> None:
        super().__init__(coordinator, f"button_{action_id}")
        self._action_id = action_id
        self._attr_translation_key = action_id
        icon = data.get("icon")
        if icon:
            self._attr_icon = icon

    async def async_press(self) -> None:
        await self.coordinator.device.async_send_action(self._action_id)
class DenonAvrEqApply(DenonAvrEntity, ButtonEntity):
    """Write the edited band curve to the receiver.

    The band sliders stage their values locally (the receiver accepts only a
    full band block, not a single band); pressing this applies the whole curve.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:content-save"

    def __init__(self, coordinator: DenonAvrCoordinator) -> None:
        super().__init__(coordinator, "button_eq_apply", sub_device="eq")
        self._attr_translation_key = "eq_apply"

    async def async_press(self) -> None:
        await self.coordinator.device.graphic_eq.apply()


class DenonAvrEqCurveCopy(DenonAvrEntity, ButtonEntity):
    """Copy the reference curve into the manual graphic EQ as a starting point."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:content-copy"

    def __init__(self, coordinator: DenonAvrCoordinator) -> None:
        super().__init__(coordinator, "button_eq_curve_copy", sub_device="eq")
        self._attr_translation_key = "eq_copy_curve"

    async def async_press(self) -> None:
        await self.coordinator.device.graphic_eq.curve_copy()


class DenonAvrEqSetDefaults(DenonAvrEntity, ButtonEntity):
    """Reset the manual graphic EQ to its defaults (a flat curve)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:restore"

    def __init__(self, coordinator: DenonAvrCoordinator) -> None:
        super().__init__(coordinator, "button_eq_set_defaults", sub_device="eq")
        self._attr_translation_key = "eq_default"

    async def async_press(self) -> None:
        await self.coordinator.device.graphic_eq.set_defaults()
