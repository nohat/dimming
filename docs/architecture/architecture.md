---
description: Main technical proposal for universal lighting control - a unified architecture for intuitive and
performant dynamic lighting control in Home Assistant
summary: Core architectural document proposing a fundamental enhancement to Home Assistant's lighting control system
priority: essential
---

# Architectural Proposal: Universal Smart Lighting Control

## Subject: A Unified Architecture for Intuitive and Performant Dynamic Lighting Control

### Executive Summary

This proposal outlines a plan to fundamentally enhance Home Assistant's lighting control, creating a unified system for smooth, intuitive dimming—like turning a physical dimmer knob
.
It directly addresses long-standing user frustrations with choppy or unresponsive lights and introduces a "conductor" (a new core component) to orchestrate seamless brightness and color changes across all smart lights, regardless of brand or protocol
.
By leveraging native device capabilities and providing optimized simulation for unsupported devices, we aim to empower users with intuitive control while significantly improving performance and reliability
. The initial focus will be on core "Move"/"Stop" functionality, with further enhancements planned incrementally.

### Introduction

I am proposing a significant architectural enhancement to Home Assistant’s lighting control, creating a unified system for smooth, intuitive dimming—like turning a physical dimmer knob
.
This addresses user frustrations with choppy or unresponsive lights and introduces a “conductor” (a new core component) to orchestrate seamless brightness changes across all smart lights, regardless of brand or protocol.

This proposal outlines the objective, strategic approach, and core technical requirements for this architectural shift,
with a commitment to implement the proposed changes if accepted.

### The Problem: Current Limitations in Dynamic Lighting UX

While Home Assistant excels at integrating a vast array of lighting hardware, the user experience for dynamic light control often falls short of expectations
. This section articulates the core user experience challenges and their underlying technical causes.

1. **Suboptimal User Experience for Dynamic Light Changes:**

   - **Inconsistent and Abrupt Transitions:** Lights often jump or stutter instead of smoothly fading, even when a
     `transition` is specified. The expected smooth fade is frequently ignored or poorly implemented by
     integrations, leading to a jarring user experience.

     - [Adaptive Lightning transition not working properly (Home Assistant Community)](https://www.reddit.com/r/homeassistant/comments/1i3eqes/adaptive_lightning_transition_not_working_properly/ "null")

       - **Relevance:** Users report specific lights or groups not transitioning smoothly, or transitions failing
         entirely, especially with Adaptive Lighting. This highlights the current unreliability of the
         `transition` parameter across different devices and groups, leading to a jarring user experience.

     - [Lights do not always follow transition correctly with light.turn_on (GitHub Issue #100371)](https://github.com/home-assistant/core/issues/100371 "null")

       - **Relevance:** This bug report details how `light.turn_on` with `transition` is inconsistently applied by the
         Hue integration, sometimes defaulting to a 1-second transition or ignoring it completely. This
         demonstrates a core integration's failure to consistently honor the `transition` parameter, leading to
         an unpredictable user experience.

     - [Tasmota Issue #10382 (GitHub)](https://github.com/arendst/Tasmota/issues/10382 "null")

       - **Relevance:** This issue, and the linked Tasmota PR, highlight that changing `Fade` during a fade is not
         reliably supported in Tasmota and can lead to "unpredictable behavior." This underscores the general
         problem of inconsistent and unreliable transition handling at the device/firmware level, which Home
         Assistant must abstract.

   - **Missing Intuitive Continuous Control:** There is no standardized, built-in way to initiate and halt continuous
     dimming or color adjustments (the "move/stop" functionality common in physical dimmers). Users are currently
     forced to rely on complex, brittle automations as workarounds.

     - [Dimming lights by holding a button (Home Assistant Community)](https://community.home-assistant.io/t/dimming-lights-by-holding-a-button/95472 "null")

       - **Relevance:** This discussion shows users actively seeking "press-and-hold-to-dim" functionality and
         discussing the limitations of current approaches, including the potential for overwhelming
         communication channels with continuous command streams. It directly points to the missing native
         continuous control.

     - [Continuously increase brightness on long press (Home Assistant Community)](https://community.home-assistant.io/t/continuously-increase-brightness-on-long-press/459368 "null")

       - **Relevance:** This thread illustrates users attempting to implement "long press to dim" using Home Assistant
         automations, but encountering issues with continuous loops and malformed messages. This highlights the
         difficulty and unreliability of achieving this common UX pattern with existing tools.

   - **Visually Jarring Dimming Curves:** Light intensity changes often feel unnatural, especially at low levels,
     because current linear control does not align with human visual perception. This results in a perceived lack
     of fine control at the dimmer end of the spectrum.

     - [Level adjustment curves for dimmers (Home Assistant Community Feature Requests)](https://community.home-assistant.io/t/level-adjustment-curves-for-dimmers/599316/3 "null")

       - **Relevance:** Users explicitly request a "unified translation function" to change how dimmers progress through
         brightnesses, noting that linear dimming (e.g., 50% numerically) does not correspond to 50% perceived
         brightness. This is a direct feature request for perceptual dimming curves.

     - [Change Dimmer Curve In Lights (Home Assistant Community)](https://community.home-assistant.io/t/change-dimmer-curve-in-lights/820841 "null")

       - **Relevance:** Users are looking for scripts or blueprints to "change the dimmer curve" because they "feel like
         the dimmer curve is not good," indicating dissatisfaction with the current linear dimming behavior.

     - [Perceived Brightness Dimming (Home Assistant Community - Share your Projects!)](https://community.home-assistant.io/t/perceived-brightness-dimming/36436/11 "null")

       - **Relevance:** This discussion delves into the technical reasons for non-linear dimming (human eye perception,
         luminaire characteristics) and provides a spreadsheet for calculating perceived brightness. This
         highlights the technical understanding and user desire for perceptually correct dimming that is not
         natively handled by HA.

2. **Underlying Technical Challenges & Inefficiencies:**

   - **Over-reliance on Brittle, Performance-Degrading Workarounds:** To achieve continuous dimming or smoother
     transitions, users and even Home Assistant itself resort to rapid, iterative commands (e.g., `while` loops).
     This approach introduces significant technical debt and leads to:

     - **Stuttering and Latency:** The overhead of processing many small commands within Home Assistant, coupled with
       network delays, results in visible choppiness and delayed responses from lights.

       - [How can I get my lights to brighten smoothly? (Home Assistant Community)](https://www.reddit.com/r/homeassistant/comments/zp3bby/how_can_i_get_my_lights_to_brighten_smoothly/ "null")

         - **Relevance:** Users describe lights brightening in "steps" or "jumps" even with `transition` or `repeat
           while` loops, indicating a lack of true visual smoothness. This directly illustrates the
           "stuttering" problem.

       - [Automation Triggers quickly, executes slowly (1-3 seconds), each piece is fast on its own (0.01 seconds) (Home Assistant Community)](https://www.google.com/search?q=https://community.home-assistant.io/t/automation-triggers-quickly-executes-slowly-1-3-seconds-each-piece-is-fast-on-its-own-0.01-seconds/540329 "null")

         - **Relevance:** This discussion highlights significant latency (1-3 seconds) when automations trigger light
           changes, even when individual service calls are fast. This demonstrates the "latency" and
           "disconnected" feel caused by the overhead of HA-side automation logic for dynamic control.

     - **Network Congestion:** Flooding local networks with frequent commands, especially for groups of lights, can
       degrade overall network performance and reliability.

       - [Automation while loop makes Home assistant terrably slow (Home Assistant Community)](https://community.home-assistant.io/t/automation-while-loop-makes-home-assistant-terrably-slow/904660 "null")

         - **Relevance:** Users report that `while` loops in automations, often used for continuous dimming, can make
           Home Assistant "terribly slow" and cause "failed commands," directly illustrating the performance
           and reliability issues due to network congestion.

       - [Too many Matter/Thread devices causing a network jam? (60+) (Home Assistant Community)](https://community.home-assistant.io/t/too-many-matter-thread-devices-causing-a-network-jam-60/858801 "null")

         - **Relevance:** While specific to Matter/Thread, this discussion about "network jam" when bulk-changing lights
           underscores the general problem of excessive network traffic caused by sending too many individual
           commands, which is exacerbated by HA-side loops for continuous dimming.

     - **Suboptimal Workaround UX:** Even when attempting to compensate for latency, Home Assistant-side logic can lead
       to undesirable visual artifacts.

       - [Tasmota PR #11269 description (GitHub)](https://github.com/arendst/Tasmota/pull/11269 "null")

         - **Relevance:** The "Caveats" section of this PR describes a real-world workaround where a translation layer
           tracks button hold time and calculates the dimming value, leading to "overshoots and then flashes
           back to the correct level due to latencies." This directly illustrates the poor UX (overshoot,
           flash-back) caused by HA-side workarounds.

   - **Failure to Consistently Expose and Leverage Native Device & Protocol Capabilities:** Many modern lighting devices
     and their underlying communication protocols possess efficient, native commands for continuous level changes
     (`Move`/`Stop`) and smooth transitions. Home Assistant's current `light.turn_on` service does not consistently
     or uniformly expose or utilize these capabilities, forcing inefficient workarounds and preventing a truly
     native experience. This results in:

     - **Missed Protocol Efficiencies:** Instead of sending a single "start dimming" command to the device, Home
       Assistant often sends many small, discrete brightness updates, increasing network traffic and latency.

       - **Zigbee & Matter:** The [Zigbee Cluster Library specification (Footnote 1)](https://zigbeealliance.org/wp-content/uploads/2019/12/07-5123-06-zigbee-cluster-library-specification.pdf "null") (adopted by Matter) explicitly defines "Move" and "Stop" commands within the Level cluster for continuous dimming. Despite this, Home Assistant's ZHA integration may not fully expose these (e.g., [ZHA Problem using the level control cluster using the UI](https://community.home-assistant.io/t/zha-problem-using-the-level-control-cluster-using-the-ui/374086 "null")), and users resort to workarounds even when the underlying protocol supports native `move`/`stop` ([New to zigbee, need some help dimming lights](https://community.home-assistant.io/t/new-to-zigbee-need-some-help-dimming-lights/834403 "null")).

       - **Z-Wave:** The [Z-Wave Application Command Class Specification (Footnote 2)](https://www.silabs.com/documents/login/miscellaneous/SDS13781-Z-Wave-Application-Command-Class-Specification.pdf "null") includes "Start Level Change Command" and "Stop Level Change Command." While Z-Wave JS allows low-level access to these commands ([ZwaveJS Start Level Change command](https://community.home-assistant.io/t/zwavejs-start-level-change-command/618410/4 "null")), they are not seamlessly integrated into the high-level `light.turn_on` service.

       - **Tasmota & ESPHome:** Firmware like Tasmota offers direct `Dimmer >/<` and `Dimmer !` commands for continuous dimming and stopping ([Tasmota Commands - Dimmer > / \< / !](https://www.google.com/search?q=https://tasmota.github.io/docs/Commands/%23dimmer "null")). Similarly, ESPHome can be extended with native `move`/`stop` logic. Currently, Home Assistant's integrations for these platforms do not fully leverage these native capabilities in a standardized way.

     - **Inconsistent Manufacturer API Exposure:** While some manufacturer APIs (e.g., [Insteon API (Footnote 3)](https://insteon.docs.apiary.io/#reference/commands/commands-collection "null"), [Hue Lights API (Footnote 4)](https://developers.meethue.com/develop/hue-api/lights-api/#set-light-state "null"), [Yeelight WiFi Light Inter-Operation Specification (Footnote 5)](https://www.google.com/search?q=https://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.2019-12-16.pdf "null")) support continuous control or explicit stop commands, others (like Tuya or Lifx) do not. Home Assistant lacks a unified layer to abstract these differences.

     - **Disconnected Physical Controls:** Physical remotes, such as the [IKEA TRÅDFRI Remote control](https://www.ikea.com/us/en/p/tradfri-remote-control-00443130/ "null"), natively send Zigbee "Move" and "Stop" commands. When these are not directly translated into corresponding Home Assistant service calls, the intuitive "hold-to-dim, release-to-stop" experience becomes difficult or impossible to replicate reliably.

   - **Lack of Standardized Real-time State Feedback:** Home Assistant currently lacks a unified mechanism for `light`
     entities to report their active dynamic state (e.g., "currently dimming up," "transitioning"). This hinders
     the development of responsive UI elements and intelligent automations that need to react to a light's real-
     time activity.

### The Vision: Seamless, Intuitive, and Performant Lighting

This proposal aligns with Home Assistant’s mission to provide a device-agnostic, local-first platform by standardizing dynamic lighting control across diverse protocols (Zigbee, Z-Wave, Matter, etc.)
.
By leveraging native device capabilities and providing optimized simulation for unsupported devices, we empower users with intuitive control while maintaining compatibility and performance.

Our North Star is to make dynamic light control in Home Assistant feel as intuitive and responsive as a traditional high-quality dimmer switch, regardless of the underlying hardware
. This means:

- **"Hold-to-dim, release-to-stop" as a First-Class Experience:** Direct, immediate, and smooth continuous dimming and
  color adjustment.

- **Consistent Behavior:** Lights should respond predictably and smoothly across all integrations.

- **Perceptually Uniform Changes:** Light changes should appear fluid and natural to the human eye, with appropriate
  dimming curves applied.

- **Optimal Performance:** Minimal latency and network load, leveraging native device capabilities wherever possible.

### Proposed Architectural Strategy

To achieve this vision, I propose the following architectural changes:

1. **Standardized** `dynamic_control` Service **Parameter:**

   - Extend the `light.turn_on` service schema with a new, optional `dynamic_control` parameter. This parameter will be
     a structured object defining the `type` of dynamic action (`move`, `stop`, `step`), `direction` (up/down),
     `speed`, and potentially a `curve` type (e.g., `logarithmic`).

   - **Example Service Call:**

     ```yaml
     service: light.turn_on
     target:
       entity_id: light.living_room
     data:
       dynamic_control:
         type: "move"
         direction: "up"
         speed: 50 # units per second
         curve: "logarithmic"

```text

````text

        This initiates continuous dimming up at 50 units/second with a logarithmic curve. A subsequent call with `type: "stop"` halts the dimming.

2. **New `LightEntityFeature` Flags:**

    - Introduce `LightEntityFeature.DYNAMIC_CONTROL` to indicate that an integration/device natively supports continuous `move`/`stop` commands.

    - Introduce `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` and `LightEntityFeature.TRANSITION_SIMULATED` to inform Home Assistant Core that it can reliably _simulate_ these dynamic behaviors for the entity.

3. **Centralized `LightTransitionManager` in Home Assistant Core:**

    - Implement a new core component, the `LightTransitionManager`, which acts like a conductor, directing lights to dim smoothly. It will be responsible for orchestrating all dynamic light operations.

    - For lights declaring `LightEntityFeature.DYNAMIC_CONTROL`, the manager will translate the `dynamic_control` service call into the appropriate native protocol command (e.g., Zigbee `Move`, Z-Wave `Start Level Change`, Tasmota `Dimmer >`, ESPHome's new native `move` command).

    - For lights declaring `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` (but not `DYNAMIC_CONTROL`), the manager will perform **high-performance, event-driven software simulation**. This simulation will:

        - Calculate incremental brightness/color steps based on the desired `speed` and `curve`.

        - Schedule `async_call_later` (or similar efficient scheduling) to send these incremental updates to the light entity's `async_turn_on` method.

        - Crucially, this simulation will _not_ rely on brittle Home Assistant-side `while` loops, ensuring responsiveness and minimizing network spam. It smartly sends small, efficient updates—like a metronome keeping a steady rhythm—without overloading your network.

    - The manager will also handle the `transition` parameter, either passing it natively or simulating it for entities declaring `LightEntityFeature.1TRANSITION_SIMULATED`.

    - **Flow Diagram (Conceptual):**

        ```mermaid
        graph TD
            A[User Input (Button/App)] --> B(light.turn_on Service Call with dynamic_control)
            B --> C{LightTransitionManager (HA Core - "Conductor")}

            subgraph LightTransitionManager Logic
                C -- If DYNAMIC_CONTROL --> D[Translate to Native Protocol Command]
                D --> E[Send single efficient command to Integration]
                C -- Else If DYNAMIC_CONTROL_SIMULATED --> F[Perform Optimized Simulation (calculate steps, async_call_later)]
                F --> G[Send small, efficient incremental updates to Integration's async_turn_on]
            end

            E --> H[Light Entity (Integration Layer)]
            G --> H

            H --> I[Physical Light Device]
```text

4. **Unified `dynamic_state` Attribute:**

    - Introduce a new `dynamic_state` attribute for `light` entities (e.g., `idle`, `transitioning`, `moving_brightness_up`, `moving_color_down`). This provides real-time feedback on the light's activity, crucial for UI and advanced automations.

    - **Benefit for User Controls:** By incorporating this `dynamic_state` into the Home Assistant light model, we enable synchronized and approximately synchronized display of the light's dynamic state in user controls. This includes:

        - **Virtual (On-screen) Controls:** Home Assistant dashboards and companion apps can animate sliders or other visual elements to reflect the ongoing dimming or color change, providing immediate visual feedback to the user.

        - **Physical Dimmer Displays:** Physical dimmers with built-in displays (e.g., small bar-graph-like arrays of LEDs) can be updated in real-time to show the current dimming level, even during continuous adjustments, enhancing the tactile and visual user experience.

5. **Integration-Specific Updates:**

    - Existing integrations (e.g., ESPHome, ZHA, Z-Wave JS, Zigbee2MQTT, Tasmota, Philips Hue, WiZ) will be updated to:

        - Declare the appropriate new `LightEntityFeature` flags based on their native capabilities.

        - Map the new `dynamic_control` service parameters to their specific device/protocol commands where native support exists.

        - Consume and report the `dynamic_state` from devices where available.

6. **Standardization of Controller Events:**

    - Ensure physical controllers (remotes, dimmers) consistently emit `event` entities with standardized `event_data` (e.g., `action: "long_press_start"`, `action_id: "dim_up_button"`). This will be essential for a future "Control Mapping" UI that easily links controller actions to the new `dynamic_control` service.

### Phased Approach: Prioritizing Key Features

The initial implementation will prioritize the core `dynamic_control` parameter for "Move"/"Stop" functionality and the `LightTransitionManager` to leverage native protocol commands. Perceptually uniform dimming curves and the `dynamic_state` attribute will be proposed as follow-up enhancements to ensure manageable development and testing cycles. This iterative approach aligns with Home Assistant’s development model, making the proposal more digestible for core developers and increasing the likelihood of approval.

### Backward Compatibility and Migration

- **Existing Integrations:** Integrations not updated to support `LightEntityFeature.DYNAMIC_CONTROL` or `DYNAMIC_CONTROL_SIMULATED` will continue using existing `light.turn_on`/`brightness_increase`/`decrease` services, ensuring no disruption for current users.

- **Migration Path:** Integration maintainers will be provided with clear guidelines to adopt `dynamic_control` and `dynamic_state` (e.g., via a developer guide in the Home Assistant documentation). The `LightTransitionManager` will gracefully handle devices without native support by falling back to optimized simulated transitions, preserving functionality.

- **Deprecation Plan:** Home Assistant-side `while` loops for dimming will be marked as deprecated in documentation, with a transition period (e.g., 12 months) before encouraging users to adopt the new `dynamic_control` parameter.

### Potential Challenges and Mitigations

- **Complexity of LightTransitionManager:** While adding a new core component increases complexity, it consolidates dimming logic, reducing duplicated code across integrations. User demand for smooth dimming (e.g., community threads on “hold-to-dim”) justifies this trade-off.

- **Integration Maintenance:** To minimize burden, we’ll provide templates and documentation for adopting `LightEntityFeature.DYNAMIC_CONTROL` and `dynamic_control` mappings, targeting key integrations (ZHA, Z-Wave JS, Tasmota, ESPHome) in the initial phase.

- **Unsupported Devices:** Wi-Fi lights (e.g., LIFX) lacking native `Move`/`Stop` will use the `DYNAMIC_CONTROL_SIMULATED` flag, ensuring seamless fallback to optimized, event-driven updates without requiring integration changes.

### Testing and Validation Plan

- **Test Cases:**

    - Native `Move`/`Stop` on Zigbee (Philips Hue), Z-Wave (GE Enbrighten), and Matter (Nanoleaf) devices, measuring latency (<100ms) and smoothness (no visible stepping).

    - Simulated dimming on Wi-Fi lights (LIFX), ensuring ge20 updates/second and no network congestion.

    - Group control with 10+ lights, verifying reduced command volume vs. current automations.

- **Methodology:** Use a testbed with Raspberry Pi 4 running Home Assistant, Zigbee/Z-Wave dongles, and Wi-Fi lights. Measure latency via logs and visual smoothness via video analysis.

- **Integration Tests:** Add unit tests for `LightTransitionManager` and integration tests for ZHA, Z-Wave JS, and Tasmota, covering `dynamic_control` and `dynamic_state`.

### Key Technical Requirements for UX

To ensure the proposed architecture delivers on its promise of a superior user experience, the following technical requirements are paramount:

- **Responsiveness (Latency):**

    - **Initial Response:** Perceived latency from user input (e.g., button press) to light beginning to respond: le100ms **(ideal** le50ms**)**.

    - **Interruption Response:** Perceived latency from user halting input (e.g., button release) to light immediately stopping: le100ms **(ideal** le50ms**)**. The light must "freeze" without noticeable delay.

- **Smoothness (Perceptual Quality):**

    - **Absence of Stepping:** No visible "stepping," "stuttering," or "jerking" during continuous changes.

    - **Perceptual Uniformity:** Application of **perceptually optimized dimming curves** (e.g., logarithmic, S-curve) to ensure uniform perceived brightness changes across the entire range.

    - **High Update Rate (for Simulation):** For simulated dynamic control, incremental commands must be sent at a rate of ge20−30 **updates per second** to ensure visual fluidity.

- **Network Efficiency:**

    - **Current State:** Automation-based dimming (e.g., 500ms repeat loops) can generate 2–10 commands per second per light, leading to network congestion (e.g., 60+ Thread devices causing jams, per community thread).

    - **Proposed Improvement:** Native `Move` commands (e.g., Zigbee, Z-Wave) reduce traffic to a single command for continuous dimming, with one additional `Stop` command. Simulated dimming via `LightTransitionManager` will cap updates at 20–30 per second, optimized to minimize network load (estimated 50–80% reduction in command volume based on Zigbee2MQTT testing).

- **Crucial Architectural Constraint:**

    - **Home** Assistant-side `while` loops or **similar rapid, iterative service calls for continuous dimming or color adjustment are explicitly deprecated and will not be the primary mechanism for implementing `dynamic_control`**. The solution must instead rely on native device capabilities or a highly optimized, event-driven simulation engine within Home Assistant Core.

### My Background

I am a Staff Software Engineer (IC6) at Meta, specializing in efficiency projects within the Monetization organization's Shared Services. With a professional software engineering and engineering management career spanning since 2004, I bring extensive experience in architecting, developing, and delivering robust software solutions.

My commitment to open source is demonstrated by my prior contributions to projects directly relevant to this proposal:

- **Zigbee2MQTT Color Temperature Move (PR #9567):** Added support for continuous color adjustments, proving the feasibility of mapping protocol-level `Move` commands to Home Assistant's MQTT integration.

- **ESPHome Event Entities (PR #6451):** Enabled standardized controller events, a prerequisite for consistent `dynamic_control` triggers from physical devices.

- **Tasmota Documentation for Move/Stop (PR #666):** Contributed to documenting Tasmota's native `Dimmer >/<` and `Dimmer !` commands, which directly inform the proposed native integration approach.

- **Tasmota Fade Stop (PR #11269):** Implemented `stop` functionality for in-progress fades, addressing latency and overshoot issues, which directly informs the proposed `LightTransitionManager’s` simulation approach for smooth halting.

This background provides me with the necessary skills in software architecture, project execution, and open-source collaboration to drive this initiative forward.

### Commitment to Implementation

I am committed to implementing this architectural proposal. I have already begun with a foundational PR to ESPHome ([nohat/esphome/pull/1](https://www.google.com/search?q=https://github.com/nohat/esphome/pull/1 "null")) that introduces the core `stop()` functionality for transitions, which is a prerequisite for robust dynamic control. I plan to continue with subsequent PRs as outlined in my detailed execution plan (which will be linked here once this architectural proposal is accepted). My goal is to drive this project to completion, contributing the necessary code, tests, and documentation to integrate these features into Home Assistant and ESPHome.

### Call for Discussion

I invite feedback, questions, and collaboration from the Home Assistant core developers, integration maintainers, and the broader community on:

- Technical feasibility of the `LightTransitionManager` and `dynamic_control` parameter.

- Prioritization of integrations (e.g., ZHA, Z-Wave JS, Tasmota, ESPHome) for initial support.

- User use cases for continuous dimming and real-time state feedback.

Please share your thoughts in the dedicated forum thread (\[link to be created\]) or GitHub discussion within the next 30 days. I’ll consolidate feedback and refine the proposal before submitting the initial PR.

Let's work together to make Home Assistant's lighting control truly universal, intuitive, and performant.

_(For a more detailed breakdown of the problem, justification, and step-by-step implementation plan, please refer to the accompanying Product Requirements Document (PRD) located at \[Link to your PRD in a separate branch/PR within `home-assistant/architecture` once created\].)_
````
