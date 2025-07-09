# ZHA and Z-Wave Integration

To effectively connect Home Assistant's new universal light functionality (including enhanced transitions and `dynamic_control`) to Zigbee (ZHA) and Z-Wave (Z-Wave JS) devices, we'll need specific updates within those integrations. This involves mapping Home Assistant's high-level service calls to the native commands of each protocol and interpreting device reports to update Home Assistant's state.

Here's how we'd approach updating the ZHA and Z-Wave JS integrations:

______________________________________________________________________

## Updating ZHA Integration for Enhanced Lighting Control

ZHA relies on `zigpy` to interact with Zigbee devices, which uses the Zigbee Cluster Library (ZCL). The **Level Control Cluster (0x0008)** is key here.

### ZHA PR Strategy

**PR ZHA.1: ZHA - Implement `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to ZCL Commands**

- **Description:** Update ZHA's light platform to declare native `LightEntityFeature.DYNAMIC_CONTROL` for compatible devices and map the new `dynamic_control` service parameters to Zigbee Level Control Cluster commands.
- **Changes in `homeassistant/components/zha/light.py` and `zigpy` core:**
    - **Feature Declaration:** For `LightEntity` platforms representing dimmable lights, add `LightEntityFeature.DYNAMIC_CONTROL` to `supported_features` if the device's quirks (or its ZCL attributes) indicate support for Level Control Cluster `Move`, `Stop`, and `Step` commands.
    - **Mapping `dynamic_control` to ZCL Commands:**
        - When `light.turn_on` receives `dynamic_control: {type: 'move', direction: 'up', ...}`:
            - Send a **Level Control `Move` command (0x01)** to the device's Level Control cluster.
            - Parameters: `mode` (0x00 for up), `rate` (derived from `speed` parameter, potentially scaled), `options_mask`, `options_override`.
        - When `light.turn_on` receives `dynamic_control: {type: 'move', direction: 'down', ...}`:
            - Send a **Level Control `Move` command (0x01)**.
            - Parameters: `mode` (0x01 for down), `rate`, `options_mask`, `options_override`.
        - When `light.turn_on` receives `dynamic_control: {type: 'stop', ...}`:
            - Send a **Level Control `Stop` command (0x03)** to the device.
        - When `light.turn_on` receives `dynamic_control: {type: 'step', direction: 'up'/'down', step_size: N, ...}`:
            - Send a **Level Control `Step` command (0x02)**.
            - Parameters: `mode`, `step_size` (derived from `step_size`), `transition_time` (derived from `ramp_time`), `options_mask`, `options_override`.
    - **Existing `transition` handling:** ZHA already uses the **Level Control `Move to Level` command (0x00)** for the `brightness` + `transition` parameter. This behavior would remain, as it's the native way Zigbee handles fades to a specific level.
- **Benefit:** Enables native "hold-to-dim" and "step" functionality for Zigbee devices that support the Level Control Cluster, reducing network traffic and providing optimal responsiveness.
- **Testing:** Test `light.turn_on` with `dynamic_control` parameters on various dimmable Zigbee lights to verify native command execution and behavior.

**PR ZHA.2: ZHA - Report `dynamic_state` from Zigbee Devices**

- **Description:** Implement logic within ZHA to listen for Zigbee device reports (e.g., from Level Control Cluster attributes or command responses) and translate them into Home Assistant's `dynamic_state` attribute.
- **Changes in `homeassistant/components/zha/light.py` and `zigpy` callbacks:**
    - Monitor Level Control Cluster attribute reports (specifically `CurrentLevel`) and command responses (e.g., from `Move`, `Stop`).
    - Internally track the light's assumed dynamic state (e.g., `moving_brightness_up`, `moving_brightness_down`, `idle`) based on these commands and reports.
    - Update the `light` entity's `dynamic_state` attribute (as exposed by HA Core's `LightEntity`).
- **Benefit:** Home Assistant's UI and automations gain real-time visibility into the dynamic activity of Zigbee lights.
- **Testing:** Observe `dynamic_state` attribute changes in Home Assistant's developer tools when controlling Zigbee lights with native dynamic commands and transitions.

______________________________________________________________________

### Updating Z-Wave JS Integration for Enhanced Lighting Control

Z-Wave JS interacts with Z-Wave devices using Z-Wave Command Classes. The **Multilevel Switch Command Class (0x26)** is the primary one for dimming, and **Color Switch Command Class (0x33)** for color.

#### Z-Wave JS PR Strategy

**PR ZWAVE_JS.1: Z-Wave JS - Implement `LightEntityFeature.DYNAMIC_CONTROL` & Map `dynamic_control` to Z-Wave Commands**

- **Description:** Update Z-Wave JS's light platform to declare native `LightEntityFeature.DYNAMIC_CONTROL` for compatible devices and map `dynamic_control` service parameters to Z-Wave Multilevel Switch and Color Switch Command Class commands.
- **Changes in `homeassistant/components/zwave_js/light.py` (and potentially `python-zwave-js` library if new capabilities are needed at a lower level):**
    - **Feature Declaration:** For `LightEntity` platforms backed by Multilevel Switch devices, add `LightEntityFeature.DYNAMIC_CONTROL` to `supported_features` if the node supports `Start Level Change` and `Stop Level Change` commands.
    - **Mapping `dynamic_control` to Z-Wave Commands:**
        - When `light.turn_on` receives `dynamic_control: {type: 'move', direction: 'up', ...}`:
            - Send a **Multilevel Switch `Start Level Change` command (0x04)**.
            - Parameters: `up/down` (up), `duration` (derived from `speed` or `ramp_time`, or `0xFF` for default).
        - When `light.turn_on` receives `dynamic_control: {type: 'move', direction: 'down', ...}`:
            - Send a **Multilevel Switch `Start Level Change` command (0x04)**.
            - Parameters: `up/down` (down), `duration`.
        - When `light.turn_on` receives `dynamic_control: {type: 'stop', ...}`:
            - Send a **Multilevel Switch `Stop Level Change` command (0x05)**.
        - For `dynamic_control: {type: 'step', ...}`:
            - This might involve sending a `Multilevel Switch Set` command (0x01) to a calculated new target value with a `duration`. Z-Wave doesn't have a direct "step" command like Zigbee's.
    - **Existing `transition` handling:** Z-Wave JS already handles `transition` by including a `duration` parameter in the `Multilevel Switch Set` command. This behavior would remain the primary way for fixed-duration fades to a target.
- **Benefit:** Enables native "hold-to-dim" and potentially "step" functionality for Z-Wave dimmers, leveraging the protocol's capabilities.
- **Testing:** Test `light.turn_on` with `dynamic_control` parameters on various dimmable Z-Wave devices to verify native command execution.

**PR ZWAVE_JS.2: Z-Wave JS - Report `dynamic_state` from Z-Wave Devices**

- **Description:** Implement logic within Z-Wave JS to interpret device value notifications (especially for Multilevel Switch) and internal node states, and translate them into Home Assistant's `dynamic_state` attribute.
- **Changes in `homeassistant/components/zwave_js/light.py` and Z-Wave JS driver event listeners:**
    - Listen for `value_updated` events for the `Multilevel Switch` value.
    - More importantly, listen for notifications related to `Start Level Change` and `Stop Level Change` command class reports, if the device sends them (some Z-Wave devices report status on these commands).
    - Internally track the light's assumed dynamic state (`moving_brightness_up`, `moving_brightness_down`, `idle`) based on sent commands and received reports.
    - Update the `light` entity's `dynamic_state` attribute.
- **Benefit:** Home Assistant's UI and automations gain real-time visibility into the dynamic activity of Z-Wave lights.
- **Testing:** Observe `dynamic_state` attribute changes in Home Assistant's developer tools when controlling Z-Wave lights with native dynamic commands and transitions.

______________________________________________________________________

### General Considerations for Both Integrations

- **Fallback to Simulation:** Crucially, if a specific ZHA/Z-Wave device _doesn't_ support the native `Move`, `Stop`, or `Step` commands (e.g., an older Zigbee Light Link 1.0 device that only supports `Move to Level`), these integrations would **not** declare `LightEntityFeature.DYNAMIC_CONTROL`. In such cases, the Home Assistant Core's `LightTransitionManager` (from PR 3.3) would detect the absence of native support but the presence of `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` (which the integration would generally declare if it's a dimmable light), and Home Assistant would then **simulate** the `move`/`stop` by sending rapid `Set` or `Move to Level` commands.
- **Color Control:** Similar `Move`/`Stop` concepts exist for the Zigbee Color Control Cluster and Z-Wave Color Switch Command Class. These would be extended to handle `dynamic_control` for color as well, mapping to hue/saturation/color temperature changes.
- **Rate/Duration Mapping:** The `speed` and `ramp_time` parameters in `dynamic_control` will need careful mapping to Zigbee's "rate" or Z-Wave's "duration" fields, potentially involving scaling or predefined steps to ensure smooth device-side operation.
- **Device Quirk/Configuration:** Some devices might have specific quirks or configuration parameters that influence how these commands behave. The integrations might need to account for these (e.g., via ZHA quirks or Z-Wave JS device configurations).

By implementing these updates, Home Assistant will be able to speak the native "dynamic control" language of Zigbee and Z-Wave devices directly, providing the best possible performance and responsiveness when supported, while maintaining a consistent user experience through intelligent simulation for other devices.
