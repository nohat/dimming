Yes, there is clear evidence that core Home Assistant and ESPHome team members are aware of the functionality gap regarding smooth, interruptible dimming (the "move/stop" functionality). It's less of a complete oversight and more of a complex challenge that has been acknowledged at various levels.

Here's a breakdown of comments and discussions from core developers:

### Home Assistant Core Team's Perspective:

1.  **Bram Kragten (HA Core Developer):**
    * In the Home Assistant Community thread "WhyTH is there not an options for smoothly dimming/brighten light and stopping the dimming/brighten effect?" (Source 1.3 from previous search results, dated August 2020), a user expresses frustration with the lack of a smooth dimming/brightening and stopping effect.
    * **Bram Kragten's comment:** "That will also not work for a lot of devices, Hue for example only allows a X number of requests per second." This comment directly acknowledges the *limitation* of simply spamming `brightness_step` commands (the common workaround) due to device and network rate limits. It implicitly confirms that achieving truly smooth, interruptible dimming is a known challenge due to underlying protocol/device constraints. The core team is aware that direct automation loops are often insufficient.

2.  **Paulus Schoutsen (Home Assistant Creator):**
    * While not always directly on "move/stop," Paulus often speaks to the core philosophy of Home Assistant that underpins this project:
        * **"You should not have to adapt to technology" / "The perfect app is no app":** (Source 5.3) This philosophy implies that basic, intuitive interactions like "hold to dim, release to stop" should *just work* without complex user-written automations. The fact that users *do* have to write complex automations for this highlights a gap against this ideal.
        * **Emphasis on local, unified control:** (Source 5.2, 5.4) His vision for Home Assistant as a central hub that integrates all devices and provides an "animation layer on top" strongly supports the idea of a universal `dynamic_control` service and the `LightTransitionManager` to normalize control across disparate devices.

3.  **`light.adjust` Service Discussion (GitHub Architecture Discussion #537 - Source 3.2, 3.3):**
    * This GitHub discussion from September 2022 directly explores adding a `light.adjust` service to change light attributes without necessarily turning the light on. While not specifically "move/stop," it's part of the broader conversation about more granular and flexible light control beyond simple `turn_on`/`turn_off`.
    * **Comments within this thread (by various contributors, sometimes including core team members or frequent maintainers):** Discuss the varying support for such features at the firmware level (e.g., LIFX has `set_state`, Hue doesn't), and the complexities of ensuring consistency. This demonstrates awareness of the inherent challenges of consistent light behavior across diverse integrations.

### ESPHome Team's Perspective:

1.  **OttoWinter (ESPHome Creator):**
    * **Dimming switch/rotary encoder (ESPHome Feature Request Issue #185):** (Source 2.4 from previous search results, updated April/May 2019) This issue directly asks for "If to control dimming by holding the button pressed" and "Start a dim 'cycle' that you can stop at the desired brightness."
    * **OttoWinter's Comment (May 28, 2019):** He closed the issue as "completed" with the comment, "With the latest changes in esphome, this will be possible: `on_press: - while: condition: - binary_sensor.is_on: the_button then: - light.dim_relative: id: the_light relative_brightness: 1% transition_length: 0.01s - delay: 0.01s.`"
    * **Interpretation:** This indicates that from ESPHome's perspective, the *building blocks* (`dim_relative`, `while` loops, `delay`) were provided to *allow users to implement* "hold-to-dim" logic in YAML. It implies that a dedicated, first-class "move/stop" API for the light component itself was not considered necessary at the time, as it could be constructed from existing primitives. This shows awareness of the *need* for the functionality, but a design decision that it belonged in the YAML automation layer rather than a direct core light component feature.

    * **Monochromatic light. PWM. Dimming (ESPHome Issue #48):** (Source 4.4 from previous search results, updated Feb/Mar 2019) OttoWinter also directly commented on the topic of dimming curves (gamma correction) to address the non-linear human perception of light. This shows a clear understanding of the perceptual aspects of dimming.

### Conclusion on Acknowledgment:

It's clear that the "move/stop" dimming functionality is **not off the radar**. It's a **known functionality gap and a frequent user request**.

* **Home Assistant core developers** are aware of the limitations of current workarounds (network spam, device rate limits) and the desire for more consistent, intuitive light control. Their work on broader light domain improvements and general platform philosophy points to this being an area ripe for enhancement.
* **ESPHome developers** have provided the low-level tools (`dim_relative`, `while` loops) to *enable* users to create this functionality in YAML, suggesting it was seen as something that could be composed rather than a specific, integrated light component feature.

Our project specifically aims to elevate this composite functionality into a first-class, standardized, and natively/simulated supported feature across Home Assistant and ESPHome, directly addressing these long-standing user pain points and architectural complexities.