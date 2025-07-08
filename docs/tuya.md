# Analysis of Tuya API Support for Continuous Lighting Dimming and Chinese User Community Sentiment

## I. Executive Summary

This report investigates Tuya's API capabilities regarding continuous lighting dimming, specifically the "touch-and-hold" followed by "release" modality, and examines the sentiment within Tuya's native Chinese user community concerning this functionality.

The analysis concludes that Tuya's ecosystem, particularly at its lower-level serial communication protocols and through specific Zigbee extensions, explicitly supports continuous dimming modalities functionally equivalent to the "touch-and-hold" and "release" paradigm. Commands such as "start continuous increase/decrease" and "end" are well-defined for brightness, color temperature, and hue control. While higher-level Tuya Cloud APIs often abstract this into setting target values with inherent transition times, the underlying capability for smooth, continuous adjustment is a core design principle.

Furthermore, an examination of Tuya's Chinese developer documentation and community discussions reveals no widespread concern or expressed need for this specific dimming method as a missing feature. Instead, the concepts of "stepless dimming" (无极调光) and "continuous dimming" (连续调光) are consistently highlighted and detailed, indicating that this functionality is both expected and implemented across Tuya's smart home devices. This suggests that the native Chinese user community values and experiences this form of intuitive control, which Tuya delivers through various technical means, rather than it being a significant pain point.

## II. Understanding Tuya's Dimming Modalities

Tuya's approach to lighting dimming is multifaceted, encompassing high-level cloud APIs for broad application control and lower-level device protocols for granular, real-time adjustments. This layered architecture caters to diverse development needs and user experiences.

### Tuya's Core Dimming API (Cloud and Standard Instruction Set)

Tuya's primary interface for controlling devices via its cloud services and the Smart Life application relies on Data Points (DPs). These DPs are designed for ease of use and abstraction, allowing developers to define desired light states without needing to manage highly granular, continuous commands directly at the cloud level.

The `bright_value` Data Point (DP) is a fundamental integer type that enables brightness to be set directly within a specified range, typically from 10 to 1000, with increments of 1. This DP is primarily used for setting an  

_absolute_ brightness level. For more complex ambient light adjustments, the `control_data` DP is employed. This JSON-structured DP allows for the modification of brightness, color temperature, hue, saturation, and value (HSV). A key parameter within  

`control_data` is `change_mode`, which supports either "direct" or "gradient" transitions. The "gradient" mode facilitates a gradual transition to a specified target state, providing a smooth visual change. However, it is important to note that this is typically a transition  

_to a defined end state_, rather than a continuous adjustment that remains active as long as a user input (like a "hold" action) persists.

The design of these high-level DPs prioritizes developer convenience and abstraction for common application scenarios. This approach means that while the platform effectively facilitates setting desired light states with smooth transitions, it does not explicitly expose granular "start/stop" commands in the same manner as a "touch-and-hold" interaction might imply at the cloud API level. This design choice simplifies integration for many common use cases, but it can lead to a perception that continuous adjustment mechanisms are absent if one only examines the highest-level interfaces. Nevertheless, the inherent capability for "gradient" transitions within the `control_data` DP confirms Tuya's commitment to delivering smooth lighting changes, which is the desired effect of continuous dimming.

### Tuya's Serial Protocol for Stepless/Continuous Dimming

While the higher-level cloud APIs abstract some of the granular control, Tuya's lower-level serial communication protocols provide explicit support for continuous dimming, directly enabling functionalities akin to "touch-and-hold." These protocols are typically used for direct communication between a device's Microcontroller Unit (MCU) and its lighting module, allowing for precise, real-time adjustments.

A clear demonstration of this capability is found in the "Brightness Stepless Adjustment" (亮度无极调节) command, identified as **0x03**, within Tuya's serial protocol documentation. This command is specifically designed for continuous dimming. Its first byte defines the action: `0` initiates a "continuous increase start," `1` initiates a "continuous decrease start," and `2` signals "end". The third byte of this command specifies the rate of brightness change as a percentage per second, allowing for customizable dimming speeds. This command structure is a direct functional equivalent to the "move" and "stop" commands found in standard smart home protocols for continuous control.  

Similarly, continuous adjustment is supported for other lighting parameters:

*   **Color Temperature Stepless Adjustment (色温无极调节) - Command 0x05:** This command utilizes the same byte 1 structure (`0` for continuous increase start, `1` for continuous decrease start, and `2` for end) to facilitate continuous adjustment of color temperature. The rate of change for color temperature is also configurable, ranging from 20% to 100% per second.  
    
*   **Hue Stepless Adjustment (H值无极调节) - Command 0x07:** This command also supports continuous adjustment of hue, employing the identical `start`/`end` byte structure for its first byte.  
    

The explicit presence of these "start" and "end" commands at the serial protocol level directly contradicts the initial premise that Tuya lacks "touch-and-hold" functionality. This capability is clearly embedded and defined at the device communication layer.

The observation that these granular commands exist at the device-to-module serial protocol level, yet appear abstracted at the cloud-to-device API, points to a multi-layered architectural approach within Tuya's ecosystem. This structure suggests that physical controls (such as dimmer knobs or touch panels) or custom applications built closer to the device hardware can directly leverage these precise continuous dimming commands. For developers creating such specialized interfaces, understanding and utilizing the serial protocol is essential to achieve fine-grained control. Conversely, standard cloud-integrated solutions might rely on the Tuya platform to manage continuous dimming internally, perhaps by translating high-level target value commands into sequences of these lower-level continuous adjustments, or by having the device firmware handle the continuous input from a physical dimmer.

The following table summarizes Tuya's serial protocol commands for continuous dimming, highlighting their functional equivalence to the "touch-and-hold" paradigm:

| Command Name (English) | Command Name (Chinese) | Command Code | Byte 1 (Action) | Byte 2 (Target) | Byte 3 (Rate) | Relevant Sources |
| --- | --- | --- | --- | --- | --- | --- |
| Brightness Stepless Adjustment | 亮度无极调节 | 0x03 | 0: Continuous Increase Start1: Continuous Decrease Start2: End | 1: White Light Brightness2: Colored Light Brightness | Percentage per 1s (range unspecified in source) |     |
| Color Temperature Stepless Adjustment | 色温无极调节 | 0x05 | 0: Continuous Increase Start1: Continuous Decrease Start2: End | Reserved (No meaning) | Percentage per 1s (range 20%~100%) |     |
| Hue Stepless Adjustment | H值无极调节 | 0x07 | 0: Continuous Increase Start1: Continuous Decrease Start2: End | N/A | Percentage per 1s (range unspecified in source) |     |

### Tuya's Advanced Dimming Features

Beyond explicit commands, Tuya's overall approach to lighting control emphasizes a sophisticated and user-centric dimming experience. This is evident in several advanced features integrated across its platform.

Tuya Smart utilizes a logarithmic dimming curve combined with a dimming depth of one thousandth. This design is specifically chosen to align with the human eye's physiological response, which is more sensitive to changes at lower brightness levels and less so at higher levels. The result is a "comfortable and soft" dimming performance that is intended to be more conducive to human eye health. This fundamental design choice ensures that even when a target brightness is set, the transition is visually smooth and pleasing.  

The concept of "stepless dimming" (无极调光), which denotes continuous, smooth adjustment without noticeable steps, is a pervasive feature across Tuya's lighting solutions. This includes smart dimmer relays and generic light bulb templates. For instance, dimmer relays are explicitly stated to support "stepless dimming and synchronized and independent control with the app and wall-mounted switches". The Smart Life app's user interface facilitates this by allowing users to "drag the brightness and color temperature sliders to adjust the brightness and color temperature" , which is a common visual representation of continuous dimming. Furthermore, a "soft start" feature, where lights gradually brighten upon activation, is a default behavior, typically taking 800ms to reach full brightness. This gradual transition provides a visual buffer for the eyes, enhancing comfort.  

The consistent emphasis on "comfortable and soft" dimming, logarithmic curves, and stepless adjustment across various products and app interfaces (such as sliders) indicates that Tuya's design philosophy prioritizes a smooth and intuitive user experience for dimming. This aligns perfectly with the underlying intent behind "touch-and-hold" dimming, as both aim for continuous, fluid adjustment. The availability of these features, whether through the app or dedicated hardware, demonstrates Tuya's commitment to delivering the _effect_ of continuous dimming, even if the specific API command structure varies across different layers of their ecosystem.

## III. Comparison with Zigbee/Matter Level Control Cluster

Understanding Tuya's dimming mechanisms benefits from a comparison with established smart home protocols like Zigbee and Matter, particularly their Level Control Cluster. This comparison highlights Tuya's adherence to standards while also showcasing its proprietary extensions.

### Zigbee/Matter Level Control Cluster Commands

The Zigbee Level Control Cluster is a standard component for managing light brightness, and its specifications are extended by Matter to ensure interoperable control across smart home devices. Within this cluster, commands like "move" and "stop" are fundamental for facilitating continuous dimming. For example, a Philips Hue Dimmer Switch utilizes "move level" commands when its dimming buttons are held, and sends a "stop" command upon release, effectively controlling continuous dimming. The "move" command initiates a continuous change in brightness, and the "stop" command halts this change at the current light level.  

Additionally, the `onLevel` attribute in Zigbee/Matter plays a role in the user experience of dimming. This attribute allows developers to specify a default brightness level for a light to turn on to when an "on" command is received. This feature enables a smooth ramp-up from zero brightness to a desired level, preventing an abrupt "pop" to a previously high brightness before dimming down, thereby enhancing the user's perception of control and comfort. The user's understanding of "move" and "stop" as standard commands for continuous dimming within Zigbee/Matter is accurate and well-supported by documentation, highlighting the standardized approach to such functionality in these protocols.  

### Tuya's Interoperability with Zigbee/Matter

Tuya has demonstrated a strong commitment to smart home interoperability by becoming a board member of the Connectivity Standards Alliance (CSA) and actively supporting the Matter connectivity standard. Tuya has achieved official certification for over 100 devices, including those in the lighting category, under the Matter standard. Furthermore, Tuya offers various Zigbee and Matter gateways and solutions, facilitating the integration of its devices into broader smart home ecosystems.  

While Tuya supports standard Zigbee, its strategy also involves the utilization of manufacturer-specific clusters and Data Points (DPs) to implement advanced or proprietary functionalities. This dual approach allows for broad compatibility while retaining unique features and a streamlined developer experience within their platform. For instance, within the standard Zigbee Level Control Cluster (0x0008), Tuya has implemented custom DPs such as "tuya Level Command" (0x00F0) and "tuya Level control" (0xF000). These DPs accept a level value (0-1000) and a `transtime` (transition time), indicating Tuya's own mechanism for setting a target level with a smooth transition.  

Most notably, within the standard Zigbee OnOff Cluster (0x0006), Tuya has introduced "custom" commands under `0xFC Rotate commands`. These include `0x00 Rotate right`, `0x01 Rotate left`, and `0x02 Rotate stop`. These commands are explicitly designed for continuous rotary control, which is functionally identical to the "touch-and-hold" and "release" paradigm for dimming. For example, a Tuya Smart Knob is known to send "LevelCtrl command" to a group of devices, implying its ability to interact with standard Zigbee dimming mechanisms.  

Tuya's strategy of simultaneously supporting open standards like Zigbee and Matter while also developing proprietary extensions (custom clusters and DPs) reveals a pragmatic approach to smart home interoperability. The presence of "Rotate commands" (0xFC) with explicit "start" (right/left) and "stop" actions within a _standard_ Zigbee cluster (OnOff) is a direct functional parallel to the "touch-and-hold" and "release" paradigm. This demonstrates that Tuya _does_ implement continuous control commands within its Zigbee devices, albeit potentially through its own specific interpretations or extensions within existing standard clusters. Consequently, while Tuya devices are designed to integrate with broader Matter/Zigbee ecosystems, achieving the most granular or specific control might sometimes necessitate familiarity with Tuya's proprietary additions.

## IV. Chinese User Community Sentiment and Discussions

Understanding the sentiment and technical discussions within Tuya's native Chinese user community is crucial for gauging the perceived importance and implementation of continuous dimming modalities.

### Overview of Tuya's Chinese Developer and User Forums

Tuya maintains a robust developer platform that includes a prominent "社区" (Community) section. This community serves as a central hub for developers to engage in technical discussions, share knowledge, and seek support for various aspects of the Tuya ecosystem. The community features active and popular topics covering areas such as Bluetooth device development, chip-specific light control, and app pairing.  

Tuya's commitment to a global audience is further evidenced by its comprehensive multilingual support, including Chinese, for UI text across its platform. The availability of AI translation tools for developers also highlights a concerted effort to cater to its diverse user base, including native Chinese speakers. The existence of a highly active and technically focused Chinese developer community, evidenced by detailed discussions and extensive documentation, suggests that if "touch-and-hold" dimming were a significant  

_missing_ feature or a major point of dissatisfaction, it would likely be a prominent subject of discussion or complaint, similar to how other technical challenges are addressed. The absence of such explicit grievances indicates that the functionality is either well-understood and implementable through existing means (e.g., serial protocol or custom DPs) or that current dimming solutions adequately meet user expectations.

### Analysis of Dimming-Related Discussions

Direct searches for "触摸长按调光" (touch-and-hold dimming) within the provided Chinese forum snippets did not yield explicit results, suggesting that this specific phrasing is not a common topic of complaint regarding a missing feature. However, searches for "连续调光" (continuous dimming) and "无极调光" (stepless dimming) consistently led to numerous relevant technical documents in Chinese. These documents extensively detail the implementation of such features, particularly at the serial protocol level, as discussed in Section II.  

Tuya's official documentation and product solutions frequently emphasize "flexible brightness adjustment" and the ability to "freely adjust brightness" (自由调节亮度). The Smart Life app's user interface supports this through intuitive "dragging sliders to adjust brightness" , which is a common visual representation of continuous dimming. The consistent focus across Tuya's materials is on providing a "comfortable and soft" dimming experience and promoting "stepless dimming".  

General smart home discussions in Chinese forums tend to focus on broader solutions, system integration, and overall user convenience, rather than specific dimming modalities. Interestingly, a general discussion on smart lighting control (not specific to Tuya) explicitly describes a remote control "single-button dimming operation" where holding the button initiates a "gradual brightening dimming process" and releasing it stops the dimming. This description perfectly matches the user's query regarding "touch-and-hold" functionality, indicating that this is a recognized and desired user expectation within the broader smart lighting market.  

The lack of explicit complaints regarding the _absence_ of "touch-and-hold" dimming within Chinese community forums, juxtaposed with the widespread use of terms like "stepless dimming" and "continuous dimming" in Tuya's official Chinese technical documentation, strongly suggests that this functionality is not only present but also a fundamental and expected feature. Users likely experience this intuitive control through the Tuya Smart Life app's slider interfaces or through physical dimmer hardware that translates continuous input into the underlying serial protocol commands. Therefore, the prevailing sentiment is not one of a missing feature, but rather an affirmation that this type of smooth, continuous dimming is a core capability within the Tuya ecosystem.

## V. Conclusion and Recommendations

### Summary of Findings

The investigation into Tuya's API support for lighting dimming modalities like "touch-and-hold" followed by "release" and the sentiment of the native Chinese user community yields several key conclusions:

*   **Tuya API Support:** Tuya's ecosystem unequivocally supports continuous lighting dimming functionalities that are equivalent to the "touch-and-hold" and "release" paradigm. This support is explicitly detailed in its low-level serial communication protocols, where commands such as `0x03` for brightness, `0x05` for color temperature, and `0x07` for hue include specific bytes for "start continuous increase/decrease" and "end". Furthermore, Tuya's custom Zigbee extensions, particularly the "Rotate commands" (0xFC) within the standard OnOff cluster (0x0006), provide a direct parallel to the "move" and "stop" concept for continuous control.  
    
*   **Cloud API Abstraction:** The higher-level Tuya Cloud API, which utilizes DPs like `bright_value` and `control_data`, tends to abstract this continuous control. These DPs typically facilitate setting absolute brightness values or initiating "gradient" transitions to a target state. While this simplifies integration for many applications, it may not expose explicit "start/stop" commands directly at the cloud API level, requiring deeper protocol understanding for such granular control.  
    
*   **Zigbee/Matter Comparison:** Tuya is an active participant and implementer of Zigbee and Matter standards, demonstrating interoperability. However, its approach often incorporates proprietary extensions alongside standard clusters. The functional outcome of continuous dimming is consistently achieved, even if the precise command structure differs from the standard Zigbee Level Control Cluster's "move" and "stop" commands.  
    
*   **Chinese Community Sentiment:** There is no discernible evidence in the provided materials of widespread discussion or concern within the native Chinese user community specifically lamenting the _absence_ of "touch-and-hold" dimming. Conversely, Tuya's Chinese developer documentation and product descriptions frequently emphasize and detail "stepless dimming" (无极调光) and "continuous dimming" (连续调光) as core, expected features, highlighting a "comfortable and soft" user experience. This indicates that the functionality is present and valued, rather than being a missing element or a source of dissatisfaction.  
    

### Recommendations

Based on these findings, the following recommendations are provided:

*   **For Developers Seeking "Touch-and-Hold" Functionality:** Developers aiming to implement direct "touch-and-hold" control should delve into Tuya's device-level serial protocols and utilize the MCU SDKs. These resources explicitly define the "start/stop" commands (e.g., commands 0x03, 0x05, 0x07) necessary for such continuous control. For Tuya Zigbee devices, exploring the custom "Rotate commands" (0xFC) within the OnOff cluster can provide the desired continuous control mechanism.
    
*   **Understanding API Layers:** It is important for developers to recognize that Tuya's API ecosystem operates on multiple layers. The higher-level Cloud API simplifies development by abstracting complex device interactions, making it suitable for many common smart home applications. However, lower-level protocols and custom extensions offer more granular control, which is essential for specialized user interfaces or unique interaction modalities.
    
*   **Leveraging User Experience Principles:** Tuya's consistent emphasis on "stepless" and "soft" dimming across its platform indicates a strong commitment to a superior user experience. Developers should leverage these inherent capabilities to provide smooth and intuitive lighting control in their applications, regardless of the specific underlying command structure or protocol.
    
*   **Engaging with the Community:** While explicit complaints about this specific dimming modality are not prominent, the Chinese developer community is highly active and serves as a valuable resource for in-depth technical implementation details regarding Tuya's extensive dimming capabilities and overall smart home solutions.


---
Implementing direct "start" and "stop" brightness adjustment service calls in Home Assistant's `light` entity would be a significant enhancement, moving beyond the current `brightness_pct` and `transition` parameters. This would allow for a more intuitive "touch-and-hold" dimming experience, similar to what's found in native Zigbee/Matter Level Control Clusters. Here's what would be needed for both the official Tuya integration and significant unofficial ones:

### I. Home Assistant Core `light` Entity Changes

The fundamental change would occur within Home Assistant Core itself, specifically in the `homeassistant.components.light` domain.

1.  **Define New Service Calls:** New service calls, such as `light.start_dimming` and `light.stop_dimming`, would need to be introduced.
    *   `light.start_dimming`: This service would likely accept parameters like `entity_id` (the light to control), `direction` (e.g., 'up' or 'down'), and an optional `rate` (e.g., percentage per second or steps per second).
    *   `light.stop_dimming`: This service would simply take `entity_id` to halt any ongoing continuous dimming.
2.  **Update `LightEntity` Base Class:** The `LightEntity` base class would need to be extended with abstract methods (or default implementations) for `async_start_dimming` and `async_stop_dimming`. This would provide a standardized interface for all light integrations to implement this new functionality.
3.  **Service Schema Definition:** The YAML schema for these new services would need to be defined, allowing users to call them via automations, scripts, and the developer tools.

This core change would enable a more efficient approach to continuous dimming, especially for light groups, as a single "adjust" message could be sent to a group rather than individual messages to each light.[1]

### II. Official Tuya Integration Changes

The official Home Assistant Tuya integration primarily communicates with devices via the Tuya Cloud API.[2, 3] This presents a challenge because the high-level Tuya Cloud API generally abstracts continuous dimming into setting target brightness values with a `gradient` transition, rather than exposing explicit "start" and "stop" commands.[4]

1.  **Simulation of Continuous Dimming:**
    *   **`async_start_dimming` Implementation:** When `light.start_dimming` is called, the official Tuya integration would likely need to initiate a background task or loop. This loop would periodically send `bright_value` updates to the Tuya Cloud API, incrementally increasing or decreasing the brightness based on the specified `direction` and `rate`.
    *   **`async_stop_dimming` Implementation:** When `light.stop_dimming` is called, this background task would need to be terminated, stopping the stream of brightness updates.
    *   **Challenges:** This simulation approach can introduce latency and may be subject to Tuya Cloud API rate limits (e.g., 200 DP reports per 60 seconds by default).[5, 6] This could result in less smooth dimming or unresponsive behavior if updates are throttled. The user experience might not be as fluid as direct hardware control.
2.  **Potential for Raw DP Commands (If Exposed via Cloud):**
    *   Tuya's lower-level serial protocols *do* support explicit "start continuous increase/decrease" and "end" commands (e.g., `0x03` for brightness).[7, 8]
    *   If Tuya were to expose these low-level serial commands via a "Raw type" Data Point (DP) through their *cloud API*, the official integration *could* potentially leverage this. This would involve sending hexadecimal payloads representing these commands.[9, 10] However, it's not explicitly documented that the cloud API supports sending these specific "move/stop" commands via raw DPs for continuous dimming.[9] Even if technically possible, it might be less officially supported for general use cases and could require complex payload construction.

### III. Unofficial Tuya Integrations Changes

Unofficial integrations, such as Local Tuya and Zigbee2MQTT, often offer more direct control over devices, which could make implementing continuous dimming more straightforward.

1.  **Local Tuya Integration:**
    *   Local Tuya communicates directly with Tuya Wi-Fi devices on the local network using their local keys and DP IDs.[11, 12]
    *   **Device-Specific DP Mapping:** The key for Local Tuya would be to identify if the specific Tuya Wi-Fi device exposes the "start/stop" continuous dimming commands (like the `0x03` serial protocol command) as accessible DPs locally. These might be custom "Raw type" DPs or specialized "Value" DPs that interpret start/stop signals.[7, 8, 9]
    *   **Implement `async_start_dimming` and `async_stop_dimming`:** If such DPs are found, the Local Tuya integration would need to implement these new Home Assistant service methods. This would involve constructing and sending the appropriate local DP commands (e.g., specific hexadecimal payloads for raw DPs or defined values for custom DPs) to the device.
    *   **Configuration:** Users might need to manually configure these specific DPs within Local Tuya, as automatic discovery might not expose these granular commands by default.[12, 13, 14]
    *   **`tuyapi` Library:** Libraries like `tuyapi`, often used by unofficial integrations, already support sending arbitrary DP values [15, 16], which would be crucial for this implementation.

2.  **Zigbee2MQTT (for Tuya Zigbee Devices):**
    *   This is arguably the most promising path for native continuous dimming. Zigbee2MQTT acts as a bridge, translating Zigbee device commands to MQTT messages for Home Assistant.[17, 18]
    *   **Existing "Move/Stop" Support:** Crucially, Zigbee2MQTT *already supports* "move" and "stop" commands for brightness (and color temperature) for many Zigbee lights, including Tuya Zigbee devices.[19, 20] These commands are part of the standard Zigbee Level Control Cluster and are designed for continuous adjustment until a "stop" command is received.
    *   **Home Assistant MQTT Light Integration Update:** The primary change here would be within Home Assistant's `light.mqtt` integration. It would need to be updated to:
        *   Translate the new `light.start_dimming` service call into the appropriate `brightness_move` MQTT message (e.g., `{"brightness_move": -40}` for dimming down at a rate of 40 units per second).[19, 20]
        *   Translate the `light.stop_dimming` service call into a `brightness_move: 0` (or `stop`) MQTT message.[19, 20]
    *   **Efficiency Benefits:** This approach is highly efficient because it leverages the native Zigbee protocol's continuous dimming commands, avoiding the need for Home Assistant to send a rapid stream of individual brightness updates, which can otherwise flood the Zigbee network.[21] No changes would typically be required within Zigbee2MQTT's core or its Tuya Zigbee device converters, as the functionality is already exposed via MQTT.

In summary, while the official Tuya integration would likely need to simulate continuous dimming via repeated cloud API calls, unofficial local integrations (especially Zigbee2MQTT) are better positioned to leverage existing device-level "start/stop" commands for a more responsive and efficient continuous dimming experience.

---

To effectively implement deep support for smooth dimming across the Home Assistant ecosystem, leveraging the competitive dynamics between official and unofficial Tuya integrations, a multi-pronged strategy is required. This involves defining a common abstraction in Home Assistant Core, understanding the capabilities of various lighting protocols, and then developing or enhancing integrations to map these capabilities to the new core services.

Here's how we can approach this:

**1. Home Assistant Core Abstraction: The Foundation for Deep Support**

The first crucial step is to introduce a standardized way for Home Assistant to represent and control continuous dimming. This would involve:

* **New Service Calls:**
    * `light.start_dimming`: This service would initiate continuous brightness adjustment.
        * `entity_id` (Required): The light entity to control.
        * `direction` (Required): `up` or `down`.
        * `rate` (Optional): An abstract speed or rate for dimming. This could be a numerical value (e.g., 1-100) that integrations translate to their underlying protocol's specifics, or a percentage per second.
        * `color_mode` (Optional): To extend beyond just brightness, allowing continuous adjustment of `color_temp` or `hue` where supported by the underlying device/protocol.
    * `light.stop_dimming`: This service would halt any ongoing continuous brightness adjustment.
        * `entity_id` (Required): The light entity to control.

* **LightEntity Enhancements:**
    * The `LightEntity` base class in Home Assistant Core would need new abstract methods (e.g., `async_start_dimming`, `async_stop_dimming`) that each light integration must implement if it supports this functionality.
    * A new `LightEntityFeature` (e.g., `LightEntityFeature.CONTINUOUS_DIMMING`) would be introduced. Integrations supporting these new services would declare this feature, allowing the Home Assistant UI and automations to dynamically offer these controls.

**2. Leveraging Competition: The Tuya Case Study**

The competitive dynamic between the official and unofficial Tuya integrations can be a powerful catalyst for broader adoption of these new dimming services:

* **Unofficial (Local Tuya / Zigbee2MQTT for Tuya Zigbee):** These integrations often have direct access to device-level commands or underlying protocols, making them ideal candidates for *first* implementing support for `start_dimming` and `stop_dimming`.
    * **Local Tuya:** Can directly leverage Tuya's low-level serial protocol commands (e.g., 0x03 for brightness, 0x05 for color temp, 0x07 for hue with "start continuous increase," "start continuous decrease," and "end" actions). This would involve crafting specific hexadecimal payloads (e.g., via `TuyaSend6`) and mapping them to the new Home Assistant services. This offers the deepest, most direct control for compatible devices.
    * **Zigbee2MQTT (for Tuya Zigbee devices):** Already supports Zigbee's `brightness_move` and `brightness_move: 0` for stopping, and some Tuya Zigbee devices expose custom "Rotate commands" (0xFC) which achieve continuous dimming. Home Assistant's MQTT light platform can be extended to expose these existing Zigbee2MQTT functionalities as the new `light.start_dimming` and `light.stop_dimming` services. This is perhaps the most straightforward path for many Tuya Zigbee devices.
* **Official Tuya Integration (Cloud-based):**
    * **The Challenge:** The official integration relies on the Tuya Cloud API, which primarily exposes DPs for setting absolute values or initiating gradient transitions to a fixed target. Direct "start/stop" commands are not explicitly documented at this cloud API level.
    * **The Leverage:** If unofficial integrations prove the immense value and user demand for native continuous dimming, it creates pressure on Tuya to expose such functionality via their official Cloud API. Home Assistant (and its community developers) could advocate for Tuya to introduce new, dedicated Cloud API endpoints or DP types that directly map to the device-level "start/stop" commands. Until then, the official integration might have to resort to inefficient rapid incremental updates, which would highlight the superiority of local/Zigbee solutions for this feature, thus fostering competition.

**3. Major Light Integrations with Underlying Support**

Several other major Home Assistant light integrations already have the underlying protocol support that could easily map to the proposed `light.start_dimming` and `light.stop_dimming` services:

* **Zigbee (ZHA & Zigbee2MQTT):**
    * **Underlying Support:** The Zigbee Level Control Cluster (0x0008) explicitly defines "Move to Level (with on/off)", "Move", and "Stop" commands. The "Move" command takes a move mode (up/down) and a rate. "Stop" halts the movement.
    * **Implementation:** Both ZHA and Zigbee2MQTT (via MQTT commands) already handle these. Adapting their Home Assistant integration components to expose these commands as the new `light.start_dimming` and `light.stop_dimming` services would be relatively straightforward.
* **Matter:**
    * **Underlying Support:** Matter's Clusters (built on ZCL, similar to Zigbee) are expected to include a Level Control Cluster with functionality analogous to Zigbee's "Move" and "Stop" commands.
    * **Implementation:** As Matter support matures in Home Assistant, the Matter integration would implement the `async_start_dimming` and `async_stop_dimming` methods by calling the corresponding Matter device commands.
* **Z-Wave (Z-Wave JS):**
    * **Underlying Support:** Z-Wave's Multilevel Switch Command Class (specifically for dimmers) has commands like `SwitchMultilevelSet` with a `dimmingDuration` (for transitions) and implicitly supports "start/stop" by sending `SwitchMultilevelStartLevelChange` and `SwitchMultilevelStopLevelChange`.
    * **Implementation:** The Z-Wave JS integration would map the new Home Assistant services to these Z-Wave commands.
* **MQTT (Generic MQTT Light):**
    * **Underlying Support:** While MQTT itself is a messaging protocol, not a device protocol, many devices expose "start/stop" dimming via MQTT (as seen with Zigbee2MQTT's `brightness_move`).
    * **Implementation:** The Home Assistant MQTT light integration could be enhanced to include new configuration parameters (`brightness_move_command_topic`, `brightness_move_payload_up`, `brightness_move_payload_down`, `brightness_stop_payload`, etc.) that allow users to define how `light.start_dimming` and `light.stop_dimming` translate to MQTT messages for their devices.
* **ESPHome:**
    * **Underlying Support:** ESPHome lights already support `transition_length` for smooth changes to a target brightness. More importantly, ESPHome code can be fully customized. You can implement precise control loops in ESPHome's YAML/C++ to respond to specific Home Assistant commands.
    * **Implementation:** ESPHome light components could be extended to have a `start_dimming` and `stop_dimming` action in their YAML configuration. These actions would then trigger internal C++ code that directly manipulates the LED PWM duty cycle, either incrementally or decrementally, until a "stop" command is received or a limit is reached. This offers highly granular control at the device level, bypassing the need for rapid HA service calls. The ESPHome integration in Home Assistant would then simply call these new ESPHome actions.
* **Philips Hue:**
    * **Underlying Support:** The Hue Bridge API supports "transitiontime" for smooth changes to a new state. While it doesn't have explicit "start/stop" like Zigbee's Level Control cluster (as the bridge abstracts this), it can achieve smooth dimming. However, true continuous "move" functionality might be simulated by the bridge itself or would require rapid updates. Further investigation into the Hue API's raw command capabilities for continuous level adjustment would be needed.
* **Insteon:**
    * **Underlying Support:** Insteon's dimmers traditionally supported "ramp rate" and "start/stop" dimming via direct commands, allowing for continuous adjustment.
    * **Implementation:** The Insteon integration would need to map the new HA services to these existing Insteon commands.

By systematically implementing these new core services and features across integrations, Home Assistant can establish deep, consistent support for smooth dimming, enhancing the user experience significantly. The competition between Tuya integrations can serve as a proving ground, demonstrating the value of direct device-level control for superior performance in this crucial smart home functionality.

---

