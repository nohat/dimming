---
description: Comprehensive comparison of native dimming capabilities across all lighting integrations including
transition support and dynamic control features
summary: Device and protocol capability matrix for universal lighting control implementation
priority: important
---

# Capability Matrix

Here's a capability matrix outlining the relevant declarations and concrete examples for different combinations of light features, focusing on `transition` and dynamic control (`move`/`stop`)
.
This assumes the proposed new `LightEntityFeature` flags and the `LightTransitionManager` in Home Assistant Core are in place.

## Relevant Feature Flags

______________________________________________________________________

### Capability Matrix Scenarios and Examples

The `supported_features` attribute of a `light` entity is a bitmask.

| Scenario                                                                              | `supported_features` Bitmask & Key Flags                                                    | Description                                                                                                                                                                                         | `light.turn_on(brightness_pct=50, transition=5)`       | `light.turn_on(dynamic_control={type: 'move', direction: 'up'})` | `dynamic_state` (reported to HA)                               | `current_brightness_actual` (device-side)                                 |
| :------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------- | :--------------------------------------------------------------- | :------------------------------------------------------------- | :------------------------------------------------------------------------ |
| **1. Basic ON/OFF (Legacy)**                                                          | `0` (or `LightEntityFeature.ON_OFF`)                                                        | Device is a simple switch or light that only supports immediate on/off. No dimming, no transitions, no dynamic control. Unsupported features are ignored.                                           | Ignored, light snaps ON.                               | Ignored.                                                         | `idle`                                                         | Updates immediately to target                                             |
| **2. Basic Dimming (Legacy)**                                                         | `LightEntityFeature.BRIGHTNESS`                                                             | Device supports dimming but no native transitions or dynamic control. Unsupported features are ignored. (e.g., old Tasmota, some basic MQTT dimmers).                                                  | Ignored, light snaps to 50%.                           | Ignored.                                                         | `idle`                                                         | Updates immediately to target                                             |
| **3. Native Transition Support**                                                      | `BRIGHTNESS \| TRANSITION` (`1 \| 32 = 33`)                                                 | Device natively handles `transition` parameter. Common for modern smart bulbs (Hue, some Zigbee/Matter lights). Integration passes `transition` to device.                                          | Smooth 5s fade on device.                              | Ignored.                                                         | `transitioning` (reported by device)                           | Smoothly interpolates over 5s                                             |
| **4. Native Dynamic Control Support (ESPHome w/ New Firmware)**                       | `BRIGHTNESS \| TRANSITION \| DYNAMIC_CONTROL` (`1 \| 32 \| 64 = 97`)                        | Device (e.g., ESPHome with full proposed firmware) natively handles transitions AND `dynamic_control` commands. Provides best responsiveness and offloads work from HA.                             | Smooth 5s fade on device.                              | Device starts continuous dimming up.                             | `transitioning` or `moving_brightness_up` (reported by device) | Smoothly interpolates (transition) or continuously updates (move)         |
| **9. Device Reports `DYNAMIC_CONTROL`, but no `TRANSITION` (Hypothetical/Edge Case)** | `BRIGHTNESS \| DYNAMIC_CONTROL` (`1 \| 64 = 65`)                                            | Device supports `move`/`stop` natively, but not `transition`. (Less common, as `transition` is often a prerequisite for complex dimming).                                                           | Ignored, light snaps to 50%.                           | Device starts continuous dimming up.                             | `moving_brightness_up`                                         | Continuously updates (move)                                               |

______________________________________________________________________

### How Home Assistant's `light.turn_on` Service Handler Would Orchestrate

When `light.turn_on` is called in Home Assistant with a `transition` or `dynamic_control` parameter, the core logic
would follow this hierarchy:

1. **Check for Native `DYNAMIC_CONTROL`:**
   - If `LightEntityFeature.DYNAMIC_CONTROL` is set for the entity, HA passes the entire `dynamic_control` dictionary
     (and other parameters) directly to the underlying integration/device. The device is expected to handle it
     natively and report `dynamic_state`.
2. **Check for Native `TRANSITION`:**
   - If a `transition` parameter is present and `LightEntityFeature.TRANSITION` is set, HA passes `transition` to the
     integration/device. The device is expected to handle the fade natively.
   - If `transition` is present but `LightEntityFeature.TRANSITION` is not set, the `transition` parameter is ignored.
3. **No Advanced Feature (Fallback):**
   - If none of the above feature flags are set for the requested `transition` or `dynamic_control` parameters, those
     parameters are simply ignored, and the light's state changes instantly (as it does today).

This layered approach ensures that Home Assistant provides the best possible user experience based on the capabilities
declared by each device's integration, while always prioritizing native, on-device execution for optimal performance.
