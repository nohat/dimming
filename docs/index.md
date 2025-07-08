# Universal Smart Lighting Control Documentation

Welcome to the comprehensive documentation for the Universal Smart Lighting Control project - a unified architecture for intuitive and performant dynamic lighting control in Home Assistant.

## 🎯 Project Overview

This project proposes a fundamental enhancement to Home Assistant's lighting control, creating a unified system for smooth, intuitive dimming—like turning a physical dimmer knob. It addresses long-standing user frustrations with choppy or unresponsive lights and introduces a "conductor" (a new core component) to orchestrate seamless brightness and color changes across all smart lights, regardless of brand or protocol.

## 📚 Quick Start Guide

### New to this project?
1. **Start here**: [Core Architecture Proposal](architecture/architecture.md) - The main architectural document
2. **Understand the scope**: [Scope & Requirements](architecture/scope.md)
3. **See the big picture**: [Project Concepts](architecture/pro_concepts.md)

### Ready to dive deeper?
- **Technical Strategy**: Browse the [Technical Strategy](technical-strategy/ha_strategy.md) section for implementation details
- **Integration Support**: Check [Integration Guides](integration-guides/top_lighting_integrations.md) for platform-specific information
- **Implementation Plans**: Review [Implementation](implementation/eng_execution.md) for execution details

## 📖 Complete Documentation Index

*This documentation contains {{ doc_count() }} pages across 7 main sections (last updated {{ last_updated() }})*

### 🏠 [Current State](current-state/)
*{{ section_summary("current-state") }}*

| Document | Description |
|----------|-------------|
| [Overview](current-state/current_state.md) | Current state of dynamic dimming in Home Assistant |
| [Community Discussions](current-state/community_discussions.md) | Key community discussions and user feedback |
| [Challenges & Risks](current-state/challenges.md) | Technical challenges and implementation risks |
| [Core Contributors](current-state/core_contribs.md) | Key people and teams in lighting control development |

### 🏗️ [Architecture](architecture/)
*{{ section_summary("architecture") }}*

| Document | Description |
|----------|-------------|
| [Core Proposal](architecture/architecture.md) | **Main architectural document** for universal lighting control |
| [Project Concepts](architecture/pro_concepts.md) | Fundamental concepts and design principles |
| [Scope & Requirements](architecture/scope.md) | Detailed scope definition and requirements |
| [Project Plan](architecture/project_plan.md) | High-level timeline and execution strategy |

### ⚡ [Technical Strategy](technical-strategy/)
*{{ section_summary("technical-strategy") }}*

| Document | Description |
|----------|-------------|
| [Home Assistant Strategy](technical-strategy/ha_strategy.md) | **Core integration approach** and LightTransitionManager |
| [ESPHome Proposal](technical-strategy/esphome_proposal.md) | ESPHome-specific implementation strategy |
| [ESPHome Strategy](technical-strategy/esphome_strategy.md) | Detailed ESPHome technical approach |
| [Light State Enhancements](technical-strategy/light_state_enhancements.md) | Proposed light entity state improvements |
| [Non-linear Dimming](technical-strategy/nonlinear_dimming.md) | Perceptually uniform dimming curves |
| [Simultaneous Dimming](technical-strategy/simultaneous_dimming.md) | Coordinated multi-light brightness control |

### 🔌 [Integration Guides](integration-guides/)
*{{ section_summary("integration-guides") }}*

| Document | Description |
|----------|-------------|
| [Top Lighting Integrations](integration-guides/top_lighting_integrations.md) | Overview of popular lighting platforms |
| [Capability Matrix](integration-guides/capability_matrix.md) | **Comprehensive capability comparison** across platforms |
| [ZHA & Z-Wave](integration-guides/zha_zwave.md) | Zigbee and Z-Wave implementation details |
| [Zigbee2MQTT](integration-guides/zigbee2mqtt.md) | Zigbee2MQTT integration strategy |
| [Tasmota](integration-guides/tasmota.md) | Tasmota device integration approach |
| [Tuya](integration-guides/tuya.md) | Tuya Smart integration patterns |

### 🚧 [Implementation](implementation/)
*{{ section_summary("implementation") }}*

| Document | Description |
|----------|-------------|
| [Engineering Execution](implementation/eng_execution.md) | **Primary implementation roadmap** and development phases |
| [Execution Plan B](implementation/execution_plan_b.md) | Alternative implementation approach |

### 🚀 [Future Enhancements](future-enhancements/)
*{{ section_summary("future-enhancements") }}*

| Document | Description |
|----------|-------------|
| [Control Mapping](future-enhancements/control_mapping.md) | Advanced control mapping and customization |
| [Auto-Detected Controller Defaults](future-enhancements/defaults.md) | Intelligent default configuration system |

### 📚 [Resources](resources/)
*{{ section_summary("resources") }}*

| Document | Description |
|----------|-------------|
| [Kickoff Post](resources/kickoff_post.md) | Original community kickoff and discussion links |

## 🔗 Key Documents

| Priority | Document | Description |
|----------|----------|-------------|
| 🔥 **Essential** | [Architecture Proposal](architecture/architecture.md) | Main technical proposal for universal lighting control |
| 🔥 **Essential** | [Home Assistant Strategy](technical-strategy/ha_strategy.md) | Core Home Assistant integration approach |
| ⚡ **Important** | [Capability Matrix](integration-guides/capability_matrix.md) | Device and protocol capability comparison |
| ⚡ **Important** | [Engineering Execution](implementation/eng_execution.md) | Detailed implementation roadmap |
| 📋 **Reference** | [Project Plan](architecture/project_plan.md) | High-level project timeline and milestones |
| 📋 **Reference** | [ESPHome Proposal](technical-strategy/esphome_proposal.md) | ESPHome-specific implementation strategy |

## 🚀 Project Goals

- **Intuitive Control**: "Hold-to-dim, release-to-stop" as a first-class experience
- **Consistent Behavior**: Lights respond predictably across all integrations
- **Perceptually Uniform**: Natural-feeling light changes with appropriate dimming curves
- **Optimal Performance**: Minimal latency and network load using native device capabilities

## 🛠️ Technical Highlights

- New `dynamic_control` service parameter for continuous dimming
- Centralized `LightTransitionManager` in Home Assistant Core
- Native protocol support (Zigbee Move/Stop, Z-Wave Level Change)
- Optimized simulation for unsupported devices
- Real-time state feedback with `dynamic_state` attribute

## 📖 Navigation

Use the navigation menu on the left to explore all documentation sections:

- **Architecture**: Core proposals and project concepts
- **Technical Strategy**: Implementation approaches and enhancements
- **Integration Guides**: Platform-specific documentation
- **Implementation**: Execution plans and contribution guides
- **Resources**: Community posts and reference materials

---

*This documentation is part of an ongoing effort to enhance Home Assistant's lighting control capabilities. For questions or feedback, please refer to the [Kickoff Post](resources/kickoff_post.md) for community discussion links.*
