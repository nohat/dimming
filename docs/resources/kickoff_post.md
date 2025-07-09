# Kickoff: Revolutionizing Smart Lighting Control in Home Assistant

Hey Home Assistant Community!

We're incredibly excited to announce a major new initiative aimed at transforming how you interact with your smart lights
.
We're embarking on a project to bring **universal, seamless, and highly responsive dynamic control** to _all_ your lights within Home Assistant.

## The Problem We're Solving: Inconsistent Lighting Experiences

Many of us have experienced the frustration of inconsistent light behavior:

- You tell a light to transition over 5 seconds, but it just **snaps** to the new brightness.

- You try to set up a "hold-to-dim" feature for a physical button, and it becomes a **complex YAML puzzle** involving
  many incremental commands.

- These workarounds often **flood your network** with commands, leading to choppy performance or unreliability.

- It's hard to tell if your light is actually _doing_ something like fading, or if it just changed.

This inconsistency stems from how Home Assistant currently interacts with smart lighting devices.
While some advanced bulbs natively handle smooth transitions, many do not, and Home Assistant largely relies on the device itself to interpret these commands
.
The sophisticated "move" and "stop" commands found in industry standards like Zigbee's Level Control Cluster or Matter's equivalents often aren't exposed in a unified, user-friendly way.

## Our Vision: A Seamless & Intelligent Lighting Future

Imagine:

- **Every light responds natively** when you ask it to, whether it's a gradual sunrise or a quick fade.

- **"Hold-to-dim" just works** for any dimmable light, with instant responsiveness from your physical buttons or UI.

- **Your automations are simpler**, as Home Assistant intelligently handles the complex dimming and color change logic.

- **Your network is happier**, with fewer unnecessary commands being sent.

- **You get real-time feedback** on what your lights are actively doing, like "dimming up" or "transitioning to warm
  white."

This project will introduce a standardized approach to lighting control that leverages native device capabilities.
Devices with advanced features (like those running ESPHome with new firmware) will handle dynamic changes directly on-device for optimal performance and responsiveness.
For devices without native support, Home Assistant will provide a clean, consistent experience by gracefully handling unsupported features.

## Why This Matters: Context, Rationale, and Justification

This isn't just about adding new features; it's about fundamentally improving the core lighting experience:

1. **Elevated User Experience:** Smooth, natural light changes are crucial for ambiance, comfort, and a premium smart
   home feel. This project aims to deliver that universally.

2. **Simplified Automation & Control:** By building advanced dynamic control directly into the `light.turn_on` service
   and ESPHome, we significantly reduce the complexity of automations. No more convoluted `repeat` loops or custom
   scripts for basic dimming behavior!

3. **Improved Performance & Reliability:** Offloading high-frequency calculations and continuous dimming/color changes
   to the device (ESPHome) reduces network chatter and latency, making your lights more responsive and your network less congested.

4. **Alignment with Industry Standards:** By introducing concepts like `move`/`stop` actions and explicit dynamic state
   reporting, we're aligning Home Assistant's `light` domain more closely with robust lighting standards like Matter
   and Zigbee, future-proofing our capabilities.

5. **Backward Compatibility Guaranteed:** A core principle of this project is that all changes will be **fully backward-
   compatible**. Your existing automations and configurations will continue to work exactly as they do today. New
   features will be introduced as optional enhancements.

## The Proposed Solution: A Layered Approach

Our plan involves simultaneous, incremental enhancements in both ESPHome and Home Assistant:

- **ESPHome Firmware:** We'll enhance the ESPHome light component to perform continuous dimming and color adjustment on-
  device with custom curves and speeds. Crucially, ESPHome will report its real-time "dynamic state" back to Home
  Assistant (e.g., `moving_brightness_up`, `transitioning`).

- **Home Assistant Core:** We'll update the `light.turn_on` service to accept powerful new `dynamic_control` parameters.
  Home Assistant will intelligently determine if a light natively supports these commands (like our new ESPHome
  firmware). For devices without native support, Home Assistant will provide a clean, consistent experience by gracefully handling unsupported features.

- **Frontend & Automations:** With the `dynamic_state` exposed, the Home Assistant UI can provide better feedback, and
  automations can become smarter and simpler.

## Project Plan Overview (High-Level)

We've broken this ambitious project into manageable phases, with each Pull Request (PR) delivering a useful and tested
feature:

1. **ESPHome Foundation:** Internal C++ refinements for smoother transitions and defining dynamic control profiles in
   YAML.

2. **ESPHome Native Dynamic Control:** Implementing on-device continuous brightness/color changes and reporting dynamic
   state to Home Assistant.

3. **Home Assistant Universal Handling:** Core logic in Home Assistant to understand and manage native dynamic commands
   across all light integrations, ensuring consistent behavior and graceful degradation for unsupported features.

4. **Ecosystem Integration & UX:** Frontend updates, simplified local button bindings for ESPHome, and comprehensive
   documentation to empower users and developers.

## How You Can Contribute

This is a large undertaking, and community involvement is key to its success:

- **Feedback:** Share your thoughts on the proposed features and any use cases you have.

- **Testing:** As PRs roll out, we'll need enthusiastic testers to try the new features on diverse hardware and provide
  feedback.

- **Documentation:** Help us write clear and concise documentation for the new capabilities.

- **Development:** If you're a developer interested in contributing to Home Assistant or ESPHome, we welcome your
  expertise! Reach out on the developer channels.

## Estimated Timeline

We anticipate this project will unfold over approximately 7-8 months, with continuous releases of new features along the
way.

We believe this initiative will bring a significant leap forward in the quality and consistency of smart lighting control within Home Assistant
. We're excited to embark on this journey with all of you!

Stay tuned for updates as we kick off the development!
