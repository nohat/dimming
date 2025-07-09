# Control Mapping: Intelligent Defaults and Auto-Configuration

## Overview

This document outlines future enhancements to the Control Mapping system that would provide intelligent, auto-populated defaults based on device capabilities and common usage patterns. These features would build upon the core Control Mapping implementation to deliver an exceptional out-of-box experience.

## Relationship to Core Control Mapping

These enhancements extend the Phase 3 User Interface implementation described in `control_mapping.md`, specifically enhancing the Mapping Wizard (PR 3.2) with intelligent suggestions and automated configuration capabilities.

## Enhanced User Experience Goals

Transform the Control Mapping wizard from a manual configuration tool into an intelligent assistant that:

1. **Recognize Controller Type:** Identify the connected device as a "dimmer switch," "scene remote," "rotary controller," etc., based on its declared capabilities (e.g., exposed event entities, device class, or integration-specific metadata).

1. **Infer Common Actions:** For recognized controller types, suggest common mappings for its standard buttons/controls to relevant light actions.

1. **Pre-populate Light Action Defaults:** When a light is selected as a target, pre-fill the `dynamic_control` parameters with sensible defaults (e.g., `logarithmic` curve, `medium` speed for dimming, `toggle` for on/off).

1. **Recognizes Controller Types**: Automatically identifies device capabilities and common usage patterns

1. **Suggests Optimal Mappings**: Provides pre-configured mappings based on device type and target lights

1. **Populates Intelligent Defaults**: Auto-fills dynamic control parameters with perceptually optimized settings

1. **Enables One-Click Setup**: Allows complete configuration with minimal user interaction

## Future Enhancement Phases

### Phase 6: Intelligent Configuration (Future)

Building upon the core Control Mapping implementation, this phase would add intelligent automation to the configuration process.

#### PR 6.1: Controller Profile System

**File:** `homeassistant/helpers/controller_profiles.py`

**Implementation:**

````python
class ControllerProfile(TypedDict):
    """Device-specific mapping suggestions and defaults."""
    device_model_patterns: List[str]
    device_class: str  # "dimmer", "scene_controller", "rotary", etc.
    suggested_mappings: List[SuggestedMapping]
    compatibility_matrix: Dict[str, List[str]]  # light types -> recommended features

class SuggestedMapping(TypedDict):
    """Pre-configured mapping suggestion."""
    controller_event: ControllerEventData
    light_action_template: Dict[str, Any]
    priority: int  # For ordering suggestions
    description: str  # User-friendly description
```text

**Profile Storage:**

- Integration-specific profiles in `homeassistant/components/{integration}/controller_profiles/`
- Community-contributed profiles via Home Assistant Community Store
- User-customizable profile overrides

#### PR 6.2: Suggestion Engine

**File:** `homeassistant/core/control_mapping/suggestions.py`

**Features:**

- Device compatibility analysis
- Context-aware suggestions (room, light types, existing mappings)
- Machine learning from user configuration patterns
- Community usage pattern integration

### Phase 7: Advanced Intelligence (Future)

#### PR 7.1: Adaptive Learning

**Features:**

- Learn from user modifications to suggestions
- Improve suggestions based on usage patterns
- Community-driven improvement of default profiles
- Personalized configuration recommendations

#### PR 7.2: Context-Aware Automation

**Features:**

- Room-based automatic target selection
- Time-of-day dependent configurations
- Integration with Home Assistant Areas and Zones
- Seasonal lighting profile adjustments

## Enhanced User Experience Flow

### Scenario: Zero-Configuration Setup

**User adds a Lutron Pico Remote to their living room with existing Wiz light group.**

#### Step 1: Automatic Detection

- System recognizes Pico as "5-button dimmer controller"
- Identifies nearby "Living Room Lights" group in same area
- Loads Lutron Pico controller profile

#### Step 2: Intelligent Suggestions

The "Configure Controls" wizard presents a complete suggested configuration:

**Suggested Configuration: "Living Room Dimmer Setup"**

- **On Button** → Toggle Living Room Lights
- **Off Button** → Turn Off Living Room Lights
- **Dim Up (Hold)** → Smooth Dim Up (logarithmic curve, medium speed)
- **Dim Up (Release)** → Stop Dimming
- **Dim Down (Hold)** → Smooth Dim Down (logarithmic curve, medium speed)
- **Dim Down (Release)** → Stop Dimming
- **Favorite Button** → Activate "Movie Time" scene (if available)

#### Step 3: One-Click Activation

- User clicks "Accept All" → Complete setup in 5 seconds
- Alternative: Individual modification of any suggestion
- Test mode: Try configurations before committing

## Technical Implementation Strategy

### Controller Profile Architecture

#### Profile Definition Structure

```json
{
  "profile_id": "lutron_pico_5button_v1",
  "display_name": "Lutron Pico 5-Button Remote",
  "device_patterns": {
    "manufacturer": "Lutron",
    "model_patterns": ["PJ2-.*-L01", "Pico.*Remote"]
  },
  "controller_class": "scene_dimmer",
  "default_mappings": [
    {
      "event_data": {"action": "single", "action_id": "on"},
      "light_action": {"toggle": {}},
      "description": "Toggle lights on/off",
      "priority": 1
    },
    {
      "event_data": {"action": "long_press", "action_id": "dim_up"},
      "light_action": {
        "dynamic_control": {
          "type": "move",
          "direction": "up",
          "curve": "logarithmic",
          "speed": "medium"
        }
      },
      "description": "Smooth dim up",
      "priority": 2
    }
  ],
  "advanced_features": {
    "native_binding_support": true,
    "multi_target_capable": true,
    "scene_integration": true
  }
}
```text

#### Target Selection Intelligence

```python
class TargetSelector:
    """Intelligent target light selection."""

    def suggest_targets(self, controller_device: Device) -> List[LightTarget]:
        """Suggest appropriate light targets."""
        # Area-based selection
        # Recent activity analysis
        # Compatibility checking
        # User preference learning
```text

### Suggestion Engine Components

#### Compatibility Matrix

- Controller capabilities × Light features → Recommended configurations
- Protocol optimization (native vs. simulated)
- Performance considerations for different device combinations

#### Community Intelligence

- Anonymized usage pattern collection
- Popular configuration sharing
- Best practice recommendations
- Community-contributed profiles

### User Interface Enhancements

#### Enhanced Wizard Flow

1. **Auto-Detection**: "We found a Lutron Pico Remote in your Living Room"
2. **Context Awareness**: "This pairs well with your Living Room Lights"
3. **Suggestion Preview**: Visual preview of suggested mappings
4. **Bulk Configuration**: "Accept All" vs. individual customization
5. **Test Mode**: Try before commit functionality

#### Progressive Disclosure

- **Basic Mode**: One-click suggested configurations
- **Advanced Mode**: Full customization with intelligent defaults
- **Expert Mode**: Raw event mapping for power users

## Benefits and Impact

### User Experience Improvements

- **Setup Time**: Reduce from 5+ minutes to <30 seconds for common scenarios
- **Success Rate**: Increase successful configurations through intelligent defaults
- **Discoverability**: Surface advanced features through contextual suggestions
- **Accessibility**: Lower technical barriers for all user skill levels

### Technical Benefits

- **Reduced Support Load**: Fewer configuration-related issues
- **Community Growth**: Easier onboarding for new users
- **Ecosystem Development**: Encourage integration developers to provide profiles
- **Data-Driven Improvement**: Learn from real usage patterns

### Integration with Core Features

- **Light Groups**: Automatic group detection and targeting
- **Areas/Zones**: Context-aware suggestions based on physical layout
- **Scenes**: Integration with existing scene configurations
- **Automations**: Suggest automation enhancements alongside control mapping

## Implementation Roadmap

### Phase 6.1: Foundation (3-4 months)

- Controller profile system architecture
- Basic suggestion engine
- Enhanced wizard UI with suggestion support

### Phase 6.2: Intelligence (2-3 months)

- Machine learning integration
- Community data collection
- Advanced compatibility analysis

### Phase 7: Advanced Features (3-4 months)

- Adaptive learning system
- Context-aware automation
- Community contribution platform

## Success Metrics

### Quantitative Targets

- **Configuration Time**: <30 seconds for 80% of setups
- **User Success Rate**: >95% successful first-time configurations
- **Feature Adoption**: >60% of users accept suggested configurations
- **Community Contribution**: 100+ community-contributed profiles

### Qualitative Goals

- Seamless, intuitive setup experience
- Professional-grade lighting behavior out-of-box
- Reduced technical barriers for mainstream adoption
- Strong community ecosystem around controller profiles
````
