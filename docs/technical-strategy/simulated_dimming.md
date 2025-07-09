# Simulated Dimming / Dynamic Control (Optional Fallback)

_This document consolidates all discussion around "simulated dimming"—sometimes referred to as
`SIMULATED_DYNAMIC_CONTROL`, `DYNAMIC_CONTROL_SIMULATED`, or `LightEntityFeature.TRANSITION_SIMULATED`—into
one place.  The goal is to keep this functionality **optional** and **decoupled** from the core dimming
architecture so that the rest of the project docs no longer need to reference it._

## 1  Context & Motivation

Some dimmable lights (e.g. Wi-Fi bulbs such as LIFX) lack native **dynamic control** commands (`move` / `stop`) or
**smooth transitions**.  Without a fallback, automation loops must send many `turn_on` commands per second, flooding
Zigbee/Thread networks and producing visible stepping.

A software-level simulation inside Home Assistant Core can provide a smoother UX while shielding integrations from
complex internal timers.  However, this is strictly a **“nice-to-have”** feature.  Native control remains the primary
path; simulations should never block rollout of the rest of the dimming project.

## 2  Proposed Feature Flags

| Flag | Hex | Purpose |
|------|-----|---------|
| `LightEntityFeature.TRANSITION_SIMULATED` | `0x80` (128) | Integration (or HA Core) can simulate smooth `transition` when a device lacks native support. |
| `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` | `0x100` (256) | Integration (or HA Core) can simulate `dynamic_control` (`move`/`stop`) commands. |

Integrations may declare one or both.  HA Core will fallback only when the corresponding native capability flag is
_absent_ and the applicable `*_SIMULATED` flag is _present_.

## 3  HA Core Architecture Sketch

```text
light.turn_on(brightness, transition, dynamic_control)  
        |   
        v  
LightTransitionManager.choose_mode()
        |-- if supports(DYNAMIC_CONTROL): delegate to integration/device
        |-- elif supports(DYNAMIC_CONTROL_SIMULATED): start async simulation loop  ↴
        |     • calculate delta per ~40 ms (≤25 FPS)
        |     • schedule incremental turn_on calls
        |     • cancel on stop, new command, or brightness target reached
        |
        |-- elif transition and supports(TRANSITION): native transition
        |-- elif transition and supports(TRANSITION_SIMULATED): simulate via loop
        `-- else: immediate brightness set
```

Key notes:

1. Simulation runs inside the event loop using `async_call_later`, preventing busy-waiting.
2. Internal light state is updated with helper attrs such as `dynamic_state: simulated_moving_brightness_up` so that the
   UI can reflect movement.
3. Simulations auto-cancel on new commands.
4. Updates are capped (~20–30 Hz) to avoid network congestion.

## 4  Integration Guidelines

• **ESPHome** – declare `DYNAMIC_CONTROL_SIMULATED` until native dynamic control is detected, then drop the flag at
runtime.

• **Zigbee / ZHA, Z-Wave JS** – typically _do not_ need simulation because native `Move`/`Stop` exists.  Only add the
flag if the underlying device truly cannot handle `Move`.

• **Tasmota, Tuya, etc.** – may choose to declare the simulated flags as temporary fallback while waiting
for upstream firmware updates.

• **Zigbee2MQTT** - Supports native `brightness_move`/`color_temp_move` commands for most Zigbee 3.0+ devices. Only use `DYNAMIC_CONTROL_SIMULATED` for older devices that don't support the Zigbee Level Control `Move`/`Stop` commands. Z2M devices should be tested with native commands first before falling back to simulation.

```python
class MyLight(LightEntity):
    _attr_supported_features = (
        LightEntityFeature.BRIGHTNESS |  # native brightness
        LightEntityFeature.DYNAMIC_CONTROL_SIMULATED  # allow HA Core sim
    )
```

### Fallback Guidance for Protocol Integrations

While native support is preferred, some integrations or individual devices may lack the necessary Zigbee `Move`/`Stop` commands or the Z-Wave Multilevel-Switch `Start/Stop Level Change` equivalents.  In these cases the integration **should declare** the appropriate `*_SIMULATED` flag so Home Assistant Core can take over.

| Scenario | Recommended Action |
|----------|-------------------|
| Zigbee device (via ZHA) without Level-Control `Move`/`Stop` support | Do **not** set `DYNAMIC_CONTROL`; instead set `DYNAMIC_CONTROL_SIMULATED` so HA Core will drive smooth movement by sending incremental `Move to Level` commands. |
| Z-Wave dimmer lacking `Start/Stop Level Change` | Declare `DYNAMIC_CONTROL_SIMULATED`. HA Core will fallback by scheduling rapid `Multilevel Switch Set` packets. |
| Any device missing native `transition` capability | Declare `TRANSITION_SIMULATED` to allow HA Core’s transition loop. |

These flags should be regarded as temporary aids; integration maintainers are encouraged to drop them once firmware or protocol updates add proper native commands.

## 5  Testing & Validation

1. **Unit tests** for `LightTransitionManager` covering: native control, simulated control, cancellation, and edge cases.
2. **Integration tests** with a mock light that declares only `*_SIMULATED` flags.
3. **Performance tests**: ensure ≤100 ms latency, ≤30 Hz command rate, and no visible stepping.
4. **Network load measurements**: show ~50–80 % reduction vs. naïve automation loops.

## 6  Pros & Cons

### Pros

• Better UX on devices lacking native capabilities.
• Reduces network chatter relative to automation-based dimming.
• Requires minimal work in individual integrations once the core helper exists.

### Cons

• Adds complexity to HA Core.
• Risk of race conditions if integrations also try to simulate.
• Requires careful rate limiting to avoid flooding networks.

## 7  Open Questions

1. Should simulation live in HA Core or a helper library?  
2. How to expose simulated state in the UI (`dynamic_state`) without clutter?  
3. Do we need user-configurable max FPS or per-integration overrides?  

## 8  PR Timeline & Implementation Steps

Below is a high-level pull-request roadmap distilled from earlier documents.  The intent is to keep scheduling details out of other docs and maintain them centrally here.

| PR | Scope | Summary |
|----|-------|---------|
| **A.1** | HA Core | Introduce `LightEntityFeature.TRANSITION_SIMULATED` flag. |
| **A.2** | HA Core | Add transition-simulation logic to `LightTransitionManager` / `light.async_turn_on`. |
| **A.3** | HA Core | Introduce `LightEntityFeature.DYNAMIC_CONTROL_SIMULATED` flag. |
| **A.4** | HA Core | Add dynamic-control simulation logic (move/stop) to manager. |
| **B.1** | ESPHome Integration | Temporarily declare `DYNAMIC_CONTROL_SIMULATED` until devices get native support; drop flag dynamically when detected. |
| **B.2** | Other Integrations | Provide guidance / PRs for ZHA, Zigbee2MQTT, Z-Wave JS, etc. to opt-in by setting `*_SIMULATED` flags where appropriate. |

---

## 9  Revision History & Sources

This document consolidates content previously scattered across:

- `technical-strategy/ha_strategy.md`
- `implementation/eng_execution.md`
- `implementation/execution_plan_b.md`
- `architecture/architecture.md`
- `architecture/project_plan.md`
- `integration-guides/*`
- and other docs listed in commit history.

All other documents should now omit detailed discussion of simulated dimming and instead reference this file if
needed.
