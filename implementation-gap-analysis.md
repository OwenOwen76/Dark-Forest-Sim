# Dark Forest Sim
## Implementation Gap Analysis

**Status:** Initial repository audit  
**Repository:** `OwenOwen76/Dark-Forest-Sim`  
**Branch:** `main`  
**Audit snapshot:** November 21, 2026  
**Purpose:** Compare the current implementation against the Simulation Architecture Specification and establish a practical implementation order.

---

# 1. Executive Summary

The current project has a functional foundation for controlling and inspecting a civilization simulation.

It already includes:

- A basic 3D universe.
- Civilization state and lifecycle.
- Event creation and propagation.
- Civilization scheduling.
- A narrator toolbox.
- A separate civilization MCP server.
- An OpenAI-compatible LLM client.
- Agent conversation persistence.
- Tool-call journaling.
- A FastAPI interface.
- A browser-based inspector with live inference streaming.

However, the current implementation is primarily a **simulation framework and interaction prototype**, not yet a complete civilization simulator.

The most significant gap is the lack of actual evolving civilization systems.

Population and energy currently exist as a handful of stored values and mathematical calculators. They are not yet connected to systems that continuously calculate births, deaths, energy production, industrial consumption, material extraction, infrastructure degradation, or other consequences.

Similarly, the existing event system models information travelling through space, but it does not yet represent a complete physical communication system.

## 1.1 Overall assessment

| Area | Current status | Assessment |
|---|---|---|
| 3D universe | Implemented | Basic |
| Civilization representation | Implemented | Very limited |
| Event propagation | Implemented | Basic |
| Civilization scheduling | Implemented | Partial |
| Civilization runtime | Implemented | Partial |
| LLM integration | Implemented | Partial |
| Civilization MCP | Implemented | Basic |
| Narrator tools | Implemented | Basic foundation |
| Physics calculators | Implemented | Useful collection |
| Economic calculators | Implemented | Very limited |
| Technology simulation | Implemented | Random breakthrough calculator only |
| Domain simulation | Mostly missing | Major development required |
| Knowledge system | Implemented | Very limited |
| Stochastic engine | Mostly missing | Major development required |
| Persistence | Implemented | Partial |
| Fresh-process continuation | Not demonstrated | Major development required |
| GUI | Implemented | Early prototype |
| Automated testing | Implemented | Good foundational coverage |

The project should retain its existing foundation rather than be rewritten.

The next development phase should expand the existing architecture into a real simulation engine.

---

# 2. Current Repository Structure

The current implementation is relatively compact.

```text
dark_forest_sim/
├── civilization_mcp.py
├── engine/
│   ├── civilization.py
│   ├── event.py
│   ├── scheduler.py
│   ├── space.py
│   └── universe.py
├── inspector/
│   ├── proxy.py
│   └── static/
│       └── index.html
└── narrator/
    ├── agents.py
    ├── api.py
    ├── data.py
    ├── economics.py
    ├── llm.py
    ├── persistence.py
    ├── physics.py
    ├── registry.py
    ├── runtime.py
    ├── technology.py
    └── world.py
```

The current tests cover civilization state, physics, economics, MCP tools, runtime behavior, persistence, and the inspector.

The architecture document is already present as `sim-architecture.md`.

---

# 3. Existing Implementation Assessment

## 3.1 Universe and spatial model

**Files:**
- `engine/space.py`
- `engine/universe.py`
- `engine/event.py`

**Status: Implemented foundation**

### Existing functionality

The project already has:

- Three-dimensional positions.
- Euclidean distance calculations.
- Civilization locations.
- Universe time.
- Generic events.
- Event propagation.
- Per-civilization event deliveries.
- Arrival-time calculations.
- Event arrival processing.

The spatial model correctly uses X, Y, and Z coordinates.

Events can travel between civilizations according to distance and propagation speed.

The universe also prevents duplicate event deliveries and processes arrivals according to simulation time.

### Missing functionality

There is currently no actual astronomical universe model.

Missing components include:

- Galaxies and galactic structure.
- Stars and stellar properties.
- Stellar systems.
- Planets and moons.
- Orbital parameters.
- Planetary environments.
- Resource deposits.
- Spatial resource distributions.
- Stellar evolution.
- Universe generation.
- Persistent universe generation seeds.

The current civilization position represents a location in 3D space, but there is no underlying physical object representing the planet or stellar system.

### Recommendation

Retain the existing `Position` and basic distance functionality.

Extend the world model through an astronomical object hierarchy rather than replacing the current spatial foundation.

Do not introduce a complicated astronomical generator until the intended universe scale is decided.

---

## 3.2 Civilization representation

**File:** `engine/civilization.py`

**Status: Implemented, but severely limited**

The current civilization contains:

- ID.
- Name.
- Position.
- Local year.
- Status.
- Resources.

`CivilizationResources` currently contains five variables:

1. Population.
2. Annual population growth rate.
3. Energy production.
4. Energy reserves.
5. Energy consumption per person.

This is a useful initial representation, but it does not yet constitute a civilization model.

### Missing functionality

The model currently has no representation for:

- Demographic cohorts.
- Biological populations.
- Food production.
- Material inventories.
- Resource extraction.
- Industrial facilities.
- Infrastructure.
- Technology capabilities.
- Research projects.
- Ecology.
- Economy.
- Governance.
- Society.
- Military capabilities.
- Communications infrastructure.
- Exploration missions.
- Active construction projects.

There is also no shared domain-state structure.

### Important design issue: state validation

The current resource model rejects negative energy production, energy reserves, and energy consumption.

It also rejects population growth rates less than or equal to -100%.

These restrictions make sense as ordinary physical validation, but they conflict with the architecture requirement that the human operator can directly set unusual authoritative values.

We should separate:

- Whether a value can be represented.
- Whether a value is physically plausible.
- Whether a calculation can operate on it.

The engine should not silently clamp unusual operator-specified values.

For example, a negative gravitational parameter should be representable if the operator explicitly sets it, even if ordinary orbital calculations subsequently report that their assumptions are violated.

### Recommendation

This is the first major development area.

Design the authoritative civilization state before adding more civilization statistics.

The model should support the 19 domains while keeping the civilization-facing summary compact.

---

## 3.3 Civilization scheduling

**File:** `engine/scheduler.py`

**Status: Partially implemented**

### Existing functionality

The scheduler supports:

- Sleeping civilizations.
- Scheduled wake times.
- Manual wake operations.
- Automatic waking when due.
- Selecting the active civilization with the lowest local year.
- Advancing the universe when no civilization is active.
- Stopping at the next scheduled wake or event arrival.

This is a good starting point.

### Missing functionality

The scheduler does not yet implement the complete simulation lifecycle.

Missing or incomplete:

- Full automatic turn orchestration.
- Narrator-controlled civilization selection.
- Complete runtime handoffs.
- Pause behavior.
- Suspension behavior.
- Runtime recovery coordination.
- Domain updates during elapsed time.
- More comprehensive scheduled event processing.

### Important temporal issue

There is a potential correctness problem in the current sleep scheduling.

The scheduler calculates wake time using:

`civilization.year + years`

However, it compares that value against:

`universe.current_time`

These are not necessarily the same clock.

For example:

- Universe time is 100.
- Civilization local year is 20.
- Civilization sleeps for 10 years.
- Current implementation schedules wake time at 30.

Since the universe is already at year 100, the civilization may wake immediately rather than sleeping for another 10 universe years.

The intended behavior should be:

- Calculate the absolute wake timestamp relative to current universe time.
- Advance the universe to that timestamp.
- Update the civilization's local year when it wakes.

This preserves the previously established rule that civilization-local time changes when the civilization wakes.

**This should be corrected before building domain time advancement on top of the scheduler.**

---

## 3.4 Events and knowledge

**Files:**
- `engine/event.py`
- `narrator/data.py`
- `narrator/world.py`

**Status: Partially implemented**

### Existing functionality

Events have:

- IDs.
- Types.
- Creation times.
- Descriptions.
- Origins.
- Propagation speeds.
- Optional target civilizations.

Deliveries track:

- Recipient.
- Distance.
- Departure time.
- Arrival time.
- Delivery status.

The knowledge system only exposes events after they physically arrive at the recipient civilization.

This is an important existing information-boundary mechanism.

### Missing functionality

The current system does not represent the complete progression from physical signal to understood information.

Missing:

- Transmitters.
- Receivers.
- Antennas.
- Signal power and bandwidth.
- Noise.
- Signal detection.
- Decoding.
- Interpretation.
- Measurement uncertainty.
- Knowledge confidence.
- Information staleness.
- Independent observations.
- Scientific inference.

Currently, an arrived event is essentially made available as known information.

### Recommendation

Preserve event propagation.

Develop a separate information and communication model that uses physical signals and updates civilization knowledge through explicit observation and processing stages.

Do not confuse event arrival with complete understanding.

---

## 3.5 Physics and economics

**Files:**
- `narrator/physics.py`
- `narrator/economics.py`

**Status: Calculators implemented; simulation systems missing**

### Existing physics calculators

The current physics module includes:

- Signal detection range.
- Waste heat power.
- Infrared detection range.
- Cooling duration.
- Signal travel time.
- Signal arrival time.
- Lorentz factor.
- Relativistic travel time.
- Proper travel time.
- Relativistic kinetic energy.
- Relativistic momentum.

These are useful foundations.

### Existing economic calculators

The economics module includes:

- Kardashev energy output.
- Compound population growth.
- Energy demand.
- Energy surplus.
- Energy deficit.

### Missing functionality

These calculators do not currently form connected physical or economic systems.

For example:

- Waste heat is not automatically generated by civilization energy consumption.
- Energy reserves are not automatically depleted through consumption.
- Population growth is not driven by age structure, fertility, and mortality.
- Industrial production does not consume materials or energy.
- Infrastructure does not impose operating requirements.
- Resource extraction does not change resource deposits.
- Technology does not improve actual production capabilities.

### Recommendation

Keep the calculators as reusable mathematical functions.

Build domain systems around them that consume authoritative state, calculate consequences, and update the relevant stocks and flows.

A calculator should not become a substitute for a simulation model.

---

## 3.6 Technology

**File:** `narrator/technology.py`

**Status: Minimal prototype**

The current technology module provides a reproducible random breakthrough roll.

It can return:

- No breakthrough.
- Minor breakthrough.
- Major breakthrough.
- Revolutionary breakthrough.

However, it does not model scientific or engineering development.

Missing:

- Research projects.
- Existing scientific knowledge.
- Technological prerequisites.
- Research capacity.
- Experimental infrastructure.
- Prototypes.
- Manufacturing capabilities.
- Deployment capabilities.
- Learning by doing.
- Knowledge diffusion.
- Technology-specific uncertainty.

The current breakthrough calculator should eventually be replaced or incorporated into a more comprehensive research and innovation model.

A breakthrough should depend on actual research activity and the civilization's capabilities, not merely an independent probability roll.

---

## 3.7 Civilization runtime and LLM integration

**Files:**
- `narrator/runtime.py`
- `narrator/agents.py`
- `narrator/llm.py`

**Status: Partially implemented**

### Existing functionality

The runtime already supports:

- One active civilization ID.
- Civilization activation.
- Agent conversation histories.
- Agent statuses.
- LLM requests.
- Pending action proposals.
- Narrator approval or rejection.
- Turn completion.
- Agent persistence.
- Tool-call journal records.

The LLM client validates assistant messages and tool-call structures.

The agent state supports statuses such as:

- Ready.
- Thinking.
- Waiting for tool.
- Sleeping.
- Waiting for clarification.
- Interrupted.
- Error.

The tool-call journal supports:

- Pending.
- Executing.
- Completed.
- Failed.
- Uncertain.

This is a meaningful foundation for reliable agent orchestration.

### Missing functionality

The runtime does not yet implement the complete desired turn lifecycle.

Important gaps:

1. No explicit pause operation.
2. No explicit suspend operation.
3. No complete termination workflow.
4. No runtime-safe interruption mechanism.
5. No complete automatic scheduler handoff.
6. No complete tool-execution loop inside the agent turn.
7. No demonstrated recovery of unfinished LLM tool interactions.
8. No complete preservation of pending execution state across process restarts.

The current `run_agent_turn` method obtains one LLM response, stores it, and returns it.

It does not itself implement a complete cycle of receiving tool calls, executing them, returning tool results to the LLM, and continuing until the turn finishes.

The MCP server exists separately, but its presence does not by itself complete the runtime orchestration.

### Important concurrency issue

The current runtime holds its asynchronous lock while awaiting the LLM response.

That means the runtime does not yet have the necessary architecture for independently handling pause or suspension requests during an active LLM operation.

The eventual implementation should distinguish:

- Runtime state synchronization.
- Active LLM requests.
- Tool execution.
- Safe interruption boundaries.
- Scheduler ownership.

The lock should not become a mechanism that prevents the very controls the runtime needs to support.

---

## 3.8 Persistence

**File:** `narrator/persistence.py`

**Status: Good foundation, incomplete recovery**

### Existing functionality

The current persistence system supports:

- Versioned JSON saves.
- Schema versions 1 and 2.
- Universe time.
- Civilizations.
- Civilization resources.
- Events.
- Event deliveries.
- Scheduler wake times.
- Agent states.
- Conversation messages.
- Tool-call journal.
- Atomic file replacement.
- File synchronization.
- Basic schema validation.

The runtime also has recovery behavior:

- Running agents are marked interrupted after restart.
- Executing tool calls become uncertain.
- Pending and completed tool calls retain their recorded states.

This is a particularly useful foundation.

### Missing persistent state

The current save format does not yet contain:

- Universe generation seed.
- Random generator states.
- Stochastic configuration.
- Astronomical objects.
- Planetary environments.
- Resource deposits.
- Domain-specific civilization state.
- Infrastructure.
- Production systems.
- Active projects.
- Domain event queues.
- Civilization knowledge beyond the existing event-delivery model.
- Complete simulation configuration.
- Full execution continuation information.

### Important recovery limitation

The current runtime can restore a pending action record, but an asyncio future from the previous process cannot survive a restart.

Consequently, the saved proposal can be inspected and resolved, but the original waiting request cannot simply continue as though nothing happened.

The same distinction applies to unfinished LLM requests.

### Required validation

The existing persistence tests establish serialization and restoration behavior.

They do not demonstrate the complete required workflow:

Save → destroy process → start fresh process → load → resume simulation → verify continued operation.

That needs a dedicated integration test using a separate process.

---

## 3.9 Narrator and civilization tools

**Files:**
- `narrator/registry.py`
- `narrator/world.py`
- `narrator/data.py`
- `civilization_mcp.py`

**Status: Basic foundation implemented**

### Narrator tools

The narrator toolbox currently exposes five consolidated tools with selectable operations.

The current groups cover:

- Civilization modification.
- Event management.
- Timeline management.
- Universe queries.
- Mathematics and physics.

This is a good approach because it avoids creating an excessively large collection of unrelated tools.

The distinction between world modification and read-only mathematics/data is already present.

### Civilization tools

The MCP server currently exposes 17 tools.

These include:

- Inspect own civilization.
- Inspect known events.
- Distance calculations.
- Travel calculations.
- Signal detection.
- Waste heat.
- Infrared detection.
- Cooling.
- Signal arrival.
- Relativistic calculations.
- Energy budget.
- Population growth.
- Action proposals.
- Time advancement.

### Missing functionality

The current tools do not yet provide the domain access required by the architecture.

Missing examples:

- Inspect population structure.
- Inspect resource inventories.
- Inspect energy systems.
- Inspect industrial capabilities.
- Inspect active projects.
- Inspect infrastructure.
- Inspect technology.
- Investigate known astronomical objects.
- Conduct observations.
- Evaluate potential projects.
- Propose structured physical actions.
- Manage exploration missions.

These should be introduced as their corresponding simulation systems become available.

The goal should not be to create a large toolbox immediately.

Tools should expose actual simulation capabilities, not placeholder operations.

---

# 4. Domain-by-Domain Gap Analysis

The following table compares the 19 domains against the current repository.

| Domain | Existing foundation | Missing implementation | Priority |
|---|---|---|---|
| Demographics | Population and compound growth | Cohorts, fertility, mortality, migration, stochastic births and deaths | High |
| Biology and health | None | Species profiles, health, disease, medical systems | Later |
| Food and agriculture | None | Food production, crops, water, soil, storage | Later |
| Energy | Production, reserve, consumption fields and calculators | Generation, storage, distribution, dispatch, depletion and losses | Critical |
| Materials and resources | None | Deposits, inventories, extraction, processing, recycling | Critical |
| Industry | None | Facilities, production chains, machinery, labor and capacity | Critical |
| Infrastructure | None | Assets, networks, degradation, maintenance, failures and repair | High |
| Technology and science | Breakthrough probability calculator | Research, prerequisites, prototypes, engineering and deployment | High |
| Astronomy | 3D positions and distance | Stars, planets, orbital mechanics, environments and generation | High |
| Thermodynamics | Waste-heat and cooling calculators | Integrated heat balance, thermal storage and physical consequences | High |
| Ecology and environment | None | Environmental stocks, ecosystems, regeneration and pollution | Later |
| Economy and trade | Energy-budget calculation | Physical economy, allocation, financial systems and trade | Later |
| Logistics and transportation | Distance and travel calculations | Networks, vehicles, shipments, propulsion and delivery | High |
| Governance | None | Institutions, authority, administration and policies | Later |
| Society and culture | None | Social groups, norms, cultural transmission and relationships | Later |
| Military and security | None | Assets, readiness, intelligence, sustainment and defense | Later |
| Information and communication | Generic event propagation and signal calculators | Physical communication infrastructure, detection, decoding and knowledge processing | High |
| Exploration and expansion | Spatial positions and generic events | Missions, surveys, discoveries, settlements and construction | Later |
| Risk and resilience | Generic event handling | Reliability, dependencies, correlated failures and recovery analysis | Cross-cutting |

The priorities indicate architectural dependencies, not the relative importance of the domains.

For example, biology and ecology are essential to a complete simulation, but their implementation will be more meaningful once the resource, energy, and environmental foundations exist.

---

# 5. Major Architectural Gaps

These are the most important issues that must be resolved before the project expands substantially.

## 5.1 No shared simulation update engine

Currently, the project has separate calculators and event handling, but no general mechanism for updating all civilization domains as time passes.

This is the largest missing foundation.

The engine needs to know:

- Which systems require updates.
- When those updates occur.
- What inputs they consume.
- What state they modify.
- What events they produce.
- How they interact with other domains.

A time advance must actually simulate the elapsed period.

It cannot merely change the clock or put a civilization to sleep.

## 5.2 No shared stock-flow accounting

The current resource model stores a few values directly.

There is no reusable accounting mechanism for:

- Energy.
- Materials.
- Food.
- Water.
- Fuel.
- Population.
- Biomass.
- Waste.

This should be implemented before creating complex economic and industrial systems.

## 5.3 No shared capacity and project system

There is no common mechanism for determining whether a civilization can complete a project.

The engine needs to account for:

- Prerequisites.
- Available resources.
- Production capacity.
- Infrastructure.
- Energy.
- Time.
- Bottlenecks.
- Project progress.

This is essential to the division of responsibility between the LLM and the simulation engine.

## 5.4 No simulation-wide stochastic engine

The current technology module creates a new `random.Random(seed)` instance for each breakthrough roll.

This provides reproducibility for an individual calculation, but it does not provide a persistent simulation-wide random system.

The engine needs independently managed random streams with persisted states.

## 5.5 No complete knowledge model

The existing event-delivery model provides a useful first information boundary.

However, the architecture requires a much broader distinction between:

- Authoritative truth.
- Observation.
- Measurement.
- Estimation.
- Inference.
- Belief.
- Unknown information.

This needs to become a shared system used by all relevant domains.

## 5.6 No complete domain interaction mechanism

The current calculators do not automatically affect each other.

Energy production does not drive industrial capacity.

Industrial capacity does not consume material inventories.

Resource depletion does not constrain construction.

These interactions need to emerge from shared state and domain update rules.

---

# 6. GUI Gap Analysis

**Files:**
- `inspector/proxy.py`
- `inspector/static/index.html`

**Status: Working prototype**

The current interface has three top-level tabs:

1. Simulation.
2. Narrator.
3. Civilization.

It already provides:

- Live model activity.
- Reasoning and response streaming where supplied by the inference server.
- Tool-call streaming.
- A civilization status area.
- A file viewer.
- Narrator tool execution.
- Pending action approval.
- Civilization activation.
- Civilization inspection.
- Known-event inspection.
- Action proposals.
- Turn completion.

The inspector also has a bounded event queue to prevent unlimited buffering.

## 6.1 Missing GUI components

| Planned feature | Current state |
|---|---|
| Main control room | Partial |
| Live reasoning stream | Partial |
| Live tool-call stream | Partial |
| Tool results in activity stream | Not fully integrated |
| Civilization list and detailed inspection | Partial |
| Full civilization modification | Missing |
| 2D map of 3D universe | Missing |
| Contextual object inspection | Missing |
| Start/pause/suspend/terminate | Missing |
| Dedicated calculator page | Missing |
| Device usage monitor | Missing |
| Graphical file picker | Missing |
| Markdown and LaTeX rendering | Missing |
| Syntax-highlighted code | Missing |
| Dedicated live log | Missing |
| Structured log persistence | Missing |

The current file viewer accepts a manually entered file path and displays its contents as text. It is not yet the planned graphical file browser and document viewer.

The current activity stream receives inference events through the proxy, including tokens, reasoning, and tool-call fragments. It does not yet constitute the complete structured execution stream described in the architecture.

## 6.2 Recommendation

Do not begin the complete GUI overhaul yet.

The interface should eventually represent actual backend domain state.

Building elaborate inspection panels before the underlying state model exists would create unnecessary rework.

The current inspector should remain usable as a development and debugging interface while the simulation backend is expanded.

---

# 7. Testing Gap Analysis

The repository already has a substantial test foundation.

Existing test areas include:

- Civilization resources.
- Civilization APIs.
- Civilization knowledge.
- MCP tool registration.
- Economics.
- Physics.
- Relativistic calculations.
- Technology calculators.
- Agent state.
- Agent lifecycle.
- Tool-call journaling.
- Persistence.
- Inspector proxy behavior.

The previously recorded local baseline was:

**200 passed.**

That result is historical; the current GitHub repository was inspected read-only, and its tests were not executed again during this audit.

## 7.1 Missing test categories

The architecture requires additional coverage for:

### Domain simulation

- Population cohort updates.
- Energy accounting.
- Material conservation.
- Industrial production constraints.
- Infrastructure degradation.
- Agricultural production.
- Ecological interactions.

### Cross-domain integration

- Energy shortage affecting industry.
- Material shortage delaying construction.
- Environmental changes affecting agriculture.
- Industrial activity generating waste heat.
- Logistics limiting resource availability.
- Communications delays affecting knowledge.

### Time and scheduling

- Local civilization time versus universe time.
- Large time advances.
- Multiple scheduled civilizations.
- Events arriving during long time advances.
- Domain-specific update frequencies.
- Correct handling of events at the same timestamp.

### Randomness

- Independent random streams.
- Seed reproducibility.
- Random state persistence.
- Continuation after restart.
- Unrelated random calls not affecting other domains.

### Information boundaries

- Unknown objects remain unknown.
- Other civilizations' private state is inaccessible.
- Signals cannot be understood before processing.
- Knowledge does not update automatically.
- Narrator-only information is not exposed.

### Runtime and recovery

- Pause during an active turn.
- Suspension at a safe boundary.
- Runtime handoff.
- Stale tool-call rejection.
- Interrupted LLM requests.
- Uncertain tool-call recovery.

### Fresh-process persistence

A dedicated integration test must save a simulation, terminate the original process, load it in another process, and verify that it continues correctly.

---

# 8. Recommended Implementation Order

The architecture document contains a broad implementation roadmap. Based on the actual repository, I recommend the following more concrete sequence.

The intention is to preserve existing functionality while building the missing foundations in a controlled order.

## Phase 1 — Finalize the authoritative civilization model

**Goal:** Replace the current five-field resource representation with a structured foundation capable of supporting the 19 domains.

Work:

1. Review the existing `Civilization` and `CivilizationResources` classes.
2. Define the authoritative civilization state.
3. Establish domain boundaries.
4. Define variable units and accounting rules.
5. Define the distinction between internal state and civilization-facing summaries.
6. Establish operator modification semantics.
7. Preserve compatibility with existing save data where practical.

Do not implement all 19 domains in this phase.

The objective is to establish a sound state structure that can support them.

**Completion condition:** The civilization model can represent the required state without forcing unrelated domains into one flat resource object.

## Phase 2 — Establish simulation time and update mechanics

**Goal:** Make time advancement meaningful and correct.

Work:

1. Correct the global/local wake-time relationship.
2. Define the simulation's internal time representation.
3. Establish event scheduling.
4. Define domain update interfaces.
5. Establish update frequencies.
6. Implement safe advancement to the next relevant event or update.
7. Ensure large time advances process intermediate simulation activity.

The current universe clock rounds to tenths of a year. This is insufficient for the planned daily and monthly processes.

The internal time representation must support the finest required temporal resolution without making long-duration simulation impractical.

**Completion condition:** Advancing time produces correct state changes and respects scheduled events and civilization wake times.

## Phase 3 — Implement shared simulation mechanics

**Goal:** Create the reusable foundation for all domains.

Implement:

1. Stock-and-flow accounting.
2. Capacity and constraints.
3. Network foundations.
4. Projects and processes.
5. Uncertainty and knowledge representation.
6. Independent stochastic streams.
7. Shared event scheduling and domain update integration.

These mechanisms should be developed and tested before large domain implementations.

**Completion condition:** At least two different domain models can use the same shared mechanisms without duplicating their core logic.

## Phase 4 — Implement the first connected civilization systems

**Goal:** Establish a scientifically meaningful civilization simulation.

Recommended starting systems:

1. Demographics.
2. Energy.
3. Materials.
4. Industry.
5. Infrastructure.
6. Thermodynamics.

These systems form a particularly important connected foundation.

For example:

- Population influences demand.
- Energy supports production.
- Industry consumes materials and energy.
- Materials constrain manufacturing.
- Infrastructure provides distribution and production capacity.
- Energy-consuming activity generates waste heat.

These interactions should be tested together.

**Completion condition:** A civilization can undergo meaningful resource and industrial changes over simulated time, with consequences determined by the engine.

## Phase 5 — Expand physical and environmental systems

Implement:

1. Astronomy.
2. Biology and health.
3. Food and agriculture.
4. Ecology and environment.

The astronomy model establishes the physical environment.

The remaining systems establish the biological and environmental constraints under which civilizations operate.

**Completion condition:** A civilization's population and resource conditions can respond to its physical environment.

## Phase 6 — Expand civilization organization and capabilities

Implement:

1. Technology and science.
2. Economy and trade.
3. Logistics and transportation.
4. Information and communication.
5. Exploration and expansion.
6. Governance and institutions.
7. Society and culture.
8. Military and security.
9. Risk and resilience.

These systems should build on the earlier physical foundations.

Risk and resilience should remain cross-cutting rather than becoming an isolated simulation subsystem.

**Completion condition:** Civilizations can make meaningful strategic decisions, undertake projects, communicate, explore, and interact while facing realistic constraints.

## Phase 7 — Complete civilization runtime and MCP

**Goal:** Connect the complete simulation to the civilization agents.

Work:

1. Review existing runtime behavior.
2. Implement the complete tool-call cycle.
3. Bind tool execution to civilization identity.
4. Implement safe turn completion.
5. Implement pause.
6. Implement suspension.
7. Implement termination.
8. Complete automatic scheduling and handoffs.
9. Implement recovery of interrupted work.

The existing MCP tools should be expanded as domain systems become available.

Do not create placeholder tools for systems that do not exist yet.

**Completion condition:** Multiple civilizations can independently operate through one LLM runtime without violating identity, scheduling, or information boundaries.

## Phase 8 — Complete persistence

**Goal:** Make the simulation reliably resumable.

Work:

1. Extend the persistence schema.
2. Save every authoritative domain state.
3. Save random generator states.
4. Save events and scheduled updates.
5. Save civilization knowledge.
6. Save agent state.
7. Save tool-call execution state.
8. Implement safe recovery.
9. Test fresh-process continuation.

**Completion condition:** A saved simulation can be resumed in a completely new process and continue correctly.

Persistence should be developed alongside the new state systems rather than postponed until the very end.

## Phase 9 — Complete the GUI

**Goal:** Replace the current prototype layout with the planned interface.

Implement:

1. Main control room.
2. 3D universe map with 2D projection.
3. Civilization and object inspection.
4. Simulation controls.
5. Calculator page.
6. Device usage monitor.
7. Full file viewer.
8. Structured and human-readable logging.

**Completion condition:** The GUI can inspect and control the actual simulation without implementing its own simulation logic.

## Phase 10 — Final validation and first run

Test:

- All domain systems.
- Cross-domain interactions.
- Long-duration simulation.
- Information boundaries.
- Stochastic reproducibility.
- Runtime lifecycle.
- Fresh-process persistence.
- GUI behavior.
- Performance.

Only after these tests should the first serious simulation run begin.

---

# 9. Existing Code: Preserve, Extend, or Replace

The following summarizes how the current implementation should be treated.

| Existing component | Recommendation |
|---|---|
| `Position` | Preserve and extend |
| `Universe` | Extend substantially |
| `Event` | Preserve basic event model; expand event system |
| `Civilization` | Redesign and expand |
| `CivilizationResources` | Replace flat representation with structured domain state |
| `CivilizationScheduler` | Preserve core concepts; correct temporal behavior and expand orchestration |
| `narrator/physics.py` | Preserve useful calculators; integrate into domain models |
| `narrator/economics.py` | Preserve useful calculations; expand into economic systems |
| `narrator/technology.py` | Redesign as a research and innovation system |
| `narrator/data.py` | Expand inspection and knowledge functionality |
| `narrator/world.py` | Preserve world operations; expand modification mechanisms |
| `narrator/registry.py` | Preserve consolidated toolbox approach |
| `civilization_mcp.py` | Expand as domain capabilities become available |
| `narrator/agents.py` | Extend for complete lifecycle and recovery |
| `narrator/runtime.py` | Expand substantially |
| `narrator/persistence.py` | Extend schema and recovery behavior |
| `inspector/proxy.py` | Preserve streaming foundation and expand event types |
| `inspector/static/index.html` | Overhaul after backend capabilities stabilize |

A complete rewrite is not justified by the current gaps.

The existing project already contains useful code and tested behavior.

---

# 10. Critical Issues to Resolve Before Large-Scale Implementation

These should be addressed before expanding the simulation substantially.

| Issue | Why it matters | Required resolution |
|---|---|---|
| Global/local time mismatch | Can cause civilizations to wake at incorrect times | Define absolute wake timestamps |
| Coarse universe time resolution | Cannot accurately support daily/monthly systems | Establish finer internal time representation |
| No domain update engine | Time advancement does not simulate civilization development | Implement shared update orchestration |
| Flat civilization state | Cannot support the planned domains cleanly | Establish structured authoritative state |
| Strict resource validation | Conflicts with operator-defined unusual states | Separate representation from physical validity |
| No shared stock-flow system | Risks inconsistent resource accounting | Implement reusable accounting |
| No persistent RNG streams | Prevents reliable stochastic continuation | Implement and persist independent streams |
| Incomplete knowledge model | Limits scientific discovery and information security | Implement shared epistemic state |
| Incomplete runtime lifecycle | Cannot safely pause or suspend agents | Implement explicit runtime controls |
| No complete fresh-process recovery | Long-running simulations cannot be reliably resumed | Implement process-level continuation tests |

---

# 11. Recommended Immediate Development Target

The next implementation target should be:

## Phase 1: Authoritative Civilization Model

Before writing the new model, its structure should be designed and agreed upon.

The design should answer:

1. What is the top-level structure of a civilization?
2. Which domains own which state?
3. Which quantities are stocks, flows, capacities, or derived values?
4. How are units represented?
5. Which values are authoritative?
6. Which values are derived?
7. Which information belongs to civilization knowledge rather than authoritative state?
8. How does the human operator modify arbitrary state?
9. How are civilization-facing summaries generated?
10. How will the model be persisted and versioned?

The existing five resource variables should not simply be expanded into a much larger flat list.

Instead, the model should be organized around domain ownership and shared simulation mechanisms.

The first actual simulation systems should then be developed against that model.

---

# 12. Final Assessment

The current project is not starting from zero.

It already has a useful foundation for:

- Spatial representation.
- Civilization identity and lifecycle.
- Event propagation.
- Scheduling.
- LLM communication.
- MCP tool access.
- Narrator operations.
- Persistence.
- GUI inspection.

The missing work is primarily the transition from a framework that can represent and control civilizations into an engine that can actually simulate them.

The most important development principle is:

**Build the shared mechanics once, then let the civilization domains use them to produce consistent consequences.**

The project should avoid implementing 19 disconnected systems or exposing hundreds of independent statistics.

It should maintain detailed internal models, present compact decision-relevant summaries, and allow civilizations to investigate further through tools.

The recommended immediate next step is to finalize the authoritative civilization state model, with temporal semantics and shared accounting requirements defined alongside it.

That will provide the foundation for the rest of the simulation without forcing major architectural restructuring later.
