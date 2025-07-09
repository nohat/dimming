# Light State Management Enhancements

This is an excellent follow-up question! The core of Home Assistant's state model for lights, and indeed for most entities, is to represent the _current, stable, observed state_
. This works well for static values, but less so for dynamic, ongoing processes like "move/stop" transitions.

Here's how Home Assistant's light state currently works and what would need to be enhanced to properly represent dynamic
states:

## Home Assistant Light State Model - Current Limitations

Home Assistant's `light` entities (derived from `homeassistant.components.light.LightEntity`) typically expose the
following relevant state attributes:

- **`state`**: "on" or "off".
- **`brightness`**: (0-255) The current brightness level.
- **`color_mode`**: e.g., `ColorMode.HS`, `ColorMode.RGB`, `ColorMode.COLOR_TEMP`, `ColorMode.BRIGHTNESS`,
  `ColorMode.ONOFF`.
- **Color Attributes**: `hs_color`, `rgb_color`, `xy_color`, `color_temp_kelvin`, etc., reflecting the current color.
- **`effect`**: The currently active effect (e.g., "blink", "rainbow").
- **`supported_features`**: A bitmask indicating capabilities like `TRANSITION`, `FLASH`, `EFFECT`, `BRIGHTNESS`,
  `COLOR_TEMP`, `COLOR`.

**The key limitation for "move/stop" and dynamic transitions:**

- **`brightness` and color attributes represent the _current_ observed value, not the _target_ or _transitioning_
  state.**
    - If a light is slowly dimming from 100% to 0% over 30 seconds, Home Assistant's `brightness` attribute will update
      incrementally as the light dims. It won't tell you "this light is currently actively dimming towards 0%."
- **No explicit "transitioning" state:** There's no attribute like `is_transitioning: true` or `transition_target: 0%`
  that would inform other automations or the UI about an active, ongoing, commanded transition.
- **`transition` is an _input parameter_, not an _output state attribute_.** When you call `light.turn_on` with
  `transition: 5s`, that `transition` value isn't stored in the light's state attributes. It's a one-time instruction
  to the device.

### Enhancements to the Home Assistant Light State Model

To truly support dynamic "move/stop" and more sophisticated transitions, we'd want to add state attributes that
represent the _intent_ and _progress_ of a dynamic light change.

Here's what Home Assistant's `LightEntity` could benefit from:

1. **`transition_state` (New Attribute):**

   - **Purpose:** Indicate if a light is currently undergoing a commanded transition, and what kind.
   - **Possible Values:**
     - `idle` (default, no active transition)
     - `transitioning` (a standard `turn_on` with `transition` is active)
     - `moving_brightness_up`
     - `moving_brightness_down`
     - `moving_color_temp_up`
     - `moving_color_temp_down`
     - `moving_color` (for continuous hue/saturation changes)
   - **Benefit:** Automations could _trigger_ or _condition_ on `transition_state`. E.g., "if light is
     `moving_brightness_up`, then disable motion sensor dimming."

2. **`transition_target_brightness` / `transition_target_color` (New Attributes):**

   - **Purpose:** If a transition is active, what is the intended final brightness/color?
   - **Values:** Same format as `brightness` (0-255) or color attributes.
   - **Benefit:** The UI could show "50% (-> 80%)" indicating current and target. Automations could use this to make
     smart decisions.

3. **`transition_progress` (New Attribute, Optional):**

   - **Purpose:** A percentage (0-100%) indicating how far along an ongoing transition is.
   - **Values:** Float from 0.0 to 100.0.
   - **Benefit:** For advanced UI elements or visualizers, or for debugging. Less critical for automations but useful.

4. **`transition_mode` (New Attribute, Optional):**

   - **Purpose:** If a `light.move_brightness` (or similar) command is active, what are the parameters of that move?
   - **Values:** A dictionary that might contain:
     - `action: 'move'`
     - `direction: 'up'`
     - `speed: 'medium'` (or the resolved numeric value)
     - `curve: 'logarithmic'`
     - `ramp_time: 0.5`
   - **Benefit:** Provides full context about the current dynamic operation. This is likely more for diagnostic or
     advanced display than common automation logic.

5. **`dimming_curve` / `min_output` / `max_output` (New Configuration/Attribute, per light):**

   - **Purpose:** These are properties of the light _itself_ (or its current operating mode). They define how it behaves.
   - **Location:** Ideally, these would be configurable via `customize:` or a light's device settings, and then exposed
     as read-only state attributes.
   - **Benefit:** Home Assistant, when sending commands, could account for these curves. E.g., if a light has a
     `logarithmic` dimming curve, the UI slider might be adjusted to _appear_ linear even though it sends non-
     linear underlying values. Or, Home Assistant knows not to command below `min_output`.

### How these enhancements would propagate

1. **ESPHome Firmware:** The ESPHome `light` component would become the primary intelligence for managing the
   "move/stop" logic. It would actively calculate the current brightness based on the received `move` command, curve,
   speed, and ramp time. It would then _report_ these dynamic `brightness` values back to Home Assistant in real-
   time. Crucially, when a `move` command is active, ESPHome would also need to report the new `transition_state` and
   `transition_target_brightness` (if applicable) to Home Assistant.

2. **Home Assistant Integrations (e.g., ESPHome via Native API, MQTT, ZHA, Matter):**

   - These integrations would be responsible for translating the incoming messages from the physical device (ESPHome) or
     the protocol (Zigbee, Matter) into Home Assistant's internal `LightEntity` state attributes.
   - For `light.move_brightness` service calls originating _from_ Home Assistant, the integration would pass these
     complex parameters down to the device (ESPHome) or protocol (Zigbee/Matter cluster command).
   - They would update `transition_state`, `transition_target_brightness`, etc., based on what the device is _doing_ or
     what command was just sent.

3. **Home Assistant Core `LightEntity`:**

   - The base `LightEntity` class would be extended to include these new attribute properties.
   - It would have methods for integrations to update these properties.
   - It would be responsible for dispatching state change events when these new attributes change, allowing automations
     and frontend components to react.

4. **Home Assistant Frontend:**

   - UI elements (e.g., light cards, developer tools) could then visually represent "Light is dimming up (target 80%)"
     instead of just showing the current brightness bouncing around.
   - More advanced control panels could surface the `transition_mode` details, `min_output`, `max_output`, and allow
     selection of `curve` profiles.

### Challenges

- **Real-time Reporting:** For smooth transitions, devices (like ESPHome) would need to report their `brightness` and
  `transition_state` frequently enough to provide a smooth update in Home Assistant. This means more state updates,
  which can increase network traffic, though typically manageable for a few lights.
- **State Latency:** There will always be some latency between the actual light change on the device and Home
  Assistant's state reflecting it. However, if the device manages the _entire_ transition locally and just reports
  state, this latency becomes less critical than when HA is sending rapid commands.
- **Complexity:** Adding these attributes and managing their lifecycle adds complexity to the core `light` component and
  all integrations. It requires careful design and testing.

Ultimately, by enhancing the light state model to explicitly track _what a light is doing_ (its dynamic state) rather
than just _what its current output is_, Home Assistant can move beyond basic control to a much richer, more responsive,
and more intuitive lighting experience, aligning with professional standards and modern smart home protocols.

______________________________________________________________________

This is where the concept of "control hierarchy" or "arbitration" becomes crucial.
In professional lighting systems, a sophisticated control engine decides which command takes precedence when multiple sources try to control the same light
.
For Home Assistant and ESPHome, we can build a layered system that achieves seamless blending, responsiveness, and graceful fallback.

### Principles of the Hierarchy

1. **Device-Local Priority for Dynamic Control:** The device itself (e.g., ESPHome) should have the highest priority for
   managing _ongoing, dynamic_ changes like "move/stop" operations triggered by a physical button on the device. This
   ensures the best responsiveness and avoids network latency issues.
2. **Home Assistant as the Orchestrator/State Reporter:** Home Assistant acts as the central brain, issuing high-level
   commands, receiving state updates, and providing a unified abstraction layer for the user and automations. It
   becomes the "source of truth" for the current _observed_ state, but not necessarily the _executor_ of every micro-
   step of a transition.
3. **Fallback for Less Capable Devices:** If a device (or its integration) doesn't support the advanced dynamic
   commands, Home Assistant should gracefully fall back to its existing methods (e.g., rapid-fire `turn_on` commands
   with small increments).
4. **Clear Precedence Rules:** Define how new commands override or interact with ongoing operations.

### Proposed Layered System Architecture

**Layer 1: Device Hardware & Firmware (ESPHome)**

- **Role:** Real-time execution, local control logic, precise state management, and continuous reporting.
- **Capabilities:**
    - **Native "Move/Stop" Engine:** Implements the `light.move_brightness` (and color) logic directly in the ESPHome
      light component. This includes:
        - Receiving `move` (direction, speed, curve, ramp_time) and `stop` commands.
        - Executing the brightness/color ramp locally, calculating intermediate values based on the specified curve and speed.
        - Handling `ramp_time` for smooth acceleration/deceleration.
        - Managing the minimum/maximum output levels.
        - **Local Event Handling:** Processes physical button presses/releases directly on the ESP. When a "hold" is
          detected, it initiates a local `move` operation. On "release," it initiates a local `stop`. This is
          _not_ sent to HA for every tiny brightness change.
    - **Instantaneous State Reporting:** Periodically (e.g., every 50-100ms during active transition, or on significant
      change, or at a fixed interval during idle) publishes its `current_brightness`, `current_color`, and
      crucially, its **`transition_state`** (e.g., `moving_brightness_up`, `idle`). This makes the dynamic state
      visible to Home Assistant.
    - **Command Prioritization:**
        - **Local Manual Control:** If a physical button on the ESPHome device is _actively being held_ for a "move"
          operation, this typically has the highest priority. An incoming HA command (e.g., `light.turn_on` to
          a specific brightness) would _override_ the local move, _stopping_ the move and transitioning to the
          new HA-commanded state. This ensures user intent from a physical control is respected but can be
          overridden by central control.
        - **Incoming HA Commands (`light.adjust_brightness`):** These commands always take precedence over any _passive_
          local state (e.g., if the light was just sitting at a set brightness). If a
          `light.adjust_brightness.move` is received, it starts the local move. If a `light.turn_on` is
          received, it stops any existing dynamic move and transitions to the new target.
        - **Default Behavior on Startup/Loss of HA:** The device should retain its last known state or revert to a safe
          default if HA is unavailable.

**Layer 2: Home Assistant Core & Integrations**

- **Role:** Command translation, state aggregation, exposing capabilities, fallback for less capable devices, and
  central automation/UI.
- **Capabilities:**
    - **`light` Domain Service Calls:** Implements the sophisticated `light.adjust_brightness` service as discussed,
      with parameters for `action` (move, stop, set, step), `speed`, `curve`, `ramp_time`, `min/max_output`, etc.
    - **`LightEntity` State Attributes:** Extends the `LightEntity` to include `transition_state`,
      `transition_target_brightness`, etc.
    - **Integration Adapters (e.g., ESPHome Native API, MQTT, ZHA, Matter):**
        - **Sending Commands:** When `light.adjust_brightness` is called for an entity, the integration determines if
          the underlying device supports the advanced features.
            - **If supported (e.g., ESPHome with new firmware):** Translates the `HA.adjust_brightness` service call
              directly into a concise, high-level device command (e.g., a custom ESPHome API command or a
              specific MQTT message `move/up/logarithmic`). The device then handles the continuous
              dimming.
            - **If NOT supported (e.g., legacy Zigbee, simpler MQTT light):** Falls back to sending rapid, small
              `light.turn_on` commands with incremental brightness changes to _simulate_ the "move" on the
              HA side. The `stop` command would simply issue a `turn_on` to the current `brightness`. This
              ensures compatibility but with a less responsive UX.
        - **Receiving State:** Listens for periodic state updates from devices.
            - **From capable devices (ESPHome):** Reads `current_brightness`, `current_color`, `transition_state`, etc.,
              directly and updates the `LightEntity` attributes.
            - **From less capable devices:** Continues to infer state from reported `brightness` values. If Home
              Assistant is simulating a "move," it will update its own internal `transition_state` for
              that entity.
    - **Arbitration Logic (for HA-side conflicts):** If multiple automations or users in HA issue conflicting commands
      (e.g., one automation starts dimming up, another tries to set a specific brightness), HA's existing conflict
      resolution (last command wins, or more complex blueprints) would apply. The key is that the _device_ is the
      ultimate arbiter for _local_ real-time commands.

**Layer 3: Home Assistant Frontend & Automation Engine**

- **Role:** User interface, automation creation, and high-level control.
- **Capabilities:**
    - **Dynamic UI Elements:** Light cards could show `brightness` and `transition_state` (e.g., a "dimming up"
      indicator). Sliders could dynamically move as the device adjusts, providing real-time feedback.
    - **Enhanced Automations:** Users can trigger automations based on the new `transition_state` attributes ("When
      light enters `moving_brightness_up` state...").
    - **Simplified Blueprints:** Designers can create blueprints for button controllers that seamlessly implement "hold-
      and-release" using the new `light.adjust_brightness` service call, reducing complexity for end-users.

### Ensuring Optimal Interaction and Seamless Blending

1. **"Source of Truth" Delegation:**
   - **Device as Source for _Instantaneous Output_**: The ESPHome device is the definitive source for its _current_
     light output (brightness/color). It pushes these updates.
   - **HA as Source for _Desired State/Command Intent_**: Home Assistant is the definitive source for _what command was
     last sent_ and _what the overall system intends_ for the light. This is reflected in the new
     `transition_target` and `transition_mode` attributes.
2. **Clear Override/Precedence Rules:**
   - **Command Takes Precedence:** Any new command (from HA or a local button) _interrupts_ and _overrides_ an ongoing
     dynamic operation. A `light.turn_on` to a fixed brightness stops a `move_brightness` and transitions to the
     new fixed value. A `light.adjust_brightness.stop` stops any ongoing `move`.
   - **Local Control Overrides Remote During Active Hold:** If a user is physically holding a button on the device to
     dim, the device should prioritize that input locally for maximum responsiveness. If an HA command comes in
     _while the button is held_, the device needs to decide:
     - Option A (Simpler): The HA command immediately takes over, and the local button's effect is overridden for the
       duration of the HA command. When the HA command finishes, and the button is still held, the local move
       resumes.
     - Option B (More Complex but Better UX): The HA command momentarily takes over. If the button is _still held_ after
       the HA command, the local control _re-asserts_ its `move` command, potentially to continue from the new
       brightness level. This requires careful state tracking on the device.
     - **Recommendation:** Option A is simpler to implement initially. For Option B, the HA command would be treated as
       a temporary "override" that sets a new base from which the local "move" could continue.
3. **Heartbeat/Watchdog:** Home Assistant integrations can implement a simple "heartbeat" or "watchdog" for devices that
   are _expected_ to report `transition_state`. If a device is commanded into a `moving_brightness_up` state but
   stops reporting updates, HA can flag it as unresponsive or revert its own internal state model.
4. **Error Handling & Fallbacks:**
   - If a device reports an `transition_state` that Home Assistant doesn't understand, it can log a warning and default
     to the `brightness` value.
   - If a `light.adjust_brightness` command is sent to a device that doesn't support it, the integration should defer to the fallback mechanism detailed in [`technical-strategy/simulated_dimming.md`](../technical-strategy/simulated_dimming.md).
5. **Documentation:** Clear documentation for users and developers on how this hierarchy works, which commands take
   precedence, and what to expect from state attributes during dynamic operations is paramount.

This layered approach ensures that the most capable devices (like advanced ESPHome firmware) can deliver the best, most responsive user experience with local control, while the entire ecosystem benefits from standardized command structures and rich state representation in Home Assistant
.
Less capable devices can still participate, albeit with a slightly less seamless (but still functional) experience, creating a robust and adaptable smart home platform.
