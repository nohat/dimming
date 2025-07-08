You are absolutely correct, and I appreciate the precise clarification! My apologies for the oversight.

You are 100% right:

* **`Dimmer +` / `Dimmer -`** are indeed for **step increments**. While they can be used in rapid succession to *simulate* continuous dimming, they are not the dedicated "move" commands.
* **`Dimmer <` (dim down continuously)**, **`Dimmer >` (dim up continuously)**, and **`Dimmer !` (stop)** are the correct Tasmota commands for **continuous "move" and "stop" functionality**.

This is an important distinction because it means Tasmota offers *even more direct* native support for our `dynamic_control: {type: move}` and `type: stop}` than I initially stated.

Let's revise the Tasmota implementation plan to reflect this accurate mapping.

---

## Revised Implementation for Tasmota Devices

### 1. Understanding Tasmota's Capabilities for Dynamic Control (Corrected)

* **Native `move`/`stop` (Confirmed & Direct):**
    * `Dimmer >`: Starts dimming the light *up* continuously.
    * `Dimmer <`: Starts dimming the light *down* continuously.
    * `Dimmer !`: Stops any ongoing continuous dimming operation initiated by `Dimmer >` or `Dimmer <`.
    * This is a perfect, direct mapping for our `dynamic_control: {type: move}` and `type: stop}`.
* **Step Increments:**
    * `Dimmer +<value>` / `Dimmer -<value>`: Increments/decrements brightness by a specified value (e.g., `Dimmer +10`). This is ideal for our `dynamic_control: {type: step}`.
* **Transitions (`Fade`):** Still relevant, but as noted, varies in reliability.
* **Dimming Curves (`Gamma`, `DimmerRange`):** Still static internal firmware settings, not dynamic commands.
* **MQTT Communication:** Remains the primary method.
* **Controller Events:** Remains relevant for physical controls.

### 2. Revised Required Changes for Tasmota Support

The core work remains in `homeassistant/components/tasmota/light.py`, but the mapping to Tasmota's MQTT commands will be more precise.

#### **PR Tasmota.1 (Revised): HA Tasmota Light - Declare `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Tasmota MQTT Commands**

* **Goal:** Leverage Tasmota's native `Dimmer >`, `Dimmer <`, and `Dimmer !` commands.
* **Files to Modify:**
    * `homeassistant/components/tasmota/light.py`
* **Logic to Implement:**
    1.  **Feature Declaration:**
        * In the `TasmotaLight` entity's setup:
            * If the Tasmota device supports the `Dimmer` command (which implies support for `Dimmer >`, `<` and `!`), **unconditionally add `LightEntityFeature.DYNAMIC_CONTROL`** to its `_attr_supported_features`. This is a strong native capability.
            * Still declare `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` as a fallback, especially for `transition` (due to `Fade` unreliability) or if the specific Tasmota firmware version or `SetOption` doesn't fully expose `Dimmer >` / `<` behavior as expected.
    2.  **Mapping `dynamic_control` to MQTT Payloads:**
        * Modify the `async_turn_on` method in `TasmotaLight`.
        * If `dynamic_control` is present in `kwargs` and `LightEntityFeature.DYNAMIC_CONTROL` is supported:
            * **`type: "move"`:**
                * If `direction: "up"`, publish `Dimmer >` to the `cmnd/tasmota_device/Dimmer` topic.
                * If `direction: "down"`, publish `Dimmer <` to the `cmnd/tasmota_device/Dimmer` topic.
                * **Speed Parameter:** Tasmota's `Dimmer >` and `Dimmer <` use an internal, fixed dimming speed (configurable via `DimmerSpeed` command in Tasmota, but not typically dynamically per command).
                    * The `speed` parameter from `dynamic_control` will largely be **ignored for native `move` commands sent to Tasmota.** Home Assistant's `LightTransitionManager` will primarily use the `speed` parameter when it falls back to *simulating* `move` (by sending rapid `Dimmer +<value>` / `-<value>` commands, or `SetOption114 1` with `Fade` if reliable).
                    * It's worth considering if the HA Tasmota integration could send a `DimmerSpeed <value>` command *before* `Dimmer >` / `<` if a `speed` parameter is provided, but this changes the device's default behavior, which might be undesirable. For initial implementation, letting Tasmota use its configured `DimmerSpeed` for native commands is simplest.
            * **`type: "stop"`:**
                * Publish `Dimmer !` to the `cmnd/tasmota_device/Dimmer` topic.
            * **`type: "step"`:**
                * If `direction: "up"`, publish `Dimmer +{step_size}` to the `cmnd/tasmota_device/Dimmer` topic.
                * If `direction: "down"`, publish `Dimmer -{step_size}` to the `cmnd/tasmota_device/Dimmer` topic.
                * The `step_size` from `dynamic_control` maps directly here.
        * **Curve Handling:** Unchanged. Tasmota's `Gamma` and `DimmerRange` are static firmware settings. HA Core's `LightTransitionManager` will handle dynamic curve application when simulating.
* **Testing:**
    * **Integration Tests:** Critical to verify the correct `Dimmer >`, `Dimmer <`, and `Dimmer !` commands are sent and that the light responds as expected.
    * **Manual Testing:** Confirm the perceived smoothness and responsiveness using real Tasmota devices.

#### **PR Tasmota.2 (Unchanged): HA Tasmota Light - Report `dynamic_state` from Tasmota Devices**

* The logic here remains the same: infer `dynamic_state` based on the `Dimmer >`, `Dimmer <`, and `Dimmer !` commands sent, and update the entity's `_attr_dynamic_state`.

#### **PR Tasmota.3 (Unchanged): HA Tasmota - Standardized `event_data` for Tasmota Controllers**

* The logic for standardizing controller events from Tasmota devices remains the same.

### Summary of Correction:

This correction significantly streamlines the Tasmota integration for `move`/`stop`. Instead of relying on rapid stepping or the unreliable `Fade` for continuous dimming, we can directly leverage Tasmota's dedicated `Dimmer >`, `Dimmer <`, and `Dimmer !` commands, providing a much more robust and native experience. Thank you for catching that!

----

Okay, let's dive into the Tasmota integration. Tasmota is a fantastic open-source firmware, and its integration with Home Assistant is primarily via MQTT. This gives us good flexibility, as Tasmota exposes a lot of its functionality directly through MQTT commands and telemetry.

My research confirms that Tasmota is quite capable of handling continuous dimming natively, which is excellent for our project.

---

## Implementing Universal Lighting Control for Tasmota Devices

The Home Assistant Tasmota integration (`homeassistant/components/tasmota/`) manages devices running Tasmota firmware, typically communicating over MQTT. This integration uses MQTT Discovery to automatically configure devices in Home Assistant.

### 1. Understanding Tasmota's Capabilities for Dynamic Control

* **Native `move`/`stop`:** Tasmota firmware has built-in commands for continuous dimming:
    * `Dimmer +` / `Dimmer -`: Increments/decrements brightness by a small step. If held, it continues to change.
    * `Dimmer !`: Stops any ongoing `Dimmer +`/`-` operation.
    * These are ideal for mapping to our `dynamic_control: {type: move}` and `dynamic_control: {type: stop}`.
* **Transitions:** Tasmota has a `Fade` parameter (often controlled by `SetOption114 1` or `SetOption20 1` for dimmers) which enables smooth transitions. However, its reliability and smoothness can vary significantly between devices and Tasmota versions.
* **Dimming Curves:** Tasmota offers `Gamma` correction (e.g., `Gamma 2.2`) and `DimmerRange` settings in its firmware. These are *static* configurations that alter how Tasmota interprets linear brightness values internally for a more perceptual output. They are not dynamic commands sent by Home Assistant. Our HA Core `LightTransitionManager` will handle dynamic curve application for simulated devices.
* **MQTT Communication:** Tasmota devices publish their state and receive commands via MQTT topics (e.g., `cmnd/tasmota_device/Dimmer`, `stat/tasmota_device/POWER`).
* **Controller Events:** Tasmota devices can be configured to send MQTT messages for button presses, rotary encoder movements, etc., which Home Assistant can consume as `event` entities or MQTT device triggers.

### 2. Required Changes for Tasmota Support

The primary work will be within the **Home Assistant Tasmota integration** (`homeassistant/components/tasmota/light.py`) to map our new `dynamic_control` service parameters to Tasmota's MQTT commands and to interpret Tasmota's state.

This would fit into **Phase 3b: Integration-Specific Updates** of our overall plan.

#### **PR Tasmota.1: HA Tasmota Light - Declare `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Tasmota MQTT Commands**

* **Goal:** Enable Home Assistant's Tasmota light platform to leverage Tasmota's native `Dimmer +`/`-` and `Dimmer !` commands.
* **Files to Modify:**
    * `homeassistant/components/tasmota/light.py`
    * Potentially `homeassistant/components/tasmota/discovery.py` if new discovery flags are needed from Tasmota (though we might infer capability from existing `commands` list).
* **Logic to Implement:**
    1.  **Feature Declaration:**
        * In the `TasmotaLight` entity's setup:
            * If the Tasmota device is a dimmable light and supports the `Dimmer` command, add `LightEntityFeature.DYNAMIC_CONTROL` to its `_attr_supported_features`. We might need to check for specific Tasmota `SetOption` values (like `SetOption114`) or infer from the device's advertised capabilities.
            * Always declare `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for all dimmable Tasmota lights. This is crucial for fallback, given the varying reliability of Tasmota's `Fade` and the possibility that a user hasn't configured `Dimmer +`/`-` behavior.
    2.  **Mapping `dynamic_control` to MQTT Payloads:**
        * Modify the `async_turn_on` method in `TasmotaLight`.
        * If `dynamic_control` is present in `kwargs` and `LightEntityFeature.DYNAMIC_CONTROL` is supported:
            * **`type: "move"`:**
                * Translate `direction` to `Dimmer +` (for `up`) or `Dimmer -` (for `down`).
                * The `speed` parameter from `dynamic_control` doesn't have a direct equivalent in Tasmota's `Dimmer +`/`-` (which uses internal firmware-defined steps). We would send the `Dimmer +` or `Dimmer -` command repeatedly. The repetition rate would be determined by the `LightTransitionManager` in HA Core if it's simulating, or Tasmota's internal rate if native.
                * Publish this command to the device's `cmnd/tasmota_device/Dimmer` topic.
            * **`type: "stop"`:**
                * Map to Tasmota's `Dimmer !` command.
                * Publish this command to the device's `cmnd/tasmota_device/Dimmer` topic.
            * **`type: "step"`:**
                * Map to Tasmota's `Dimmer <value>` command (e.g., `Dimmer 10` to increase by 10%). This would be a single command.
                * Publish this command.
        * **Curve Handling:** Tasmota's `Gamma` and `DimmerRange` are static device settings. The `curve` parameter from `dynamic_control` will be ignored by the Tasmota integration. HA Core's `LightTransitionManager` will apply the curve by sending stepped linear brightness values if simulation is active.
* **Testing:**
    * **Integration Tests:** Requires a Tasmota device flashed with a dimmable light configuration.
        * Call `light.turn_on` with `dynamic_control: {type: move, direction: up}`. Verify light dims smoothly.
        * Call `light.turn_on` with `dynamic_control: {type: stop}`. Verify light halts.
        * Monitor MQTT traffic to confirm the correct Tasmota `Dimmer +`/`-` and `Dimmer !` commands are being sent.
    * **Manual Testing:** Same as above, using a real Tasmota device.

#### **PR Tasmota.2: HA Tasmota Light - Report `dynamic_state` from Tasmota Devices**

* **Goal:** Allow Home Assistant to accurately reflect the `dynamic_state` of Tasmota-connected lights.
* **Files to Modify:**
    * `homeassistant/components/tasmota/light.py`
* **Logic to Implement:**
    1.  **State Consumption:** The `tasmota_light` integration needs to listen for state updates from Tasmota's `stat` topic (e.g., `stat/tasmota_device/RESULT` or `stat/tasmota_device/POWER`).
    2.  **Inferring `dynamic_state`:**
        * When Home Assistant sends a `Dimmer +`/`-` command, the `tasmota_light` entity should optimistically set its `dynamic_state` to `moving_brightness_up`/`down`.
        * When a `Dimmer !` command is sent, set it to `idle`.
        * If the light's `POWER` or `Dimmer` state changes rapidly over a short period (indicating an ongoing transition or dimming), the integration could infer `transitioning` or `moving_brightness_up`/`down` if no explicit `dynamic_control` command was just sent by HA.
    3.  **Update Entity State:** Set the `_attr_dynamic_state` of the `tasmota_light` entity and trigger a state update.
* **Testing:**
    * **Integration Tests:** Verify `dynamic_state` changes correctly in Home Assistant's Developer Tools -> States when controlling Tasmota lights via `dynamic_control` service calls or physical controls (if Tasmota is configured to report them).

#### **PR Tasmota.3: HA Tasmota - Standardized `event_data` for Tasmota Controllers**

* **Goal:** Ensure Tasmota-based physical controls (buttons, rotary encoders) emit standardized `event` entities with consistent `event_data` for the "Control Mapping" phase.
* **Files to Modify:**
    * `homeassistant/components/tasmota/device_trigger.py` (or similar for MQTT Event entities)
* **Logic to Implement:**
    1.  **Event Entity Creation:** If a Tasmota device is configured with `Button` or `Encoder` components and sends MQTT messages for these, the MQTT integration (which Tasmota builds upon) should create an `event` entity (e.g., `event.my_tasmota_button_action`).
    2.  **Standardized `event_data`:** The `event_data` attribute of these `event` entities should conform to our `ControllerEventData` schema (e.g., `{"action": "single", "action_id": "button_1"}` or `{"action": "rotate_left", "value": 5.0}`). Tasmota's `ButtonTopic` and `SwitchTopic` configurations are highly flexible, so this might involve recommending specific Tasmota configurations in documentation to ensure the MQTT payload is easily parsable into our standard `event_data`.
* **Testing:**
    * **Integration Tests:** Pair a Tasmota device configured as a button or rotary encoder. Trigger various actions. Verify that the corresponding `event` entity in Home Assistant fires with the correct, standardized `event_data`.

### Summary for Tasmota:

Tasmota's native `Dimmer +`/`-` and `Dimmer !` commands provide a strong foundation for implementing `dynamic_control` directly. The work primarily involves mapping these MQTT commands within the Home Assistant Tasmota integration and ensuring proper state reporting. The flexibility of Tasmota's MQTT messaging also makes it suitable for standardizing controller events.