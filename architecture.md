Dark Forest Sim
Simulation Architecture Specification

Status: Proposed architecture
Purpose: Establish the scientific, technical, and structural foundations of the simulation.

1. Project Vision

Dark Forest Sim is a scientifically grounded civilization simulation in which large language models control individual civilizations.

The universe contains physical objects, resources, environments, and civilizations. Each civilization develops independently, makes decisions using its available knowledge, and experiences the consequences of its actions.

The fundamental principle is:

The LLM decides what a civilization attempts.
The simulation engine determines what actually happens.

An LLM cannot simply declare that it has constructed a spacecraft, discovered technology, or established a colony. It must satisfy the necessary physical, technological, economic, industrial, and logistical requirements.

Civilizations can make mistakes, pursue inefficient strategies, misunderstand information, and make disastrous decisions. The engine should not protect them from the consequences of their decisions.

If a civilization collapses because of poor resource management, political instability, environmental destruction, or military miscalculation, that is a legitimate simulation outcome.

The objective is emergent civilization development rather than predetermined storytelling.

1.1 Governing Principles
Physical consistency and conservation of resources.
Causal interactions between simulation systems.
Independent civilization decision-making.
Strict separation between authoritative reality and civilization knowledge.
Reproducible stochastic processes.
Scientifically defensible approximations.
Persistent, recoverable simulation state.
Decision-oriented information rather than overwhelming statistics.
Meaningful consequences without artificial protection from failure.
Modular architecture that supports future expansion.
2. Overall Architecture

The simulation should use cooperating architectural layers rather than 19 independent engines.

2.1 Core Components
Simulation Engine

Responsible for simulation time, event scheduling, physical calculations, stochastic processes, domain updates, conservation accounting, persistence, and orchestration.

World Model

Maintains the authoritative physical universe, including spatial structure, stars, planets, resources, environments, and physical events.

Civilization Model

Maintains each civilization's actual population, resources, technology, infrastructure, economy, institutions, and activities.

Civilization Runtime

Manages LLM execution, context preparation, tool calls, civilization switching, turn completion, and interruption recovery.

Only one civilization should occupy the active LLM runtime at a time.

Knowledge System

Maintains what each civilization has observed, discovered, received, calculated, or inferred.

Interface Layer

Provides world inspection, civilization management, simulation controls, narrator interaction, execution logs, and visualization.

The interface must never become the authority for simulation logic.

3. Authoritative State and Civilization Knowledge

A strict distinction must exist between physical truth and subjective knowledge.

3.1 Authoritative State

The engine maintains the actual state of the universe and every civilization.

Examples include:

Actual astronomical properties.
Resource deposits.
Environmental conditions.
Population and infrastructure.
Technological capabilities.
Spacecraft positions.
Signal transmissions.
Active projects and events.

Civilizations cannot automatically access this information.

3.2 Subjective State

Each civilization maintains its own understanding of reality.

This includes:

Known objects and locations.
Scientific discoveries.
Observations and measurements.
Estimates and uncertainty.
Beliefs and hypotheses.
Strategic objectives.
Historical records.
Perceived threats and relationships.

Civilizations may have incorrect beliefs or outdated information.

These errors should influence their decisions naturally.

3.3 State Modification

Normal civilization actions must follow this process:

The LLM proposes an action.
The engine validates permissions and prerequisites.
Resources and capabilities are evaluated.
The engine determines whether the action can proceed.
Projects or immediate operations are created.
The engine calculates actual consequences.
Relevant results become available to the civilization.

The LLM must never directly modify authoritative state.

The human operator and authorized narrator tools may have separate modification permissions.

4. Shared Simulation Mechanics

The 19 domains should reuse common mechanisms wherever possible.

4.1 Stocks and Flows

Physical and economic quantities should use explicit accounting.

S_next = S_current + inflows - outflows

Examples include population, energy reserves, materials, water, food, and fuel.

Conservation rules must be defined for relevant quantities.

Recycling must account for recovery efficiency and losses.

4.2 Capacity and Constraints

Systems should distinguish:

Installed capacity.
Available capacity.
Utilization.
Demand.
Unmet demand.
Maintenance.
Operating limitations.

Installed capacity must not be confused with actual operational capability.

4.3 Networks

Use a shared graph foundation:

G = (V, E)

It should support infrastructure, transportation, energy distribution, communications, trade, and other connected systems.

Edges may have capacity, distance, travel time, reliability, cost, and restrictions.

Individual domains implement their own network behavior.

4.4 Projects and Processes

Major activities should use a common project system.

Examples include construction, research, exploration, spacecraft production, and settlement establishment.

Projects require:

Objectives.
Prerequisites.
Resources.
Capabilities.
Production capacity.
Progress.
Duration.
Dependencies.
Failure conditions.

Projects must progress according to actual available resources and constraints.

4.5 Uncertainty

Information should distinguish exact values, observations, estimates, inferences, hypotheses, and unknowns.

Measurements should support confidence, uncertainty, source, and observation time.

4.6 Stochastic Processes

Randomness must use reproducible, independently managed random streams.

Separate streams should exist for demographics, biology, ecology, environmental events, technology, and other stochastic systems.

Persist seeds, algorithms, configurations, and generator states.

5. Spatial and Temporal Models
5.1 Spatial Model

The universe must use genuine three-dimensional coordinates (X, Y, Z).

The interface may display two-dimensional projections.

Support hierarchical spatial representation:

Galaxy.
Galactic regions.
Stellar systems.
Stars.
Planets and moons.
Planetary regions.
Settlements.
Facilities and strategic assets.

Galaxy generation should use astrophysically reasonable distributions rather than uniform random placement.

For example, a simplified stellar disk can use:

ρ(R,z) ∝ exp(-R/Rd) exp(-|z|/zd)

Perlin noise may introduce correlated variation but must not replace physical models.

5.2 Temporal Model

Use event-driven scheduling combined with domain-specific update frequencies.

Different systems operate at different timescales:

System	Typical resolution
Communications	Event-driven
Spacecraft	Continuous/event-driven
Weather	Daily
Agriculture	Daily/seasonal
Industry	Daily/monthly
Infrastructure	Monthly/yearly
Demographics	Annual
Ecology	Monthly/yearly
Technology	Monthly/yearly
Culture	Generational

These are guidelines, not rigid requirements.

Large time advances must process intermediate events and domain updates rather than skipping directly to the destination.

5.3 Civilization-Local Time

Each civilization maintains its own local integer year.

Its local year advances when it wakes and takes its turn.

Sleeping civilizations do not automatically advance their local clocks when global simulation time progresses.

This behavior must remain consistent throughout scheduling and persistence.

6. The 19 Simulation Domains

The domains represent interconnected aspects of civilization. They are not independent engines.

Each domain must document its scientific foundation, assumptions, variables, units, update frequency, stochastic behavior, and limitations.

1. Demographics

Population cohorts, fertility, mortality, migration, births, and deaths. Use cohort-component models and appropriate stochastic processes.

2. Biology and Health

Species biology, nutrition, disease, injuries, health conditions, epidemiology, and medical capabilities. Support models such as SIR and SEIR where appropriate.

3. Food and Agriculture

Crop production, agricultural land, soil, nutrients, freshwater, storage, spoilage, and food security. Production must depend on environmental and industrial conditions.

4. Energy

Generation, storage, distribution, consumption, fuel requirements, conversion efficiency, and transmission losses. Distinguish power (W) from energy (J).

5. Materials and Resources

Resource deposits, extraction, processing, inventories, recycling, reserves, and waste. Distinguish geological resources from economically recoverable reserves and available inventory.

6. Industry and Manufacturing

Factories, production lines, machinery, labor, energy, materials, throughput, maintenance, and manufacturing constraints.

7. Infrastructure

Buildings, facilities, transportation networks, power grids, communication infrastructure, degradation, maintenance, repair, and expansion.

8. Technology and Science

Scientific knowledge, theoretical designs, engineering, prototypes, manufacturing capability, and deployment. Research must depend on prerequisites, capacity, resources, and time.

9. Astronomy and Planetary Systems

Galactic structure, stars, planetary systems, orbital mechanics, stellar evolution, planetary environments, and geological properties. Maintain consistency between related astronomical properties.

10. Thermodynamics

Energy conversion, waste heat, thermal storage, cooling, and radiative dissipation.

Use appropriate thermodynamic relationships, including:

P = εσAT⁴

Waste heat must emerge from actual energy-consuming processes.

11. Ecology and Environment

Ecosystems, biomass, biodiversity, water, nutrients, soil, pollution, environmental conditions, and resource regeneration.

Distinguish physical environment, living ecosystems, and extractable natural resources.

12. Economy and Trade

Production, consumption, allocation, investment, markets, financial systems, and trade.

Distinguish the physical economy from the financial economy. Money cannot create physical resources.

Trade requires actual goods, transportation, and delivery.

13. Logistics and Transportation

Transportation networks, vehicles, spacecraft, shipments, routes, capacity, fuel, travel time, and reliability.

Spacecraft propulsion must respect mass, energy, fuel, and applicable physical constraints.

14. Governance and Institutions

Political systems, authority, administration, laws, enforcement, factions, legitimacy, corruption, and institutional capacity.

Avoid reducing governance to a single stability score.

15. Society and Culture

Social groups, relationships, beliefs, traditions, education, language, cooperation, competition, inequality, and cultural evolution.

Do not assume every member of a civilization shares identical beliefs.

16. Military and Security

Military assets, readiness, defense, intelligence, detection, sustainment, logistics, maintenance, and industrial support.

Distinguish nominal capability from actual readiness and operational capability.

17. Information and Communication

Signal transmission, propagation, detection, reception, decoding, interpretation, bandwidth, noise, and information processing.

Communication must respect physical propagation delays.

18. Exploration and Expansion

Surveys, probes, exploration missions, discoveries, resource assessments, settlement projects, and expansion.

Discovery must update civilization knowledge rather than authoritative physical reality.

19. Risk and Resilience

Reliability, redundancy, reserves, vulnerabilities, correlated failures, cascading consequences, and recovery capabilities.

This is a cross-domain framework rather than an independent collection of arbitrary statistics.

7. Domain Interactions

Domains must interact through actual mechanisms.

Examples:

Energy shortages reduce industrial production.
Industrial shortages delay infrastructure maintenance.
Material shortages delay construction.
Environmental degradation reduces agricultural productivity.
Population changes affect consumption and labor.
Governance affects resource allocation.
Infrastructure failures disrupt logistics and communications.
Exploration produces discoveries that can influence scientific research.
Waste heat emerges from energy consumption.
Military capability depends on industrial production and logistical support.

Cascading failures should emerge naturally.

For example:

Drought → freshwater shortage → agricultural disruption → food shortage → health decline → population consequences → political instability.

The engine should model the underlying mechanisms rather than manually scripting the entire chain.

8. Civilization Actions and Tools

Civilizations interact with the engine through scoped tools.

Organize tools into:

Inspection.
Calculation.
Knowledge acquisition.
Action proposals.
Action execution.
Time advancement.

Inspection exposes decision-relevant information.

Calculation tools provide hypothetical results without modifying authoritative state.

Action proposals are validated by the engine.

Rejected, delayed, constrained, or partially completed actions must return understandable explanations.

Every tool call must be bound to an explicit civilization identity and runtime session.

Stale calls must never execute under another civilization's permissions.

9. Civilization Runtime and Scheduling

Only one civilization should actively use the LLM runtime at a time.

The scheduler selects eligible civilizations and manages their turns.

Turn Lifecycle
Select civilization.
Update its local year.
Prepare its available context.
Activate its runtime identity.
Invoke the LLM.
Process tool calls.
Validate and execute actions.
Complete or interrupt the turn.
Persist resulting state.
Release the runtime.
Select the next civilization.
Runtime Controls

Pause: Allow the current turn to finish, then stop automatic scheduling.

Suspend: Interrupt at a safe boundary, preserve context and pending work, and release the runtime.

Terminate: Save complete state and shut down the runtime. Require pausing or suspending first.

Tool execution must track:

Pending.
Executing.
Completed.
Failed.
Uncertain.

Uncertain operations must not be blindly repeated after recovery.

10. Persistence and Recovery

Persistence is a foundational requirement.

Save:

World state.
Civilization state.
Simulation and local time.
Domain state.
Knowledge and observations.
Active projects.
Event queue.
Scheduler state.
Random generator states.
Simulation configuration.
Agent context.
Tool-call journal.
Recovery information.

All persistent schemas must be versioned.

Required Continuation Test
Create a simulation.
Advance it.
Save it.
Destroy the original process.
Start a fresh process.
Load the simulation.
Restore events, scheduler, domains, and random streams.
Recover interrupted operations.
Resume execution.
Verify continued correctness.

An interrupted LLM request must never be falsely treated as completed.

11. Civilization-Facing Information

The normal civilization context should remain compact.

Prioritize:

Overall condition.
Population trends.
Energy availability.
Important material constraints.
Industrial and infrastructure conditions.
Technological capabilities.
Environmental pressures.
Political and social developments.
Active projects.
Relevant discoveries and external observations.
Immediate opportunities and threats.

Detailed information should be available through inspection tools.

Forecasts and hypothetical scenarios must remain separate from authoritative state.

The objective is to give civilizations enough information to make meaningful decisions without overwhelming their context.

12. Narrator and Human Operator

The narrator is a separate actor with access to authoritative world information.

It may:

Inspect the universe.
Inspect civilizations.
Modify world conditions.
Create events.
Control simulation time.
Inspect calculations.
Review execution history.
Manage simulation settings.

Separate narrator tools into:

World Modification: Authorized changes to authoritative state.

Mathematics and Data: Read-only inspection and calculations.

Narrator permissions must never transfer to civilization agents.

Human modifications should be logged.

13. Logging and Observability

Maintain two complementary logging systems.

Structured Logs

Record timestamps, simulation time, civilization identity, events, tool calls, arguments, results, state changes, errors, and runtime transitions.

Human-Readable Logs

Present understandable simulation activity rather than raw JSON.

The live control room should eventually display LLM responses, tool calls, results, errors, action proposals, runtime transitions, and civilization handoffs.

14. Scientific Fidelity and Model Selection

Every model must document:

What it represents.
Governing equations or mechanisms.
Assumptions.
Inputs and outputs.
Units.
Update frequency.
Stochastic behavior.
Limitations.

Avoid false precision.

Stored numerical precision must not be confused with actual scientific certainty.

The operator must be able to introduce unusual or physically implausible values without silent correction.

Distinguish:

Structurally representable state.
Physically plausible state.
Computationally operable state.

If a calculation cannot operate under the supplied conditions, report the problem explicitly rather than silently clamping values.

15. Implementation Roadmap

Implementation should proceed incrementally.

Stage 1 — Civilization Representation

Establish authoritative civilization state, domain boundaries, units, accounting rules, and civilization-facing summaries.

Stage 2 — Runtime and Scheduling

Implement civilization switching, identity isolation, turn lifecycle, pause, suspension, termination, and interruption handling.

Stage 3 — Civilization Tools

Implement inspection, calculations, knowledge acquisition, action proposals, validation, and information boundaries.

Stage 4 — Shared Mechanics

Implement stock-flow accounting, capacity, networks, projects, uncertainty, stochastic streams, and event scheduling.

Stage 5 — Domain Simulation

Implement the 19 domains, prioritizing interconnected foundations such as energy, materials, industry, infrastructure, astronomy, and ecology.

Stage 6 — Persistence

Implement complete state saving, fresh-process loading, deterministic continuation, and interrupted-operation recovery.

Stage 7 — GUI

Build five main pages:

Control Room: Live execution, civilizations, world map, inspection, and controls.
Calculator: Categorized physical and mathematical tools.
Device Monitor: Hardware and model usage.
File Viewer: Markdown, LaTeX, code, JSON, and text.
Live Log: Human-readable activity and structured records.
Stage 8 — Final Validation

Audit scientific consistency, information boundaries, conservation, domain interactions, persistence, runtime recovery, and performance.

Stage 9 — First Simulation

Run an extended simulation as a validation exercise.

Observe civilization decisions, physical consequences, emergent behavior, performance, and unexpected interactions.

16. Testing Strategy

Testing must cover individual mechanisms and complete simulation behavior.

Unit Tests

Physical calculations, accounting, resource flows, signal propagation, travel, projects, and random streams.

Domain Tests

Verify that individual systems behave according to their documented assumptions.

Integration Tests

Verify cross-domain consequences such as energy shortages, agricultural disruption, infrastructure failures, and technological development.

Information-Boundary Tests

Ensure civilizations cannot access undiscovered objects, private foreign state, unreceived communications, or narrator-only information.

Runtime Tests

Verify scheduling, identity isolation, pause, suspension, termination, and interrupted-operation recovery.

Persistence Tests

Verify actual continuation in a fresh process.

Long-Duration Tests

Identify numerical instability, accounting errors, event accumulation, performance degradation, and state corruption.

17. Decisions Requiring Further Specification

The following should be decided through requirements and performance testing rather than arbitrary assumptions.

Universe Scale

Local stellar neighborhood, galactic region, entire galaxy, or larger abstract universe.

Civilization Complexity

Population resolution, infrastructure aggregation, industrial detail, and social representation.

Performance Budget

Number of civilizations, stellar systems, active events, projects, and detailed objects.

Biological Generality

Define the initial species-independent biological abstraction without prematurely building an unnecessarily universal biology engine.

Economic and Social Generality

Support different civilization structures without assuming every civilization resembles modern human societies.

18. Final Architectural Rules
The engine is authoritative over physical reality.
LLMs make decisions; the engine determines consequences.
Civilization knowledge is separate from world truth.
No civilization receives information it has not legitimately acquired.
Physical quantities obey applicable conservation rules.
Shared mechanisms should be implemented once and reused.
Domains interact through causal mechanisms.
Different domains may use different temporal resolutions.
Randomness must be reproducible and independently managed.
Persistence must support fresh-process continuation.
Interrupted operations must never be silently treated as completed.
Operator modifications must not silently clamp unusual values.
Hypothetical forecasts must remain separate from authoritative state.
Civilization-facing information should prioritize useful decisions.
Detailed information should be accessible through investigation tools.
Models must document assumptions and limitations.
Scientific complexity should be introduced when it improves simulation behavior.
Avoid arbitrary scores that conceal important underlying variables.
Avoid disconnected domain-specific implementations.
Every major feature must be independently and collectively testable.
Conclusion

Dark Forest Sim should be built as a unified simulation engine with shared physical, computational, and organizational mechanisms.

Its foundation consists of:

An authoritative three-dimensional universe.
Structured civilization models.
Shared physical and organizational mechanisms.
Reproducible event and stochastic systems.
Strict information boundaries.
A controlled multi-civilization runtime.
Reliable persistence and recovery.
Decision-oriented interfaces.

The objective is not to simulate every conceivable detail of a civilization.

It is to simulate enough of its physical, biological, economic, technological, and organizational reality that decisions have meaningful consequences.

Civilizations should be free to succeed, fail, stagnate, prosper, or disappear through the natural consequences of their actions and circumstances.
