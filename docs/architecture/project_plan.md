# Project Plan: Universal Smart Lighting Control

## 1. Project Title

**Universal Smart Lighting Control: Enhanced Transitions and Dynamic Control for All Lights**

## 2. Project Goal

To provide a seamless, responsive, and consistent user experience for dynamic light control (including smooth
transitions and continuous dimming/color adjustment) across all controllable lights in Home Assistant, regardless of
their native device capabilities, by strategically enhancing both ESPHome and Home Assistant Core.

## 3. Motivation & Rationale

Currently, users face inconsistent behavior when attempting to control smart lights with effects like smooth transitions
or "hold-to-dim" functionality.

- **Inconsistent Transitions:** Many lights (especially older or simpler ones) ignore the `transition:` parameter in
  `light.turn_on`, resulting in abrupt state changes ("snapping") instead of smooth fades.

- **Complex Workarounds:** Achieving continuous dimming (e.g., "hold-to-dim" from a physical button or a UI slider)
  often requires complex, custom Home Assistant automations or community-developed scripts that send rapid,
  incremental commands.

- **Network Overload:** These software-based workarounds can flood the local network (Wi-Fi, Zigbee, Z-Wave) with
  frequent commands, leading to performance issues, unreliability, and a choppy user experience.

- **Lack of Unified State Feedback:** Home Assistant lacks a standardized way to know if a light is _actively_
  transitioning or undergoing continuous adjustment, hindering rich UI feedback and intelligent automations.

- **Discrepancy with Standards:** Modern lighting standards like Matter and Zigbee Light Link (ZLL) include explicit
  commands for continuous movement (`Move to Level`, `Step`, `Stop`), which are not universally or consistently
  exposed and handled in Home Assistant.

This project aims to address these pain points by introducing a layered hierarchy of state control that prioritizes on-
device processing where possible and intelligently simulates complex behaviors within Home Assistant for less capable
devices.

## 4. Key Deliverables

- **ESPHome Firmware Enhancements:**

    - On-device, high-resolution smooth transitions for all light types.

    - Native "move/stop" and "step" functionality for brightness and color.

    - Configurable dimming/color curves and speed profiles via YAML.

    - Real-time reporting of light's dynamic state (`moving_up`, `transitioning`, `idle`).

    - Simplified local button bindings for dynamic control.

- **Home Assistant Core Enhancements:**

    - Extended `light.turn_on` service schema to support `dynamic_control` parameters.

    - Introduction of new `LightEntityFeature` flags for `TRANSITION_SIMULATED` and `DYNAMIC_CONTROL_SIMULATED`.

    - Centralized `LightTransitionManager` (or similar core logic) to intelligently simulate transitions and dynamic
      control for lights that don't support them natively.

    - Consumption and exposure of ESPHome's new `dynamic_state` attributes.

- **Improved User Experience:**

    - Consistent and smooth light transitions/dynamic adjustments across heterogeneous devices.

    - Reduced complexity of automations for dynamic light control.

    - More informative Home Assistant UI feedback on light activity.

- **Documentation:** Comprehensive updates for both ESPHome and Home Assistant.

## 5. Phases & Milestones

### Phase 1: ESPHome Foundation (Internal Firmware Capabilities)

- **Goal:** Equip ESPHome light components with the fundamental capabilities for smooth internal transitions and the
  framework for dynamic control.

- **Timeline:** 4-6 weeks (allowing for thorough testing and review per PR).

    - **PR 1.1: ESPHome - Internal `LightState` Time-Based Interpolation Refinement**

        - **Description:** Enhance the `LightState`'s internal handling of `transition_length` to ensure high-
          resolution, time-based interpolation of brightness and color changes. This PR will focus on
          optimizing the existing transition mechanism to achieve maximum smoothness and prepare for more
          complex dimming curves, even if the current implementation already offers basic time-based changes,
          this ensures it's robust and precise enough for the dynamic control features.

        - **Output:** Smoother transitions for existing `transition:` parameters on ESPHome lights.

    - **PR 1.2: ESPHome - YAML Configuration for Custom Dimming Curves & Speed Profiles**

        - **Description:** Add top-level `dynamic_control_profiles` schema under `light:` component in ESPHome YAML for
          defining reusable `speed` and `curve` characteristics.

        - **Output:** Users can define custom dimming behaviors in YAML, ready for future use.

### Phase 2: ESPHome Native Dynamic Control

- **Goal:** Implement the core on-device "move/stop" and "step" logic in ESPHome and enable reporting of its dynamic
  state.

- **Timeline:** 6-8 weeks.

    - **PR 2.1: ESPHome - `LightCall` Expansion for `dynamic_control` Parsing**

        - **Description:** Extend the `light.turn_on` service schema in ESPHome's Native API to accept the
          `dynamic_control` parameter and parse it into internal `LightCall` / `LightState` structures. No
          functional change to light output yet.

        - **Output:** ESPHome devices can receive richer commands. Debug logs show parsed `dynamic_control` parameters.

    - **PR 2.2: ESPHome - On-Device Continuous Brightness `move`/`stop`**

        - **Description:** Implement the `loop()` logic within `LightState` to perform continuous brightness adjustment
          (`move` up/down, `stop`) based on received `dynamic_control` commands, using configured
          curves/speeds.

        - **Output:** ESPHome lights respond to internal "move" commands (e.g., from local buttons) with smooth, on-
          device continuous dimming.

    - **PR 2.3: ESPHome - On-Device Continuous Color `move`/`stop`/`step`**

        - **Description:** Extend PR 2.2 to apply continuous control and stepping for color properties (hue, saturation,
          color temperature).

        - **Output:** Full range of on-device dynamic light control.

    - **PR 2.4: ESPHome - `dynamic_state` Reporting via Native API**

        - **Description:** Add new attributes (`dynamic_state`, `active_speed_profile`, `active_curve_profile`,
          `dynamic_target_brightness`, etc.) to the `LightState` and ensure they are published via the Native
          API.

        - **Output:** Home Assistant (via debug tools) can now observe the light's current dynamic activity.

### Phase 3: Home Assistant Universal Handling

- **Goal:** Enable Home Assistant Core to understand and orchestrate universal transitions and dynamic control,
  including simulation for non-native devices.

- **Timeline:** 8-10 weeks.

    - **PR 3.1: HA Core - Introduce `LightEntityFeature.TRANSITION_SIMULATED`**

        - **Description:** Add a new `LightEntityFeature` flag in Home Assistant Core to allow integrations to declare
          their ability to simulate transitions.

        - **Output:** Standardized declaration for simulated transition capability.

    - **PR 3.2: HA Core - Universal Transition Simulation Logic**

        - **Description:** Implement the core logic within `light/__init__.py` to simulate `transition_length` for
          entities that support `TRANSITION_SIMULATED` but not native `TRANSITION`.

        - **Output:** All lights can now honor the `transition:` parameter, providing smooth fades (native or
          simulated). This is a _major_ win for UX.

    - **PR 3.3: HA Core - Introduce `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` & Universal Dynamic Control
      Simulation Logic**

        - **Description:** Add `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` and implement core logic in
          `light/__init__.py` to simulate `dynamic_control` for entities that declare
          `DYNAMIC_CONTROL_SIMULATED` but not native `DYNAMIC_CONTROL`.

        - **Output:** HA can now simulate "move/stop" commands for any dimmable light, enabling consistent behavior.

    - **PR 3.4: HA Core - ESPHome Integration Update (Orchestration & State Consumption)**

        - **Description:** Update `homeassistant/components/esphome/light.py` to:

            - Send `dynamic_control` parameters over Native API to compatible ESPHome devices (PR 2.1+).

            - Consume and map ESPHome's new `dynamic_state` attributes to the HA `LightEntity`.

            - Set `LightEntityFeature.DYNAMIC_CONTROL` for ESPHome lights detected with native support.

            - Conditionally set `LightEntityFeature.TRANSITION_SIMULATED` and
              `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` for ESPHome devices if native support is not
              detected.

        - **Output:** ESPHome devices are fully integrated with HA's new capabilities; HA accurately reflects ESPHome's
          dynamic state.

### Phase 4: Ecosystem Integration & User Experience

- **Goal:** Enhance the user-facing experience and encourage adoption across the Home Assistant ecosystem.

- **Timeline:** 4-6 weeks (ongoing).

    - **PR 4.1: HA Frontend - Basic Dynamic State UI Feedback**

        - **Description:** Implement simple visual indicators in standard light cards (e.g., text, icon changes) to show
          when a light's `dynamic_state` is active (`moving_up`, `transitioning`, etc.).

        - **Output:** Users get real-time visual feedback on light activity.

    - **PR 4.2: ESPHome - Convenient Local Button Bindings**

        - **Description:** Add simplified YAML syntax in ESPHome to easily bind `binary_sensor` events (e.g.,
          `on_press`, `on_release`) to trigger the internal light `move`/`stop` functions for ultra-responsive
          local dimming.

        - **Output:** Users can easily configure physical dimming buttons on ESPHome devices with optimal responsiveness.

    - **PR 4.3: Documentation & Developer Guidance**

        - **Description:** Comprehensive updates to ESPHome and Home Assistant documentation, including:

            - New YAML configurations and service calls.

            - Explanation of the control hierarchy and simulation.

            - Guidelines for other integration developers to adopt `_SIMULATED` features.

            - Best practices for automations using dynamic control.

        - **Output:** Clear resources for users and developers.

    - **PR 4.4: Community Blueprint & Integration Examples (Ongoing)**

        - **Description:** Collaborate with the community to create example automations and blueprints that leverage the
          new `dynamic_control` features.

        - **Output:** Easier adoption and wider use of the new functionality.

## 6. High-Level Timeline

- **Phase 1 (ESPHome Foundation):** ~1.5 months

- **Phase 2 (ESPHome Native Dynamic Control):** ~2 months

- **Phase 3 (Home Assistant Universal Handling):** ~2.5 months

- **Phase 4 (Ecosystem Integration & UX):** ~1.5 months (ongoing for documentation and community)

- **Total Estimated Project Duration:** ~7.5 - 8 months (allowing for review, iteration, and unforeseen complexities).

## 7. Team / Contributors

- **Core ESPHome Developers:** Lead C++ and Python development for ESPHome.

- **Core Home Assistant Developers:** Lead Python development for Home Assistant Core and Native API integration.

- **Frontend Developers:** UI/UX implementation in Home Assistant.

- **Technical Writers:** Documentation.

- **Community Testers:** Crucial for feedback and bug reporting across diverse hardware.

## 8. Risks & Mitigations

- **Complexity of State Management:**

    - _Mitigation:_ Incremental PRs, clear internal design documents, extensive unit and integration tests.

- **Performance Overhead of Simulation:**

    - _Mitigation:_ Optimize the `LightTransitionManager` for efficiency. Prioritize native control whenever available.
      Document best practices for large installations.

- **Network Congestion from Simulation:**

    - _Mitigation:_ Fine-tune update rates for simulated transitions. Encourage adoption of native `DYNAMIC_CONTROL` for
      high-frequency updates.

- **Backward Compatibility Issues:**

    - _Mitigation:_ Rigorous testing with existing configurations and device types. Utilize optional parameters and new
      feature flags rather than modifying existing required ones.

- **Coordination between ESPHome & Home Assistant:**

    - _Mitigation:_ Clear communication channels (GitHub discussions, dedicated issues), phased rollout, and cross-
      project collaboration on PRs.
