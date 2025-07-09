# Community Discussions on Light Control Limitations

This document catalogs community discussions that highlight the need for improved light control in Home Assistant, focusing on hold-to-dim functionality, smooth transitions, and move/stop commands.

## Hold-to-Dim and Continuous Control

### "Dimming lights by holding a button" (January 2019)

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/dimming-lights-by-holding-a-button/95472>

**User Quote:**

> _"I've been thinking it would be somewhat complex, its just something that has a huge WAF and is how the dimming systems you buy usually work. I can't be the only one that has been wanting functionality like this in HA in some way?"_

**Issue:** Users want basic hold-to-dim functionality that mimics traditional dimmer switches.

### "Dim/Brighten light on button Long Press" (January 2022)

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/dim-brighten-light-on-button-long-press/374420/37>

**User Quote:**

> _"I have an Aqara Mini Switch that supports long press hold and long press release and i am trying to use the feature to dim or brighten the light in the WC."_

**Issue:** User struggles with Repeat Until in automation builder. Contributors recommend complex Node-RED flows or YAML automations with repeat-while sequences, but these solutions are complex and brittle.

### "Need help with dimming controls" (Reddit)

**Platform:** Reddit r/homeassistant
**URL:** <https://www.reddit.com/r/homeassistant/comments/1cfoj5i/need_help_with_dimming_controls/>

**User Quote:**

> _"I always noticed when using the dimming arrows it only would do it in steps. No matter what if you hold down the down button, it will dim about 10% and stop."_

**Professional Installation Impact:**

> _"I have actually sold a bunch of HA jobs coming up. This is one of them. I literally ripped out Lutron homeworks dimmers because I said this was the way better way."_

**Frustration with Complexity:**

> _"I have to do all those conditions and programming to get a dimmer to dim like a normal dimmer? ... I'd rather pay someone to put all 40 Lutron dimmers back in before doing that."_

**Issue:** A professional installer is considering abandoning Home Assistant entirely due to lack of basic dimming functionality.

### Smart Home Junkie YouTube Tutorial

**Platform:** YouTube
**URL:** <https://www.youtube.com/watch?v=L-bcabdaMxE>
**Title:** "Dim Lights THE RIGHT WAY In Home Assistant - TUTORIAL"

**Problems with Current Approach:**

- Requires complex, brittle automations
- Uses inefficient while loops with arbitrary delays
- Manual timing and state management
- Different approaches needed for single lights vs. groups
- Creator acknowledges complexity: "if you don't know what trigger IDs are, watch my video about that"

## Protocol-Specific Limitations

### "Updating HA light brightness after stopping a smooth dimming down action" (October 2022)

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/updating-ha-light-brightness-after-stopping-a-smooth-dimming-down-action/481826>

**User Quote:**

> _"There isn't a service level equivalent to that cluster command"_

**Issue:** User wants to use ZHA level cluster commands to stop dimming when long press ends, but no Home Assistant service exists.

### "How to use cluster command in automation?"

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/how-to-use-cluster-command-in-automation/769100>

**User Quote:**

> _"It seems like I need a cluster command ... when I want to implement smooth dimming."_

**Workaround Impact:**

> _"I gave it up to get smooth dimming with cluster command. I've just bind the dimmers directly to the zigbee groups which bypasses home assistant."_

**Issue:** User bypasses Home Assistant entirely to achieve basic dimming functionality.

### "ZwaveJS Start Level Change command"

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/zwavejs-start-level-change-command/618410>

**Issue:** Users try to access Z-Wave `Start Level Change` and `Stop Level Change` commands directly via `zwave_js.set_value` or `zwave_js.invoke_cc_api` for smooth dimming, highlighting that protocol capabilities exist but aren't accessible through standard Home Assistant services.

### "Is there a way to send Matter Cluster commands from Home Assistant?"

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/is-there-a-way-to-send-matter-cluster-commands-from-home-assistant/851976>

**User Quote:**

> _"I previously made two blueprints to dim lights using a pico remote that sends a stop and stop dimming command through Zigbee. Z2M Pico Remote and ZHA pico remote. I would like to make something similar for matter bulbs, but I haven't been able to figure out a way to send cluster commands to matter devices."_

**Issue:** User successfully implemented Zigbee solutions but can't replicate for Matter devices.

## Alternative Solutions and Workarounds

### "\[pyscript\] Dim lights with single push button"

**Platform:** Home Assistant Community
**URL:** <https://community.home-assistant.io/t/pyscript-dim-lights-with-single-push-button/284405>

**Issue:** Requires pyscript and complex automation loops with service calls.

### ESPHome Feature Request #185

**Platform:** GitHub (ESPHome)
**URL:** <https://github.com/esphome/feature-requests/issues/185>
**Title:** "Dimming switch/rotary encoder"

**Issue:** Users want continuous dimming from physical controls in ESPHome. While closed due to `dim_relative`, discussion shows demand for "stop" mechanism.

## Common Problems with Current Workarounds

### Transition Issues

**The Problem:** Users expect smooth fades using `transition:` parameter but lights often snap to new brightness/color.

**The Cause:** Many smart lights don't natively support smooth transitions. Home Assistant passes the parameter, but devices ignore it if unsupported.

**Current Workarounds:**

- Manual scripts with `async_call_later` or `repeat` loops
- Rapid, small brightness/color changes over time

**Limitations:**

- **Network flooding:** Zigbee/Z-Wave networks overwhelmed with commands
- **Choppy animation:** Not smooth on slower networks
- **Complex setup:** Significant YAML for each light/group
- **Not interruptible:** Difficult to stop ongoing transitions

### Universal Dimming Curves

**The Problem:** Brightness percentage vs. perceived brightness isn't linear. Lights may dim little for first 50%, then rapidly for last 50%.

**Current Workarounds:**

- Template lights with mathematical transformations
- Exponential curves for logarithmic perception

**Limitations:**

- Requires significant YAML knowledge
- Must be configured per light type

## Key Themes

1. **User Frustration:** Complexity and unreliability of automation-based solutions
1. **Professional Impact:** Installers considering abandoning Home Assistant
1. **Protocol Capability Gap:** Native protocol support exists but isn't exposed through standard services
1. **Workaround Limitations:** Network flooding, complexity, and poor user experience
1. **Universal Need:** Desire for consistent behavior across all light types and protocols

## Community Needs Summary

The community clearly articulates need for:

1. **Universal Transition Handling:** Consistent fading for all lights, regardless of native support
1. **Universal Continuous Control:** Standardized move/stop commands for intuitive hold-to-dim experiences
1. **Advanced Control:** Configurable transition curves and speeds
1. **State Feedback:** Real-time reporting of transition/motion states
1. **Protocol Abstraction:** Single interface that works across Zigbee, Z-Wave, Matter, and WiFi devices
