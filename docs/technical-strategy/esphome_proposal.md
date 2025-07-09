# ESPHome Enhancement Proposal

To truly provide comprehensive functional compatibility with the entire Zigbee/Matter specification for lighting control within ESPHome, while preserving backward compatibility and extending existing APIs, we need a layered approach that enhances both the ESPHome light component and its communication with Home Assistant.

The core idea is to enrich the existing `light.turn_on` service with new parameters that encapsulate the dynamic control aspects of Zigbee/Matter's Level Control and Color Control clusters, and to enable ESPHome to internally manage and report these dynamic states.

## Comprehensive Proposal: ESPHome Light Component Enhancement

This proposal focuses on extending the existing `light` component and its associated actions and state management.

### 1. Enhancing the `light.turn_on` Service Call

Instead of introducing entirely new top-level service calls like `light.adjust_brightness` or `light.move_brightness`, we will overload the existing `light.turn_on` service with new, optional parameters. This aligns with the principle of incremental improvement without breaking existing integrations.

**Proposed New Parameters for `light.turn_on`:**

The existing `light.turn_on` service already accepts `brightness_pct`, `rgb_color`, `color_temp_kelvin`, and `transition`. We will add a new `dynamic_control` parameter, which is a dictionary that allows specifying "move", "stop", or "step" actions for brightness and color.

````yaml
# Example Home Assistant Service Call (new capabilities)
service: light.turn_on
target:
  entity_id: light.my_esphome_light
data:
  # Standard parameters still apply for 'set' actions
  # brightness_pct: 50
  # rgb_color: [255, 0, 0]
  # transition: 1s

  # NEW: Dynamic control for brightness and color
  dynamic_control:
    # Brightness adjustment actions
    brightness_action:
      type: "move"          # Can be "move", "stop", "step", or "none" (default, for standard set/transition)
      direction: "up"       # Required for "move" and "step": "up" | "down"
      speed: "medium"       # Optional for "move": string (profile name) or float (percentage_per_second)
      curve: "logarithmic"  # Optional for "move"/"step": string (profile name)
      ramp_time: 0.5s       # Optional for "move": Time (e.g., 0.5s)

    # Color adjustment actions (similar structure)
    color_action:
      type: "move"
      mode: "hue"           # Required for "move"/"step" color: "hue" | "saturation" | "color_temp"
      direction: "up"
      speed: "slow"
      curve: "linear"
      ramp_time: 0.2s

    # Global stop command within dynamic_control (convenience)
    stop_all: true          # Optional: if true, stops all ongoing dynamic brightness/color moves.
                            # If `brightness_action` or `color_action` is also 'stop', this is redundant.
```text

**Backward Compatibility Rationale for `light.turn_on`:**

- Existing automations and integrations that call `light.turn_on` with just `brightness_pct`, `rgb_color`, `transition`, etc., will continue to work exactly as they do today. The `dynamic_control` parameter is _optional_.
- If `dynamic_control` is _not_ provided, the `light.turn_on` service behaves as it always has (i.e., it performs a "set" operation to the specified target brightness/color over the given transition time). Internally, ESPHome would treat this as a `type: "none"` for `brightness_action` and `color_action`.
- If `dynamic_control` _is_ provided, its actions (e.g., "move", "stop", "step") would override or augment the standard parameters. For instance, `brightness_action: {type: "move", direction: "up"}` would take precedence over a `brightness_pct` in the same call, initiating a continuous move. A `brightness_action: {type: "stop"}` would halt any ongoing move or transition.

### 2\. Global Light Component Configuration Enhancements (ESPHome YAML)

To support the sophisticated parameters like `speed` and `curve` with named profiles, we'd add new global configurations.

```yaml
# In your ESPHome device's main YAML file
light:
  - platform: my_light_platform # e.g., rgbww, monochromatic, fastled
    name: "My ESPHome Light"
    # ... existing light config ...

    # NEW: Global dynamic control profiles
    dynamic_control_profiles:
      speeds:
        # Define named speed profiles (e.g., percentage per second)
        slow: 5%_per_second
        medium: 15%_per_second
        fast: 30%_per_second
        # Custom speeds can also be defined directly in the service call

      curves:
        # Define named dimming/color transition curve profiles
        logarithmic:
          type: "logarithmic" # Standard logarithmic curve
        s_curve:
          type: "s_curve"     # Standard S-curve
        incandescent_emulation:
          type: "custom"      # Custom points for incandescent-like dimming
          points:
            - [0, 0]          # Input %, Output %
            - [10, 1]
            - [30, 5]
            - [60, 25]
            - [100, 100]
        # Custom curves can be defined with 'points' or other curve parameters
```text

**Rationale for Global Profiles:**

- **Reusability:** Avoids repeating complex `speed` and `curve` definitions in every automation.
- **Simplicity:** Users can select meaningful names (`"slow"`, `"logarithmic"`) instead of raw numbers.
- **Consistency:** Ensures all lights using the same profile behave identically.
- **Centralized Management:** Easy to adjust dimming characteristics across multiple lights.

### 3\. Enhancing Home Assistant's Light Entity State

Home Assistant needs to reflect the dynamic nature of these new controls. The new state attributes would provide real-time feedback on what the light is _doing_, not just its instantaneous value.

**Proposed New State Attributes for Home Assistant `light` Entities:**

- **`dynamic_state`**:
    - **Type:** String
    - **Values:** `idle`, `moving_brightness_up`, `moving_brightness_down`, `moving_color_temp_up`, `moving_color_temp_down`, `moving_hue_up`, `moving_hue_down`, etc. (similar to Zigbee/Matter cluster states).
    - **Purpose:** Indicates if a dynamic operation is currently active.
- **`dynamic_target_brightness_pct`**:
    - **Type:** Integer (0-100) or Float
    - **Purpose:** If a `move` operation has a theoretical end point (e.g., moving up until 100% or down until 0%), this would indicate that. For `stop`, it would be the value at which it was stopped.
- **`dynamic_target_color` / `dynamic_target_color_temp`**:
    - **Type:** Same as existing `rgb_color`, `color_temp_kelvin`.
    - **Purpose:** Similar to `dynamic_target_brightness_pct` for color properties.
- **`active_speed_profile`**:
    - **Type:** String
    - **Purpose:** The name of the currently active speed profile (`"slow"`, `"medium"`, etc.) if a `move` is active.
- **`active_curve_profile`**:
    - **Type:** String
    - **Purpose:** The name of the currently active dimming/color curve profile (`"logarithmic"`, `"s_curve"`, etc.).

**How ESPHome would report these to Home Assistant:**

ESPHome's `LightState` internal class would be updated to track these dynamic properties. It would use its `publish_state()` mechanism (e.g., triggered periodically during dynamic operations, or on significant changes in dynamic state) to send these new attributes via the Native API or MQTT to Home Assistant.

### 4\. Internal ESPHome Logic (C++ Implementation)

The core logic would reside within the `light::LightState` class and its platform implementations (e.g., `MonochromaticLightOutput`, `RGBWWLightOutput`).

- **New Internal State Variables:**
    - `bool is_moving_brightness_`: Tracks if a brightness move is active.
    - `MoveDirection brightness_move_direction_`: Enum `UP`, `DOWN`, `NONE`.
    - `float brightness_move_speed_val_`: Internal resolved speed (e.g., percentage per millisecond).
    - `float brightness_ramp_progress_`: Tracks progress of the `ramp_time` for smooth starts/stops.
    - `LightCurveType brightness_active_curve_`: Enum/Pointer to current curve logic.
    - Similar variables for color components (hue, saturation, color temperature).
    - `unsigned long last_update_time_`: To calculate time elapsed for moves.
- **`write_state` Method Enhancement:** This method (called by Home Assistant) will be responsible for parsing the new `dynamic_control` parameters.
    - If `dynamic_control.brightness_action.type == "move"`:
        - Sets `is_moving_brightness_ = true`, stores `direction`, resolves `speed` (from profile or direct value), sets up `ramp_time` logic.
        - **Crucially, it does NOT set a fixed `target_brightness` immediately.** Instead, the `loop()` function will continuously update the _current output_ based on the move parameters.
        - Updates Home Assistant's `dynamic_state` and related attributes.
    - If `dynamic_control.brightness_action.type == "stop"`:
        - Sets `is_moving_brightness_ = false`, clears `brightness_move_direction_`.
        - The current instantaneous brightness becomes the new fixed target.
        - Updates Home Assistant's `dynamic_state` to `idle`.
    - If `dynamic_control.brightness_action.type == "step"`:
        - Calculates the new target brightness by applying the `amount` and `direction` to the `current_brightness`.
        - Initiates a standard transition to this new target over the `transition_length` using the specified `curve`. This would behave like a `set` with a very short transition, but ensure the "step" concept is handled.
        - Updates Home Assistant's `dynamic_state` to `transitioning` briefly.
    - If standard parameters (`brightness_pct`, `rgb_color`) are present and no `dynamic_control` is specified, it behaves as existing `light.turn_on` (sets `target_brightness`, `is_moving_brightness_ = false`).
- **`loop()` Method Integration:**
    - This is where the magic happens for `move` actions. In each `loop()` iteration (typically every 16ms):
        - If `is_moving_brightness_` is true:
            - Calculates the time elapsed since the last update.
            - Determines the current brightness increment/decrement based on `speed`, `curve`, and `ramp_time`.
            - Applies the `min_output`/`max_output` constraints.
            - Sets the raw light output (e.g., PWM duty cycle, LED values) to this new calculated instantaneous brightness.
            - Periodically calls `publish_state()` to update Home Assistant.
- **Local Physical Control (e.g., from a connected `binary_sensor`):**
    - `on_press` of a dimming button: Internally calls the equivalent of `write_state` with `dynamic_control.brightness_action.type: "move"`. This local command should generally take precedence over existing _remote_ commands.
    - `on_release` of a dimming button: Internally calls `write_state` with `dynamic_control.brightness_action.type: "stop"`.
    - The `last_command_source` (local vs. HA) logic on the device can determine precedence. If a physical button is held, it should maintain control until released or a high-priority HA command is issued.

### 5\. Home Assistant Integration Layer (Example: ESPHome Native API)

The Home Assistant ESPHome integration would need to:

- **Map HA Service Calls to ESPHome Commands:** Translate the new `light.turn_on` parameters (especially `dynamic_control`) into corresponding Native API messages that ESPHome understands.
- **Process ESPHome State Reports:** Parse the incoming state reports from ESPHome, including the new `dynamic_state`, `active_speed_profile`, `active_curve_profile`, and `dynamic_target` attributes, and update the Home Assistant `LightEntity` accordingly.
- **Fallback Logic:** If an ESPHome device _doesn't_ support the new `dynamic_control` features (e.g., it's running older firmware), the Home Assistant integration would fall back to its current behavior of simulating "move" with rapid `turn_on` commands. The Home Assistant `LightEntity` might then internally set its `dynamic_state` to `simulated_moving_brightness_up`, etc.

### Benefits of this Approach

- **Complete Standard Compatibility:** Directly implements Zigbee/Matter's "move/stop" and "step" commands.
- **Seamless Backward Compatibility:** Existing automations and `light.turn_on` calls continue to function.
- **Optimal UX:**
    - **Responsiveness:** Real-time, on-device execution for dynamic control.
    - **Smoothness:** Dimming curves and ramp times ensure professional-grade transitions.
    - **Intuitive Control:** Empowers the "hold-and-release" interaction.
- **Efficient State Management:** ESPHome handles the high-frequency state changes locally, only reporting significant state updates or dynamic state changes to Home Assistant.
- **Reduced Network Traffic:** Fewer individual commands sent from HA to device during continuous dimming.
- **Simplified Automations (for new features):** Home Assistant blueprints and automations become cleaner and more readable.
- **Layered Fallback:** Ensures a working (though less optimal) experience for older or less capable devices without breaking anything.

This comprehensive proposal outlines a path to enhance ESPHome's light component, making it a truly state-of-the-art solution for smart lighting control within the Home Assistant ecosystem, fully aligning with industry standards while maintaining a commitment to user experience and compatibility.

---

You're absolutely right! My apologies again for not fully capturing the nuance of Tasmota's dedicated `Dimmer <`, `Dimmer >`, and `Dimmer !` commands. That was a significant omission, as those commands are indeed central to how Tasmota provides dynamic control on the device. Thanks for keeping me honest and helping me refine my understanding!

Now, let's build a strategic, incremental implementation plan for ESPHome and Home Assistant, ensuring each PR delivers a self-contained, useful feature. This will allow for continuous integration, testing, and feedback, minimizing disruption.

---

## Incremental Implementation Strategy: ESPHome & Home Assistant Light Control

The goal is to implement the proposed dynamic light control features in ESPHome and integrate them seamlessly with Home Assistant through a series of pull requests (PRs). Each PR will introduce a concrete, useful feature on its own, building towards the full solution.

### Core Philosophy for PRs

- **Self-contained:** Each PR should implement a complete, testable feature.
- **Backward-compatible:** No existing functionality should break.
- **Useful:** Even partial implementations should provide tangible benefits.
- **Minimal impact:** Focus on isolated changes where possible.

---

### Phase 1: ESPHome - Laying the Foundation for Dynamic Control

**PR 1: ESPHome - Internal Light State Refinements & Time-Based Interpolation**

- **Description:** Introduce internal C++ structures within `LightState` (and relevant `LightOutput` implementations) to track not just `target_brightness`, but also `current_brightness_actual` (the instantaneous output value), `transition_start_time`, `transition_duration`, and potentially the `LightTransformer` for curves. This PR focuses on making the light component capable of smoother, more precise internal transitions _if_ commanded to.
- **Changes:**
    - Modify `LightState` to store a precise floating-point `current_brightness_actual` (0.0-1.0) that is updated in the `loop()` method.
    - Enhance `LightState::start_transition_` to properly use a given `transition_length` for time-based interpolation, rather than just step-wise changes.
    - Introduce basic internal linear interpolation for brightness/color over a `transition_length`.
    - Ensure `publish_state()` accurately reflects this instantaneous `current_brightness_actual`.
- **Benefit:** Enables truly smooth transitions when `transition:` is used, without requiring Home Assistant to send rapid updates. The light handles it locally. This is a foundational improvement for all transitions.
- **Testing:** Verify existing `transition:` functionality on lights is smoother.

**PR 2: ESPHome - YAML Configuration for Custom Dimming Curves and Profiles**

- **Description:** Add the ability to define named `dimming_profiles` (for `speed` and `curve`) in the ESPHome `light:` component configuration. These profiles won't be used by actions yet, but define the global settings.
- **Changes:**
    - Update `esphome/components/light/light.py` to add a new `dynamic_control_profiles` schema under `light:`.
    - Implement validation for `speeds` (e.g., percentage_per_second) and `curves` (e.g., `logarithmic`, `s_curve`, or `custom` points).
    - Add corresponding C++ structs/enums in `esphome/components/light/light.h` and helper functions in `esphome/components/light/light_state.cpp` to store and interpret these profiles.
- **Benefit:** Provides a structured way for users to define sophisticated light behavior. This is useful for future features and offers early configuration flexibility.
- **Testing:** Validate YAML parsing and C++ code generation for these new configuration options. No runtime change yet.

### Phase 2: ESPHome - Implementing Dynamic Actions

**PR 3: ESPHome - `LightCall` Expansion for `dynamic_control` (Parsing & Internal State)**

- **Description:** Extend the `LightCall` mechanism in ESPHome to parse the new `dynamic_control` parameter when received from the Native API. This PR will focus on receiving these commands and setting internal flags/parameters in `LightState` but _not_ yet implementing the continuous motion.
- **Changes:**
    - Modify `esphome/components/light/light.py` to add the `dynamic_control` optional parameter to `light.turn_on`'s schema.
    - Define sub-schemas for `brightness_action` and `color_action` with `type`, `direction`, `speed`, `curve`, `ramp_time`, `mode`.
    - Update `LightCall`'s `perform()` method in C++ (`esphome/components/light/light_state.cpp`) to extract and store these new parameters into new temporary `LightCall` structs or directly into `LightState` members.
    - Introduce `LightState::is_dynamic_moving_brightness_`, `LightState::moving_brightness_direction_`, etc.
- **Benefit:** The ESPHome device is now capable of receiving the high-level `dynamic_control` commands, laying the groundwork for on-device execution. No visible user change yet unless debugging logs are enabled.
- **Testing:** Use `logger: level: DEBUG` to confirm ESPHome device receives and parses the new `dynamic_control` commands correctly.

**PR 4: ESPHome - On-Device Continuous Brightness `move`/`stop` Implementation**

- **Description:** Implement the core logic for continuous brightness change (`move` and `stop`) within the ESPHome `LightState::loop()` method, using the parameters set by `LightCall`.
- **Changes:**
    - In `esphome/components/light/light_state.cpp`, update the `loop()` method.
    - If `is_dynamic_moving_brightness_` is true:
        - Implement the logic to continuously calculate the new `current_brightness_actual` based on `direction`, `speed` (resolved from profiles), `curve`, and `ramp_time`.
        - Apply `min_output` and `max_output` constraints.
        - Call `set_immediately_` to update the actual light output.
        - Implement the `stop` logic, where `dynamic_control.brightness_action.type == "stop"` sets `is_dynamic_moving_brightness_ = false` and fixes the `current_brightness_actual`.
    - Implement a mechanism to automatically stop a `move` if the `min_output` or `max_output` is reached.
- **Benefit:** The ESPHome device can now handle continuous dimming fully on-device, independent of rapid updates from Home Assistant. This dramatically improves responsiveness and smoothness for brightness control.
- **Testing:** Thoroughly test `light.turn_on` calls with `dynamic_control.brightness_action.type: "move"` and `"stop"` via Home Assistant developer tools (even though HA doesn't know about it yet). Observe the physical light's behavior.

**PR 5: ESPHome - On-Device Continuous Color `move`/`stop`/`step` Implementation**

- **Description:** Extend the continuous control logic to color properties (hue, saturation, color temperature) following the same `move`/`stop`/`step` pattern as brightness.
- **Changes:**
    - Similar to PR4, extend `LightState::loop()` to handle `is_dynamic_moving_color_` based on `mode` (hue/saturation/color_temp), `direction`, `speed`, `curve`, and `ramp_time`.
    - Implement `step` actions for both brightness and color (calculate new target, then trigger a short transition).
- **Benefit:** Full on-device dynamic control for all core lighting properties.
- **Testing:** Test various `color_action` scenarios.

**PR 6: ESPHome - `dynamic_state` Reporting via Native API**

- **Description:** Introduce new state attributes in `LightState` and ensure they are published via the Native API to Home Assistant.
- **Changes:**
    - Add `dynamic_state`, `active_speed_profile`, `active_curve_profile` (and `dynamic_target_brightness`, `dynamic_target_color` if applicable) as internal attributes in `LightState`.
    - Modify `LightState::publish_state()` to include these new attributes in the Native API message whenever they change (e.g., when a `move` starts/stops, or when a profile is activated). Use `batch_delay` if needed in the API component config.
- **Benefit:** Home Assistant can now _see_ what the light is doing dynamically. This is crucial for UI feedback and robust automations.
- **Testing:** Verify Home Assistant's developer tools show these new attributes updating in real-time.

### Phase 3: Home Assistant - Integration and UX

**PR 7: Home Assistant Core - Extend `light.turn_on` Schema & ESPHome Integration Update**

- **Description:** Update the `light` domain schema in Home Assistant Core to accept the new `dynamic_control` parameters. Update the `esphome` integration to send these new parameters over the Native API.
- **Changes:**
    - Modify `homeassistant/components/light/__init__.py` to expand the `LIGHT_TURN_ON_SCHEMA` with the `DYNAMIC_CONTROL_SCHEMA` including `brightness_action` and `color_action`.
    - Update `homeassistant/components/esphome/light.py` to:
        - Map the incoming `light.turn_on` service call data, specifically the `dynamic_control` part, to the corresponding ESPHome Native API call parameters.
        - Ensure existing parameters (`brightness_pct`, `rgb_color`, `transition`) are handled correctly (e.g., if `dynamic_control` is absent, use existing behavior).
- **Benefit:** Home Assistant can now officially issue the new, powerful dynamic light commands to ESPHome devices.
- **Testing:** Automations in HA can now call `light.turn_on` with `dynamic_control`. Test this with a deployed ESPHome device running PR6.

**PR 8: Home Assistant Core - `LightEntity` State Attribute Parsing & UX Hooks**

- **Description:** Modify Home Assistant's `LightEntity` to consume and expose the new `dynamic_state` and related attributes received from ESPHome devices.
- **Changes:**
    - In `homeassistant/components/light/__init__.py`, update `LightEntity` (or a base class if needed) to have properties for `dynamic_state`, `active_speed_profile`, `active_curve_profile`, etc.
    - In `homeassistant/components/esphome/light.py`, parse the incoming state messages from ESPHome (which contain the new attributes from PR6) and map them to the `LightEntity` properties.
- **Benefit:** The Home Assistant frontend, automations, and other integrations can now react to and display the dynamic activity of the light.
- **Testing:** Verify the HA developer tools UI shows the new light attributes updating. Create simple automations that trigger on `dynamic_state` changes.

**PR 9: Home Assistant Frontend - Basic UI Integration (Optional, but good UX)**

- **Description:** A small frontend PR to show simple visual feedback in the light card (e.g., a spinning icon or text indicating "Dimming Up") when `dynamic_state` is not `idle`.
- **Changes:**
    - Modify relevant frontend light card components (e.g., `ha-card-light`) to conditionally display UI elements based on the new `dynamic_state` attribute.
- **Benefit:** Immediate visual feedback for users that dynamic control is active.

### Phase 4: Fallback and Refinements

**PR 10: Home Assistant Core - Intelligent Fallback for `dynamic_control`**

- **Description:** Implement the fallback mechanism within Home Assistant's `light` domain/integrations for devices that _do not_ report support for `dynamic_control` (e.g., older ESPHome firmware, or other integrations like Zigbee Home Automation before a similar update).
- **Changes:**
    - In `homeassistant/components/light/__init__.py` or within specific integrations (like `esphome`), add logic: if `dynamic_control` is used in a `light.turn_on` call, but the target device's integration does not indicate support for it (e.g., a new `SUPPORT_DYNAMIC_CONTROL` feature flag, or lack of presence of `dynamic_state` in received attributes), then Home Assistant should simulate the `move` by sending rapid `turn_on` commands with incremental brightness/color changes.
    - The `LightEntity` in HA would then set its _own_ internal `dynamic_state` to `simulated_moving_up` etc., to provide consistent feedback.
- **Benefit:** Ensures `dynamic_control` works on all devices (with varying degrees of smoothness/responsiveness) and provides a graceful degradation path.
- **Testing:** Test with an old ESPHome firmware that doesn't have the new features, confirm HA falls back to sending rapid commands and updates its internal state correctly.

**PR 11: ESPHome - Local Button Integration (YAML Syntax)**

- **Description:** Add convenient YAML syntax to easily bind `binary_sensor` `on_press` and `on_release` events to the new `light.turn_on` `dynamic_control` actions directly in ESPHome.
- **Changes:**
    - Introduce new actions or enhance existing ones in `binary_sensor` or a new `light` automation section to make it simple to specify `light.turn_on` with `dynamic_control` for `move` on `on_press` and `stop` on `on_release`.
    - Ensure proper C++ generation for these local controls to directly call the internal `LightState` `move`/`stop` methods, bypassing the Native API for ultimate responsiveness.
- **Benefit:** Enables easy configuration of physical "hold-and-release" buttons with optimal responsiveness on the device itself.
- **Testing:** Flash device with buttons, verify physical dimming works perfectly.

### Post-Implementation & Future Enhancements

- **Documentation:** Comprehensive documentation for both ESPHome and Home Assistant covering the new features, how to configure them, and the expected behavior.
- **Blueprints:** Create Home Assistant blueprints that leverage the new `dynamic_control` and `dynamic_state` for common button controllers.
- **Zigbee/Matter Integrations:** Once the core `light` domain and ESPHome are robust, other integrations (ZHA, Matter) can be updated to leverage these new standard-aligned service calls and report their own `dynamic_state`. This means a ZHA light, when dimming, could also report `moving_brightness_up`, creating a unified experience.

This strategic rollout ensures that each step provides concrete value, is manageable for review and testing, and incrementally builds towards a powerful and seamless lighting control experience.
````
