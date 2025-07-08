That's an excellent next step\! Moving beyond blueprints to a more core, discoverable "pairing" mechanism for control devices (like dimmer switches and remotes) with lights is crucial for a truly user-friendly Home Assistant. This kind of functionality lives at the intersection of device capability, event handling, and a simplified configuration experience.

Here's a brainstorm on how Home Assistant's built-in device functionality and support could be evolved to allow for easy, discoverable ability to "pair" a control device with a light, building on the "Universal Smart Lighting Control" project plan.

### The Current Challenge & Why Blueprints Exist

Currently, the gap between a control device (which emits events) and a target light (which consumes services) is bridged manually through Home Assistant's automation engine:

  * **Control Devices (e.g., Zigbee remotes, Z-Wave dimmer switches):** These typically don't directly control lights in a centralized hub system. Instead, they emit **events** when a button is pressed, held, or rotated (e.g., `zha_event`, `zwave_js_value_updated`, `mqtt_event`). The event data contains specifics like button ID, action type (`short_press`, `long_press`, `release`).
  * **Light Entities:** These expose **services** like `light.turn_on`, `light.toggle`, `light.set_brightness`, etc.
  * **The Bridge (Blueprints/Automations):** Users manually create automations that:
    1.  **Listen** for specific events from a control device.
    2.  **Extract** relevant data from the event (e.g., which button was pressed).
    3.  **Call** the appropriate `light` service on a target light entity, often with templated brightness/transition logic.

While flexible, this is not discoverable, requires technical understanding of event structures, and can be cumbersome to manage across many devices. Some protocols like Zigbee and Z-Wave *do* support direct "binding" (where a controller talks directly to a light without the hub), but this is often hidden, complex to configure, and bypasses Home Assistant's ability to inject advanced logic like custom dimming curves or complex scenes.

### Proposed Core Architectural Evolution: "Control Mapping"

The goal is to create a **declarative, discoverable, and robust mechanism** to link a control device's actions to a target light's dynamic control parameters directly within Home Assistant's core, going beyond simple automations.

This would require a new conceptual "Control Mapping" layer.

**Core Architectural Enhancements & Evolution Path:**

This new functionality would naturally fit as **Phase 5** of the existing "Universal Smart Lighting Control" project plan, building directly on the new `dynamic_control` service and `dynamic_state` attributes.

#### Phase 5: Advanced Device Control Mapping

  * **Goal:** Provide a first-class, discoverable mechanism within Home Assistant to "pair" control devices with lights, enabling rich dynamic control without complex blueprints.

#### PR 5.1: Core - Standardized `ControllerAction` Definition

  * **Description:** Introduce a canonical, structured definition for common actions emitted by control devices (e.g., button presses, long-press starts/stops, rotations). This standardizes how Home Assistant understands what a control device *does*, abstracting away protocol-specific event details.
  * **Detailed Changes:**
      * **File:** `homeassistant/helpers/device_action.py` (or a new `homeassistant/helpers/controller_action.py`).
      * **Logic:** Define a new schema/dataclass for `ControllerAction` events, e.g.:
        ```python
        class ControllerActionEvent(TypedDict):
            device_id: str
            action_type: Literal["button_press", "button_long_press_start", "button_long_press_stop", "dial_rotate", "dial_click"]
            action_id: str # e.g., "button_1", "up", "down", "left", "right", "center"
            # Optional: value for dial_rotate, e.g., degrees or steps
            value: NotRequired[float]
        ```
      * **Integration Updates:** Update existing major control device integrations (ZHA, Z-Wave JS, MQTT, Philips Hue, Lutron Caseta, etc.) to emit these *standardized* `ControllerActionEvent`s into the Home Assistant event bus, mapping their specific event structures to this new format. This would likely involve updates to their respective `device_trigger.py` or event listener files.
  * **Interactions:** Standardizes event consumption across Home Assistant, simplifying the `ControlMapping` service.
  * **Testing:** Unit tests for event mapping. Integration tests for control devices to ensure standard events are emitted correctly.

#### PR 5.2: Core - `homeassistant.link_control` Service (or similar)

  * **Description:** Implement a new core service that allows declarative association of a specific `ControllerAction` (from PR 5.1) from a control device to a `light.turn_on` call on a target light entity, including `dynamic_control` parameters. This service would internally generate and manage a persistent, non-user-editable "device link" or "internal automation."
  * **Detailed Changes:**
      * **File:** `homeassistant/components/homeassistant/services.yaml` (new service definition) and a new internal module `homeassistant/core/control_mapping.py`.
      * **Logic:**
          * Define a service schema like:
            ```yaml
            homeassistant.link_control:
              fields:
                controller_device_id:
                  selector: device
                  entity_filter: # Filter for devices that declare controller capabilities
                    integration: # Can be filtered by integration or a new capability tag
                    supported_features: # Future: filter by device capabilities
                  description: The ID of the control device.
                controller_action:
                  # Selector for standardized action types/ids from PR 5.1
                  selector: dict # Placeholder - ideally a custom selector for ControllerActionEvent
                  description: The specific action on the control device.
                target_light_entity_id:
                  selector: entity
                  domain: light
                  description: The target light entity.
                light_action: # The action to perform on the light
                  selector: dict # Mimics light.turn_on data section, allowing dynamic_control
                  description: Parameters for the light.turn_on service call.
            ```
          * The service handler would:
              * Validate inputs.
              * Internally create and manage a low-level event listener for `ControllerActionEvent` (from PR 5.1).
              * When the event fires, it would execute a `homeassistant.core.callback` that calls `hass.services.async_call('light', 'turn_on', light_action_data)`.
              * These internal "links" would be persisted in Home Assistant's configuration storage (e.g., `.storage/core.device_links`).
      * **Considerations:** How to manage these internal links (add, remove, list). Ensure they are resilient to restarts and device re-pairing.
  * **Interactions:** Directly uses `ControllerAction` from PR 5.1 and `light.turn_on` with `dynamic_control` from Phase 3.
  * **Testing:** Unit tests for service validation and internal link creation. Integration tests simulating controller events and verifying light service calls.

#### PR 5.3: Frontend - "Link Controls" UI Flow

  * **Description:** Develop a user-friendly, guided UI flow within the Home Assistant frontend to make `link_control` discoverable and easy to configure.
  * **Detailed Changes:**
      * **Files:** `homeassistant/frontend/src/panels/config/devices/device-detail-card.ts`, new `homeassistant/frontend/src/panels/config/devices/link-control-dialog.ts`.
      * **Logic:**
          * Add a new button (e.g., "Link Controls" or "Configure Buttons") on the device page for recognized controller devices.
          * This button launches a dialog/wizard:
              * **Step 1: Select Controller Action:** Present a list of available `ControllerAction`s for the current device (e.g., "Button 1 - Short Press", "Button 2 - Long Press Start", "Dial Rotate Up"). This leverages the standardized events. The UI might even suggest pressing/interacting with the physical device to "learn" the action.
              * **Step 2: Select Target Light:** Allow the user to pick one or more light entities.
              * **Step 3: Define Light Action:** Provide a simplified interface to choose the desired light behavior. This would essentially be a tailored `light.turn_on` data editor, strongly featuring:
                  * `Toggle`
                  * `Turn On` / `Turn Off`
                  * `Dim Up` / `Dim Down` (using `dynamic_control: {type: 'move', direction: 'up/down'}`)
                  * `Stop Dimming` (using `dynamic_control: {type: 'stop'}`)
                  * `Step Brightness` / `Step Color Temp` (using `dynamic_control: {type: 'step'}`)
                  * **Curve Selection:** A dropdown for `curve` (`linear`, `logarithmic`, `s_curve`, `square_law`).
              * **Step 4 (Optional): Native Binding Opt-in:** If the integration (ZHA/Z-Wave JS) supports programmatic native binding for the selected action/device, present an option: "Perform direct device binding (faster, works without Home Assistant, but no custom curves)?"
              * **Finalize:** Call the `homeassistant.link_control` service with the collected data.
  * **Interactions:** Consumes `ControllerAction` from PR 5.1, calls `link_control` service from PR 5.2.
  * **Testing:** User acceptance testing for intuitiveness and ease of use. Frontend integration tests.

#### PR 5.4: Integration Updates (ZHA/Z-Wave JS) for Native Binding Management

  * **Description:** Expose programmatic APIs within ZHA (`zigpy`) and Z-Wave JS (`python-zwave-js`) to manage native device bindings. Integrate this into the `homeassistant.link_control` service to allow users to opt for direct device-to-device control where protocol permits.
  * **Detailed Changes:**
      * **Files:** `homeassistant/components/zha/config_flow.py`, `homeassistant/components/zha/light.py`, `homeassistant/components/zwave_js/config_flow.py`, `homeassistant/components/zwave_js/light.py` (and potentially underlying `zigpy`/`python-zwave-js` libraries).
      * **Logic:**
          * **Expose Binding APIs:** Add new internal APIs to ZHA (e.g., `zha.async_bind_level_control(source_device_id, target_device_id)`) and Z-Wave JS (e.g., `zwave_js.async_set_association(controller_node_id, group_id, target_node_id)`). These APIs would wrap the protocol-specific commands for creating/removing bindings/associations.
          * **Integration with `homeassistant.link_control`:** The `homeassistant.link_control` service handler (from PR 5.2) would check if `native_binding_requested` is true. If so, it would call the appropriate ZHA/Z-Wave JS binding API instead of creating the internal software automation.
          * **Capabilities Declaration:** ZHA and Z-Wave JS would need to declare which `ControllerAction`s and `LightEntity` features can *actually* be natively bound for specific devices (e.g., some dimmers can bind long press to Level Control, others can't). This information would feed into the UI (PR 5.3).
      * **Considerations:** Managing existing bindings. Handling unbinding. Potential for multiple bindings to a single light from different controllers.
  * **Interactions:** Used by PR 5.2 and surfaced in PR 5.3.
  * **Testing:** Integration tests for programmatic binding success and device-to-device control. Verify functionality when Home Assistant is offline.

#### PR 5.5: Documentation

  * **Description:** Comprehensive guides on using the new control mapping UI and the trade-offs of native binding vs. Home Assistant software control.
  * **Detailed Changes:**
      * **Files:** `home-assistant.io` repository.
      * **Content:**
          * A new "Control Mapping" section detailing the UI flow and `homeassistant.link_control` service.
          * Clear explanations of `ControllerAction` types.
          * A dedicated section explaining the pros and cons of "Native Binding" vs. "Home Assistant Software Control" for dynamic lighting, helping users make informed choices (e.g., native binding for ultimate speed/offline capability vs. software control for custom curves/complex logic/multi-protocol control).
  * **Interactions:** Essential for user adoption.
  * **Testing:** Peer review for clarity, accuracy, and completeness.

This holistic approach transforms the complex task of linking controls and lights into a discoverable, powerful, and intuitive feature directly within Home Assistant's core.

---
You've hit on a crucial point that aligns perfectly with Home Assistant's philosophy of leveraging existing, well-defined constructs. You are absolutely right\! The existing "Event" entity construct is highly relevant, and it makes much more sense to **evolve and standardize within that framework** rather than introducing an entirely new `ControllerAction` event system.

This approach offers several significant benefits:

  * **Coherence:** Aligns with how Home Assistant already handles discrete, non-stateful occurrences (like button presses).
  * **Discoverability:** Event entities are already visible in the UI (e.g., in Developer Tools -\> States, and in device pages).
  * **Reusability:** Existing automation triggers for "event" entities can immediately benefit from richer, standardized payloads.
  * **Reduced Complexity:** Avoids creating redundant event buses or concepts.

### How to Evolve the "Event" Entity for `ControllerAction`

Instead of a new `ControllerActionEvent`, the plan would be to define a **standardized schema for the `event_data` attribute** that integrations populate when emitting events from their control devices (e.g., for ZHA `zha_event`, Z-Wave JS `zwave_js_value_updated` which sometimes contain action data, or dedicated `event` entities for button presses).

Here's how we'd update the project plan with this refinement:

-----

### Revised Phase 5: Advanced Device Control Mapping (Leveraging `Event` Entities)

  * **Goal:** Provide a first-class, discoverable mechanism within Home Assistant to "pair" control devices with lights, enabling rich dynamic control without complex blueprints, by leveraging and standardizing the existing `Event` entity type.

#### PR 5.1: Core - Standardized `Event` Entity `event_data` for Controllers

  * **Description:** Define a canonical, structured schema for the `event_data` attribute of `event` entities emitted by control devices. This standardizes how Home Assistant understands what a control device *does*, abstracting away protocol-specific event details and making this data easily consumable by other services and the UI.
  * **Detailed Changes:**
      * **File:** `homeassistant/helpers/event.py` (or a new `homeassistant/helpers/controller_events.py` for specific type definitions).
      * **Logic:** Define a standardized `event_data` schema (e.g., as a `TypedDict` or `dataclass`) that integrations should adhere to for controller actions.
        ```python
        # Conceptual schema for event.event_data for controller actions
        class ControllerEventData(TypedDict):
            action: str # e.g., "single", "double", "long_press", "long_release", "rotate_left", "rotate_right"
            action_id: NotRequired[str] # Optional: More specific ID if 'action' is generic (e.g., "button_1_single")
            # Optional fields for contextual data
            value: NotRequired[float] # For rotary controllers (e.g., degrees or steps)
            # Add other relevant device-specific data if needed (e.g., endpoint for Zigbee)
        ```
      * **Integration Updates:** Update existing major control device integrations (ZHA, Z-Wave JS, MQTT, Philips Hue, Lutron Caseta, etc.) to:
          * If they already expose `event` entities for button presses/actions, ensure their `event_data` conforms to this new standardized `ControllerEventData` schema.
          * If not, introduce `event` entities for discrete controller actions (e.g., an `event.my_remote_button_press` entity that triggers with different `event_data` for each button/action type).
          * For ZHA, this might involve updating quirks or `zha/core/device.py` to map Zigbee cluster commands (e.g., `OnOff`, `LevelControl`, `Scenes`, `Basic` commands for button events) to this standardized `event_data`.
          * For Z-Wave JS, this would involve updates to `zwave_js/light.py` or specific device handlers to parse `Central Scene`, `Multilevel Switch` reports, etc., into this `event_data` format for a dedicated `event` entity.
  * **Interactions:** This provides the structured, discoverable event data for the `homeassistant.link_control` service and the UI.
  * **Testing:** Unit tests for `event_data` schema validation. Integration tests for control devices across integrations to ensure their emitted `event` entities have correctly structured `event_data`.

#### PR 5.2: Core - `homeassistant.link_control` Service (Refined)

  * **Description:** Implement a new core service that allows declarative association of a specific action from an `event` entity with a `light.turn_on` call on a target light entity, including `dynamic_control` parameters.
  * **Detailed Changes:**
      * **File:** `homeassistant/components/homeassistant/services.yaml` (new service definition) and `homeassistant/core/control_mapping.py`.
      * **Logic:**
          * The service schema now specifically targets `event` entities and their actions:
            ```yaml
            homeassistant.link_control:
              fields:
                controller_entity_id: # New: targeting the event entity
                  selector: entity
                  domain: event # Filter for event entities
                  description: The ID of the control event entity (e.g., event.my_remote_button).
                controller_action_data: # Matches the new standardized event_data schema
                  selector: dict # Will be a custom selector in UI
                  description: The specific action from the control device event data (e.g., {action: "long_press", action_id: "button_1"}).
                target_light_entity_id:
                  selector: entity
                  domain: light
                  description: The target light entity.
                light_action: # The action to perform on the light (mimics light.turn_on data)
                  selector: dict
                  description: Parameters for the light.turn_on service call (e.g., dynamic_control).
            ```
          * The service handler internally creates a persistent listener for the specified `controller_entity_id` and filters by `event_data` matching `controller_action_data`. When a match occurs, it triggers the `light.turn_on` service with the `light_action` data.
  * **Interactions:** Directly uses the standardized `event` entity events from PR 5.1 and `light.turn_on` with `dynamic_control` from Phase 3.
  * **Testing:** Unit tests for service validation and internal link creation. Integration tests simulating specific `event` entity events and verifying light service calls.

#### PR 5.3: Frontend - "Link Controls" UI Flow (Refined)

  * **Description:** Develop a user-friendly, guided UI flow that makes `link_control` discoverable and easy to configure, by presenting the `event` entities and their actions.
  * **Detailed Changes:**
      * **Files:** `homeassistant/frontend/src/panels/config/devices/device-detail-card.ts`, new `homeassistant/frontend/src/panels/config/automation/editor/event-trigger-editor.ts` (or similar for custom `link_control` UI).
      * **Logic:**
          * On a **device page** for a controller (e.g., a dimmer switch), a new button "Configure Controls" (or similar) would appear.
          * This button launches a dialog/wizard that presents:
              * **Step 1: Select Controller Event:** A dropdown of `event` entities associated with this device (e.g., `event.my_remote_button`).
              * **Step 2: Select Specific Action:** Based on the selected `event` entity, the UI dynamically lists the *known, standardized actions* (e.g., "Short Press", "Long Press", "Rotate Left") derived from the `ControllerEventData` schema. Users could even perform the physical action to "learn" it.
              * **Step 3: Select Target Light:** Allow the user to pick one or more light entities.
              * **Step 4: Define Light Action:** Provide a tailored `light.turn_on` data editor, heavily featuring controls for `dynamic_control` (e.g., "Dim Up/Down", "Stop Dimming", "Step Brightness", `curve` selection).
              * **Step 5 (Optional): Native Binding Opt-in:** If the integration (ZHA/Z-Wave JS) supports programmatic native binding for the selected `event` entity's action and target light, present an option: "Optimize for Native Binding (faster, works offline, but may limit advanced HA features like custom curves)." This opt-in would call the native binding APIs (from PR 5.4) instead of the internal software automation.
              * **Finalize:** Call the `homeassistant.link_control` service.
  * **Interactions:** Consumes `event` entities from PR 5.1, calls `link_control` service from PR 5.2.
  * **Testing:** User acceptance testing for intuitiveness and ease of use. Frontend integration tests.

#### PR 5.4: Integration Updates (ZHA/Z-Wave JS) for Native Binding Management (No Change)

  * This PR's scope remains largely the same, focusing on exposing programmatic APIs within ZHA and Z-Wave JS to manage native device bindings/associations, and integrating this with the `homeassistant.link_control` service. The key is that the `homeassistant.link_control` service (and its UI) will now drive whether to use these native binding APIs.

#### PR 5.5: Documentation (No Change in Scope, Content Adjusted)

  * The scope remains the same, but the content will be adjusted to reflect the use of `event` entities for controller actions.

This refined approach provides a clean, discoverable, and powerful way to link control devices to lights, tightly integrated into Home Assistant's existing event-driven architecture, while supporting the new dynamic lighting capabilities.

----

This is an excellent scenario to walk through, as it highlights the interplay between different integrations, Home Assistant Core's new features, and the proposed control mapping.

Let's imagine this future Home Assistant environment where the "Universal Smart Lighting Control" and "Advanced Device Control Mapping" phases are complete.

-----

## Walkthrough: Controlling Wiz Lights with a Lutron Pico Remote

This walkthrough describes how you, as a Home Assistant user, would set up a Lutron Pico remote to dynamically control a group of Wiz lights, including smooth, perceptually optimized dimming, and what happens behind the scenes.

**Scenario:** You have several Wiz smart bulbs in your living room, grouped as `light.living_room_wiz_lights`. You also have a Lutron Pico remote paired via your Lutron Caseta Smart Bridge Pro and integrated into Home Assistant. You want the Pico's "Dim Up" and "Dim Down" buttons to smoothly adjust the brightness of your Wiz lights, with a natural, logarithmic dimming curve.

-----

### Part 1: User Experience - Setting up the Control Mapping

This is what you would see and do in the Home Assistant UI.

1.  **Ensure Devices are Integrated:**

      * You have already configured your **Lutron Caseta integration** in Home Assistant, and your Pico remote appears as a device (e.g., `remote.pico_living_room_dimmer`).
      * You have configured your **Wiz integration** and all your Wiz lights are visible (e.g., `light.wiz_bulb_1`, `light.wiz_bulb_2`).
      * You have created a **Home Assistant Light Group** named `light.living_room_wiz_lights` that includes all your individual Wiz bulbs.

2.  **Navigate to the Control Device:**

      * In Home Assistant, go to **Settings \> Devices & Services \> Devices**.
      * Find and click on your **Lutron Pico remote** device (e.g., "Pico Living Room Dimmer").

3.  **Initiate Control Mapping:**

      * On the device page for your Pico remote, you'll see a new section or button labeled **"Configure Controls"** (from **Phase 5, PR 5.3**). Click this.

4.  **Select the Controller Event:**

      * A wizard appears. It will list the `Event` entities associated with this device. For a Pico, you might see `event.pico_living_room_dimmer_events`. Select this.
      * The wizard then dynamically displays the **standardized actions** (from **Phase 5, PR 5.1**) that this event entity can emit. For a Pico, you'd see:
          * `button_on_press`
          * `button_off_press`
          * `button_favorite_press`
          * `button_dim_up_start`
          * `button_dim_up_stop`
          * `button_dim_down_start`
          * `button_dim_down_stop`
      * You'll first select **`button_dim_up_start`**.

5.  **Select the Target Light(s):**

      * The wizard prompts you to select the target entity. You choose **`light.living_room_wiz_lights`**.

6.  **Define the Light Action (Dim Up):**

      * Now, you define *what happens* to the light group when that Pico button action occurs. This interface directly maps to the new `light.turn_on` `dynamic_control` parameters.
      * You would choose:
          * **Action Type:** `Dim Up (Continuous)`
          * **Speed:** `Medium` (or specify a custom percentage per second)
          * **Dimming Curve:** `Logarithmic` (this will be the default, but you could explicitly pick it or another one like `linear` or `s_curve`).
      * The UI would internally construct the `dynamic_control` payload:
        ```yaml
        dynamic_control:
          type: move
          direction: up
          speed: medium
          curve: logarithmic
        ```
      * You confirm and save this link.

7.  **Define the Light Action (Stop Dimming - for Dim Up Release):**

      * You repeat steps 4-6, but this time you select **`button_dim_up_stop`** from the Pico actions.
      * For the Light Action, you choose:
          * **Action Type:** `Stop Dimming`
      * The UI internally constructs:
        ```yaml
        dynamic_control:
          type: stop
        ```
      * You confirm and save this link.

8.  **Repeat for Dim Down:** You perform steps 4-7 again, but for `button_dim_down_start` (with `direction: down`) and `button_dim_down_stop`.

-----

### Part 2: Behind the Scenes - The Technical Flow

Now, let's trace what happens when you press and release the "Dim Up" button on your Pico remote:

1.  **Physical Button Press (Lutron Pico):** You long-press the "Dim Up" button on your Pico remote.

2.  **Lutron Caseta Bridge to Home Assistant:** Your Lutron Caseta Smart Bridge detects this long-press event and communicates it to the **Lutron Caseta integration** in Home Assistant.

3.  **Standardized Event Emission (Phase 5, PR 5.1):**

      * The Lutron Caseta integration (now updated with the `ControllerAction` standardization) processes the raw Lutron event.
      * It then emits a **standard Home Assistant event** for your Pico remote's event entity (e.g., `event.pico_living_room_dimmer_events`).
      * The `event_data` for this event conforms to the new standard:
        ```json
        {
          "action": "long_press",
          "action_id": "button_dim_up_start"
        }
        ```
      * This event is put onto the Home Assistant event bus.

4.  **Control Mapping Listener (Phase 5, PR 5.2):**

      * The internal listener (created by the `homeassistant.link_control` service when you set up the mapping) is constantly monitoring the event bus.
      * It detects the `event.pico_living_room_dimmer_events` with the matching `action` and `action_id`.
      * Upon a match, this listener triggers a `light.turn_on` service call.

5.  **`light.turn_on` Service Call:**

      * The service call is directed at your light group:
        ```yaml
        service: light.turn_on
        target:
          entity_id: light.living_room_wiz_lights
        data:
          dynamic_control:
            type: move
            direction: up
            speed: medium
            curve: logarithmic
        ```

6.  **Light Group Expansion (Home Assistant Core):**

      * The `light` group integration in Home Assistant Core receives this service call.
      * It expands the call, effectively sending the exact same `light.turn_on` service call to *each individual Wiz light entity* within the `light.living_room_wiz_lights` group.

7.  **Wiz Integration (No Native Dynamic Control):**

      * The `light.turn_on` call reaches each individual **Wiz light entity**.
      * The Wiz integration (like many Wi-Fi-based integrations) generally *does not* support `LightEntityFeature.DYNAMIC_CONTROL` natively (it can't translate `move`/`stop` into a single Wiz API call, nor does it typically accept a `curve` parameter).
      * However, because the Wiz integration *does* declare `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` and `LightEntityFeature.TRANSITION_SIMULATED`, it signals to Home Assistant Core that it *can* be smoothly controlled via simulation.

8.  **HA Core Simulation Takes Over (Phase 3, PR 3.3):**

      * For *each individual Wiz light*, the `LightTransitionManager` in Home Assistant Core detects the lack of native `DYNAMIC_CONTROL` support but the presence of `DYNAMIC_CONTROL_SIMULATED`.
      * It interprets the `dynamic_control: { type: move, direction: up, curve: logarithmic }` parameter.
      * It begins to **calculate a series of rapid, incremental brightness steps** using the `logarithmic` dimming curve. This ensures that the *perceived* brightness change is smooth and natural to your eye.
      * It then schedules very frequent (e.g., every 50ms) `light.turn_on` service calls to each individual Wiz light, each time providing the next calculated linear `brightness_pct` value.
      * Simultaneously, the `LightTransitionManager` updates the `dynamic_state` of `light.living_room_wiz_lights` (and its individual members) to `simulated_moving_brightness_up`.

9.  **Wiz Lights Adjust:**

      * Each Wiz light integration rapidly receives these `light.turn_on` calls with the individual `brightness_pct` values.
      * The Wiz light devices then adjust their actual light output based on these commands.
      * Because the `brightness_pct` changes are small, frequent, and calculated according to the logarithmic curve, the group of Wiz lights dims up smoothly and perceptually evenly to your eye.

10. **Stopping the Dimming (User releases button):**

      * You release the "Dim Up" button on the Pico.
      * The Lutron Caseta integration emits another standardized event: `event.pico_living_room_dimmer_events` with `event_data: { "action": "long_release", "action_id": "button_dim_up_stop" }`.
      * The corresponding `homeassistant.link_control` listener triggers `light.turn_on` targeting `light.living_room_wiz_lights` with `dynamic_control: { type: stop }`.
      * The `LightTransitionManager` receives this `stop` command for each Wiz light, immediately ceases its simulation, and sets the `dynamic_state` of the light group and its members back to `idle`. The lights hold their current brightness.

-----

### Key Benefits of this Approach:

  * **Discoverability & Simplicity:** No need to write YAML automations or find blueprints. The UI guides you through a few clicks.
  * **Intuitive Control:** A simple "long press" on a physical dimmer button directly translates to smooth, continuous dimming.
  * **Perceptual Accuracy:** The `logarithmic` curve ensures the dimming *feels* natural and even to your eyes, even for lights (like Wiz) that don't natively support such curves.
  * **Universal Compatibility:** This setup works for *any* light that declares `DYNAMIC_CONTROL_SIMULATED`, regardless of its underlying integration (Wi-Fi, Zigbee, Z-Wave, etc.).
  * **Powerful Logic:** All the advanced logic (curves, speeds) is handled centrally by Home Assistant Core, abstracting away device-specific limitations.
  * **Group Control:** Seamlessly applies dynamic control to entire light groups.