---
description: Core Home Assistant integration approach featuring the centralized LightTransitionManager component for
unified lighting control
summary: Technical strategy for implementing universal lighting control in Home Assistant core
priority: essential
---

# Home Assistant Strategy for Native Lighting Control

Home Assistant currently passes the `transition` parameter to the device/integration. If the device doesn't support it, the parameter is ignored, and the light snaps to the new state. This document outlines our strategy for implementing native dynamic control capabilities in Home Assistant.

## Strategy for Home Assistant: Native Dynamic Control

This builds on the ESPHome implementation where devices report their `dynamic_state` and understand `dynamic_control` commands.

### Core Design Principles

1. **Native Capabilities First**: Features are only available on devices that support them natively.
2. **Graceful Degradation**: Unsupported service calls are ignored, similar to how unsupported `transition` parameters are handled today.
3. **Clear State Reporting**: Devices report their current dynamic state (e.g., `moving_up`, `idle`) when supported.

### Key Components

- **`LightEntityFeature.DYNAMIC_CONTROL`**: A feature flag that integrations set when a device natively supports dynamic control commands.
- **Centralized `LightTransitionManager`**: A core utility in Home Assistant's `light` domain that:
    - Determines if a light supports native dynamic control via `supported_features`.
    - Translates high-level `dynamic_control` commands into device-specific protocol commands.
    - Tracks and reports the current dynamic state of each light.

### Implementation Approach

1. **Define `LightEntityFeature.DYNAMIC_CONTROL`**: This flag indicates that a device natively supports dynamic control commands.

- **Changes:**
    - Add `` to `homeassistant/components/light/__init__.py`'s
      `LightEntityFeature` enum.
- **Benefit:** Provides a standardized way for integrations to declare their capability for _software-based_
  transitions.
- **Testing:** Only code change, no functional change.

**: Home Assistant Core - Core Transition Simulation Logic**

- **Description:** Implement a generic `LightTransitionManager` (or integrate the logic directly into
  `light/__init__.py`) that handles `transition_length` for lights that have
  .
- **Changes:**
    - Modify `homeassistant/components/light/__init__.py`'s `async_turn_on` service handler.
    - If a `transition` is specified:
        - Check `light.supported_features` for `LightEntityFeature.TRANSITION`. If present, pass the call to the
          integration as is.
        - If `LightEntityFeature.TRANSITION` is _not_ present, but  _is_ present:
            - Read the light's current state (brightness, color).
            - Calculate the steps needed to reach the target over the `transition_length`.
            - Use `async_call_later` or a dedicated `homeassistant.helpers.event` scheduler to send a series of
              `light.turn_on` calls with incremental values to the integration over the specified
              duration.
            - During simulation, set an internal `_current_transition_target` and `_is_simulating_transition` flag on
              the `LightEntity` to manage state.
            - Ensure new commands during an active simulation cancel the ongoing simulation.
- **Benefit:** All lights, regardless of native device support, will now properly honor `transition_length` from
  `light.turn_on` calls, providing a consistent user experience. This is a _major_ UX improvement.
- **Testing:** Test `light.turn_on` with `transition` on various devices: one that natively supports it (e.g., Hue), one
  that doesn't but where the integration implements , and one that supports neither.

**: Home Assistant Core - Expose Simulated Transition State (Optional but Recommended)**

- **Description:** For lights that support native dynamic control, update their internal `LightEntity` state to reflect
  this (e.g., `dynamic_state: moving_brightness_up`).
- **Changes:**
    - Extend `LightEntity` with a `dynamic_state` property to report the current dynamic activity.
    - The `LightTransitionManager` updates this `dynamic_state` to reflect the current activity (e.g., `moving_up`, `idle`).
- **Benefit:** Consistent state reporting across native and simulated transitions, beneficial for UI and automations.

**: Home Assistant Core - Introduce ``**

- **Description:** Add a new `LightEntityFeature` flag for integrations that can simulate the "move/stop" dynamic
  control.
- **Changes:**
    - Add `` to `homeassistant/components/light/__init__.py`'s
      `LightEntityFeature` enum.
- **Benefit:** Standardized capability declaration for software-based dynamic control.

**: Home Assistant Core - Core Dynamic Control Simulation Logic**

- **Description:** Extend the `LightTransitionManager` (or the `light.async_turn_on` handler) to handle
  `dynamic_control` parameters for lights that have .
- **Changes:**
    - Modify `homeassistant/components/light/__init__.py`'s `async_turn_on` service handler.
    - If `dynamic_control` is specified:
        - **Priority 1: Native support:** Check if the integration's entity supports
          `LightEntityFeature.DYNAMIC_CONTROL` (which the ESPHome integration would set after ESPHome PR6). If
          yes, pass the `dynamic_control` parameter directly to the integration.
        - **Priority 2: Simulated support:** If `LightEntityFeature.DYNAMIC_CONTROL` is _not_ present, but  _is_ present:
        - **Priority 2: Simulated support:** If `LightEntityFeature.DYNAMIC_CONTROL` is _not_ present, but
          `` _is_ present:
            - Implement simulation logic for `type: "move"`: continuously send incremental `light.turn_on` commands.
            - Implement simulation logic for `type: "stop"`: immediately send a `light.turn_on` to the _current_
              brightness/color to halt the simulated movement.
            - Manage the internal `LightEntity` state (`dynamic_state: simulated_moving_up`, etc.) during this process.
            - Ensure new commands cancel ongoing simulations.
- **Benefit:** Provides a consistent "move/stop" experience across all capable lights, regardless of native device
  firmware support.
- **Testing:** Test `light.turn_on` with `dynamic_control` for `move` and `stop` on various device types (native
  support, simulated support).

- **Description:** For the ESPHome integration (`homeassistant/components/esphome/light.py`), conditionally declare
  `` for ESPHome lights until they are detected as supporting native
  `dynamic_control` (from ESPHome PR6).
- **Changes:**
    - In `homeassistant/components/esphome/light.py`, when creating the `EsphomeLight` entity, initially set
      `_attr_supported_features` to include ``.
    - Once ESPHome PR6 is merged and the ESPHome device reports its `dynamic_state` attributes, the HA integration can
      then dynamically detect native support and remove ``, letting
      the native device handle it. This ensures a smooth transition and preference for native support.
- **Benefit:** ESPHome lights benefit from HA's simulation _before_ the ESPHome firmware fully supports native
  `dynamic_control`, providing a consistent experience during the phased rollout.

**: Other Integrations - Opt-in to Simulation (Example: ZHA, Zigbee2MQTT)**

- **Description:** Provide guidance and potentially examples for other popular light integrations (e.g., ZHA,
  Zigbee2MQTT) to _opt-in_ to setting `` and
  `` for their respective `LightEntity` platforms, if their underlying
  communication methods allow for rapid command sending.
- **Changes:**
    - This would be PRs to those _other_ integrations, where they would add the new `LightEntityFeature` flags to their
      `LightEntity` setup.
- **Benefit:** The benefits of universal transitions and dynamic control extend across the entire Home Assistant
  ecosystem, not just ESPHome.

______________________________________________________________________

1. **Capability Declaration:** Integrations will declare what they _can_ do:
   - `LightEntityFeature.TRANSITION`: Device natively handles `transition`.
   - `LightEntityFeature.DYNAMIC_CONTROL`: Device natively handles `dynamic_control` (move/stop).
   - ``: Integration can _simulate_ `transition` if not native.
   - ``: Integration can _simulate_ `dynamic_control` if not native.
2. **Core Orchestration:** Home Assistant's `light` domain (`__init__.py`) acts as the central orchestrator:
   - When `light.turn_on` is called with `dynamic_control`:
     - It checks if the target `LightEntity` supports the feature natively via `LightEntityFeature.DYNAMIC_CONTROL`.
     - If supported, it passes the command to the device's implementation.
     - If not supported, the command is ignored (no simulation is performed).
   - For `transition` parameter:
     - It's passed through to the device if supported.
     - If not supported, it's ignored (maintaining current behavior).
     - If neither is supported, the parameter is effectively ignored (current behavior), or a warning/error could be logged.
3. **State Reporting:** Whether native or simulated, the `LightEntity`'s `dynamic_state` attribute (as per ESPHome
   PR6/HA PR8) should accurately reflect the light's current activity, providing consistent feedback to the UI and
   automations.

This layered approach ensures that Home Assistant provides the best possible experience for every light, leveraging
native capabilities when available and intelligently simulating them when not, leading to a much more consistent and
powerful lighting control system.
