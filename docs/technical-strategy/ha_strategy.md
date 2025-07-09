---
description: Core Home Assistant integration approach featuring the centralized LightTransitionManager component for
unified lighting control
summary: Technical strategy for implementing universal lighting control in Home Assistant core
priority: essential
---

<!-- summary: Core Home Assistant integration approach featuring the centralized LightTransitionManager component -->

# Home Assistant Strategy

My search confirms the current situation: Home Assistant typically _passes_ the `transition` parameter to the device/integration
. If the device doesn't support it, it's often simply ignored, and the light snaps to the new state.
There are community scripts (like "Light Fader") that try to simulate this by sending rapid, incremental commands, but this is not a built-in core HA feature.

So, yes, we absolutely should "smarten up" Home Assistant to provide better, consistent transition and dynamic control handling for all lights, regardless of native device support
. This is a critical piece of the puzzle for a truly unified and high-quality user experience.

Here's how we can strategize this as a series of PRs, integrating it with the previous ESPHome plan:

______________________________________________________________________

## Strategy for Home Assistant: Universal Transition & Dynamic Control

This builds on the previous ESPHome PRs, especially the ones where ESPHome learns to report its `dynamic_state` and
understand `dynamic_control` (ESPHome PRs 1-6).

### Phase 0: Pre-requisite & Core Concepts (Internal HA discussions/design)

Before writing code for this, a clear design document within Home Assistant Core would be beneficial.

- **Define `LightEntityFeature.SIMULATED_TRANSITION` and `LightEntityFeature.SIMULATED_DYNAMIC_CONTROL`**: New feature
  flags that integrations can set if they _can_ simulate these behaviors even if the device doesn't natively support
  them. This is distinct from the device's native capabilities.
- **Establish a Centralized `LightTransitionManager` (or similar concept):** A core utility in Home Assistant's `light`
  domain that can be used by integrations to offload transition/dynamic control logic. This manager would:
    - Determine if a light supports native transition/dynamic control (via `supported_features` or new flags).
    - If not natively supported but `SIMULATED_...` is supported, it generates the incremental commands.
    - Update the light entity's _internal_ state to reflect the simulation (e.g., `dynamic_state:
      simulated_moving_brightness_up`).
    - Handle cancellation of simulations if a new command arrives.

### Phase 1: Home Assistant - Universal Transition Simulation (`transition_length`)

**PR A.1: Home Assistant Core - Introduce `LightEntityFeature.TRANSITION_SIMULATED`**

- **Description:** Add a new `LightEntityFeature` flag to indicate that an integration _can_ simulate
  `transition_length` even if the device doesn't expose `LightEntityFeature.TRANSITION`.
- **Changes:**
    - Add `LightEntityFeature.TRANSITION_SIMULATED` to `homeassistant/components/light/__init__.py`'s
      `LightEntityFeature` enum.
- **Benefit:** Provides a standardized way for integrations to declare their capability for _software-based_
  transitions.
- **Testing:** Only code change, no functional change.

**PR A.2: Home Assistant Core - Core Transition Simulation Logic**

- **Description:** Implement a generic `LightTransitionManager` (or integrate the logic directly into
  `light/__init__.py`) that handles `transition_length` for lights that have
  `LightEntityFeature.TRANSITION_SIMULATED`.
- **Changes:**
    - Modify `homeassistant/components/light/__init__.py`'s `async_turn_on` service handler.
    - If a `transition` is specified:
        - Check `light.supported_features` for `LightEntityFeature.TRANSITION`. If present, pass the call to the
          integration as is.
        - If `LightEntityFeature.TRANSITION` is _not_ present, but `LightEntityFeature.TRANSITION_SIMULATED` _is_ present:
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
  that doesn't but where the integration implements `TRANSITION_SIMULATED`, and one that supports neither.

**PR A.3: Home Assistant Core - Expose Simulated Transition State (Optional but Recommended)**

- **Description:** For lights that are _simulating_ a transition, update their internal `LightEntity` state to reflect
  this (e.g., `dynamic_state: simulated_transitioning`).
- **Changes:**
    - Extend `LightEntity` with a `dynamic_state` property (as discussed in ESPHome PR6/HA PR8 for native ESPHome support).
    - The `LightTransitionManager` would update this `dynamic_state` to `simulated_transitioning` while active.
- **Benefit:** Consistent state reporting across native and simulated transitions, beneficial for UI and automations.

### Phase 2: Home Assistant - Universal Dynamic Control Simulation (`move`/`stop`)

**PR A.4: Home Assistant Core - Introduce `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED`**

- **Description:** Add a new `LightEntityFeature` flag for integrations that can simulate the "move/stop" dynamic
  control.
- **Changes:**
    - Add `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` to `homeassistant/components/light/__init__.py`'s
      `LightEntityFeature` enum.
- **Benefit:** Standardized capability declaration for software-based dynamic control.

**PR A.5: Home Assistant Core - Core Dynamic Control Simulation Logic**

- **Description:** Extend the `LightTransitionManager` (or the `light.async_turn_on` handler) to handle
  `dynamic_control` parameters for lights that have `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED`.
- **Changes:**
    - Modify `homeassistant/components/light/__init__.py`'s `async_turn_on` service handler.
    - If `dynamic_control` is specified:
        - **Priority 1: Native support:** Check if the integration's entity supports
          `LightEntityFeature.DYNAMIC_CONTROL` (which the ESPHome integration would set after ESPHome PR6). If
          yes, pass the `dynamic_control` parameter directly to the integration.
        - **Priority 2: Simulated support:** If `LightEntityFeature.DYNAMIC_CONTROL` is _not_ present, but
          `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` _is_ present:
            - Implement simulation logic for `type: "move"`: continuously send incremental `light.turn_on` commands.
            - Implement simulation logic for `type: "stop"`: immediately send a `light.turn_on` to the _current_
              brightness/color to halt the simulated movement.
            - Manage the internal `LightEntity` state (`dynamic_state: simulated_moving_up`, etc.) during this process.
            - Ensure new commands cancel ongoing simulations.
- **Benefit:** Provides a consistent "move/stop" experience across all capable lights, regardless of native device
  firmware support.
- **Testing:** Test `light.turn_on` with `dynamic_control` for `move` and `stop` on various device types (native
  support, simulated support).

### Phase 3: Integration-Specific Updates & Refinements

**PR B.1: ESPHome Integration - Declare `DYNAMIC_CONTROL_SIMULATED` (Conditional)**

- **Description:** For the ESPHome integration (`homeassistant/components/esphome/light.py`), conditionally declare
  `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for ESPHome lights until they are detected as supporting native
  `dynamic_control` (from ESPHome PR6).
- **Changes:**
    - In `homeassistant/components/esphome/light.py`, when creating the `EsphomeLight` entity, initially set
      `_attr_supported_features` to include `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED`.
    - Once ESPHome PR6 is merged and the ESPHome device reports its `dynamic_state` attributes, the HA integration can
      then dynamically detect native support and remove `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED`, letting
      the native device handle it. This ensures a smooth transition and preference for native support.
- **Benefit:** ESPHome lights benefit from HA's simulation _before_ the ESPHome firmware fully supports native
  `dynamic_control`, providing a consistent experience during the phased rollout.

**PR B.2: Other Integrations - Opt-in to Simulation (Example: ZHA, Zigbee2MQTT)**

- **Description:** Provide guidance and potentially examples for other popular light integrations (e.g., ZHA,
  Zigbee2MQTT) to _opt-in_ to setting `LightEntityFeature.TRANSITION_SIMULATED` and
  `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for their respective `LightEntity` platforms, if their underlying
  communication methods allow for rapid command sending.
- **Changes:**
    - This would be PRs to those _other_ integrations, where they would add the new `LightEntityFeature` flags to their
      `LightEntity` setup.
- **Benefit:** The benefits of universal transitions and dynamic control extend across the entire Home Assistant
  ecosystem, not just ESPHome.

______________________________________________________________________

### How to Handle It (Summary)

1. **Capability Declaration:** Integrations will declare what they _can_ do:
   - `LightEntityFeature.TRANSITION`: Device natively handles `transition`.
   - `LightEntityFeature.DYNAMIC_CONTROL`: Device natively handles `dynamic_control` (move/stop).
   - `LightEntityFeature.TRANSITION_SIMULATED`: Integration can _simulate_ `transition` if not native.
   - `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED`: Integration can _simulate_ `dynamic_control` if not native.
2. **Core Orchestration:** Home Assistant's `light` domain (`__init__.py`) acts as the central orchestrator:
   - When `light.turn_on` is called with `transition` or `dynamic_control`:
     - It first checks if the target `LightEntity` supports the feature _natively_. If yes, it just passes the command.
     - If not native, it checks if the entity supports the _simulated_ version of the feature. If yes, the Home
       Assistant core takes over and executes the simulation (sending rapid commands).
     - If neither is supported, the parameter is effectively ignored (current behavior), or a warning/error could be logged.
3. **State Reporting:** Whether native or simulated, the `LightEntity`'s `dynamic_state` attribute (as per ESPHome
   PR6/HA PR8) should accurately reflect the light's current activity, providing consistent feedback to the UI and
   automations.

This layered approach ensures that Home Assistant provides the best possible experience for every light, leveraging
native capabilities when available and intelligently simulating them when not, leading to a much more consistent and
powerful lighting control system.
