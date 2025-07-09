# Detailed Execution Plan: Implementing Universal Light Move/Stop Control

This document provides a step-by-step guide for a software engineer/community member to implement and merge support for `move`/`stop` dynamic light control and `dynamic_state` reporting into Home Assistant and ESPHome.

## 1. Project Scope & Goal

The immediate goal for this plan is to enable **smooth, interruptible continuous dimming and color adjustment** using `move` and `stop` commands, along with clear `dynamic_state` feedback. This will be achieved by:

- Adding native `move`/`stop` capabilities to ESPHome lights.

- Extending Home Assistant's `light.turn_on` service to support a `dynamic_control` parameter with `type: "move"` and `type: "stop"`.

- Updating the ESPHome integration in Home Assistant to leverage these native capabilities.

- Introducing a `dynamic_state` attribute to `light` entities for real-time feedback.

- Laying the groundwork for Home Assistant Core to simulate `move`/`stop` for devices without native support.

This plan focuses on ESPHome as the initial native implementation target due to its end-to-end control, making it easier to demonstrate the full workflow.

## 2. General Open-Source Contribution Workflow

Before diving into specific PRs, here's the standard workflow for contributing to Home Assistant and ESPHome:

1. **Fork the Repository:** Create your own fork of `home-assistant/core` and `esphome/esphome` on GitHub.

2. **Clone Your Fork:** Clone your forked repositories to your local development machine.

````text
    git clone https://github.com/YOUR_GITHUB_USERNAME/home-assistant.git
    git clone https://github.com/YOUR_GITHUB_USERNAME/esphome.git

```text

3. **Set Up Development Environment:**

    - **Home Assistant:** Follow the official developer documentation for setting up a development environment (usually involving `venv` and `script/setup`).

    - **ESPHome:** Install ESPHome (e.g., `pip install esphome`) and ensure you can compile and flash firmwares.

4. **Create a New Branch:** For _each_ PR, create a new, descriptive branch.

```text
    git checkout -b feature/light-dynamic-control-esphome-move-stop

```text

5. **Implement Changes:** Make your code modifications.

6. **Write Tests:** Add unit tests and/or integration tests for your new functionality.

7. **Run Linting & Tests:** Ensure your code adheres to style guides and all existing tests pass.

    - Home Assistant: `script/lint`, `pytest`

    - ESPHome: `tox -e lint`, `tox -e unit`

8. **Commit Changes:** Write clear, concise commit messages.

9. **Push to Your Fork:** Push your branch to your GitHub fork.

10. **Open Pull Request (PR):** Go to your GitHub fork, and you'll see a prompt to open a PR to the upstream `home-assistant/core` or `esphome/esphome` repository.

    - **PR Description:** Crucially, write a detailed PR description explaining:

        - What the PR does.

        - Why it's needed (referencing the problem statement).

        - How it was tested.

        - Any breaking changes (should be none for these initial PRs).

        - Link to this overall plan if helpful for context.

    - **Link Related Issues:** If there are existing feature requests (like those we found), link them in your PR description.

11. **Address Feedback:** Maintainers will review your code and provide feedback. Be prepared to iterate and make changes.

12. **Merge:** Once approved, your PR will be merged!

## 3\. Detailed Implementation Plan (Step-by-Step PRs)

We'll break this down into logical, mergeable PRs. Each PR should be self-contained and ideally pass all tests on its own.

### Part 1: ESPHome Native `move`/`stop` and `dynamic_state`

This part focuses entirely on the ESPHome firmware and its Native API.

#### **PR 1.1: ESPHome - Implement `LightState` Internal `move`/`stop` Logic**

- **Goal:** Add the core continuous dimming/color change and immediate stop logic directly into the ESPHome light component's `LightState`. This is the "brain" of the on-device dynamic control.

- **Files to Modify:**

    - `esphome/components/light/light_state.h`

    - `esphome/components/light/light_state.cpp`

- **Logic to Implement:**

    1. **Internal State Variables:** Add private member variables to `LightState` to manage dynamic control:

        - `bool is_moving_dynamic_{false};`

        - `LightCall::DynamicControlType dynamic_control_type_{LightCall::DYNAMIC_CONTROL_NONE};`

        - `LightCall::DynamicControlDirection dynamic_control_direction_{LightCall::DYNAMIC_CONTROL_DIRECTION_NONE};`

        - `float dynamic_control_speed_{0.0f};` (e.g., brightness % per second)

        - `float dynamic_control_target_brightness_{0.0f};` (if moving to a specific target)

        - `float dynamic_control_target_color_temp_{0.0f};` (if moving color temp)

        - `float dynamic_control_target_hue_{0.0f};` (if moving hue)

        - `float dynamic_control_target_saturation_{0.0f};` (if moving saturation)

        - `uint32_t dynamic_control_start_time_{0};`

    2. **`LightState::loop()` Updates:**

        - Modify the `loop()` method. If `is_moving_dynamic_` is `true`:

            - Calculate elapsed time since `dynamic_control_start_time_`.

            - Based on `dynamic_control_direction_` and `dynamic_control_speed_`, calculate the _next target brightness/color value_.

            - Apply this value using the existing `set_brightness_` (and color) methods.

            - Handle reaching 0% or 100% (or min/max color temp/hue/sat). Stop moving if limits are hit.

    3. **`stop()` Method Integration:** The `nohat` PR's `stop_` flag is a good starting point. Extend `LightState::on_light_command` to handle an incoming `stop` signal:

        - If a `LightCall` indicates `stop` (from a future API field), immediately set `is_moving_dynamic_ = false` and `active_transition_ = false`. This will freeze the light at its current output.

- **Testing:**

    - **Unit Tests:** Add tests for `LightState` to verify:

        - Brightness/color changes correctly over time with `move` command.

        - `stop` command immediately halts movement.

        - Min/max limits are respected.

    - **Manual Testing:** Flash an ESPHome device with this firmware. Use `api.light.turn_on` service calls (via Home Assistant's Developer Tools -> Services, or a simple ESPHome script) to manually trigger `move` (e.g., `brightness_pct: 100, transition: 60s`) and then `stop` (you'll need to manually craft a `LightCall` for `stop` via a custom component or script for now, as the HA side isn't ready yet). Observe smooth movement and immediate halts.

#### **PR 1.2: ESPHome - Native API Extension for `dynamic_control`**

- **Goal:** Extend the ESPHome Native API to allow Home Assistant to send the new `dynamic_control` parameters.

- **Files to Modify:**

    - `esphome/components/api/api_message.proto` (protobuf definition)

    - `esphome/components/api/api_message.cpp` (parsing logic)

    - `esphome/components/light/light_call.h`

- **Logic to Implement:**

    1. **Protobuf Definition:** Add a new `DynamicControl` message to `api_message.proto`:

```text
        message LightCommand {
          // ... existing fields ...
          optional DynamicControl dynamic_control = 10; // Assign a new field number
        }

        message DynamicControl {
          enum Type {
            NONE = 0;
            MOVE = 1;
            STOP = 2;
            STEP = 3;
          }
          enum Direction {
            NONE = 0;
            UP = 1;
            DOWN = 2;
          }
          optional Type type = 1;
          optional Direction direction = 2;
          optional float speed = 3; // e.g., %/sec or value/sec
          optional float step_size = 4; // for STEP type
          optional float duration = 5; // for MOVE/STEP, overrides speed if both
        }
```text

    2. **`LightCall` Structure:** Update `LightCall` to include a `DynamicControl` struct that mirrors the protobuf definition.

    3. **Parsing:** Modify `api_message.cpp` to parse the incoming `DynamicControl` protobuf message into the `LightCall` object.

    4. **`LightState::on_light_command`:** Update this method to interpret the `dynamic_control` field from the incoming `LightCall` and set the internal `LightState` variables (from PR 1.1) accordingly.

- **Testing:**

    - **Unit Tests:** Verify correct parsing of the new `DynamicControl` message.

    - **Manual Testing:** Use a custom Home Assistant script or a simple Python client to send a raw Native API `LightCommand` with the new `dynamic_control` field. Verify the ESPHome device responds correctly (e.g., starts moving, stops).

#### **PR 1.3: ESPHome - `dynamic_state` Reporting via Native API**

- **Goal:** Enable ESPHome devices to report their current dynamic activity back to Home Assistant.

- **Files to Modify:**

    - `esphome/components/api/api_message.proto`

    - `esphome/components/api/api_message.cpp`

    - `esphome/components/light/light_state.h`

    - `esphome/components/light/light_state.cpp`

    - `esphome/components/api/custom_api_device.cpp`

- **Logic to Implement:**

    1. **Protobuf Definition:** Add a new `dynamic_state` enum field to the `LightStateResponse` message in `api_message.proto`:

```text
        message LightStateResponse {
          // ... existing fields ...
          enum DynamicState {
            IDLE = 0;
            TRANSITIONING = 1;
            MOVING_BRIGHTNESS_UP = 2;
            MOVING_BRIGHTNESS_DOWN = 3;
            MOVING_COLOR_UP = 4;
            MOVING_COLOR_DOWN = 5;
          }
          optional DynamicState dynamic_state = 11; // Assign a new field number
        }
```text

    2. **`LightState` Tracking:** In `light_state.h`/`.cpp`, add an internal `DynamicState` variable to `LightState` and update it in `loop()` and `on_light_command` based on whether a transition or dynamic move is active.

    3. **API Reporting:** In `custom_api_device.cpp`, ensure that `LightStateResponse` messages include the current `dynamic_state` when sent to Home Assistant.

- **Testing:**

    - **Unit Tests:** Verify `LightState`'s internal `dynamic_state` changes correctly.

    - **Manual Testing:** Flash ESPHome device. Observe `dynamic_state` updates in Home Assistant's Developer Tools -> States when triggering transitions or `move`/`stop` commands (even if manually crafted via `api.light.turn_on` for now).

### Part 2: Home Assistant Core Integration (ESPHome Specific)

This part focuses on Home Assistant Core and its ESPHome integration.

#### **PR 2.1: HA Core - Introduce New `LightEntityFeature.DYNAMIC_CONTROL` Flag**

- **Goal:** Add the new feature flag to Home Assistant Core.

- **Files to Modify:**

    - `homeassistant/components/light/__init__.py`

- **Logic to Implement:**

    1. Add `DYNAMIC_CONTROL = 0x40` (or `64`) to the `LightEntityFeature` enum.

- **Testing:** Simple Python test to confirm the new enum value.

#### **PR 2.2: HA Core - `light.turn_on` Service Extension for `dynamic_control`**

- **Goal:** Extend the `light.turn_on` service schema to accept the new `dynamic_control` parameter.

- **Files to Modify:**

    - `homeassistant/components/light/__init__.py` (service schema definition)

- **Logic to Implement:**

    1. Modify the `LIGHT_TURN_ON_SCHEMA` to include the `dynamic_control` field with its nested `type`, `direction`, `speed`, `step_size`, `duration` parameters.

    2. **Initial Handler Logic (Placeholder):** For now, the `async_turn_on` method in `LightEntity` (or the service handler) will simply pass this `dynamic_control` parameter to the integration's `async_turn_on` method if the integration declares `LightEntityFeature.DYNAMIC_CONTROL`. No simulation logic yet, just passing through.

- **Testing:**

    - **Unit Tests:** Verify the new service schema validates correctly.

    - **Manual Testing:** Use Developer Tools -> Services to call `light.turn_on` with `dynamic_control` parameters. Verify it doesn't raise schema errors.

#### **PR 2.3: HA ESPHome Integration Update (Consume Native `dynamic_control` and `dynamic_state`)**

- **Goal:** Update the Home Assistant ESPHome integration to declare `DYNAMIC_CONTROL` support and correctly send/receive the new `dynamic_control` and `dynamic_state` data via the Native API.

- **Files to Modify:**

    - `homeassistant/components/esphome/light.py`

- **Logic to Implement:**

    1. **Feature Declaration:** In the `EsphomeLight` entity's `_attr_supported_features` property:

        - Add `LightEntityFeature.DYNAMIC_CONTROL` if the connected ESPHome device's API version (or a new capability flag from ESPHome) indicates support for the new `dynamic_control` protobuf message.

        - For now, _do not_ add `_SIMULATED` flags yet. Those come in Part 3.

    2. **Sending `dynamic_control`:** In `EsphomeLight.async_turn_on`:

        - If `dynamic_control` is present in the `kwargs`, translate it into the ESPHome Native API `LightCommand`'s `dynamic_control` protobuf message.

        - Pass this `LightCommand` to the ESPHome device.

    3. **Consuming `dynamic_state`:** In `EsphomeLight.async_on_esphome_state_update`:

        - Read the `dynamic_state` field from the incoming `LightStateResponse` protobuf message.

        - Set the `EsphomeLight` entity's `_attr_dynamic_state` (a new internal attribute) to the corresponding Home Assistant `dynamic_state` enum value.

        - Trigger a state update for the entity.

- **Testing:**

    - **Integration Tests:** This is where it all comes together.

        - Run Home Assistant with an ESPHome device flashed with PR 1.1-1.3 firmware.

        - Call `light.turn_on` with `dynamic_control: {type: move, direction: up, speed: 10}`. Verify the ESPHome light smoothly dims up.

        - Call `light.turn_on` with `dynamic_control: {type: stop}`. Verify the light halts immediately.

        - Observe the `dynamic_state` attribute in Developer Tools -> States for the ESPHome light. It should change from `idle` to `moving_brightness_up` and back to `idle`.

    - **Manual Testing:** Same as above, but interactive.

### Part 3: Home Assistant Core Simulation & Integration Updates

This part builds on the foundation, enabling the `dynamic_control` service for _all_ lights, even those without native support, and integrating specific platforms.

#### **PR 3.1: HA Core - Introduce `LightEntityFeature._SIMULATED` Flags**

- **Goal:** Add the flags that signal HA Core can simulate dynamic control.

- **Files to Modify:**

    - `homeassistant/components/light/__init__.py`

- **Logic to Implement:**

    1. Add `TRANSITION_SIMULATED = 0x80` and `DYNAMIC_CONTROL_SIMULATED = 0x100` to `LightEntityFeature`.

- **Testing:** Simple Python test.

#### **PR 3.2: HA Core - Implement `LightTransitionManager` for `dynamic_control` Simulation**

- **Goal:** Implement the logic in Home Assistant Core to simulate `move`/`stop` for lights that declare `DYNAMIC_CONTROL_SIMULATED`.

- **Files to Modify:**

    - `homeassistant/components/light/__init__.py` (main light service handler)

- **Logic to Implement:**

    1. **Service Handler Logic:** In the `light.turn_on` service handler:

        - If `dynamic_control` is present in `kwargs`:

            - Check `light.supported_features`.

            - If `LightEntityFeature.DYNAMIC_CONTROL` is _not_ present, but `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` _is_ present:

                - Initiate the simulation logic (as detailed in the previous "Engineering Execution Document" under Phase 3.3). This involves calculating steps and scheduling `async_call_later` calls back to the light entity with incremental `brightness_pct` (or color) values.

                - Manage the `dynamic_state` attribute for the entity (e.g., `simulated_moving_brightness_up`).

                - Implement cancellation logic for `type: "stop"`.

    2. **Curve Integration (Initial):** For `move` operations, default to a `logarithmic` curve if `curve` is not specified. Use a simple linear interpolation for now; full curve implementation can be a later PR.

- **Testing:**

    - **Integration Tests:** Test with a simple mock light integration that _only_ declares `DYNAMIC_CONTROL_SIMULATED`. Verify `move`/`stop` works via simulation.

    - **Manual Testing:** Test with an existing integration like WiZ or Tuya (after they declare `_SIMULATED` flags in a later PR).

#### **Part 3b: Home Assistant Integration Updates (Specific Platforms)**

This section details the necessary changes for various lighting integrations to adopt the new `dynamic_control` API, either natively or by declaring simulated support. Each of these would typically be a separate PR.

##### **PR ZHA.1: HA ZHA - Declare `DYNAMIC_CONTROL` & Map `dynamic_control` to Zigbee Commands**

- **Goal:** Enable ZHA to leverage native Zigbee Level Control `Move`/`Stop` commands.

- **Files to Modify:** `homeassistant/components/zha/light.py`, `homeassistant/components/zha/core/channels/lighting.py`

- **Logic to Implement:**

    1. **Feature Declaration:** In `ZHALight` entity setup, if the Zigbee device's Level Control cluster supports `Move` and `Stop` commands, add `LightEntityFeature.DYNAMIC_CONTROL`. Always add `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for dimmable lights as fallback.

    2. **Mapping `dynamic_control`:** In `ZHALight.async_turn_on`, translate `dynamic_control` parameters (`type: move`, `direction`, `speed`, `type: stop`, `type: step`) into appropriate Zigbee Level Control cluster commands (`Move to Level with On/Off`, `Move`, `Stop`, `Step`).

    3. **Report `dynamic_state`:** Infer `dynamic_state` from sent commands or received Zigbee attribute reports for the Level Control cluster.

- **Testing:** Integration tests with ZHA-compatible lights that support native Level Control.

##### **PR ZWAVE\_JS.1: HA Z-Wave JS - Declare `DYNAMIC_CONTROL` & Map `dynamic_control` to Z-Wave Commands**

- **Goal:** Enable Z-Wave JS to leverage native Z-Wave `Start/Stop Level Change` commands.

- **Files to Modify:** `homeassistant/components/zwave_js/light.py`

- **Logic to Implement:**

    1. **Feature Declaration:** In `ZWaveJsLight` entity setup, if the Z-Wave device's Multilevel Switch Command Class supports `Start Level Change` and `Stop Level Change`, add `LightEntityFeature.DYNAMIC_CONTROL`. Always add `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` as fallback.

    2. **Mapping `dynamic_control`:** In `ZWaveJsLight.async_turn_on`, translate `dynamic_control` parameters into Z-Wave `Multilevel Switch Start Level Change` and `Stop Level Change` commands.

    3. **Report `dynamic_state`:** Infer `dynamic_state` from sent commands or received Z-Wave value notifications.

- **Testing:** Integration tests with Z-Wave JS-compatible lights that support native Multilevel Switch commands.

##### **PR Z2M.1: HA MQTT Light - Declare `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Z2M MQTT Payloads**

- **Goal:** Enable Home Assistant's `mqtt_light` platform to leverage Zigbee2MQTT's native `brightness_move`/`stop` commands.

- **Files to Modify:** `homeassistant/components/mqtt/light.py`

- **Logic to Implement:**

    1. **Feature Declaration:** When an `mqtt_light` entity is set up (via MQTT Discovery), inspect its exposed capabilities (e.g., `brightness_move`, `color_temp_move`). If supported, add `LightEntityFeature.DYNAMIC_CONTROL`. Always declare `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for all dimmable Z2M lights as fallback.

    2. **Mapping `dynamic_control`:** In `mqtt_light.async_turn_on`:

        - **`type: "move"`:** Translate `direction` and `speed` into `{"brightness_move": <speed>}` (for up) or `{"brightness_move": -<speed>}` (for down), or `{"color_temp_move": <speed>}` / `{"color_temp_move": -<speed>}`. Publish to Z2M's `command_topic`.

        - **`type: "stop"`:** Publish `{"brightness_move": 0}` (or `{"color_temp_move": "stop"}`).

        - **`type: "step"`:** Publish `{"brightness_step": <step_size>}` or `{"color_temp_step": <step_size>}`.

- **Testing:** Integration tests with Z2M instance and compatible Zigbee lights.

##### **PR Z2M.2: HA MQTT Light - Report `dynamic_state` from Z2M Devices**

- **Goal:** Allow Home Assistant to accurately reflect the `dynamic_state` of Z2M-connected lights.

- **Files to Modify:** `homeassistant/components/mqtt/light.py`

- **Logic to Implement:**

    1. **Inferring `dynamic_state`:** When Home Assistant sends a `brightness_move` command, optimistically set `dynamic_state` to `moving_brightness_up`/`down`. When a `brightness_move: 0` is sent, set to `idle`.

    2. **Update Entity State:** Set the `_attr_dynamic_state` of the `mqtt_light` entity and trigger a state update.

- **Testing:** Integration tests verifying `dynamic_state` changes.

##### **PR Z2M.3: HA MQTT - Standardized `event_data` for Z2M Controllers**

- **Goal:** Ensure Z2M-connected remotes and switches emit standardized `event` entities.

- **Files to Modify:** `homeassistant/components/mqtt/device_trigger.py`

- **Logic to Implement:**

    1. **Event Entity Creation:** Ensure MQTT integration creates `event` entities for Z2M controllers.

    2. **Standardized `event_data`:** Map Z2M's `action` or `click` properties from MQTT messages to our `ControllerEventData` schema (e.g., `{"action": "single", "action_id": "button_1"}`).

- **Testing:** Integration tests verifying standardized event data.

##### **PR Tasmota.1 (Revised): HA Tasmota Light - Declare `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Tasmota MQTT Commands**

- **Goal:** Leverage Tasmota's native `Dimmer >`, `Dimmer <`, and `Dimmer !` commands.

- **Files to Modify:** `homeassistant/components/tasmota/light.py`

- **Logic to Implement:**

    1. **Feature Declaration:** If the Tasmota device supports the `Dimmer` command, add `LightEntityFeature.DYNAMIC_CONTROL`. Still declare `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` as fallback.

    2. **Mapping `dynamic_control`:** In `TasmotaLight.async_turn_on`:

        - **`type: "move"`:** If `direction: "up"`, publish `Dimmer >`. If `direction: "down"`, publish `Dimmer <`. `speed` parameter will be largely ignored for native commands (Tasmota uses its `DimmerSpeed` setting).

        - **`type: "stop"`:** Publish `Dimmer !`.

        - **`type: "step"`:** Publish `Dimmer +{step_size}` or `Dimmer -{step_size}`.

- **Testing:** Integration tests with Tasmota device.

##### **PR Tasmota.2 (Unchanged): HA Tasmota Light - Report `dynamic_state` from Tasmota Devices**

- **Goal:** Allow Home Assistant to accurately reflect the `dynamic_state` of Tasmota-connected lights.

- **Files to Modify:** `homeassistant/components/tasmota/light.py`

- **Logic to Implement:** Infer `dynamic_state` based on `Dimmer >`, `Dimmer <`, and `Dimmer !` commands sent, and update the entity's `_attr_dynamic_state`.

- **Testing:** Integration tests verifying `dynamic_state` changes.

##### **PR Tasmota.3 (Unchanged): HA Tasmota - Standardized `event_data` for Tasmota Controllers**

- **Goal:** Ensure Tasmota-based physical controls emit standardized `event` entities.

- **Files to Modify:** `homeassistant/components/tasmota/device_trigger.py`

- **Logic to Implement:** Map Tasmota's MQTT messages for button/encoder actions to `ControllerEventData` schema.

- **Testing:** Integration tests verifying standardized event data.

##### **PR Hue.1: HA Philips Hue Light - Declare `_SIMULATED` Flags**

- **Goal:** Inform Home Assistant Core that Hue lights can be reliably simulated for dynamic control and transitions.

- **Files to Modify:** `homeassistant/components/hue/light.py`

- **Logic to Implement:**

    1. **Feature Declaration:** Add `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` to `HueLight`'s `_attr_supported_features`. Do NOT add `LightEntityFeature.DYNAMIC_CONTROL`.

- **Testing:** Integration tests verifying smooth simulation and halting.

##### **PR Hue.2: HA Philips Hue - Standardized `event_data` for Hue Remotes**

- **Goal:** Ensure Hue remotes emit standardized `event` entities.

- **Files to Modify:** `homeassistant/components/hue/device_trigger.py`

- **Logic to Implement:** Map `hue_event` data to our `ControllerEventData` schema (e.g., `{"action": "single", "action_id": "button_1"}`).

- **Testing:** Integration tests verifying standardized event data.

##### **PR WiZ.1: HA WiZ Light - Declare `_SIMULATED` Flags**

- **Goal:** Inform Home Assistant Core that WiZ lights _must_ be simulated for smooth dynamic control and transitions.

- **Files to Modify:** `homeassistant/components/wiz/light.py`

- **Logic to Implement:**

    1. **Feature Declaration:** Add `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` to `WizLight`'s `_attr_supported_features`. Do NOT add `LightEntityFeature.DYNAMIC_CONTROL`.

- **Testing:** Integration tests verifying smooth simulation and halting.

##### **PR WiZ.2: (Optional) HA WiZ - Standardized `event_data` for any future WiZ controllers**

- **Goal:** Prepare for any future WiZ-branded physical controllers that might expose events to Home Assistant.

- **Files to Modify:** (If WiZ adds such devices, a new `homeassistant/components/wiz/device_trigger.py` or similar would be created.)

- **Logic to Implement:** If WiZ introduces devices that act as controllers and expose events to Home Assistant, ensure their event data conforms to `ControllerEventData`. (Low priority for now).

## 4\. Communication and Collaboration

- **GitHub Issues:** Before starting any PR, search existing GitHub issues and discussions. If a relevant issue exists, comment on it to state your intention to work on it and link back to this plan. If not, consider opening a new issue to discuss the proposed changes and get initial feedback.

- **Home Assistant Discord/Forums:** Engage with the Home Assistant developer community on Discord (specifically the `#devs_core` and integration-specific channels) and the community forums. Share your plans, ask for advice, and seek early feedback.

- **Small, Focused PRs:** Each PR should be as small and focused as possible. This makes review easier and faster.

- **Clear PR Descriptions:** Always provide a detailed explanation of what your PR does, why it's needed, and how it was tested. Link to this overall plan for context.

- **Be Patient and Responsive:** Open-source contributions involve review cycles. Be prepared to address feedback and make revisions.

By following this detailed, step-by-step approach, a dedicated community member can make significant contributions to this exciting new functionality in Home Assistant and ESPHome. Good luck!
````
