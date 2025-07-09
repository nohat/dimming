# Control Mapping: Advanced Device Control Integration

## Vision

Transform Home Assistant into a unified control platform where any physical control device can intuitively control any
light or light group with sophisticated dynamic behaviors, without requiring complex automations or technical expertise.

## Northstar

**Enable any user to pair any control device with any light in under 30 seconds through a guided UI, providing professional-grade lighting control with perceptual optimization and protocol-agnostic compatibility.**

## Problem Statement

Currently, connecting control devices (remotes, switches, buttons) to lights requires:

- Complex automation creation with protocol-specific event handling
- Deep technical knowledge of event structures and service calls
- Manual configuration of timing, curves, and dynamic behaviors
- Separate implementations for each device type and protocol
- Poor discoverability of capabilities and options

This creates a significant barrier to achieving intuitive lighting control that users expect from modern smart home
systems.

## Technical Strategy

### Core Architecture Principles

1. **Leverage Existing Constructs**: Build upon Home Assistant's existing Event entities rather than creating new event
   systems
2. **Declarative Configuration**: Enable simple, declarative mapping between control actions and light behaviors
3. **Protocol Abstraction**: Abstract away protocol differences through standardized interfaces
4. **Progressive Enhancement**: Support both software simulation and native hardware acceleration
5. **Backward Compatibility**: Maintain compatibility with existing automation systems

### Implementation Phases

## Phase 1: Standardized Event Schema

### Goal

Establish a unified schema for control device events that abstracts protocol differences and enables consistent handling
across integrations.

### PR 1.1: Core Event Schema Definition

**File:** `homeassistant/helpers/controller_events.py`

**Implementation:**

````python
class ControllerEventData(TypedDict):
    """Standardized event data for control device actions."""
    action: str  # "single", "double", "long_press", "long_release", "rotate"
    action_id: NotRequired[str]  # "button_1", "up", "down", etc.
    value: NotRequired[float]  # For rotary/slider controls
    duration: NotRequired[float]  # For timed actions
```text

**Integration Updates:**

- ZHA: Map Zigbee cluster commands to standardized events
- Z-Wave JS: Transform Central Scene and Multilevel Switch events
- Lutron Caseta: Standardize Pico and switch events
- MQTT: Provide event mapping templates
- ESPHome: Native support for standardized event emission

### PR 1.2: Event Entity Enhancement

**File:** `homeassistant/components/event/`

**Implementation:**

- Enhance Event entities with capability declaration
- Add device class support for control types
- Implement event history and pattern detection
- Support for multi-action events (press-and-hold sequences)

## Phase 2: Control Mapping Service

### Goal

Provide a core service for declaratively linking control device events to light entity actions with dynamic control
parameters.

### PR 2.1: Core Mapping Service

**File:** `homeassistant/components/homeassistant/services.yaml`

**Service Schema:**

```yaml
homeassistant.link_control:
  fields:
    controller_entity_id:
      selector: entity
      domain: event
      description: "Control device event entity"

    controller_action:
      description: "Specific action to trigger on"
      example: {"action": "long_press", "action_id": "button_up"}

    target_light_entity_id:
      selector: entity
      domain: light
      description: "Target light or light group"

    light_action:
      description: "Light behavior parameters"
      example:
        dynamic_control:
          type: move
          direction: up
          curve: logarithmic
          speed: medium
```text

### PR 2.2: Mapping Storage and Management

**File:** `homeassistant/core/control_mapping.py`

**Implementation:**

- Persistent storage of control mappings
- Efficient event listener management
- Mapping lifecycle (create, update, delete)
- Conflict detection and resolution
- Performance optimization for high-frequency events

### PR 2.3: Advanced Mapping Features

**Features:**

- Multi-target support (one control → multiple lights)
- Conditional mappings (time-based, state-based)
- Mapping templates and presets
- Import/export functionality
- Backup and restore capabilities

## Phase 3: User Interface

### Goal

Create an intuitive, discoverable UI that makes control mapping accessible to all users regardless of technical
expertise.

### PR 3.1: Device Integration UI

**File:** `homeassistant/frontend/src/panels/config/devices/`

**Implementation:**

- Add "Configure Controls" button to compatible devices
- Detect and display control capabilities
- Show existing mappings and status
- Quick access to common configurations

### PR 3.2: Mapping Wizard

**File:** `homeassistant/frontend/src/dialogs/control-mapping/`

**Wizard Flow:**

1. **Device Selection:** Auto-detect or manual selection
2. **Action Learning:** Physical interaction to identify events
3. **Target Selection:** Light/group picker with filtering
4. **Behavior Configuration:** Dynamic control parameter setup
5. **Testing:** Real-time validation and feedback
6. **Optimization:** Native binding vs. software control choice

### PR 3.3: Advanced Configuration

**Features:**

- Curve visualization and customization
- Speed and timing adjustment
- Scene integration
- Bulk configuration for similar devices
- Configuration templates and sharing

## Phase 4: Native Hardware Integration

### Goal

Enable direct device-to-device control where protocols support it, while maintaining Home Assistant oversight and
advanced features.

### PR 4.1: Protocol Binding APIs

**Integrations:** ZHA, Z-Wave JS, Matter

**Implementation:**

- Expose native binding capabilities through integration APIs
- Capability detection and compatibility checking
- Binding lifecycle management
- Fallback to software control when needed

### PR 4.2: Hybrid Control Architecture

**Features:**

- Automatic selection between native and software control
- Performance monitoring and optimization
- Native binding with HA feature overlay
- Protocol-specific optimization

### PR 4.3: Advanced Hardware Features

**Capabilities:**

- Multi-hop binding for complex scenarios
- Group binding for synchronized control
- Scene triggering through hardware
- Energy-efficient operation modes

## Phase 5: Ecosystem Integration

### Goal

Integrate control mapping with broader Home Assistant ecosystem and enable advanced use cases.

### PR 5.1: Automation Integration

**Features:**

- Control mappings as automation triggers
- Conditional mapping activation
- Integration with scripts and scenes
- Advanced logic and templating support

### PR 5.2: Voice and App Integration

**Features:**

- Voice commands for mapping management
- Mobile app quick configuration
- Remote mapping and troubleshooting
- Cloud synchronization for multi-instance setups

### PR 5.3: Analytics and Optimization

**Features:**

- Usage pattern analysis
- Performance metrics and optimization
- Predictive configuration suggestions
- Automated troubleshooting and diagnostics

## Technical Implementation Details

### Event Processing Architecture

```python
class ControlMappingManager:
    """Central manager for control device mappings."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.mappings: Dict[str, ControlMapping] = {}
        self.event_listeners: Dict[str, Callable] = {}

    async def add_mapping(self, mapping: ControlMapping) -> None:
        """Add a new control mapping."""
        # Validate mapping
        # Create event listener
        # Store persistently
        # Register with light entities

    async def handle_controller_event(self, event: Event) -> None:
        """Process incoming controller events."""
        # Match against registered mappings
        # Execute light actions
        # Handle native binding if available
        # Log and monitor performance
```python

### Performance Considerations

- **Event Processing Latency:** Target <10ms from physical action to light response
- **Memory Usage:** Efficient storage of mappings and event history
- **Network Optimization:** Minimize protocol overhead for frequent events
- **Scalability:** Support for hundreds of mappings per installation

### Security and Safety

- **Input Validation:** Strict validation of all mapping parameters
- **Rate Limiting:** Prevent event flooding and abuse
- **Access Control:** Restrict mapping modifications to authorized users
- **Fail-Safe Operation:** Graceful degradation when mappings fail

## User Experience Example

### Scenario: Lutron Pico + Wiz Lights

**Setup Process:**

1. Navigate to Lutron Pico device page
2. Click "Configure Controls"
3. Press and hold "Dim Up" button → System detects action
4. Select target: "Living Room Lights" group
5. Choose behavior: "Smooth Dim Up" with logarithmic curve
6. Test → Immediate feedback
7. Save → Mapping active

**Runtime Behavior:**

- Press "Dim Up" → Lights begin smooth dimming
- Release button → Dimming stops at current level
- Curve optimization ensures perceptual linearity
- Works reliably across all Wiz lights in group

### Benefits Delivered

- **30-second setup** from discovery to working control
- **Professional lighting behavior** with optimized curves
- **Protocol independence** - works with any supported light
- **Intuitive operation** matching traditional dimmer expectations
- **No technical knowledge required** for basic configuration
- **Advanced features available** for power users

## Success Metrics

- **Adoption Rate:** >80% of users with compatible devices use control mapping
- **Setup Time:** <30 seconds average for basic mappings
- **User Satisfaction:** >4.5/5 rating for ease of use
- **Technical Performance:** <10ms response latency, >99% reliability
- **Ecosystem Growth:** Increased integration of control devices
````
