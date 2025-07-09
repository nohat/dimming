# Zigbee2MQTT Integration

Great question! Integrating with Zigbee2MQTT (Z2M) is a critical part of making our Universal Smart Lighting Control truly widespread. The good news is that Z2M already exposes many of the underlying Zigbee capabilities we need, often more directly than ZHA in its current state.

Here's how we'd implement support for Zigbee2MQTT devices, building on our existing plan:

______________________________________________________________________

## Implementing Universal Lighting Control for Zigbee2MQTT Devices

Zigbee2MQTT (Z2M) is a standalone application that bridges Zigbee networks to MQTT, and Home Assistant then integrates with Z2M via its MQTT integration and MQTT Discovery. This means our changes will primarily focus on how Home Assistant's MQTT Light integration consumes and exposes Z2M's capabilities.

### 1. Understanding Zigbee2MQTT's Capabilities for Dynamic Control

My research confirms that Z2M is quite capable in this area:

- **Native `move`/`stop`:** Z2M _does_ expose Zigbee's Level Control Cluster `Move` and `Stop` commands via specific MQTT payloads. For example, `{"brightness_move": 40}` to start dimming up at 40 units/second, and `{"brightness_move": 0}` to stop (or `{"color_temp_move": "stop"}`). This is excellent!
- **Transitions:** Z2M supports `transition` parameters in its `set` payloads (e.g., `{"brightness": 100, "transition": 3}`).
- **MQTT Discovery:** Z2M uses MQTT Discovery to announce devices and their capabilities to Home Assistant. This is how Home Assistant creates `light` entities for Z2M-connected lights.
- **Controller Events:** Z2M publishes events from remotes/buttons to MQTT topics. Home Assistant can consume these via MQTT Device Triggers or Event entities.

### 2. Required Changes for Zigbee2MQTT Support

The bulk of the work will be in the **Home Assistant MQTT Light integration** (`homeassistant/components/mqtt/light.py`) to properly map our new `dynamic_control` service parameters to Z2M's MQTT payloads and to consume Z2M's state.

This would fit into **Phase 3b: Integration-Specific Updates** of our overall plan, alongside ZHA and Z-Wave JS.

#### **PR Z2M.1: HA MQTT Light - Declare `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Z2M MQTT Payloads**

- **Goal:** Enable Home Assistant's `mqtt_light` platform to leverage Z2M's native `move`/`stop` commands.
- **Files to Modify:**
    - `homeassistant/components/mqtt/light.py` (main implementation)
    - `homeassistant/components/mqtt/schema.py` (schema validation for new discovery fields)
    - `homeassistant/components/mqtt/models.py` (data models if needed)
- **Logic to Implement:**
  1. **Feature Declaration:**
     - During MQTT Discovery processing in `MqttLight.__init__()`, inspect the discovery payload for Z2M capability indicators:
       - Check if the device exposes `brightness_move`, `color_temp_move`, or similar commands in its discovery configuration
       - Look for specific device model indicators that are known to support these commands (e.g., Zigbee 3.0 compliant devices)
       - Parse any Z2M-specific capability flags from the discovery payload
     - If native Z2M move/stop support is detected, add `LightEntityFeature.DYNAMIC_CONTROL` to `_attr_supported_features`
     - Always declare `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for all dimmable Z2M lights as fallback capabilities
  1. **MQTT Topic Configuration:**
     - Extend the existing topic configuration to handle dynamic control commands:
       - Use the existing `command_topic` (typically `zigbee2mqtt/[device_friendly_name]/set`) for sending dynamic control payloads
       - Listen to the existing `state_topic` (typically `zigbee2mqtt/[device_friendly_name]`) for state feedback
       - No new topics required - leverage Z2M's existing MQTT structure
  1. **Mapping `dynamic_control` to MQTT Payloads:**
     - In `MqttLight.async_turn_on()`, add handling for the new `dynamic_control` parameter:
     - If `dynamic_control` is present in `kwargs` and `LightEntityFeature.DYNAMIC_CONTROL` is supported:
       - **`type: "move"`:**
         - For brightness: `{"brightness_move": speed}` for up, `{"brightness_move": -speed}` for down
         - For color temperature: `{"color_temp_move": speed}` for up, `{"color_temp_move": -speed}` for down
         - Speed parameter maps directly to Z2M's rate (units per second)
         - Publish to the device's `command_topic` using `self._publish()`
       - **`type: "stop"`:**
         - For brightness: `{"brightness_move": 0}`
         - For color temperature: `{"color_temp_move": "stop"}` or `{"color_temp_move": 0}`
         - Publish to the device's `command_topic`
       - **`type: "step"`:**
         - For brightness: `{"brightness_step": step_size}` for up, `{"brightness_step": -step_size}` for down
         - For color temperature: `{"color_temp_step": step_size}` for up, `{"color_temp_step": -step_size}` for down
         - Publish to the device's `command_topic`
     - **Error Handling:** Implement proper error handling for MQTT publish failures and unsupported commands
     - **Curve Handling:** Z2M does not natively support dimming curves (it sends linear Zigbee commands). The `curve` parameter in `dynamic_control` will be ignored by the MQTT integration; HA Core's `LightTransitionManager` will handle applying the curve by sending stepped linear commands if simulation is active.
- **Testing:**
    - **Integration Tests:** Requires a running Z2M instance and a compatible Zigbee light with move/stop support.
        - Call `light.turn_on` with `dynamic_control: {type: move, direction: up, speed: 40}`. Verify light dims smoothly and MQTT traffic shows `{"brightness_move": 40}`.
        - Call `light.turn_on` with `dynamic_control: {type: stop}`. Verify light halts and MQTT traffic shows `{"brightness_move": 0}`.
        - Test color temperature controls with `dynamic_control` for `color_temp_move` commands.
        - Verify fallback to simulation when native commands are not supported.
    - **Manual Testing:** Use Developer Tools to send service calls and monitor both light behavior and state changes.
    - **MQTT Traffic Monitoring:** Use tools like `mosquitto_sub` or Z2M's frontend to verify correct MQTT payloads are being sent.

#### **PR Z2M.2: HA MQTT Light - Report `dynamic_state` from Z2M Devices**

- **Goal:** Allow Home Assistant to accurately reflect the `dynamic_state` of Z2M-connected lights during dynamic operations.
- **Files to Modify:**
    - `homeassistant/components/mqtt/light.py`
- **Logic to Implement:**
  1. **State Topic Monitoring:**
     - The `mqtt_light` integration already subscribes to the device's `state_topic` for brightness and other state updates
     - Extend the `_state_message_received()` method to process additional state information
     - Monitor for rapid brightness changes that might indicate ongoing dynamic operations
  1. **Dynamic State Inference:**
     - **Command-based State Tracking:** When Home Assistant sends a `brightness_move` command via `async_turn_on()`, immediately set the entity's `_attr_dynamic_state`:
       - `{"brightness_move": positive_value}` → `moving_brightness_up`
       - `{"brightness_move": negative_value}` → `moving_brightness_down`
       - `{"brightness_move": 0}` → `idle`
       - Similar logic for `color_temp_move` commands
     - **State Validation from MQTT Messages:**
       - If Z2M provides direct feedback about ongoing move operations (device-dependent), parse and use that information
       - Monitor brightness value changes over time to validate that expected dynamic operations are actually occurring
       - Implement timeout logic: if no brightness changes are detected within expected timeframes during a supposed "move" operation, reset `dynamic_state` to `idle`
     - **Transition State Handling:**
       - For standard transitions (via `transition` parameter), Z2M typically handles these natively
       - If Home Assistant Core's `LightTransitionManager` is simulating the transition, it will manage the `transitioning` state
       - For Z2M native transitions, infer `transitioning` state when a `transition` parameter was included in the last command and brightness is still changing toward the target
  1. **State Update Mechanism:**
     - Add `_attr_dynamic_state` property to the `MqttLight` class
     - Ensure `async_write_ha_state()` is called whenever `dynamic_state` changes
     - Include the new state in the entity's state attributes for visibility in Developer Tools
  1. **Coordination with HA Core:**
     - When `LightTransitionManager` is handling simulation, ensure the MQTT integration doesn't conflict with core state management
     - Provide clear handoff between native Z2M operations and HA Core simulation based on declared features
- **Testing:**
    - **Integration Tests:** Verify `dynamic_state` changes correctly in Home Assistant's Developer Tools → States when controlling Z2M lights via `dynamic_control` service calls.
    - **State Accuracy Testing:** Confirm that `dynamic_state` accurately reflects actual light behavior and resets properly when operations complete.
    - **Timeout Testing:** Verify that stuck or failed move operations don't leave entities in incorrect dynamic states.

#### **PR Z2M.3: HA MQTT - Standardized `event_data` for Z2M Controllers**

- **Goal:** Ensure Z2M-connected remotes and switches emit standardized `event` entities with consistent `event_data` for the "Control Mapping" phase.
- **Files to Modify:**
    - `homeassistant/components/mqtt/device_automation.py` (MQTT device triggers)
    - `homeassistant/components/mqtt/event.py` (MQTT event entities)
    - `homeassistant/components/mqtt/discovery.py` (discovery payload processing)
- **Logic to Implement (in HA's MQTT integration):**
  1. **Enhanced Discovery Processing:**
     - When Z2M publishes device discovery payloads for controller devices (remotes, switches, rotary encoders), detect controller capabilities
     - Look for Z2M-specific device classes like `remote_control`, `action_sensor`, or specific device models known to be controllers
     - Automatically create appropriate `event` entities alongside any traditional sensor entities
  1. **Event Entity Creation and Management:**
     - For controller devices, create `event` entities with standardized naming (e.g., `event.ikea_tradfri_remote_action`)
     - Subscribe to the device's action topic (typically `zigbee2mqtt/[device_name]/action` or similar)
     - Process incoming MQTT messages and translate them into Home Assistant events
  1. **Standardized `event_data` Translation:**
     - Map Z2M's device-specific action payloads to our universal `ControllerEventData` schema:
       - **Button Actions:** Z2M's `{"action": "single"}` → `{"action": "single", "action_id": "button_1"}`
       - **Multi-button Devices:** Z2M's `{"action": "on"}` → `{"action": "single", "action_id": "power_on"}`
       - **Rotary Actions:** Z2M's `{"action": "rotate_left", "action_rate": 5}` → `{"action": "rotate_left", "value": 5.0}`
       - **Hold Actions:** Z2M's `{"action": "brightness_up_hold"}` → `{"action": "hold", "action_id": "brightness_up"}`
     - Handle Z2M-specific quirks and variations across different device manufacturers
     - Provide fallback handling for unknown action types
  1. **Configuration Options:**
     - Allow users to customize action mapping via MQTT configuration if needed
     - Support for device-specific action translation templates
     - Option to enable/disable automatic event entity creation
  1. **Integration with Existing MQTT Device Triggers:**
     - Ensure compatibility with existing MQTT device trigger automations
     - Provide migration path for users already using device triggers
     - Allow both event entities and device triggers to coexist
- **Testing:**
    - **Integration Tests:** Pair a Z2M-supported remote (e.g., IKEA TRÅDFRI, Philips Hue Dimmer, Aqara Cube). Trigger various button presses/holds/rotations. Verify that the corresponding `event` entity in Home Assistant fires with the correct, standardized `event_data`.
    - **Device Compatibility Testing:** Test with multiple remote types to ensure broad compatibility and consistent event mapping.
    - **Migration Testing:** Verify that existing device trigger automations continue to work alongside new event entities.

### 3. Implementation Considerations for MQTT Light Integration

#### **MQTT Discovery Payload Extensions**

To properly support the new dynamic control features, Z2M's discovery payloads should ideally include capability indicators. While this requires coordination with the Z2M project, Home Assistant can work with existing discovery information:

````json
{
  "brightness": true,
  "brightness_scale": 254,
  "color_temp": true,
  "effect": true,
  "effect_list": [...],
  "schema": "json",
  "supported_color_modes": ["color_temp", "xy"],
  "device": {...},
  "availability": [...],

  // New fields that Z2M could include:
  "brightness_move": true,
  "color_temp_move": true,
  "brightness_step": true,
  "color_temp_step": true,
  "move_rate_min": 1,
  "move_rate_max": 254,
  "step_size_min": 1,
  "step_size_max": 254
}
```text

#### **Backwards Compatibility**

The MQTT Light integration updates must maintain full backwards compatibility:

- Existing MQTT lights continue to function exactly as before
- New `dynamic_control` parameters are optional and ignored if not supported
- Fallback to simulation ensures consistent behavior across device capabilities
- No breaking changes to existing MQTT configuration schemas

#### **Performance Considerations**

- **MQTT Message Frequency:** Dynamic control operations should not flood MQTT brokers
- **State Update Throttling:** Implement reasonable throttling for `dynamic_state` updates
- **Memory Usage:** Ensure new state tracking doesn't significantly increase memory usage
- **Network Traffic:** Optimize MQTT payload sizes for move/stop commands

### Summary for Z2M

Zigbee2MQTT is exceptionally well-positioned to support our new `dynamic_control` API due to its direct exposure of Zigbee Level Control commands via clean MQTT interfaces. The implementation strategy focuses on:

**Key Advantages:**

- **Native Protocol Support:** Z2M already exposes `brightness_move`, `color_temp_move`, and `brightness_step` commands that map directly to our `dynamic_control` API
- **Mature MQTT Infrastructure:** Existing topic structure and discovery mechanisms provide a solid foundation
- **Broad Device Compatibility:** Most modern Zigbee 3.0 devices support the underlying Level Control cluster commands
- **Rich State Feedback:** Z2M provides comprehensive state information that can be leveraged for accurate `dynamic_state` reporting

**Implementation Focus:**

- **Minimal Code Changes:** Primary work is in the existing `homeassistant/components/mqtt/light.py` integration
- **Discovery-based Feature Detection:** Automatically detect and enable dynamic control capabilities based on Z2M discovery payloads
- **Robust Fallback Mechanisms:** Seamless fallback to Home Assistant simulation for devices lacking native support
- **Event Standardization:** Unified controller event handling for consistent automation experiences

**Integration Benefits:**

- **Zero Configuration:** Dynamic control works automatically for compatible devices via MQTT Discovery
- **Performance Optimization:** Native Z2M commands eliminate the need for rapid Home Assistant-generated updates
- **Future-proof Design:** Architecture supports easy extension as Z2M adds new capabilities
- **Community Alignment:** Implementation approach aligns with Z2M's existing patterns and conventions

The primary work involves mapping Home Assistant's new service parameters to Z2M's existing MQTT command structure and ensuring proper state feedback. Standardizing controller events from Z2M devices will also be key for the "Control Mapping" UI phase of the project.
````
