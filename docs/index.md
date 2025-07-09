# Smooth Dimming

**Smooth Dimming** - Responsive, Intuitive Smart Lighting Control

Smooth Dimming is the user experience of direct control of lighting brightness with intuitive and responsive controls. When users hold a button to adjust brightness, they expect smooth, natural dimming behavior similar to physical dimmer switches. That means the light should provide immediate feedback when a dimming button is pressed, and the brightness should change smoothly over time, not in abrupt steps. The dimming adjustment should stop instantly when the button is released, and the light should maintain its state accurately.

While support for this modality of control exists in many smart lighting protocols and many devices have native capabilities for smooth dimming built in to their firmware, achieving a consistent and unified experience across different platforms and devices remains a challenge. Home Assistant's current smart lighting control implementations has no native, first-class support for smooth dimming, forcing users to rely on clunky workarounds and low-level device-specific solutions which are difficult to configure and provide a subpar experience.

## 🔍 The Problem: Gaps in Home Assistant's Smart Lighting Control API surface

- **Lack of native support** for smooth dimming in Home Assistant's core light services: the `light.turn_on` service supports:
    - `brightness` and `brightness_pct` parameters for setting a specific brightness level, but does not support continuous dimming operations such as increasing or decreasing brightness.
    - `brightness_step` and `brightness_step_pct` parameters for adjusting brightness in fixed increments from the current level.
    - `transition` parameter for applying a duration to brightness changes. Such commands are fire-and-forget, lacking  real-time feedback or ability to cancel or adjust the transition mid-way.

- **Workarounds with automations**: Users often create complex automations to simulate smooth dimming behavior, but these solutions typically provide an inferior experience, with noticeable input lag and choppy dimming. These solutions rely on spamming the `light.turn_on` service with small brightness increments, which can flood delicate wireless networks, causing unexpected fluctuations in brightness, degrading the user experience of direct control.

- **Limited protocol support**: Zigbee, Z-Wave, and Matter have native commands for smooth dimming, but Home Assistant has not integrated support for these capabilities into the core light services, requiring users who want to leverage them to implement low-level, platform-specific solutions. While not all devices support these features, many do, and there is significant untapped potential for users who adopt compatible hardware to have a unified dimming experience.

## 🧩 Observations

While the problems are clear, the building blocks for a solution already exist across the smart lighting ecosystem:

- **Native protocol capabilities** - Zigbee/Matter Level Control Move/Stop commands, Z-Wave Level Change, Tasmota `Dimmer < > !`
- **Home Assistant's service architecture** - Existing light services that could be extended with dynamic control
  parameters
- **Integration diversity** - Multiple pathways (ZHA, Zigbee2MQTT, Z-Wave JS, ESPHome) that each handle different device
  types optimally
- **Community workarounds** - Existing automation patterns that demonstrate user demand and partial solutions
- **Core infrastructure** - Home Assistant's event system and state management that can coordinate multi-device
  operations
- **UI frameworks** - Frontend components that already support hold-to-dim gestures but lack backend coordination

The challenge is **orchestrating these existing capabilities** into a unified, intelligent system that automatically chooses the best approach for each device and situation.

## 💡 The Vision

A unified lighting control system that provides:

- **Natural dimming behavior** - smooth brightness changes that feel like physical dimmer switches
- **Protocol-aware optimization** - leverages native device capabilities (Zigbee Move/Stop, Z-Wave Level Change)
- **Consistent experience** across all smart lighting integrations
- **Minimal latency** and optimized network usage

## 🛠️ Proposed Solution

- **New optional parameters in the `light.turn_on` service**
    - `action`: `move_brightness`, `move_color_temp`,  `move_color`, `move_hue`, `move_saturation`, `stop`
    - `direction`: `up`, `down`
    - `speed`: an integer value representing the speed of the movement in units per second, e.g. 255 to adjust entire brightness range in 1 second, 85 to adjust in 3 seconds, etc.
    - `speed_pct`: a float value representing the speed of the movement in percentage per second, e.g. 200.0 for 200% per second, 25.0 for 25% per second, meaning the full brightness range will be adjusted in 0.5 seconds or 4 seconds respectively.
- **New light attributes**
    - `current_action`: the current action being performed (e.g. `move_brightness`, `move_color_temp`, etc.)

<!-- AUTO_TOC -->
