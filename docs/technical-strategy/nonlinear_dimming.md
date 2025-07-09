# Nonlinear Dimming Strategy

Handling requests for nonlinear dimming profiles within Home Assistant's ZHA and Z-Wave JS integrations requires a nuanced approach, as neither Zigbee nor Z-Wave protocols typically offer native, standardized commands for applying arbitrary dimming curves dynamically during a `move` or `transition`.

Instead, devices usually have a fixed internal dimming curve, or a configurable one through device-specific parameters. Therefore, the primary strategy will rely on Home Assistant Core's simulation capabilities, while also acknowledging any rare native configuration options.

Here's how to coherently handle nonlinear dimming requests for ZHA and Z-Wave JS devices:

## 1. Home Assistant Core's `LightTransitionManager` as the Primary Curve Handler

For most ZHA and Z-Wave JS lights, the `curve` parameter within the `dynamic_control` (or `transition`) service call will be interpreted and applied by the **Home Assistant Core's `LightTransitionManager`** (as described in **Phase 3, PR 3.2 & 3.3** of the project plan).

- **Mechanism:** When a `light.turn_on` service call includes a `curve` (e.g., `logarithmic`, `s_curve`, or a custom point list) in its `dynamic_control` or `transition` parameters, the `LightTransitionManager` will:
  1. Determine the light's current brightness and the target brightness.
  1. Calculate a series of intermediate brightness values **that follow the specified nonlinear curve** over the requested `transition` duration or `dynamic_control` `ramp_time`/`speed`.
  1. Send these **pre-calculated, incrementally stepped brightness commands** to the ZHA or Z-Wave JS integration at a high frequency (e.g., every 50-100ms).
- **Integration's Role:** The ZHA and Z-Wave JS integrations will simply receive these discrete, pre-curved brightness `set` commands and pass them to the device. They will not need to interpret the `curve` parameter themselves, as the curve application happens upstream in Home Assistant Core.
- **Feature Flags:** For these integrations, the presence of `LightEntityFeature.TRANSITION_SIMULATED` and `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` will signal to Home Assistant Core that it should perform this software-based, curve-aware simulation if native protocol-level curve application is not available.

### 2. Leveraging Device-Specific Configuration (If Applicable)

While not a dynamic command, some advanced Z-Wave (and rarely Zigbee via quirks) devices might expose **configuration parameters** that allow adjusting their _internal_ dimming curve.

- **Mechanism:** If such a parameter exists and is exposed by the Z-Wave JS (or ZHA quirk) integration, users could configure the device's default dimming curve at the _device level_ through the Home Assistant UI's device settings.
- **Interaction with `dynamic_control`:**
    - If a device's internal curve is configured this way, and a `dynamic_control` command with a `curve` is then sent from Home Assistant, the HA `LightTransitionManager`'s curve calculation would effectively be applied _on top of_ or _in conjunction with_ the device's internal curve. This could lead to complex or unexpected behavior, or simply the HA-imposed curve would override the perceived effect of the device's internal curve.
    - **Recommendation:** Documentation should clearly state that for consistent and predictable behavior, it's generally best to:
        - **Either** rely solely on Home Assistant's software-based curve application (`dynamic_control` with `curve`) and leave the device's internal curve (if configurable) at its default or a linear setting.
        - **Or** configure the device's internal curve (if supported) and avoid specifying a `curve` in `dynamic_control`, allowing the device to use its built-in nonlinear behavior.
- **Implementation:** The Z-Wave JS and ZHA integrations would simply expose these device configuration parameters as standard Home Assistant device configuration options, but would not dynamically interact with the `curve` parameter of the `light.turn_on` service calls.

### 3. State Reporting for Nonlinear Dimming

The `dynamic_state` attribute (as introduced in **ESPHome PR 2.4** and consumed by **HA Core PR 3.4**) will be crucial here.

- When Home Assistant is simulating a nonlinear dimming profile for a ZHA or Z-Wave JS light, the `dynamic_state` of that light entity in Home Assistant would be set to something like `simulated_moving_brightness_up_curved` or `simulated_transitioning_curved`. This provides clear feedback to the user and allows automations to react specifically to curved dimming events.

### Summary for ZHA and Z-Wave JS

For nonlinear dimming profiles (`curve` parameter in `dynamic_control`):

- **Primary Handling:** The `curve` will primarily be handled by the **Home Assistant Core's `LightTransitionManager`**. This manager will calculate the intermediate brightness steps based on the specified curve and send these individual steps as standard `set` commands to the ZHA/Z-Wave JS integration.
- **Integration's Role:** ZHA and Z-Wave JS integrations will transparently pass these stepped brightness commands to the underlying devices using `Level Control Set` (Zigbee) or `Multilevel Switch Set` (Z-Wave) commands, potentially with a `transition_time`/`duration` for each small step to ensure further smoothness at the device level.
- **Native Device Configuration (Limited):** If a specific device has configurable internal dimming curves via ZCL attributes or Z-Wave configuration parameters, these would be exposed as _static device configuration options_ within Home Assistant, separate from the dynamic `light.turn_on` service calls.
- **Consistent Experience:** This approach ensures that users get a consistent, curve-aware dimming experience regardless of whether the underlying Zigbee or Z-Wave device natively understands complex curve commands.

The integration of professional lighting control standards, particularly regarding nonlinear dimming curves, is a fantastic idea to elevate the user experience. You're right that the human eye perceives light logarithmically, not linearly, which is why a simple linear dimming curve often feels "off" – with too much change at the high end and too little control at the low end.

Here's how we can leverage these standards and practices in our work:

### Key Standards and Concepts to Leverage

1. **Human Visual Perception (Weber-Fechner Law / Stevens' Power Law):** The fundamental principle is that our perception of brightness is non-linear. A linear change in light output (e.g., from 0% to 100% measured lumens) does not equate to a linear change in _perceived_ brightness. Small changes at low light levels are much more noticeable than large changes at high light levels.

1. **Logarithmic Dimming Curves:**

   - **Rationale:** These curves are designed to compensate for human visual perception, making dimming appear smooth and even across the entire range. A `logarithmic` curve ensures that perceived brightness changes linearly with the control input. This provides finer control at low light levels where the eye is more sensitive.
   - **Industry Adoption:** Logarithmic dimming is a standard in professional and theatrical lighting control (e.g., DMX, DALI) and is often the default.

1. **DALI (Digital Addressable Lighting Interface) - IEC 62386 Standard:**

   - This is a highly relevant standard as it explicitly defines a **standard logarithmic dimming curve** (and also a linear one). DALI devices typically default to this logarithmic curve. It specifies 254 control levels, with level 1 corresponding to 0.1% light output and level 254 to 100%. This is an excellent, well-defined curve we can adopt.

1. **ANSI C137.1 (0-10V Dimming Interface):**

   - While an analog standard, drivers conforming to it sometimes offer selectable dimming curves (linear, logarithmic, soft linear, square law). This indicates the industry's recognition of the need for different curves.

1. **S-Curve / Soft Linear / Square Law:** Other common curves that provide different "feels" for dimming.

   - **S-Curve:** Offers a slower change at the beginning and end of the dimming range, with a more rapid change in the middle, often creating a more natural or visually appealing effect.
   - **Square Law:** Often used to mimic the dimming behavior of incandescent bulbs.

### How to Implement and Leverage These

The core idea is to perform the curve transformation in the software layer (either in ESPHome or Home Assistant Core's simulation) before sending the final, raw brightness value to the device.

1. **Adopt DALI Logarithmic Curve as the Default "Perceptual" Curve:**

   - **Action:** Research the exact mathematical formula or lookup table specified by DALI (IEC 62386-102) for its logarithmic curve.
   - **Implementation:** This `logarithmic` curve should be the _default_ when a `curve` is not explicitly specified in `dynamic_control`, or when `perceptual_dimming: true` (or similar, if we add such a flag) is set. This ensures that any Home Assistant-driven transition or dynamic dimming defaults to a perceptually smooth experience.
   - **Location:** This conversion logic would reside in:
     - **ESPHome (PR 1.1/1.2):** Within the `LightState`'s internal processing, transforming the target perceived brightness (0-100%) to the raw output value (0-255 PWM duty cycle, etc.) using the logarithmic curve. This applies to native ESPHome transitions and dynamic control.
     - **Home Assistant Core `LightTransitionManager` (PR 3.2/3.3):** When simulating transitions or dynamic control, this manager would calculate the intermediate steps, applying the selected `curve` (defaulting to logarithmic) to convert perceived brightness levels to linear device brightness values before sending them to the integration.

1. **Offer Predefined Named Curves as Options:**

   - **Options:** Provide a clear set of choices in both ESPHome's `dynamic_control_profiles` YAML (PR 1.2) and Home Assistant's `dynamic_control` service schema (PR 3.1).
     - `linear`: Direct mapping (1:1). Useful for debugging or specific industrial applications.
     - `logarithmic` (DALI-compliant): The recommended default for human perception.
     - `s_curve`: For a softer start/end.
     - `square_law` (or `power` with configurable exponent): To mimic incandescent.
   - **Implementation:** Define the mathematical functions for these curves in the respective codebases (ESPHome C++ and HA Python).

1. **Allow Custom Curve Definition (Advanced):**

   - **Options:** For advanced users, allow a `custom` curve type defined by a list of `[input_percentage, output_percentage]` pairs (e.g., `[[0,0], [10, 1], [50, 20], [100, 100]]`). The system would then linearly interpolate between these user-defined points.
   - **Implementation:** This requires interpolation logic (e.g., `np.interp` equivalent) in both ESPHome and the `LightTransitionManager`.

1. **Clear Documentation:**

   - **Explanation:** The documentation (PR 4.3) is paramount here. It should explain the concepts of perceived vs. measured brightness, the purpose of different dimming curves, and why logarithmic is generally preferred.
   - **Guidance:** Provide clear guidance on when to choose `linear` vs. `logarithmic` vs. other curves, and how to define custom ones.

### Impact on ZHA and Z-Wave JS Integrations

As discussed, ZHA and Z-Wave JS integrations typically don't expose a dynamic "apply this curve" command to the underlying protocols.

- **Core-Level Curve Application:** For ZHA and Z-Wave JS devices, the `curve` parameter will be handled entirely by the **Home Assistant Core's `LightTransitionManager`**. This means:
  1. The `LightTransitionManager` will take the desired perceived brightness (0-100%) and apply the selected `curve` to calculate the corresponding _linear_ brightness value (0-255 or 0-99 depending on the device's actual range).
  1. It will then send this calculated linear brightness value as a standard `SET` command (e.g., `Level Control Set` for Zigbee, `Multilevel Switch Set` for Z-Wave) to the device.
  1. This ensures that _all_ dimmable lights in Home Assistant can benefit from these perceptual dimming curves, even if the underlying hardware is "linear" in its native command interpretation.
- **Device-Specific Parameters (Caveat):** Some advanced Z-Wave (and rare Zigbee quirk) devices _might_ have configuration parameters to set their _internal_ default dimming curve. If exposed by the integration, users could set this statically. However, it's generally recommended that if a user wants dynamic curve control, they should rely on Home Assistant's `curve` parameter and keep the device's internal curve linear/default to avoid compounding effects (e.g., a "logarithmic of a logarithmic" curve).

By adopting these professional lighting control practices, we can deliver a significantly more refined and natural dimming experience across the entire Home Assistant ecosystem.
