# Better User Experience for Setup with Auto-Populated Defaults

A truly evolved Home Assistant should go beyond raw event linking and offer intelligent, discoverable defaults based on the device types being paired. This would drastically improve the out-of-box experience.

The core idea is to leverage Home Assistant's existing knowledge about device capabilities and common usage patterns.

### Vision: Intelligent Control Suggestions

Instead of merely presenting raw event actions, the UI would:

1.  **Recognize Controller Type:** Identify the connected device as a "dimmer switch," "scene remote," "rotary controller," etc., based on its declared capabilities (e.g., exposed event entities, device class, or integration-specific metadata).
2.  **Infer Common Actions:** For recognized controller types, suggest common mappings for its standard buttons/controls to relevant light actions.
3.  **Pre-populate Light Action Defaults:** When a light is selected as a target, pre-fill the `dynamic_control` parameters with sensible defaults (e.g., `logarithmic` curve, `medium` speed for dimming, `toggle` for on/off).

### How it Would Work in the UI (User Walkthrough):

Imagine you've just added a **Lutron Pico Remote** and a **Light Group (Living Room Lights)**.

1.  **Navigate to the Controller Device:**

      * Go to **Settings \> Devices & Services \> Devices**.
      * Select your **Lutron Pico Remote** device (e.g., `Pico Living Room Dimmer`).
      * Click on **"Configure Controls"**.

2.  **Intelligent Mapping Suggestions:**

      * Instead of a blank slate, the wizard (from **Phase 5, PR 5.3**) immediately presents a set of **suggested mappings** for this specific Pico remote, targeting a *default light* (which could be the most recently added dimmable light, or prompted selection):

      * **Suggested Mapping 1: Top Button (On) -\> Toggle Living Room Lights**

          * **Controller Action:** `event.pico_living_room_dimmer_events` with `event_data: {action: "button_on_press"}`
          * **Target Light:** `light.living_room_wiz_lights`
          * **Proposed Light Action:** `Toggle`

      * **Suggested Mapping 2: Bottom Button (Off) -\> Turn Off Living Room Lights**

          * **Controller Action:** `event.pico_living_room_dimmer_events` with `event_data: {action: "button_off_press"}`
          * **Target Light:** `light.living_room_wiz_lights`
          * **Proposed Light Action:** `Turn Off`

      * **Suggested Mapping 3: Dim Up Button (Hold) -\> Dim Up Living Room Lights**

          * **Controller Action:** `event.pico_living_room_dimmer_events` with `event_data: {action: "button_dim_up_start"}`
          * **Target Light:** `light.living_room_wiz_lights`
          * **Proposed Light Action (auto-populated `dynamic_control`):**
            ```yaml
            dynamic_control:
              type: move
              direction: up
              speed: medium # Sensible default speed
              curve: logarithmic # Sensible default for perceived dimming
            ```

      * **Suggested Mapping 4: Dim Up Button (Release) -\> Stop Dimming**

          * **Controller Action:** `event.pico_living_room_dimmer_events` with `event_data: {action: "button_dim_up_stop"}`
          * **Target Light:** `light.living_room_wiz_lights`
          * **Proposed Light Action:**
            ```yaml
            dynamic_control:
              type: stop
            ```

      * (And similar for Dim Down)

3.  **User Interaction with Suggestions:**

      * Each suggestion would have "Accept," "Modify," and "Ignore" options.
      * Clicking "Modify" opens the detailed action editor, pre-filled with the suggestion, allowing fine-tuning (e.g., changing speed, choosing a `square_law` curve instead of `logarithmic`).
      * The user can then "Accept All Suggestions" or go through them one by one.

### Architectural Implications for Auto-Population:

This requires a new layer of "intelligence" or metadata.

  * **Core - `ControllerProfile` Metadata:**
      * **Concept:** A new, optional metadata structure within Home Assistant that integrations can provide for their controller devices. This profile would map *internal controller actions* (e.g., button press codes) to the *standardized `ControllerEventData`* (from **Phase 5, PR 5.1**) *and* suggest default `light_action` payloads for common light control scenarios.
      * **Definition:** Could be a JSON file or a Python dictionary within the integration, perhaps part of the `device_info` or a new `controller_info` property on the `DeviceEntry`.
      * **Example (Conceptual):**
        ```json
        # homeassistant/components/lutron_caseta/controller_profiles/pico_dimmer.json
        {
          "device_model_identifiers": ["Lutron_Pico_Dimmer"],
          "suggested_mappings": [
            {
              "controller_event_data": {"action": "button_on_press", "action_id": "top_button"},
              "light_action_template": {"toggle": {}}
            },
            {
              "controller_event_data": {"action": "button_off_press", "action_id": "bottom_button"},
              "light_action_template": {"turn_off": {}}
            },
            {
              "controller_event_data": {"action": "button_dim_up_start", "action_id": "middle_up"},
              "light_action_template": {
                "dynamic_control": {
                  "type": "move",
                  "direction": "up",
                  "speed": "medium",
                  "curve": "logarithmic"
                }
              }
            },
            {
              "controller_event_data": {"action": "button_dim_up_stop", "action_id": "middle_up"},
              "light_action_template": {
                "dynamic_control": {
                  "type": "stop"
                }
              }
            }
            // ... similar for dim_down, favorite, etc.
          ]
        }
        ```
  * **Frontend Logic:** The "Configure Controls" UI (PR 5.3) would:
    1.  Read the `ControllerProfile` (if available) for the selected controller device.
    2.  Based on the `suggested_mappings` and the selected `target_light_entity_id` (perhaps it defaults to the first dimmable light group/entity), it generates the pre-filled `homeassistant.link_control` service calls.
    3.  Present these as "suggestions" to the user, allowing easy acceptance or modification.
  * **"Learn Mode" for Actions:** The UI could also offer a "Learn Mode" button. When activated, Home Assistant would listen for *any* event from that controller for a few seconds. When an event occurs, it captures its `event_data` and offers to use *that specific observed action* for the mapping. This is great for unusual buttons or devices without pre-defined profiles.

This approach makes the powerful control mapping features accessible to a much broader user base, reducing the cognitive load and setup time significantly.

-----
