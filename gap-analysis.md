# Dark Forest Sim — Implementation Gap Analysis

**Architecture reference:** `architecture.md`  
**Repository:** `OwenOwen76/Dark-Forest-Sim`  
**Reviewed:** November 21, 2026

This document tracks outstanding implementation work against the architecture specification. Existing foundations are identified as partial rather than repeatedly listed as missing.

## 1. Shared Simulation Foundations

| Area | Current state | Remaining work | Architecture |
|---|---|---|---|
| Stocks and flows | Basic stock settlement exists | Extend accounting across physical resources, materials, food, and other domains | §4.1 |
| Capacity and constraints | Energy supply is constrained by available reserves | Generalize capacity, utilization, bottlenecks, availability, and unmet demand | §4.2 |
| Networks | No general network model | Reusable graph foundation for infrastructure, transport, energy, communications, and trade | §4.3 |
| Projects and processes | No general project system | Prerequisites, resources, capabilities, progress, duration, dependencies, and failure | §4.4 |
| Knowledge and uncertainty | Basic event-delivery boundaries exist | Observations, estimates, beliefs, confidence, staleness, and information provenance | §4.5, §8 |
| Stochastic engine | Current simulation is largely deterministic | Independent reproducible random streams and persisted generator states | §4.6, §7 |
| Temporal engine | Annual demographic and interval-based energy updates exist | Event scheduling, domain-specific update frequencies, intermediate events, and adaptive advancement | §6 |
| Spatial model | Basic 3D positions and distance calculations exist | Spatial hierarchy, astronomical distributions, physical objects, and spatial generation | §5 |

## 2. Domain Simulation

Only demographics and an initial aggregate energy model currently have authoritative simulation state. Calculators and narrator tools should not be mistaken for completed simulation domains.

| Domain | Remaining implementation |
|---|---|
| Demographics | Cohorts, fertility, mortality, migration, and stochastic population changes |
| Biology and health | Species profiles, disease, nutrition, and medical systems |
| Food and agriculture | Crops, soil, water, yields, and food storage |
| Energy | Generation facilities, storage, transmission, dispatch, and losses |
| Materials and resources | Deposits, reserves, extraction, processing, inventories, and recycling |
| Industry and manufacturing | Production chains, machinery, labor, capacity, and constraints |
| Infrastructure | Networks, maintenance, degradation, failures, and repairs |
| Technology and science | Research projects, prerequisites, prototypes, testing, and deployment |
| Astronomy and planetary systems | Stellar and planetary properties, orbital mechanics, environments, and universe generation |
| Thermodynamics | Integrated energy and heat balances, radiation, cooling, and observability |
| Ecology and environment | Ecosystems, environmental stocks, regeneration, and pollution |
| Economy and trade | Physical allocation, markets, trade, and financial systems |
| Logistics and transportation | Transport networks, vehicles, propulsion, and delivery |
| Governance and institutions | Authority, institutions, policies, administration, and enforcement |
| Society and culture | Social groups, norms, education, cooperation, and cultural development |
| Military and security | Capabilities, readiness, intelligence, logistics, and defense |
| Information and communication | Detection, transmission, decoding, interpretation, and knowledge processing |
| Exploration and expansion | Missions, surveys, discoveries, settlements, and construction |
| Risk and resilience | Reliability, dependencies, correlated failures, redundancy, and recovery |

**Important:** Domains should be developed through shared mechanisms and connected where dependencies are strong. Energy, materials, industry, and infrastructure should form an early connected production system.

Architecture: §9–10.

## 3. Runtime and Civilization Integration

Existing agent state, LLM request handling, tool-call journaling, and recovery provide a foundation.

Remaining work:

- Complete the LLM tool-call execution and response cycle.
- Integrate civilization selection, activation, turns, and scheduler handoffs.
- Implement distinct pause, suspend, and terminate behavior.
- Preserve unfinished work across interruptions.
- Bind every tool execution to its originating civilization and runtime identity.
- Prevent stale requests and duplicate uncertain side effects.
- Complete civilization MCP integration with the evolving domain tools.

Architecture: §11–12.

## 4. Persistence and Continuation

Existing versioned persistence covers substantial world, scheduler, agent, journal, and simulation-engine state.

Remaining work:

- Persist all future domain state and project progress.
- Persist independent random generator states and configurations.
- Ensure event scheduling and domain clocks survive recovery.
- Complete interrupted LLM and tool-call recovery.
- Demonstrate full save → process shutdown → fresh-process load → continuation.

Architecture: §13.

## 5. Information and Civilization-Facing Context

Basic delivered-event filtering exists, but the full knowledge architecture is missing.

Remaining work:

- Separate authoritative truth from civilization beliefs and knowledge.
- Represent exact, observed, estimated, inferred, suspected, and unknown information.
- Track observation source, time, confidence, uncertainty, and staleness.
- Prevent hidden universe state and narrator-only information from leaking into civilization contexts.
- Build compact decision-oriented civilization summaries.
- Provide drill-down inspection tools.
- Keep forecasts and hypothetical calculations separate from authoritative state.

Architecture: §3, §8, §14–15.

## 6. GUI and Observability

The existing interface has simulation, narrator, and civilization views, along with an initial inference event stream.

Remaining work:

- Complete the main control room and simulation controls.
- Add a 2D projection of the 3D universe.
- Add contextual object inspection and modification.
- Complete the narrator interface and its two tool categories.
- Build the calculator page.
- Build the device and runtime usage monitor.
- Build the graphical file viewer.
- Implement the separate human-readable live log and structured JSON logging.
- Integrate runtime events, tool results, errors, action proposals, handoffs, suspension, and resume into the live execution stream.

Architecture: §15–16 and §18, Stage 7.

## 7. Scientific Fidelity and Model Documentation

Every major simulation model still needs documented assumptions and limitations.

Outstanding work:

- Define model resolution, units, update frequency, and governing mechanisms.
- Document assumptions and unsupported conditions.
- Avoid false precision and arbitrary aggregate scores.
- Preserve unusual operator-specified values without silently correcting them.
- Ensure calculations explicitly report when their assumptions are violated.

Architecture: §17 and §21.

## 8. Outstanding Design Decisions

These are architectural decisions, not implementation defects:

- Universe scale and generation parameters.
- Initial civilization complexity.
- Simulation performance budget.
- Species-independent biological abstraction.
- General economic and social abstraction.

These should be resolved when the relevant implementation work approaches, rather than prematurely over-engineered.

Architecture: §20.

## 9. Recommended Implementation Priorities

1. Complete the shared simulation foundations: capacity, constraints, projects, networks, knowledge, and stochastic processes.
2. Develop materials and resource accounting.
3. Connect energy, materials, industry, and infrastructure into a functioning production system.
4. Expand demographics and the physical environment.
5. Develop the remaining civilization domains through shared foundations.
6. Complete civilization knowledge boundaries and decision-oriented context.
7. Finish runtime orchestration, tool execution, and recovery.
8. Complete persistence and fresh-process continuation.
9. Complete the GUI and observability systems.
10. Conduct the dedicated comprehensive testing and scientific consistency review.

## 10. Completion Standard

A feature or domain is not complete merely because it has state fields, calculators, or tools.

It must:

- Maintain authoritative state.
- Advance correctly over simulation time.
- Enforce applicable physical and operational constraints.
- Interact with relevant domains.
- Respect civilization information boundaries.
- Preserve state through saving and loading.
- Expose appropriate decision-relevant information.

Detailed internal simulation should support meaningful decisions without overwhelming civilization-facing summaries.
