---
description: Detailed implementation roadmap with technical requirements, development phases, and execution strategy for universal lighting control
summary: Primary engineering execution plan covering architectural changes, API extensions, and integration updates
priority: important
---

# Engineering Execution and Implementation Plan: Universal Smart Lighting Control

## 1\. Document Overview

This document details the comprehensive engineering plan for implementing "Universal Smart Lighting Control" within Home Assistant. The initiative aims to standardize and enhance the user experience for dynamic light control, including smooth transitions and continuous dimming/color adjustments, across a diverse range of smart lighting devices. It outlines the architectural changes, API extensions, and integration-specific updates required, leveraging industry best practices for dimming curves and ensuring robust interaction with existing protocols like Zigbee and Z-Wave.

## 2\. Goals and Motivation

The primary goal is to address the current fragmentation and inconsistency in how Home Assistant handles dynamic lighting.

**Motivation:**

*   **Inconsistent User Experience:** `transition:` parameters are often ignored, leading to abrupt light changes. Continuous dimming (e.g., "hold-to-dim") requires complex, brittle automations or custom solutions.
    
*   **Performance & Reliability Issues:** Software-based dimming workarounds flood local networks (Wi-Fi, Zigbee, Z-Wave) with numerous commands, causing latency and potential network instability.
    
*   **Lack of Unified State Feedback:** Home Assistant currently lacks a standardized mechanism for integrations to report a light's active dynamic state (e.g., `moving`, `transitioning`), hindering advanced UI and automation logic.
    
*   **Leveraging Protocol Capabilities:** Modern lighting protocols (Zigbee, Z-Wave, Matter) have native commands for continuous level/color changes, which are often underutilized in Home Assistant.
    
*   **Perceptual Accuracy:** Human eye perception of brightness is non-linear. Linear dimming often feels unnatural. Adopting industry-standard non-linear (e.g., logarithmic) dimming curves will provide a more intuitive and pleasing experience.
    

## 3\. Core Concepts & New API Extensions

### 3.1. New `LightEntityFeature` Flags (Home Assistant Core)

To declare granular capabilities for native and simulated dynamic control:

*   `LightEntityFeature.TRANSITION` (Existing: `0x20` / `32`): Device natively handles `transition` parameter (e.g., `move_to_level_with_on_off` in Zigbee).
    
*   `LightEntityFeature.DYNAMIC_CONTROL` (New: `0x40` / `64`): Device natively handles continuous `move`/`stop` and `step` commands (e.g., Zigbee `Move`/`Stop Level` or Z-Wave `Start/Stop Level Change`).
    
*   `LightEntityFeature.TRANSITION_SIMULATED` (New: `0x80` / `128`): The integration (or HA Core) can simulate a smooth `transition` for this device if `TRANSITION` is not present.
    
*   `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` (New: `0x100` / `256`): The integration (or HA Core) can simulate `move`/`stop`/`step` dynamic control if `DYNAMIC_CONTROL` is not present.
    

### 3.2. Extended `light.turn_on` Service Schema (Home Assistant Core)

The `light.turn_on` service will be extended to accept a new `dynamic_control` parameter.

```
# Example light.turn_on service call
service: light.turn_on
target:
  entity_id: light.my_smart_light
data:
  brightness_pct: 75 # Standard brightness/color parameters still apply for target state
  # OR
  dynamic_control:
    type: "move" # Required: "move" | "stop" | "step"
    direction: "up" # Required for "move" and "step": "up" | "down"
    speed: "fast" # Optional for "move": "slow" | "medium" | "fast" | <float_rate_per_sec>
    curve: "logarithmic" # Optional: "linear" | "logarithmic" | "s_curve" | "square_law" | { points: [[0,0], [10,1], ...] }
    step_size: 10 # Required for "step": <float_percentage_or_value>
    duration: 5 # Optional for "move"/"step": <float_seconds> (total duration, overrides speed if both)
```

**Parameter Breakdown:**

*   `type`: Specifies the dynamic action.
    
    *   `"move"`: Initiates continuous brightness/color change.
        
    *   `"stop"`: Halts any ongoing `move` operation.
        
    *   `"step"`: Changes brightness/color by a discrete increment/decrement.
        
*   `direction`: For `move` and `step`, indicates the direction of change.
    
*   `speed`: For `move`, a predefined or custom rate of change (e.g., %/second or value/second).
    
*   `curve`: Specifies the dimming curve. This is crucial for perceived smoothness.
    
*   `step_size`: For `step`, the magnitude of the discrete change.
    
*   `duration`: For `move`/`step`, an optional total duration. If `move` and `duration` are both provided, `speed` might be calculated from `duration`.
    

### 3.3. `dynamic_state` Attribute on `LightEntity` (Home Assistant Core)

A new state attribute will be introduced on `light` entities to indicate their current dynamic activity.

```
{
  "entity_id": "light.my_smart_light",
  "state": "on",
  "attributes": {
    "brightness": 128,
    "hs_color": [240, 100],
    "dynamic_state": "moving_brightness_up", # New attribute
    "active_speed_profile": "medium",
    "active_curve_profile": "logarithmic",
    "dynamic_target_brightness": 255, # For move/transition
    "supported_features": 385 # Combination of flags
  }
}
```

**`dynamic_state` Possible Values:**

*   `idle`: Not currently undergoing dynamic change.
    
*   `transitioning`: Undergoing a smooth transition to a target state (from `transition:` parameter).
    
*   `moving_brightness_up`: Brightness is actively increasing continuously.
    
*   `moving_brightness_down`: Brightness is actively decreasing continuously.
    
*   `moving_color_up`: Color (e.g., temperature, hue) is actively changing in one direction.
    
*   `moving_color_down`: Color is actively changing in another direction.
    
*   Prefixes like `simulated_` (e.g., `simulated_transitioning`, `simulated_moving_brightness_up`) would be used when Home Assistant Core is performing the simulation.
    

### 3.4. `LightTransitionManager` (Conceptual Role in Home Assistant Core)

This is not necessarily a single class, but a set of coordinated logic within `homeassistant/components/light/__init__.py` responsible for:

*   **Capability Check:** Inspecting `LightEntity.supported_features` to determine native vs. simulated handling.
    
*   **Simulation Orchestration:** If simulation is required (`_SIMULATED` flags set):
    
    *   Calculating intermediate steps based on `transition`, `dynamic_control`, `speed`, and `curve`.
        
    *   Scheduling `async_call_later` (or similar) to send incremental `light.turn_on` commands back to the integration.
        
    *   Managing and canceling ongoing simulations when new commands arrive.
        
    *   Updating the entity's `dynamic_state` attribute.
        
*   **Passing Native Commands:** If native support is detected, packaging `dynamic_control` parameters and passing them directly to the underlying integration.
    

## 4\. Dimming Curves & Human Perception

### 4.1. The Importance of Non-Linear Dimming

Human vision is non-linear. The **Weber-Fechner Law** and **Stevens' Power Law** describe that our perception of a stimulus (like light intensity) is proportional to the logarithm of the stimulus, or to a power function of the stimulus, respectively. This means:

*   A 10% change at low brightness is perceived as a much larger change than a 10% change at high brightness.
    
*   A linear progression of measured light output (e.g., 0% to 100% lumen output) will appear to "jump" quickly at the low end and then become very subtle at the high end.
    

To achieve a perceptually smooth and intuitive dimming experience, the electrical or digital control signal sent to the light needs to be non-linear.

### 4.2. Standard Dimming Curves to Support

We will implement and provide named references for the following common dimming curves:

*   **`linear`**:
    
    *   **Description:** A direct 1:1 mapping between input (control signal) and output (light intensity).
        
    *   **Use Case:** Debugging, some industrial applications, or when a device's native curve is explicitly desired even if it's not perceptually linear.
        
    *   **Formula:** `output = input` (normalized 0-1)
        
*   **`logarithmic` (DALI-compliant)**:
    
    *   **Description:** The most common and recommended curve for general lighting, designed to match human perception. It provides finer control at lower light levels and a more gradual perceived change across the full range. This will be the **default perceptual curve**.
        
    *   **Standard:** Based on IEC 62386-102 (DALI) logarithmic dimming curve specifications. This curve scales 0.1% to 100% output over 254 steps.
        
    *   **Formula (simplified approximation, actual DALI has specific lookup table):** `output = 100 * (log10(input * 99 + 1) / log10(100))` (for input 0-1, output 0-100%). Or `output = ((input * 254)**2) / 254` if device has 254 levels (approximate for DALI).
        
*   **`s_curve`**:
    
    *   **Description:** A non-linear curve that exhibits slower changes at the beginning and end of the dimming range, with a faster change in the middle. Offers a "soft start" and "soft stop" feel.
        
    *   **Formula:** Various sigmoid functions can be used, e.g., `output = 0.5 * (1 + tanh(k * (input - 0.5)))` for some scaling factor `k`.
        
*   **`square_law` (or `power` with configurable exponent)**:
    
    *   **Description:** Mimics the behavior of incandescent lamps and is often used to ensure LEDs behave similarly. It's a parabolic curve where output is proportional to the square of the input.
        
    *   **Formula:** `output = input^2` (normalized 0-1)
        

### 4.3. Curve Application Strategy

The `curve` parameter will primarily be handled by the **Home Assistant Core's `LightTransitionManager`**.

1.  **Input:** The `light.turn_on` service receives a desired perceived brightness (e.g., 0-100%) and a `curve` (e.g., `logarithmic`).
    
2.  **Conversion:** The `LightTransitionManager` uses the specified `curve` function to convert the desired perceived brightness into the corresponding _linear_ brightness value (0-255 or 0-99/100, depending on the device's native scale).
    
3.  **Stepped Commands:** For simulated transitions/dynamic control, the manager calculates intermediate steps along this converted linear scale.
    
4.  **Device Command:** The final, linearly scaled brightness value is sent as a standard `SET` command (e.g., Zigbee `Move to Level`, Z-Wave `Set`) to the device via its integration.
    

**Why this approach?**

*   **Universal Compatibility:** Ensures all dimmable lights in HA can benefit from perceptual dimming, even if their hardware doesn't natively support it.
    
*   **Consistency:** The same curve logic is applied uniformly across different protocols.
    
*   **Performance:** While simulation generates more commands, performing the curve calculation centrally is efficient, and the goal is to fine-tune the refresh rate to balance smoothness and network load.
    

## 5\. Detailed PR-by-PR Engineering Execution

### Phase 1: ESPHome Foundation (Internal Firmware Capabilities)

*   **Goal:** Equip ESPHome light components with the fundamental capabilities for smooth internal transitions and the framework for dynamic control.
    

#### PR 1.1: ESPHome - Internal `LightState` Time-Based Interpolation Refinement

*   **Description:** Enhance `LightState`'s internal handling of `transition_length` to ensure high-resolution, time-based interpolation of brightness and color changes. Optimize the existing transition mechanism to achieve maximum smoothness and prepare for more complex dimming curves.
    
*   **Detailed Changes:**
    
    *   **File:** `esphome/components/light/light_state.cpp`
        
    *   **Logic:** Review and potentially refactor the `loop()` method's transition calculation. Ensure `light_output` values are interpolated smoothly over `transition_length` using floating-point math, converting to integer PWM/LED values only at the final output stage. Improve precision for very short transitions or very long, subtle fades.
        
    *   **Considerations:** Avoid integer truncation issues. Ensure `millis()` or `micros()` are used for precise timing.
        
*   **Interactions:** Core for all subsequent ESPHome light features.
    
*   **Testing:** Unit tests for `LightState` interpolation correctness. Manual testing with various `transition_length` values to visually confirm smoothness.
    

#### PR 1.2: ESPHome - YAML Configuration for Custom Dimming Curves & Speed Profiles

*   **Description:** Add a top-level `dynamic_control_profiles` schema under `light:` component in ESPHome YAML for defining reusable `speed` and `curve` characteristics.
    
*   **Detailed Changes:**
    
    *   **Files:**
        
        *   `esphome/components/light/light_schema.yaml`: Add new `dynamic_control_profiles` key with sub-schemas for `speed` and `curve` definitions.
            
        *   `esphome/components/light/light_state.h`/`.cpp`: Add data structures (`struct LightCurve`, `struct LightSpeed`) to store parsed profile data.
            
        *   `esphome/components/light/light_output.h`/`.cpp`: Implement curve calculation logic (linear, logarithmic, S-curve, square law, custom points).
            
    *   **Example YAML:**
        
        ```
        light:
          - platform: ...
            name: "My Light"
            # ... other light config
            dynamic_control_profiles:
              speeds:
                slow: 10.0 # %/sec
                medium: 25.0
                fast: 50.0
              curves:
                logarithmic: # Predefined logarithmic curve (DALI-like)
                  type: logarithmic
                my_custom_curve:
                  type: custom
                  points:
                    - [0.0, 0.0]
                    - [25.0, 5.0]
                    - [75.0, 60.0]
                    - [100.0, 100.0]
        ```
        
    *   **Considerations:** Ensure curve formulas are correctly normalized (0-1 input to 0-1 output). Handle edge cases for custom points (e.g., non-monotonic, out-of-range).
        
*   **Interactions:** Provides the backend for defining and using curves/speeds for native ESPHome dynamic control.
    
*   **Testing:** YAML validation for new schema. Unit tests for curve calculation functions.
    

### Phase 2: ESPHome Native Dynamic Control

*   **Goal:** Implement the core on-device "move/stop" and "step" logic in ESPHome and enable reporting of its dynamic state.
    

#### PR 2.1: ESPHome - `LightCall` Expansion for `dynamic_control` Parsing

*   **Description:** Extend the `light.turn_on` service schema in ESPHome's Native API to accept the `dynamic_control` parameter and parse it into internal `LightCall` / `LightState` structures.
    
*   **Detailed Changes:**
    
    *   **Files:**
        
        *   `esphome/components/api/api_message.cpp` (and associated protobuf definition): Add `dynamic_control` field to the `LightCommand` message.
            
        *   `esphome/components/light/light_call.h`/`.cpp`: Add a `dynamic_control_params` struct/enum to `LightCall` to hold the parsed `type`, `direction`, `speed`, `curve`, `step_size`, `duration`.
            
        *   `esphome/components/light/light_state.cpp`: Update `on_light_command` to parse the new API message field into the `LightCall` object.
            
    *   **Considerations:** Ensure robust parsing of nested `dynamic_control` parameters.
        
*   **Interactions:** Enables Home Assistant to send the new rich commands to ESPHome devices.
    
*   **Testing:** Unit tests for Native API message parsing. Integration tests sending `light.turn_on` with `dynamic_control` and verifying internal ESPHome `LightCall` state.
    

#### PR 2.2: ESPHome - On-Device Continuous Brightness `move`/`stop`

*   **Description:** Implement the `loop()` logic within `LightState` to perform continuous brightness adjustment (`move` up/down, `stop`) based on received `dynamic_control` commands, using configured curves/speeds.
    
*   **Detailed Changes:**
    
    *   **Files:** `esphome/components/light/light_state.cpp`
        
    *   **Logic:**
        
        *   Introduce new internal state variables in `LightState` to track active `dynamic_control` (`is_moving`, `move_direction`, `move_speed`, `move_curve`, `target_brightness_dynamic`).
            
        *   In `loop()`, if `is_moving` is true, calculate the next brightness step based on `move_direction`, `move_speed`, `move_curve`, and elapsed time.
            
        *   Apply the `move_curve` using the logic from PR 1.2 to convert the perceived rate into a linear output change.
            
        *   Update the light's output.
            
        *   Handle `type: "stop"` by immediately setting `is_moving = false` and applying the current brightness (or last known brightness) to stop the movement.
            
        *   Manage `duration` parameter if present, calculating `speed` from it.
            
    *   **Considerations:** Smooth stop behavior. Accurate time-based progression. Handling reaching min/max brightness during `move`.
        
*   **Interactions:** Uses curve/speed profiles from PR 1.2, receives commands from PR 2.1.
    
*   **Testing:** Unit tests for `move`/`stop` logic. Hardware testing with a light, verifying smooth continuous dimming and immediate stops.
    

#### PR 2.3: ESPHome - On-Device Continuous Color `move`/`stop`/`step`

*   **Description:** Extend PR 2.2 to apply continuous control and stepping for color properties (hue, saturation, color temperature).
    
*   **Detailed Changes:**
    
    *   **Files:** `esphome/components/light/light_state.cpp`
        
    *   **Logic:** Extend the dynamic control state variables and `loop()` logic to manage color components (e.g., `move_direction_hue`, `move_speed_color_temp`). Apply `curve` logic to color transitions where appropriate (e.g., for color temperature).
        
    *   **Considerations:** Color spaces (HS, RGB, XY, CT) for interpolation. Complexities of perceived color changes vs. linear changes in color space values.
        
*   **Interactions:** Builds on PR 2.2.
    
*   **Testing:** Hardware testing with RGBW/CCT lights, verifying smooth continuous color changes.
    

#### PR 2.4: ESPHome - `dynamic_state` Reporting via Native API

*   **Description:** Add new attributes (`dynamic_state`, `active_speed_profile`, `active_curve_profile`, `dynamic_target_brightness`, etc.) to the `LightState` and ensure they are published via the Native API.
    
*   **Detailed Changes:**
    
    *   **Files:**
        
        *   `esphome/components/light/light_state.h`: Add new attributes to `LightState` class.
            
        *   `esphome/components/light/light_state.cpp`: Update these attributes within `loop()` and `on_light_command` methods when dynamic control is active.
            
        *   `esphome/components/api/api_message.cpp` (and protobuf): Add new fields to the `LightStateResponse` message.
            
        *   `esphome/components/api/custom_api_device.cpp`: Ensure these new state attributes are regularly pushed to the Home Assistant API.
            
    *   **Considerations:** Minimize API traffic while providing timely updates.
        
*   **Interactions:** Provides crucial feedback for Home Assistant Core.
    
*   **Testing:** Monitor API traffic and Home Assistant `light` entity states for accurate `dynamic_state` updates.
    

### Phase 3: Home Assistant Universal Handling

*   **Goal:** Enable Home Assistant Core to understand and orchestrate universal transitions and dynamic control, including simulation for non-native devices.
    

#### PR 3.1: HA Core - Introduce New `LightEntityFeature` Flags

*   **Description:** Add `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` to Home Assistant's `LightEntityFeature` enum.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/light/__init__.py`
        
    *   **Logic:** Add new bitmask values to the `LightEntityFeature` enum.
        
*   **Interactions:** Basis for HA Core's intelligent handling and integration declarations.
    
*   **Testing:** Simple Python tests to confirm enum values.
    

#### PR 3.2: HA Core - Universal Transition Simulation Logic

*   **Description:** Implement the core logic within `light/__init__.py` to simulate `transition_length` for entities that support `TRANSITION_SIMULATED` but not native `TRANSITION`. This will include the curve application logic.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/light/__init__.py` (Service handler for `light.turn_on`).
        
    *   **Logic (Conceptual `LightTransitionManager`):**
        
        1.  **Intercept `turn_on`:** When `turn_on` is called with `transition`.
            
        2.  **Check Native:** If `light.supported_features` has `TRANSITION`, pass call to integration.
            
        3.  **Check Simulated:** Else if `light.supported_features` has `TRANSITION_SIMULATED`:
            
            *   Read `current_brightness` and `target_brightness` (and color if applicable).
                
            *   Identify the `curve` (default to `logarithmic` if not specified in `dynamic_control`).
                
            *   **Curve Calculation:** Implement Python functions for `linear`, `logarithmic` (based on DALI), `s_curve`, `square_law`, and custom point interpolation. These functions will map a `progress` (0-1) to an `output_percentage` (0-100%).
                
            *   **Step Calculation:** Calculate a series of `N` intermediate brightness (0-255) and color values. The values will be determined by applying the chosen `curve` to a linear progression of "perceived" time/progress.
                
            *   **Scheduling:** Use `async_call_later` or similar to schedule `N` calls back to the light entity's `async_turn_on` (without `transition`) at regular intervals over the `transition_length`.
                
            *   **State Update:** Set `light.dynamic_state` to `simulated_transitioning`.
                
            *   **Cancellation:** Implement a mechanism to cancel an ongoing simulation if a new `light.turn_on` command for the same entity is received.
                
    *   **Considerations:** Optimal refresh rate for simulation (e.g., 20-50ms) to balance smoothness and network load. Handling different light models' min/max brightness/color values.
        
*   **Interactions:** Uses new `LightEntityFeature` flags.
    
*   **Testing:** Unit tests for curve functions. Integration tests verifying smooth dimming/color transitions for devices without native `TRANSITION` but with `TRANSITION_SIMULATED`.
    

#### PR 3.3: HA Core - Universal Dynamic Control Simulation Logic

*   **Description:** Extend the `LightTransitionManager` in `light/__init__.py` to handle `dynamic_control` parameters for lights that have `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED`.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/light/__init__.py` (Service handler for `light.turn_on`).
        
    *   **Logic (extension of PR 3.2):**
        
        1.  **Intercept `turn_on` with `dynamic_control`.**
            
        2.  **Check Native:** If `light.supported_features` has `DYNAMIC_CONTROL`, pass `dynamic_control` directly to integration.
            
        3.  **Check Simulated:** Else if `light.supported_features` has `DYNAMIC_CONTROL_SIMULATED`:
            
            *   **`type: "move"`:** Calculate incremental steps based on `direction`, `speed`, and `curve`. Continuously schedule `async_call_later` to send new `light.turn_on` commands. Update `dynamic_state` to `simulated_moving_brightness_up`/`down`/`color_up`/`down`. Manage reaching min/max.
                
            *   **`type: "stop"`:** Immediately cancel ongoing `move` simulation and send a final `light.turn_on` command to the light's current brightness/color to halt movement cleanly. Update `dynamic_state` to `idle`.
                
            *   **`type: "step"`:** Calculate the new target brightness/color based on `step_size` and `direction`. Send a single `light.turn_on` to this new target, optionally with a short `transition` (handled by PR 3.2's simulation if native `TRANSITION` is absent). Update `dynamic_state` to `simulated_transitioning` for the step duration.
                
    *   **Considerations:** Ensure robust cancellation logic. Handling `duration` for `move` and `step` to calculate appropriate `speed`/`transition`.
        
*   **Interactions:** Uses new `LightEntityFeature` flags.
    
*   **Testing:** Integration tests for `move`/`stop`/`step` on simulated devices. Verify `dynamic_state` changes correctly.
    

#### PR 3.4: HA Core - ESPHome Integration Update (Orchestration & State Consumption)

*   **Description:** Update `homeassistant/components/esphome/light.py` to correctly orchestrate commands and consume state from ESPHome devices.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/esphome/light.py`
        
    *   **Logic:**
        
        *   **Feature Declaration:** When creating the `EsphomeLight` entity:
            
            *   Set `_attr_supported_features` to include `LightEntityFeature.DYNAMIC_CONTROL` if the connected ESPHome device (based on its API version or reported capabilities) supports native dynamic control (from ESPHome PR 2.1+).
                
            *   Always include `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for dimmable ESPHome lights, allowing HA Core to simulate if native is not available. This provides a layered fallback.
                
        *   **Sending `dynamic_control`:** In `async_turn_on`, if `dynamic_control` is present and `LightEntityFeature.DYNAMIC_CONTROL` is declared (meaning the device supports it natively), package these parameters and send them via the ESPHome Native API.
            
        *   **Consuming `dynamic_state`:** Listen for `LightStateResponse` from the ESPHome device. Map the received `dynamic_state` (and `active_speed_profile`, `active_curve_profile`, `dynamic_target_brightness`) from the ESPHome API into the Home Assistant `light` entity's state attributes.
            
    *   **Considerations:** Ensure smooth transition of control from HA simulation to native ESPHome control when firmware is updated.
        
*   **Interactions:** Depends on ESPHome PRs 2.1 and 2.4. Integrates with HA Core PRs 3.1, 3.2, 3.3.
    
*   **Testing:** Integration tests with ESPHome devices running new firmware and old firmware. Verify native control is preferred, and simulation kicks in when needed. Verify `dynamic_state` is accurate.
    

### Phase 3b: Integration-Specific Updates (ZHA, Z-Wave JS)

*   **Goal:** Connect Home Assistant's new universal light functionality directly to these protocols' support for move/stop.
    

#### PR ZHA.1: ZHA - Implement `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to ZCL Commands

*   **Description:** Update ZHA's light platform to declare native `LightEntityFeature.DYNAMIC_CONTROL` for compatible devices and map the new `dynamic_control` service parameters to Zigbee Level Control Cluster commands.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/zha/light.py` (and potentially `zigpy` core for new Level Control commands).
        
    *   **Logic:**
        
        *   **Feature Declaration:** For `ZhaLight` entities: If the device supports the Level Control Cluster and its `Move`, `Stop`, and `Step` commands (determined by cluster capabilities in `zigpy`), add `LightEntityFeature.DYNAMIC_CONTROL` to `_attr_supported_features`.
            
        *   **`async_turn_on` Mapping:**
            
            *   If `dynamic_control: {type: 'move', direction: 'up', ...}` is received: Call `cluster.move(move_mode=0x00, rate=derived_rate, ...)` on the Level Control cluster.
                
            *   If `dynamic_control: {type: 'move', direction: 'down', ...}`: Call `cluster.move(move_mode=0x01, rate=derived_rate, ...)`
                
            *   If `dynamic_control: {type: 'stop', ...}`: Call `cluster.stop()` on the Level Control cluster.
                
            *   If `dynamic_control: {type: 'step', ...}`: Call `cluster.step(step_mode=0x00/0x01, step_size=derived_step, transition_time=derived_time, ...)`
                
        *   **Rate/Duration Derivation:** Map `speed` and `duration` from `dynamic_control` to Zigbee's "rate" (steps/second) and "transition time" (seconds/10ths of a second) as appropriate.
            
        *   **Curve Handling:** Note that Zigbee Level Control Cluster typically doesn't support dynamic curves. The `curve` parameter in `dynamic_control` will be ignored here, as HA Core's `LightTransitionManager` is responsible for applying the curve by sending stepped linear commands (fallback).
            
        *   **Simulated Fallback:** Ensure `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` are generally declared for ZHA dimmable lights, so HA Core's simulation can take over if native `TRANSITION` or `DYNAMIC_CONTROL` are not present or applicable.
            
*   **Interactions:** Integrates `dynamic_control` with native Zigbee commands.
    
*   **Testing:** Extensive testing with various Zigbee dimmers and bulbs, including those known to support `Move`/`Stop` (e.g., Philips Hue, IKEA TRÅDFRI). Verify native vs. simulated behavior based on device capabilities.
    

#### PR ZHA.2: ZHA - Report `dynamic_state` from Zigbee Devices

*   **Description:** Implement logic within ZHA to listen for Zigbee device reports and command responses, translating them into Home Assistant's `dynamic_state`.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/zha/light.py` (and relevant `zigpy` listeners).
        
    *   **Logic:**
        
        *   Listen for `LevelControl` cluster command responses (e.g., `Move` and `Stop` commands confirm receipt).
            
        *   Monitor `CurrentLevel` attribute reports (0x0008:0x0000).
            
        *   Infer `dynamic_state` based on:
            
            *   Received `Move` command (set `dynamic_state` to `moving_...`).
                
            *   Received `Stop` command or `Move to Level` without `transition` (set `dynamic_state` to `idle`).
                
            *   Continuous `CurrentLevel` attribute changes over a duration consistent with a transition.
                
        *   Update `light` entity's `dynamic_state` attribute.
            
*   **Interactions:** Provides UI feedback.
    
*   **Testing:** Verify `dynamic_state` changes correctly in HA when controlling ZHA lights via native ZHA commands or physical controls.
    

#### PR ZWAVE\_JS.1: Z-Wave JS - Implement `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Z-Wave Commands

*   **Description:** Update Z-Wave JS's light platform to declare native `LightEntityFeature.DYNAMIC_CONTROL` for compatible devices and map `dynamic_control` service parameters to Z-Wave Multilevel Switch and Color Switch Command Class commands.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/zwave_js/light.py` (and potentially `python-zwave-js` library).
        
    *   **Logic:**
        
        *   **Feature Declaration:** For `ZWaveJsLight` entities: If the Z-Wave node supports `Multilevel Switch Command Class` with `Start Level Change` (0x04) and `Stop Level Change` (0x05) commands, add `LightEntityFeature.DYNAMIC_CONTROL` to `_attr_supported_features`.
            
        *   **`async_turn_on` Mapping:**
            
            *   If `dynamic_control: {type: 'move', direction: 'up', ...}`: Call `node.async_send_command(CommandClass.MULTILEVEL_SWITCH.commands.StartLevelChange, { 'direction': 'up', 'duration': derived_duration, ... })`.
                
            *   If `dynamic_control: {type: 'move', direction: 'down', ...}`: Call `node.async_send_command(CommandClass.MULTILEVEL_SWITCH.commands.StartLevelChange, { 'direction': 'down', 'duration': derived_duration, ... })`.
                
            *   If `dynamic_control: {type: 'stop', ...}`: Call `node.async_send_command(CommandClass.MULTILEVEL_SWITCH.commands.StopLevelChange)`.
                
            *   `type: 'step'`: Z-Wave doesn't have a direct "step" command. This would likely be handled by calculating the new target and sending a `Multilevel Switch Set` command with a short `duration` (which HA Core's `LightTransitionManager` would handle via simulation if native `TRANSITION` is not present, or the device natively).
                
        *   **Rate/Duration Derivation:** Map `speed` and `duration` from `dynamic_control` to Z-Wave's "duration" field (in seconds or 10ms ticks).
            
        *   **Color Control:** Extend similar logic for `Color Switch Command Class` (0x33) for continuous color changes if supported.
            
        *   **Curve Handling:** Z-Wave JS also typically doesn't support dynamic curves at the protocol level. The `curve` parameter will be handled by HA Core's `LightTransitionManager` (fallback).
            
        *   **Simulated Fallback:** Ensure `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` are generally declared for Z-Wave dimmable lights, so HA Core's simulation can take over if native `TRANSITION` or `DYNAMIC_CONTROL` are not present or applicable.
            
*   **Interactions:** Integrates `dynamic_control` with native Z-Wave commands.
    
*   **Testing:** Extensive testing with various Z-Wave dimmers and bulbs. Verify native vs. simulated behavior.
    

#### PR ZWAVE\_JS.2: Z-Wave JS - Report `dynamic_state` from Z-Wave Devices

*   **Description:** Implement logic within Z-Wave JS to interpret device value notifications and node states, translating them into Home Assistant's `dynamic_state`.
    
*   **Detailed Changes:**
    
    *   **File:** `homeassistant/components/zwave_js/light.py` (and Z-Wave JS event listeners).
        
    *   **Logic:**
        
        *   Listen for `value_updated` events for the `Multilevel Switch` value.
            
        *   Listen for events/notifications specifically related to `Start Level Change` and `Stop Level Change` commands, if the device generates them.
            
        *   Infer `dynamic_state` based on:
            
            *   `Start Level Change` command execution (set `dynamic_state` to `moving_...`).
                
            *   `Stop Level Change` command execution or `Set` command without duration (set `dynamic_state` to `idle`).
                
            *   Continuous `Multilevel Switch` value changes over a duration consistent with a transition.
                
        *   Update `light` entity's `dynamic_state` attribute.
            
*   **Interactions:** Provides UI feedback.
    
*   **Testing:** Verify `dynamic_state` changes correctly in HA when controlling Z-Wave JS lights via native commands or physical controls.
    

### Phase 4: Ecosystem Integration & User Experience

*   **Goal:** Enhance the user-facing experience and encourage adoption across the Home Assistant ecosystem.
    

#### PR 4.1: HA Frontend - Basic Dynamic State UI Feedback

*   **Description:** Implement simple visual indicators in standard light cards (e.g., text, icon changes) to show when a light's `dynamic_state` is active.
    
*   **Detailed Changes:**
    
    *   **Files:** `homeassistant/frontend/src/components/ha-card.ts`, `homeassistant/frontend/src/panels/lovelace/cards/hui-light-card.ts`, `homeassistant/frontend/src/state/ha-panel-states.ts`
        
    *   **Logic:** Update the light entity properties to expose `dynamic_state` to the frontend. Add conditional rendering for a small text indicator (e.g., "Fading", "Dimming Up") or a subtle animation on the light icon when `dynamic_state` is not `idle`.
        
*   **Interactions:** User-facing enhancement.
    
*   **Testing:** Visual confirmation in different UI contexts (Lovelace cards, Developer Tools -> States).
    

#### PR 4.2: ESPHome - Convenient Local Button Bindings

*   **Description:** Add simplified YAML syntax in ESPHome to easily bind `binary_sensor` events (e.g., `on_press`, `on_release`) to trigger the internal light `move`/`stop` functions for ultra-responsive local dimming.
    
*   **Detailed Changes:**
    
    *   **Files:** `esphome/components/binary_sensor/binary_sensor.yaml`, `esphome/components/binary_sensor/binary_sensor.cpp`
        
    *   **Logic:** Extend `binary_sensor` actions to include `light.move` and `light.stop` (or similar direct actions targeting the light component itself). These actions would directly call the internal `LightState` methods (from PR 2.2/2.3) without going through the Native API.
        
    *   **Example YAML:**
        
        ```
        binary_sensor:
          - platform: gpio
            pin: GPIO1
            name: "Dimmer Up Button"
            on_press:
              then:
                - light.turn_on:
                    id: my_light
                    dynamic_control:
                      type: move
                      direction: up
            on_release:
              then:
                - light.turn_on:
                    id: my_light
                    dynamic_control:
                      type: stop
        ```
        
*   **Interactions:** Improves local control responsiveness.
    
*   **Testing:** Hardware testing with physical buttons and ESPHome lights.
    

#### PR 4.3: Documentation & Developer Guidance

*   **Description:** Comprehensive updates to ESPHome and Home Assistant documentation covering the new features.
    
*   **Detailed Changes:**
    
    *   **Files:** `home-assistant.io` repository, `esphome.io` repository.
        
    *   **Content:**
        
        *   **Home Assistant Light Domain:** Detailed explanation of the `dynamic_control` service parameter, new `LightEntityFeature` flags, `dynamic_state` attribute. Explanation of native vs. simulated handling. Guidance on choosing dimming curves.
            
        *   **ESPHome Light Component:** New YAML options for `dynamic_control_profiles`, explanation of native dynamic control. Examples of local button bindings.
            
        *   **ZHA/Z-Wave JS Integrations:** Document which features are natively supported and which rely on HA Core simulation.
            
        *   **Developer Guidelines:** How other integration developers can adopt `DYNAMIC_CONTROL` and `_SIMULATED` features.
            
*   **Interactions:** Critical for user adoption and ecosystem growth.
    
*   **Testing:** Peer review of documentation clarity and accuracy.
    

#### PR 4.4: Community Blueprint & Integration Examples (Ongoing)

*   **Description:** Collaborate with the community to create example automations and blueprints that leverage the new `dynamic_control` features.
    
*   **Detailed Changes:** (This is an ongoing effort, not a single PR)
    
    *   Publish examples in the Home Assistant Community Forum and Blueprints exchange.
        
    *   Examples: "Sunrise Alarm with Perceptual Curve", "Hold-to-Dim for Any Light (with HA simulation fallback)", "Dynamic Scene Changes".
        
*   **Interactions:** Drives adoption and demonstrates new capabilities.
    
*   **Testing:** Community feedback and usage.
    

## 6\. Interactions and Control Flow

**High-Level Flow: User Action -> Light Change**

1.  **User Initiates Action:**
    
    *   UI slider/button (frontend)
        
    *   Automation (`light.turn_on` service call)
        
    *   Physical button (triggers `light.turn_on` via automation or native binding)
        
2.  **Home Assistant `light.turn_on` Service Handler (`homeassistant/components/light/__init__.py` - conceptual `LightTransitionManager`):**
    
    *   Receives `target_brightness`, `transition`, `dynamic_control` (with `type`, `direction`, `speed`, `curve`, `step_size`, `duration`).
        
    *   **Capability Check:** Queries `light.supported_features` for `DYNAMIC_CONTROL` and `TRANSITION`.
        
    *   **If Native `DYNAMIC_CONTROL` is supported (e.g., new ESPHome firmware, some Zigbee devices):**
        
        *   Parses `dynamic_control` parameters.
            
        *   Passes `dynamic_control` (and other standard `turn_on` data like `brightness_pct`, `color`) directly to the integration's `async_turn_on` method.
            
    *   **Else if Native `TRANSITION` is supported (e.g., Hue, some ZHA/Z-Wave):**
        
        *   If `transition` is present, passes `transition` (and other `turn_on` data) directly to the integration's `async_turn_on` method.
            
    *   **Else if `DYNAMIC_CONTROL_SIMULATED` is supported:**
        
        *   **SIMULATION LOGIC:** The `LightTransitionManager` initiates software-based control.
            
            *   **Curve Application:** Converts perceived input (from `dynamic_control` or `transition` target) to linear output values based on the `curve` parameter (defaulting to `logarithmic`).
                
            *   **Step Generation:** Calculates small, incremental steps for brightness/color.
                
            *   **Scheduling:** Uses `async_call_later` to schedule rapid, repeated `light.turn_on` calls (without `transition` or `dynamic_control`) back to the integration, sending these discrete steps.
                
            *   **State Update:** Sets the entity's `dynamic_state` to `simulated_moving_...` or `simulated_transitioning`.
                
            *   **Cancellation:** Manages canceling existing scheduled calls if a new command arrives.
                
    *   **Else (No Native or Simulated Advanced Control):**
        
        *   `transition` and `dynamic_control` parameters are effectively ignored.
            
        *   Standard `brightness`/`color` changes are sent as a single, immediate command to the integration.
            
        *   `dynamic_state` remains `idle`.
            
3.  **Integration (e.g., ESPHome, ZHA, Z-Wave JS):**
    
    *   Receives command from HA Core.
        
    *   **If native `dynamic_control` received (e.g., from new ESPHome firmware):** Translates to protocol-specific "move/stop" or "step" commands and sends to device.
        
    *   **If simulated `turn_on` steps received:** Translates each discrete step to a standard "set brightness/color" command with an optional small duration for smoothness and sends to device.
        
4.  **Device:** Executes the command.
    

**High-Level Flow: Device State -> Home Assistant Update**

1.  **Device Status Change:**
    
    *   Completes a native transition/move.
        
    *   Receives a `set` command.
        
    *   Physical control.
        
    *   Reports a dynamic state (new ESPHome firmware).
        
2.  **Protocol Report:** Device sends status update (Zigbee attribute report, Z-Wave `Value Notification`, ESPHome Native API `LightStateResponse`).
    
3.  **Integration (e.g., ZHA, Z-Wave JS, ESPHome):**
    
    *   Receives protocol report.
        
    *   Parses new brightness, color, and _`dynamic_state`_ (for new ESPHome firmware or inferred from ZHA/Z-Wave `Start/Stop Level Change` command reports).
        
    *   If HA Core is simulating, the `LightTransitionManager` will also be updating the `dynamic_state`. The integration's reported state would take precedence if it indicates native activity.
        
4.  **Home Assistant Entity State Update:** The `light` entity's state in Home Assistant is updated, including the new `dynamic_state` attribute, which is then reflected in the UI and available for automations.
    

## 7\. Backward Compatibility

All proposed changes prioritize backward compatibility:

*   **New Parameters are Optional:** `dynamic_control` is an entirely new, optional parameter to `light.turn_on`. Existing automations will continue to function as before.
    
*   **Feature Flags:** The new `LightEntityFeature` flags (e.g., `_SIMULATED`) are additive. Integrations can gradually opt-in or expose these capabilities.
    
*   **Graceful Fallback:** The layered approach ensures that if a device or its integration doesn't support a new feature, Home Assistant will either simulate it (if the `_SIMULATED` flag is set) or gracefully ignore the parameter, preserving current behavior.
    
*   **ESPHome Firmware:** New ESPHome firmware will be backward compatible with older Home Assistant versions (they just won't expose the new `dynamic_state` or interpret `dynamic_control` natively). Newer Home Assistant versions will automatically detect the enhanced capabilities of updated ESPHome devices.
    

## 8\. Future Work / Open Questions

*   **Advanced Curve Control:** Could users define curves directly in the UI? Could curves be applied to color transitions in more sophisticated ways (e.g., hue rotation curves)?
    
*   **Integration-Specific Optimizations:** Further research into specific quirks or advanced features of Zigbee and Z-Wave devices that could offer even more native dynamic control or state reporting.
    
*   **Battery Devices:** How do frequent commands for simulation affect battery life for battery-powered light devices? This may need to be a documented trade-off or have opt-out options.
    
*   **Group Behavior:** How do these new features interact with light groups? Ideally, the group entity would expose the same capabilities and orchestrate commands to members.
    
*   **Frontend UI:** Develop rich UI controls (e.g., sliders that react dynamically, "move" buttons) that fully leverage the new `dynamic_control` service calls and `dynamic_state` feedback.
    

## 9\. Team & Responsibilities

*   **Core ESPHome Developers:** Lead C++ firmware development (Phase 1, 2, 4.2).
    
*   **Core Home Assistant Developers (Light Domain):** Lead Python development for HA Core (Phase 3).
    
*   **Home Assistant Integration Maintainers (ZHA, Z-Wave JS):** Lead Python development for their respective integrations (Phase 3b).
    
*   **Frontend Developers:** Lead UI/UX implementation (Phase 4.1).
    
*   **Technical Writers:** Lead documentation (Phase 4.3).
    
*   **Community:** Crucial for testing, feedback, and blueprint creation (Phase 4.4).
    

## 10\. High-Level Timeline

*   **Phase 1 (ESPHome Foundation):** ~1.5 months
    
*   **Phase 2 (ESPHome Native Dynamic Control):** ~2 months
    
*   **Phase 3 (Home Assistant Universal Handling + ZHA/Z-Wave JS Updates):** ~2.5 months
    
*   **Phase 4 (Ecosystem Integration & UX):** ~1.5 months (ongoing for documentation and community contribution)
    

**Total Estimated Project Duration:** ~7.5 - 8 months (allowing for review, iteration, and unforeseen complexities).

This plan provides a detailed roadmap to deliver a significantly improved and unified lighting control experience in Home Assistant, making smart lights truly intelligent and responsive.