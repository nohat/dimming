# Native Nonlinear Dimming Support

This document outlines the strategy for handling nonlinear dimming profiles in Home Assistant, focusing on native device capabilities and standard protocols.

## Native Support Overview

Nonlinear dimming is supported through the following mechanisms:

1. **Device-Specific Configuration**: Some advanced devices expose configuration parameters for adjusting their internal dimming curves.
2. **Standard Protocol Support**: Some lighting protocols include native support for nonlinear dimming profiles.

## Implementation Strategy

### 1. Device-Specific Configuration

Some Z-Wave and Zigbee devices allow configuration of their internal dimming curves through device parameters:

- **Z-Wave**: Some devices expose configuration parameters for adjusting dimming curves
- **Zigbee**: Certain devices may expose similar parameters through manufacturer-specific clusters

These configurations are set once and affect all dimming operations on the device.

### 2. Protocol-Level Support

Standard protocols may include native support for nonlinear dimming:

- **DALI**: Includes standardized logarithmic dimming curves
- **Matter**: May include standardized dimming profiles in future versions

When available, these native implementations provide the most reliable and performant solution.

## Implementation Guidelines

### 1. Device Configuration

For devices that support configurable dimming curves:

1. **Parameter Exposure**: The Z-Wave JS and ZHA integrations should expose relevant configuration parameters through the Home Assistant UI.
2. **Documentation**: Each integration should document which devices support configurable dimming curves and how to access these settings.
3. **Default Behavior**: Devices should use their default dimming curve if no specific configuration is provided.

### 2. Service Call Behavior

When handling service calls:

- The `dynamic_control` service will only be available for devices that natively support it.
- If a device does not support a requested feature (like a specific curve type), the service call will be ignored.
- No simulation or fallback behavior will be implemented in the core or integrations.

### 3. State Reporting for Nonlinear Dimming

The `dynamic_state` attribute (as introduced in **ESPHome PR 2.4** and consumed by **HA Core PR 3.4**) will be crucial
here.

- When Home Assistant is simulating a nonlinear dimming profile for a ZHA or Z-Wave JS light, the `dynamic_state` of
  that light entity in Home Assistant would be set to something like `simulated_moving_brightness_up_curved` or
  `simulated_transitioning_curved`. This provides clear feedback to the user and allows automations to react
  specifically to curved dimming events.

### Summary for ZHA and Z-Wave JS

For nonlinear dimming profiles (`curve` parameter in `dynamic_control`):

## Native Protocol Support

### Zigbee (ZHA)

Zigbee's Level Control cluster supports the following commands for native dimming control:

- `Move to Level (with On/Off)`
- `Move (with On/Off)`
- `Step (with On/Off)`
- `Stop`

### Z-Wave

Z-Wave's Multilevel Switch command class provides similar functionality:

- `Start Level Change`
- `Stop Level Change`
- `Set`

### DALI

DALI includes standardized logarithmic dimming curves defined in IEC 62386-102.

## Future Considerations

As lighting protocols evolve, we expect to see:

1. Broader native support for standardized dimming curves
2. More devices with configurable dimming profiles
3. Enhanced protocol support for dynamic dimming control

## Standard Curve Definitions

When implementing native support for dimming curves, the following standard curves should be considered:

### DALI Logarithmic Curve

DALI (IEC 62386-102) specifies a standardized logarithmic dimming curve that matches human perception of brightness. This curve is defined by the formula:

```text
Y = (e^(X * ln(256)) - 1) / 255
```

Where:

- X is the input level (0.0 to 1.0)
- Y is the output level (0.0 to 1.0)
- e is the base of natural logarithms
- ln is the natural logarithm

### Other Standard Curves

Other common dimming curves that may be supported by devices include:

1. **Linear**: Direct 1:1 mapping of input to output
2. **S-Curve**: Smooth acceleration and deceleration
3. **Square Law**: Matches the non-linear response of human vision

## Implementation Notes

When implementing support for dimming curves:

1. **Documentation**: Clearly document which curves are supported by each device/integration
2. **Fallback Behavior**: If a requested curve is not supported, the service call should be ignored
3. **Performance**: Native implementations should be optimized for smooth performance with minimal network traffic

The integration of professional lighting control standards, particularly regarding nonlinear dimming curves, is a fantastic idea to elevate the user experience
.
You're right that the human eye perceives light logarithmically, not linearly, which is why a simple linear dimming curve often feels "off" – with too much change at the high end and too little control at the low end.

Here's how we can leverage these standards and practices in our work:

### Key Standards and Concepts to Leverage

1. **Human Visual Perception (Weber-Fechner Law / Stevens' Power Law):** The fundamental principle is that our
   perception of brightness is non-linear. A linear change in light output (e.g., from 0% to 100% measured lumens)
   does not equate to a linear change in _perceived_ brightness. Small changes at low light levels are much more
   noticeable than large changes at high light levels.

2. **Logarithmic Dimming Curves:**

   - **Rationale:** These curves are designed to compensate for human visual perception, making dimming appear smooth
     and even across the entire range. A `logarithmic` curve ensures that perceived brightness changes linearly
     with the control input. This provides finer control at low light levels where the eye is more sensitive.
   - **Industry Adoption:** Logarithmic dimming is a standard in professional and theatrical lighting control (e.g.,
     DMX, DALI) and is often the default.

3. **DALI (Digital Addressable Lighting Interface) - IEC 62386 Standard:**

   - This is a highly relevant standard as it explicitly defines a **standard logarithmic dimming curve** (and also a
     linear one). DALI devices typically default to this logarithmic curve. It specifies 254 control levels, with
     level 1 corresponding to 0.1% light output and level 254 to 100%. This is an excellent, well-defined curve we
     can adopt.

4. **ANSI C137.1 (0-10V Dimming Interface):**

   - While an analog standard, drivers conforming to it sometimes offer selectable dimming curves (linear, logarithmic,
     soft linear, square law). This indicates the industry's recognition of the need for different curves.

5. **S-Curve / Soft Linear / Square Law:** Other common curves that provide different "feels" for dimming.

   - **S-Curve:** Offers a slower change at the beginning and end of the dimming range, with a more rapid change in the
     middle, often creating a more natural or visually appealing effect.
   - **Square Law:** Often used to mimic the dimming behavior of incandescent bulbs.

### How to Implement and Leverage These

The core idea is to perform the curve transformation in the software layer (either in ESPHome or Home Assistant Core's
native implementation) before sending the final, raw brightness value to the device.

1. **Adopt DALI Logarithmic Curve as the Default "Perceptual" Curve:**

   - **Action:** Research the exact mathematical formula or lookup table specified by DALI (IEC 62386-102) for its
     logarithmic curve.
   - **Implementation:** This `logarithmic` curve should be the _default_ when a `curve` is not explicitly specified in
     `dynamic_control`, or when `perceptual_dimming: true` (or similar, if we add such a flag) is set. This ensures
     that any Home Assistant-driven transition or dynamic dimming defaults to a perceptually smooth experience.
   - **Location:** This conversion logic would reside in:
     - **ESPHome (PR 1.1/1.2):** Within the `LightState`'s internal processing, transforming the target perceived
       brightness (0-100%) to the raw output value (0-255 PWM duty cycle, etc.) using the logarithmic curve. This
       applies to native ESPHome transitions and dynamic control.
     - **Home Assistant Core `LightTransitionManager` (PR 3.2/3.3):** When handling transitions or dynamic control,
       this manager would calculate the intermediate steps, applying the selected `curve` (defaulting to
       logarithmic) to convert perceived brightness levels to linear device brightness values before sending them
       to the integration.

2. **Offer Predefined Named Curves as Options:**

   - **Options:** Provide a clear set of choices in both ESPHome's `dynamic_control_profiles` YAML (PR 1.2) and Home
     Assistant's `dynamic_control` service schema (PR 3.1).
     - `linear`: Direct mapping (1:1). Useful for debugging or specific industrial applications.
     - `logarithmic` (DALI-compliant): The recommended default for human perception.
     - `s_curve`: For a softer start/end.
     - `square_law` (or `power` with configurable exponent): To mimic incandescent.
   - **Implementation:** Define the mathematical functions for these curves in the respective codebases (ESPHome C++ and
     HA Python).

3. **Allow Custom Curve Definition (Advanced):**

   - **Options:** For advanced users, allow a `custom` curve type defined by a list of `[input_percentage,
     output_percentage]` pairs (e.g., `[[0,0], [10, 1], [50, 20], [100, 100]]`). The system would then linearly
     interpolate between these user-defined points.
   - **Implementation:** This requires interpolation logic (e.g., `np.interp` equivalent) in both ESPHome and the
     `LightTransitionManager`.

4. **Clear Documentation:**

   - **Explanation:** The documentation (PR 4.3) is paramount here. It should explain the concepts of perceived vs.
     measured brightness, the purpose of different dimming curves, and why logarithmic is generally preferred.
   - **Guidance:** Provide clear guidance on when to choose `linear` vs. `logarithmic` vs. other curves, and how to
     define custom ones.

### Impact on ZHA and Z-Wave JS Integrations

As discussed, ZHA and Z-Wave JS integrations typically don't expose a dynamic "apply this curve" command to the
underlying protocols.

- **Core-Level Curve Application:** For ZHA and Z-Wave JS devices, the `curve` parameter will be handled entirely by the
  **Home Assistant Core's `LightTransitionManager`**. This means:
  1. The `LightTransitionManager` will take the desired perceived brightness (0-100%) and apply the selected `curve` to
     calculate the corresponding _linear_ brightness value (0-255 or 0-99 depending on the device's actual range).
  2. It will then send this calculated linear brightness value as a standard `SET` command (e.g., `Level Control Set`
     for Zigbee, `Multilevel Switch Set` for Z-Wave) to the device.
  3. This ensures that _all_ dimmable lights in Home Assistant can benefit from these perceptual dimming curves, even if
     the underlying hardware is "linear" in its native command interpretation.
- **Device-Specific Parameters (Caveat):** Some advanced Z-Wave (and rare Zigbee quirk) devices _might_ have
  configuration parameters to set their _internal_ default dimming curve. If exposed by the integration, users could
  set this statically. However, it's generally recommended that if a user wants dynamic curve control, they should
  rely on Home Assistant's `curve` parameter and keep the device's internal curve linear/default to avoid compounding
  effects (e.g., a "logarithmic of a logarithmic" curve).

By adopting these professional lighting control practices, we can deliver a significantly more refined and natural
dimming experience across the entire Home Assistant ecosystem.
