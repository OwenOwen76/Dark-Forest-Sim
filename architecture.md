# Dark Forest Sim
## Simulation Architecture Specification

**Status:** Proposed architecture  
**Purpose:** Define the scientific, technical, and structural foundations of the simulation before expanding its implementation.

---

# 1. Project Vision

Dark Forest Sim is a scientifically grounded civilization simulation in which large language models control the decisions of individual civilizations.

The simulation should represent a universe containing physical objects, resources, environments, and civilizations. Each civilization develops independently, makes decisions based on its available knowledge, and experiences the consequences of its actions.

The central division of responsibility is:

- **The LLM decides what a civilization attempts to do.**
- **The simulation engine determines what actually happens.**

A civilization cannot simply declare that it has constructed a spacecraft, discovered a technology, conquered another civilization, or established a colony. It must possess the necessary resources, technology, infrastructure, industrial capacity, and time.

For example, a civilization might propose constructing 20 GW of additional generating capacity. The engine must determine whether it has sufficient materials, manufacturing capacity, energy, labor, and infrastructure. It must also account for construction time, operating requirements, and waste heat.

This principle applies throughout the simulation.

The intended result is an emergent universe in which civilizations develop through their decisions and interactions with physical reality, rather than through predetermined narratives or arbitrary roleplaying outcomes.

## 1.1 Primary objectives

The simulation should:

1. Maintain a consistent and authoritative physical universe.
2. Model civilizations using scientifically grounded systems.
3. Enforce physical, economic, technological, and logistical constraints.
4. Support independent civilization decision-making through LLM agents.
5. Preserve information boundaries between civilizations.
6. Support meaningful interactions between simulation domains.
7. Model uncertainty, incomplete knowledge, and stochastic events.
8. Support long-running simulations across different timescales.
9. Allow complete saving, loading, and continuation in a fresh process.
10. Provide enough information for civilizations to make meaningful decisions without overwhelming them with unnecessary statistics.

## 1.2 Governing principles

### Physical consistency

Physical quantities must obey their applicable conservation laws and constraints.

Energy, mass, resources, and information cannot simply appear because an agent requests them.

### Causal interactions

Simulation systems must interact through actual mechanisms.

For example:

Energy shortage → industrial production reduction → material shortages → infrastructure delays → agricultural disruption → population consequences.

These consequences should emerge from the underlying systems rather than being manually scripted as a narrative chain.

### Scientific transparency

Every major model should document:

- Its scientific foundation.
- Its assumptions.
- Its limitations.
- Its resolution.
- Its update frequency.
- Its stochastic components.

Scientific fidelity will vary depending on the system. The goal is a coherent and defensible approximation, not an unnecessarily expensive simulation of every physical process.

### Information separation

The engine knows the authoritative state of the universe.

Civilizations only know what they have discovered, observed, calculated, received, or reasonably inferred.

A civilization must never receive information simply because the engine possesses it.

### Decision-oriented information

The simulation can maintain considerable internal detail, but civilization-facing information should remain relatively compact.

Every exposed statistic should answer a practical question:

**What decision does this information help the civilization make?**

If a variable does not help a civilization make a decision, it should generally remain internal or be omitted from its normal summaries.

---

# 2. Overall Architecture

The simulation should be organized into several cooperating layers rather than 19 independent simulation engines.

## 2.1 Architectural layers

### A. Simulation Engine

Responsible for:

- Authoritative world state.
- Simulation time.
- Event scheduling.
- Stochastic processes.
- Physical calculations.
- Domain updates.
- Conservation accounting.
- Runtime orchestration.
- Persistence and recovery.

The engine is the ultimate authority on what has actually happened.

### B. World Model

Represents the physical universe independently of civilization knowledge.

Contains:

- Spatial structure.
- Stars and planetary systems.
- Physical environments.
- Resources.
- Environmental conditions.
- Physical events.
- Civilization locations.

The world model must not depend on what civilizations know about it.

### C. Civilization Model

Represents the authoritative state of each civilization.

Contains the systems necessary to describe its population, resources, infrastructure, technology, organization, and activities.

A civilization's authoritative state is maintained by the engine, not by its LLM.

### D. Civilization Runtime

Responsible for:

- Selecting the civilization that acts.
- Providing its available context.
- Managing its LLM interaction.
- Registering and executing its tools.
- Processing proposed actions.
- Managing turn completion.
- Suspending and resuming civilizations.
- Preventing cross-civilization execution errors.

Only one civilization should actively occupy the LLM runtime at a time.

### E. Knowledge and Information System

Maintains what each civilization knows about:

- Itself.
- Its surroundings.
- Other civilizations.
- Physical objects.
- Events.
- Technology.
- Communications.

Knowledge must be separate from authoritative world state.

### F. Interface and Control Layer

Provides the human operator with:

- Simulation controls.
- Civilization inspection.
- World inspection.
- Narrator interaction.
- Live execution streams.
- Direct world modification.
- Logs and persistence controls.

The interface should not become the authority for simulation logic.

---

# 3. Authoritative World and Civilization State

The simulation must maintain a clear distinction between physical truth and subjective knowledge.

## 3.1 Authoritative world state

The world state contains the exact simulation truth.

Examples include:

- Actual positions of stars and planets.
- Actual planetary properties.
- Actual resource deposits.
- Actual environmental conditions.
- Actual civilization locations.
- Actual civilization populations and capabilities.
- Actual signal transmissions.
- Actual spacecraft trajectories.
- Actual events and their outcomes.

This state is available to the simulation engine and authorized narrator operations.

It is not automatically available to civilization agents.

## 3.2 Authoritative civilization state

Each civilization has an authoritative state containing its actual condition.

This includes:

- Identity and location.
- Current local year.
- Population and demographic structure.
- Available resources.
- Energy systems.
- Industrial capacity.
- Infrastructure.
- Technology and engineering capabilities.
- Ecological and environmental conditions.
- Economic activity.
- Governance and institutions.
- Military and security capabilities.
- Active projects and missions.
- Internal events and historical records.

The exact internal representation may be considerably more detailed than the civilization's normal inspection summary.

## 3.3 Civilization subjective state

Each civilization separately maintains its own perspective.

This includes:

- Known objects and locations.
- Observations.
- Scientific knowledge.
- Estimates.
- Beliefs.
- Uncertainty.
- Strategic objectives.
- Plans.
- Relationships.
- Perceived threats.
- Historical understanding.

Subjective state must never overwrite authoritative physical truth.

A civilization can have an incorrect belief about another civilization, misunderstand a signal, or maintain outdated information about a previously observed location.

These errors are part of the simulation.

## 3.4 State modification

Normal civilization actions must pass through simulation rules.

The LLM cannot directly modify authoritative state.

Instead:

1. The civilization proposes an action.
2. The engine validates its authority and prerequisites.
3. The engine evaluates resource and capacity constraints.
4. The engine determines the resulting operation or project.
5. The simulation processes the consequences.
6. The civilization receives the resulting information according to its knowledge boundaries.

The human operator and authorized narrator tools may have separate mechanisms for directly modifying world state.

---

# 4. Shared Simulation Mechanics

The most important architectural decision is to implement reusable mechanisms that support multiple domains.

The simulation should not independently reinvent resource accounting, networks, projects, or uncertainty for every system.

## 4.1 Stocks and flows

Many simulation quantities are naturally represented as stocks that change through inflows and outflows.

General accounting:

`S_next = S_current + inflows - outflows`

Examples:

- Population.
- Energy reserves.
- Material inventories.
- Water reserves.
- Food inventories.
- Fuel.
- Stored information.

Every stock-flow model must define its accounting boundaries.

The engine should avoid creating or destroying conserved quantities without an explicit mechanism.

For example, recycling materials should recover some fraction of existing material, with the remainder accounted for as losses, waste, or unrecoverable material.

## 4.2 Capacity and constraints

A shared capacity model should represent the difference between what a system theoretically supports and what it can actually deliver.

Useful concepts include:

- Installed capacity.
- Available capacity.
- Utilization.
- Demand.
- Unmet demand.
- Operating constraints.
- Maintenance requirements.
- Bottlenecks.

A civilization might have 100 GW of installed generating capacity but only 75 GW available due to maintenance, damage, or fuel shortages.

The engine should calculate actual operation using the relevant constraints.

Capacity should not be represented as a single universal concept without defining what it means for each system.

## 4.3 Networks

A common graph foundation should support systems such as:

- Infrastructure.
- Transportation.
- Energy distribution.
- Communications.
- Trade.
- Social relationships.
- Military command.
- Industrial supply chains.

A network can be represented as:

`G = (V, E)`

Where:

- `V` represents nodes.
- `E` represents connections.

Connections may have properties such as:

- Capacity.
- Distance.
- Travel time.
- Energy requirements.
- Reliability.
- Operating cost.
- Restrictions.

Not every network needs identical behavior. The shared foundation should provide common structure while individual domains implement their own rules.

## 4.4 Projects and processes

Major civilization activities should use a reusable project/process mechanism.

Examples:

- Constructing a power plant.
- Developing a new propulsion system.
- Building a spacecraft.
- Establishing a settlement.
- Conducting scientific research.
- Constructing infrastructure.
- Surveying a planetary system.

A project should support:

- Objectives.
- Prerequisites.
- Required resources.
- Required capabilities.
- Production or construction capacity.
- Progress.
- Duration.
- Status.
- Dependencies.
- Failure conditions.
- Completion consequences.

Projects should not automatically succeed.

The engine determines their progress using actual available resources and capabilities.

## 4.5 Uncertainty and knowledge

The simulation should distinguish:

- Exact authoritative values.
- Direct observations.
- Measurements with error.
- Estimates.
- Inferences.
- Unverified hypotheses.
- Unknown information.

This mechanism should be reusable across astronomy, intelligence, exploration, economics, technology, and other domains.

## 4.6 Stochastic processes

Randomness should be a shared engine capability.

It must be reproducible and independently managed.

Different systems should use separate random streams so that unrelated random events do not change each other's outcomes.

Recommended streams include:

- Universe generation.
- Demographics.
- Biology.
- Ecology.
- Environmental events.
- Technology.
- Infrastructure failures.
- Other domain-specific stochastic processes.

The engine must persist the random seed, algorithm/version, configuration, and generator states.

---

# 5. Spatial Model

The universe is genuinely three-dimensional.

The interface may display a two-dimensional projection, but the underlying simulation must preserve all three spatial dimensions.

## 5.1 Coordinates

Positions should use:

- X.
- Y.
- Z.

Distances, travel, signal propagation, and spatial relationships must use all three dimensions.

The existing Euclidean distance approach is suitable for basic spatial calculations.

More advanced astronomical calculations can introduce additional coordinate systems where needed.

## 5.2 Spatial hierarchy

The world should support different levels of spatial detail:

1. Universe or galaxy.
2. Galactic regions.
3. Stellar systems.
4. Stars.
5. Planets and moons.
6. Planetary regions.
7. Settlements and facilities.
8. Individual strategic assets.

Not every object needs to be represented at maximum detail.

The simulation should use an appropriate spatial resolution for each domain.

For example, ordinary industrial facilities might be aggregated within a settlement, while strategically important spacecraft and interstellar colonies are represented individually.

## 5.3 Astronomical distribution

The universe should not be generated as a uniformly populated box if the intended setting is a galaxy.

A galaxy-like distribution should account for structures such as:

- Thin disk.
- Thick disk.
- Stellar halo.
- Central regions.
- Spatial density gradients.

A simplified stellar disk density model can use:

`rho(R, z) ∝ exp(-R / R_d) exp(-|z| / z_d)`

Where:

- `R` is radial distance from the galactic center.
- `z` is vertical displacement.
- `R_d` is a radial scale length.
- `z_d` is a vertical scale height.

The actual generation method should be selected after the universe's intended scale and astronomical fidelity are established.

## 5.4 Perlin noise

Perlin noise can be used to create correlated spatial variation.

Potential applications:

- Local density variation.
- Environmental variation.
- Resource distribution.
- Spatial clustering.

However, Perlin noise must not replace astrophysical models.

It is a tool for introducing correlated variation, not a physical law.

Different physical fields should use separate configurations, and generated values must remain consistent with the relevant physical constraints.

---

# 6. Temporal Model

The simulation contains processes operating over vastly different timescales.

A single universal update frequency would be inefficient and scientifically inappropriate.

## 6.1 Event-driven simulation

Events should be scheduled when something meaningful needs to occur.

Examples:

- A signal arrives.
- A spacecraft reaches a destination.
- Construction completes.
- A resource shipment arrives.
- A civilization wakes.
- A mission discovers an object.
- An infrastructure failure occurs.

Events should be processed according to simulation time.

## 6.2 Domain-specific update frequencies

Different systems require different temporal resolutions.

| Domain | Suggested resolution |
|---|---|
| Signals and communications | Event-driven |
| Spacecraft trajectories | Continuous or event-driven |
| Local weather | Daily |
| Agriculture | Daily or seasonal |
| Disease | Daily or monthly |
| Industrial production | Daily or monthly |
| Logistics | Event-driven or periodic |
| Infrastructure degradation | Monthly or yearly |
| Demographics | Annual |
| Ecology | Monthly or yearly |
| Technology research | Monthly or yearly |
| Governance | Decision-driven or periodic |
| Cultural evolution | Generational or long-term |
| Stellar evolution | Long timescales |

These are initial design guidelines, not rigid requirements.

## 6.3 Adaptive time advancement

A request to advance the simulation by a large amount of time must not simply skip all intermediate processes.

For example, advancing 1,000 years should account for:

- Population changes.
- Resource consumption.
- Industrial activity.
- Ecological changes.
- Construction and maintenance.
- Environmental events.
- Technological development.
- Arrivals and departures.
- Civilization wake schedules.

The engine should use event scheduling and appropriate domain-specific integration steps.

A large time advance may require many internal updates.

## 6.4 Civilization-local time

Each civilization maintains its own current local integer year.

Its local year advances when it wakes and experiences its turn.

It does not continuously update merely because the universe's global clock advances while it sleeps.

This distinction must be preserved throughout scheduling and persistence.

---

# 7. Stochastic Simulation and Reproducibility

Randomness is necessary for realistic population changes, environmental events, failures, and technological development.

However, randomness must be controlled.

## 7.1 Independent random streams

Unrelated systems must not share one global random sequence.

For example, an additional random draw in the technology system should not change the future demographic outcomes of a civilization.

Each system should have an independent generator or independently derived stream.

## 7.2 Reproducibility

A saved simulation must preserve:

- Original seed.
- Random algorithm and version.
- Generator states.
- Stochastic model configuration.
- Relevant domain state.

The engine should be able to continue from a saved state without silently restarting its random sequences.

## 7.3 Expected-value and stochastic modes

Where appropriate, models should support deterministic expected-value calculations as well as stochastic operation.

For example, population projections may calculate expected births and deaths, while actual simulation mode samples events.

The stochastic implementation should preserve the intended expected values.

Correlated shocks and overdispersion may be needed where independent random sampling would produce unrealistic outcomes.

---

# 8. Civilization Knowledge and Information Boundaries

Information separation is one of the most important features of Dark Forest Sim.

A civilization should not receive the universe's authoritative state through an accidental API leak.

## 8.1 Information categories

Information should distinguish at least:

- Known exactly.
- Directly observed.
- Detected but unidentified.
- Estimated.
- Inferred.
- Suspected.
- Unknown.

Information should also have relevant metadata:

- Source.
- Observation time.
- Confidence.
- Measurement uncertainty.
- Age or staleness.
- Whether it has been independently verified.

## 8.2 Knowledge progression

For communications and discoveries, a useful progression is:

1. Not observed.
2. Detected.
3. Classified.
4. Decoded.
5. Interpreted.
6. Understood and incorporated into beliefs.

Detection must not automatically imply understanding.

A civilization might detect an unusual signal but be unable to identify its source or meaning.

## 8.3 Information access rules

| Information | Civilization access |
|---|---|
| Own authoritative statistics | Exact |
| Own historical records | Exact, subject to retained records |
| Known physical objects | Observed or estimated |
| Undiscovered locations | Unknown |
| Other civilizations' resources | Unknown or estimated |
| Other civilizations' intentions | Never directly known |
| Other civilizations' technology | Inferred from observations |
| Signals | Only after physical detection and processing |
| Future events | Predictions, not authoritative truth |

The engine must enforce these boundaries at the tool and context-generation levels.

## 8.4 Knowledge changes

Knowledge should be updated through actual mechanisms:

- Observation.
- Measurement.
- Communication.
- Scientific investigation.
- Exploration.
- Intelligence gathering.
- Research.
- Inference.

A civilization's knowledge must not automatically update when the underlying world changes.

For example, discovering a planet's mineral deposits does not mean the civilization knows their exact quantities. It may need further surveys and measurements.

---

# 9. The 19 Simulation Domains

The following domains describe the systems that collectively represent a civilization and its environment.

They are not intended to become 19 isolated engines.

Each domain should use the shared mechanisms described earlier.

## 9.1 Demographics

**Purpose:** Model population size, structure, and change.

Scientific foundation:

- Cohort-component population models.
- Stochastic population forecasting.
- Age-dependent fertility and mortality.
- Migration accounting.

Internal representation:

- Age or developmental cohorts.
- Population groups.
- Births.
- Deaths.
- Migration.
- Species-specific demographic parameters.

General accounting:

`P_next = P_current + B - D + I - E`

Where:

- `B` is births.
- `D` is deaths.
- `I` is immigration.
- `E` is emigration.

Births and deaths should be modeled using suitable stochastic distributions where appropriate.

Do not assume human biology or reproductive behavior as universal.

Civilization-facing information:

- Total population.
- Population trend.
- Broad demographic structure.
- Growth or decline.
- Major demographic pressures.

## 9.2 Biology and Health

**Purpose:** Model biological conditions and population health.

Scientific foundation:

- Population biology.
- Epidemiology.
- Compartmental disease models.
- Nutrition and physiological constraints.

Internal representation:

- Biological species or population profiles.
- Health conditions.
- Disease prevalence.
- Disease transmission.
- Medical capability.
- Nutrition and environmental exposure.

Models such as SIR or SEIR may be appropriate for specific infectious diseases.

The engine should distinguish disease outbreaks, chronic health conditions, injuries, and environmental health pressures.

Civilization-facing information:

- Population health.
- Major health risks.
- Disease outbreaks.
- Medical capability.
- Health-related demographic pressures.

## 9.3 Food and Agriculture

**Purpose:** Model food production and food security.

Scientific foundation:

- Crop growth.
- Agricultural productivity.
- Soil and nutrient cycles.
- Water requirements.
- Food storage and spoilage.

Internal representation:

- Agricultural land.
- Crop types or functional groups.
- Growing conditions.
- Soil quality.
- Water availability.
- Nutrient availability.
- Production capacity.
- Food inventories.
- Storage losses.

Agricultural production should depend on environmental conditions and available inputs.

Food production is not independent of energy, materials, infrastructure, ecology, and logistics.

Civilization-facing information:

- Food availability.
- Agricultural output.
- Food reserves.
- Production limitations.
- Food security risks.

## 9.4 Energy

**Purpose:** Model energy generation, conversion, distribution, storage, and consumption.

Scientific foundation:

- Physical energy accounting.
- Power systems.
- Energy storage.
- Thermodynamic efficiency.
- Energy conversion.

Internal representation:

- Generating facilities.
- Generation technologies.
- Installed and available capacity.
- Energy storage.
- Distribution networks.
- Conversion losses.
- Consumption.
- Fuel requirements.

The engine must distinguish power from energy.

Power is measured in watts; energy is measured in joules.

Energy systems must account for generation, storage, transmission, conversion, and losses.

Civilization-facing information:

- Energy production.
- Energy consumption.
- Available capacity.
- Energy reserves.
- Energy shortages.
- Major energy constraints.

## 9.5 Materials and Resources

**Purpose:** Model physical resources and material availability.

Scientific foundation:

- Material-flow analysis.
- Stock-and-flow accounting.
- Resource extraction.
- Recycling and material recovery.

Internal representation:

- Resource deposits.
- Estimated reserves.
- Extractable resources.
- Inventories.
- Extraction facilities.
- Processing facilities.
- Recycling systems.
- Waste and losses.

Distinguish:

- Total geological resources.
- Known deposits.
- Economically or technologically recoverable reserves.
- Currently accessible inventory.

These are not interchangeable.

Civilization-facing information:

- Important material inventories.
- Resource availability.
- Major shortages.
- Extraction capacity.
- Resource dependencies.

## 9.6 Industry and Manufacturing

**Purpose:** Model the ability to transform resources into useful products.

Scientific foundation:

- Production functions.
- Industrial input-output relationships.
- Manufacturing constraints.
- Production capacity.
- Learning by doing.

Internal representation:

- Industrial facilities.
- Production lines.
- Machinery.
- Labor or equivalent productive resources.
- Material inputs.
- Energy inputs.
- Production throughput.
- Maintenance and downtime.

Industrial production must be limited by its actual inputs and production capacity.

A civilization cannot manufacture unlimited spacecraft simply because it has sufficient raw materials.

It also needs the appropriate machinery, facilities, skills, energy, and time.

Civilization-facing information:

- Industrial output.
- Major production capabilities.
- Manufacturing constraints.
- Available capacity.
- Important bottlenecks.

## 9.7 Infrastructure

**Purpose:** Model the physical systems that enable civilization-wide activity.

Scientific foundation:

- Infrastructure asset management.
- Network theory.
- Reliability engineering.
- Maintenance and lifecycle analysis.

Internal representation:

- Infrastructure assets.
- Networks.
- Capacity.
- Condition.
- Degradation.
- Maintenance.
- Failures.
- Repairs.
- Expansion.

Infrastructure should have a lifecycle:

Planned → Construction → Operational → Degraded or Maintenance → Repaired, Upgraded, or Retired.

Ordinary assets can be aggregated, while strategically important assets may be represented individually.

Civilization-facing information:

- Infrastructure capacity.
- Condition.
- Network reliability.
- Major bottlenecks.
- Maintenance burden.
- Expansion capability.

## 9.8 Technology and Science

**Purpose:** Model scientific knowledge and practical engineering capabilities.

Scientific foundation:

- Endogenous innovation.
- Research and development.
- Learning by doing.
- Knowledge diffusion.
- Technological prerequisites.

The simulation must distinguish:

1. Scientific knowledge.
2. Theoretical designs.
3. Engineering designs.
4. Prototypes.
5. Manufacturing capability.
6. Deployment capability.

Knowing how something might work does not automatically mean a civilization can build it.

Research projects should depend on:

- Existing knowledge.
- Prerequisites.
- Research capacity.
- Available materials.
- Experimental infrastructure.
- Time.
- Uncertain outcomes.

Technological breakthroughs should not be generated by simplistic random rolls disconnected from research capacity and existing knowledge.

Civilization-facing information:

- Major capabilities.
- Research priorities.
- Important limitations.
- Active research.
- Potential technological opportunities.

## 9.9 Astronomy and Planetary Systems

**Purpose:** Represent the astronomical environment and physical objects in the universe.

Scientific foundation:

- Stellar astrophysics.
- Planetary formation.
- Orbital mechanics.
- Galactic structure.
- Planetary science.

Internal representation:

- Galactic structure.
- Stellar systems.
- Stars.
- Planets.
- Moons.
- Orbital properties.
- Stellar evolution.
- Planetary environments.
- Geological properties.
- Resource deposits.

Stellar properties should be generated consistently.

Mass, luminosity, radius, temperature, age, and metallicity should not be independently randomized without regard to their physical relationships.

Planetary properties should depend on their formation and host-star context.

The habitable zone must not be treated as proof of actual habitability.

Newtonian gravity and Keplerian orbital mechanics are sufficient foundations for many systems. Full N-body simulation should only be introduced where necessary.

Civilization-facing information:

- Known stellar systems.
- Observed planetary properties.
- Estimated resources.
- Orbital and environmental conditions.
- Uncertainty about undiscovered or poorly surveyed objects.

## 9.10 Thermodynamics

**Purpose:** Enforce energy conservation and model thermal consequences.

Scientific foundation:

- Thermodynamics.
- Heat transfer.
- Radiative cooling.
- Energy conversion efficiency.

Internal representation:

- Energy inputs.
- Useful energy output.
- Waste heat.
- Thermal storage.
- Cooling capacity.
- Surface area.
- Temperature.
- Emissivity.

Radiative cooling can use the Stefan-Boltzmann relationship:

`P = εσAT⁴`

Where:

- `ε` is emissivity.
- `σ` is the Stefan-Boltzmann constant.
- `A` is radiating area.
- `T` is absolute temperature.

Waste heat should emerge from energy-consuming processes rather than being an arbitrary civilization statistic.

Thermodynamics must connect to industrial production, energy use, computing, planetary environments, and observability.

Civilization-facing information:

- Major thermal constraints.
- Waste heat.
- Cooling capacity.
- Thermal risks.
- Potential observational signatures.

## 9.11 Ecology and Environment

**Purpose:** Model environmental conditions, ecosystems, and resource regeneration.

Scientific foundation:

- Ecosystem modelling.
- Population ecology.
- Biogeochemical cycles.
- Environmental stock-flow accounting.

Keep three concepts distinct:

- Environment: physical conditions.
- Ecology: living populations and their interactions.
- Natural resources: usable physical stocks and flows.

Internal representation:

- Ecological populations.
- Biomass.
- Water.
- Nutrients.
- Soil.
- Pollution.
- Environmental conditions.
- Ecosystem productivity.
- Resource regeneration.

Logistic growth may be suitable for some populations, but coupled species and ecosystem models may be necessary elsewhere.

Environmental events should be correlated where appropriate.

For example, drought can affect agriculture, freshwater, energy generation, and ecosystems simultaneously.

Civilization-facing information:

- Ecosystem condition.
- Resource regeneration.
- Freshwater security.
- Pollution.
- Environmental trends.
- Ecological risks.

## 9.12 Economy and Trade

**Purpose:** Model allocation, production, consumption, investment, and exchange.

Scientific foundation:

- Physical input-output accounting.
- Supply-use tables.
- Economic allocation.
- Trade networks.
- Financial systems.

A critical distinction must exist between:

**Physical economy:** Actual goods, services, production, inventories, and consumption.

**Financial economy:** Money, prices, debt, ownership, credit, and financial incentives.

Money cannot create physical resources.

Funding a project does not make its required materials, labor, energy, or production capacity appear.

The allocation system should support different economic arrangements:

- Markets.
- Central planning.
- Quotas.
- Mixed systems.
- Non-monetary allocation.

Trade must represent physical movement of goods.

A trade agreement does not automatically transfer resources. The goods must be allocated, transported, and delivered.

Civilization-facing information:

- Economic output.
- Resource availability.
- Investment capacity.
- Consumption conditions.
- Trade dependencies.
- Major economic constraints.

## 9.13 Logistics and Transportation

**Purpose:** Model movement of goods, people, information-bearing equipment, and strategic assets.

Scientific foundation:

- Network flow theory.
- Transportation optimization.
- Inventory management.
- Propulsion physics.

Internal representation:

- Transport networks.
- Vehicles.
- Spacecraft.
- Shipments.
- Capacity.
- Routes.
- Travel time.
- Energy and fuel costs.
- Reliability.
- Restrictions.

Transportation should use the shared network system where applicable.

Spacecraft propulsion must connect mass, fuel, exhaust velocity, acceleration, and travel time.

The ideal rocket equation provides a useful foundation:

`Δv = v_e ln(m₀ / m_f)`

Interstellar transportation must also account for the relevant relativistic effects.

Civilization-facing information:

- Transport capacity.
- Delivery times.
- Major routes.
- Logistics reliability.
- Energy and fuel requirements.
- Bottlenecks.

## 9.14 Governance and Institutions

**Purpose:** Model how a civilization organizes authority, decisions, and collective action.

Scientific foundation:

- Institutional analysis.
- Collective-action theory.
- Political economy.
- Institutional development.

Internal representation:

- Political institutions.
- Authority structures.
- Laws and policies.
- Enforcement.
- Administrative capacity.
- Political factions.
- Regional autonomy.
- Institutional legitimacy.
- Corruption and capture.

Avoid reducing governance to a single stability statistic.

The LLM should make political decisions, while the engine determines their consequences through institutional and social mechanisms.

Civilization-facing information:

- Political structure.
- Authority.
- Administrative capabilities.
- Major political developments.
- Institutional constraints.
- Internal conflicts.

## 9.15 Society and Culture

**Purpose:** Model social organization, relationships, cultural evolution, and collective behavior.

Scientific foundation:

- Cultural evolution.
- Social networks.
- Social norms.
- Intergenerational transmission.

Internal representation:

- Social groups.
- Population distributions.
- Relationships.
- Norms.
- Traditions.
- Beliefs.
- Languages.
- Education.
- Cooperation and competition.
- Inequality.
- Internal tensions.

Culture should change through mechanisms such as:

- Education.
- Intergenerational transmission.
- Migration.
- Communication.
- Technology.
- Conflict.
- Policy.
- Contact with other civilizations.

Do not assume every member of a civilization shares identical beliefs or values.

Civilization-facing information:

- Major social groups.
- Dominant norms.
- Education and knowledge distribution.
- Social tensions.
- Inequality.
- Cultural developments.

## 9.16 Military and Security

**Purpose:** Model military capabilities, readiness, intelligence, defense, and strategic activity.

Scientific foundation:

- Military capability assessment.
- Readiness analysis.
- Logistics.
- Detection theory.
- Strategic interaction.

Internal representation:

- Military assets.
- Defensive and offensive capabilities.
- Readiness.
- Military organization.
- Detection systems.
- Intelligence.
- Sustainment.
- Fuel and consumables.
- Maintenance.
- Industrial support.
- Replacement capacity.

Military capability must not be reduced to one arbitrary strength score.

Nominal capability, readiness, mobility, sustainment, and industrial support must remain distinguishable.

Military knowledge about other civilizations must be derived from observations and intelligence, not directly exposed by the engine.

Civilization-facing information:

- Own defensive and offensive capabilities.
- Readiness.
- Mobility.
- Sustainment.
- Known threats.
- Intelligence uncertainty.

## 9.17 Information and Communication

**Purpose:** Model signals, communication systems, information transmission, and information processing.

Scientific foundation:

- Information theory.
- Communication engineering.
- Signal detection.
- Signal propagation.

Internal representation:

- Transmitters.
- Receivers.
- Antennas.
- Relays.
- Frequencies.
- Bandwidth.
- Signal power.
- Noise.
- Propagation.
- Messages.
- Encoding.
- Transmission time.
- Reception and processing.

The Shannon-Hartley theorem provides a theoretical channel capacity:

`C = B log₂(1 + S/N)`

Where:

- `B` is bandwidth.
- `S` is signal power.
- `N` is noise power.

Theoretical channel capacity must not be confused with guaranteed practical throughput.

The engine must distinguish:

- Signal transmission.
- Signal detection.
- Reception.
- Decoding.
- Interpretation.
- Understanding.

Communication must obey physical propagation delays.

Civilization-facing information:

- Communication capabilities.
- Known signals.
- Detection results.
- Network capacity.
- Communication delays.
- Reliability.
- Information uncertainty.

## 9.18 Exploration and Expansion

**Purpose:** Model discovery, investigation, resource assessment, travel, and settlement.

Scientific foundation:

- Decision-making under uncertainty.
- Active sensing.
- Exploration planning.
- Resource evaluation.
- Value of information.

Internal representation:

- Exploration missions.
- Probes.
- Spacecraft.
- Survey equipment.
- Observations.
- Resource assessments.
- Mission objectives.
- Settlement projects.
- Infrastructure deployment.

Discovery must be separated from authoritative truth.

A civilization's survey updates its own knowledge, not the underlying universe.

Expansion should follow a meaningful sequence:

Detect → Investigate → Evaluate → Plan → Construct → Launch → Travel → Arrive → Establish infrastructure → Settle.

Each stage has prerequisites, costs, uncertainty, and potential failure.

Civilization-facing information:

- Known systems.
- Exploration coverage.
- Active missions.
- Discoveries.
- Potential opportunities.
- Uncertainties.

## 9.19 Risk and Resilience

**Purpose:** Evaluate vulnerabilities, cascading failures, and the ability to withstand and recover from disruptions.

This is a cross-cutting framework, not an independent collection of physical statistics.

Scientific foundation:

- Reliability engineering.
- Risk analysis.
- Fault trees.
- Resilience engineering.
- Stochastic simulation.

Relevant properties include:

- Spare capacity.
- Reserves.
- Redundancy.
- Alternative routes.
- Maintenance.
- Dependency structure.
- Recovery capability.

Risk evaluation should consider:

- Probability.
- Consequence.
- Exposure.
- Uncertainty.
- Correlated events.
- Cascading failures.
- Recovery time.

Avoid representing resilience as a single universal score.

The relevant physical systems should handle recovery.

Civilization-facing information should provide contextual warnings, vulnerabilities, and likely consequences.

---

# 10. Domain Interactions and Causal Relationships

The domains must be connected through shared mechanisms.

They should not merely maintain independent statistics.

## 10.1 Energy and industry

Energy shortages can reduce industrial output.

Reduced industrial output can delay maintenance, construction, and resource extraction.

These consequences can create further energy shortages.

## 10.2 Materials and technology

Technological development may require specialized materials.

New technology can improve extraction, manufacturing, recycling, and energy conversion.

However, discovering a material's potential use does not guarantee the civilization can manufacture the necessary equipment.

## 10.3 Ecology and agriculture

Environmental degradation can reduce agricultural productivity.

Agricultural expansion can affect ecosystems, water availability, soil quality, and biodiversity.

Environmental shocks may simultaneously affect food production and other resource systems.

## 10.4 Infrastructure and logistics

Infrastructure failures can disrupt transportation, communication, energy distribution, and manufacturing.

Logistics can constrain the ability to repair damaged infrastructure.

## 10.5 Demographics and economy

Population changes affect labor, consumption, demand, and administrative requirements.

Economic conditions affect nutrition, health, and living conditions, which can influence demographic outcomes.

## 10.6 Governance and society

Policies affect resource allocation, institutions, education, and social conditions.

Social structures influence the implementation and acceptance of policies.

Political decisions can create long-term consequences that are not immediately visible.

## 10.7 Information and military activity

Detection systems and communication networks influence military awareness.

A civilization may misinterpret another civilization's activity.

Incomplete intelligence should influence decisions without giving agents access to hidden truth.

## 10.8 Exploration and technology

Exploration depends on propulsion, energy, industrial capacity, communications, and logistics.

Discoveries can produce new scientific knowledge and opportunities for technological development.

## 10.9 Risk and cascading failure

A single disruption may affect several domains.

For example:

Drought → reduced freshwater → reduced agricultural production → food shortage → health decline → social unrest → political instability.

The engine should model the underlying causal processes and allow these consequences to emerge.

---

# 11. Civilization Actions and Tool Architecture

Civilization agents interact with the simulation through tools.

Tools should be designed around meaningful decisions and information access.

## 11.1 Tool categories

Civilization tools should generally be organized into:

- Inspection.
- Calculation.
- Knowledge acquisition.
- Planning and proposals.
- Action execution.
- Time advancement.

The civilization should receive only the tools appropriate to its role and permissions.

## 11.2 Inspection

Inspection tools expose decision-relevant information.

Examples:

- Inspect own civilization.
- Inspect population.
- Inspect energy.
- Inspect important resources.
- Inspect active projects.
- Inspect known locations.
- Inspect observations.

Inspection should support more detailed investigation when needed.

The default response should not dump every internal variable.

## 11.3 Calculation

Calculation tools allow civilizations to reason about possible decisions.

Examples:

- Travel time.
- Energy requirements.
- Signal detection.
- Waste heat.
- Resource requirements.
- Population projections.
- Production estimates.

Calculations should be distinguishable from actual simulation changes.

A calculated projection does not automatically become an authoritative outcome.

## 11.4 Proposals and execution

The agent should express intended actions through a structured proposal mechanism.

The engine validates and executes the action according to its applicable domain rules.

Some actions may start projects rather than produce immediate results.

The agent must receive a clear explanation when an action is rejected, delayed, constrained, or only partially completed.

## 11.5 Information boundaries

Tool implementations must use the civilization's identity and permissions when retrieving information.

A stale tool call from a previous civilization must never execute under the identity of a newly active civilization.

Tool execution should be bound to an explicit runtime and civilization identity.

---

# 12. Runtime and Civilization Scheduling

The simulation should support multiple civilizations while using one active LLM context at a time.

## 12.1 Scheduler

The scheduler selects eligible civilizations.

Selection should normally follow the scheduler's default policy.

The narrator may be able to override the selection where appropriate, but only for an eligible civilization.

## 12.2 Turn lifecycle

A civilization turn should broadly follow:

1. Select civilization.
2. Update its local year.
3. Prepare its context.
4. Activate its runtime identity.
5. Invoke the LLM.
6. Process its tool calls.
7. Validate proposed actions.
8. Continue until turn completion or interruption.
9. Persist the resulting state.
10. Release the runtime slot.
11. Select the next civilization.

The exact turn boundaries should remain explicit.

## 12.3 Runtime controls

The three main controls must have distinct behavior.

### Pause

The active civilization finishes its current turn.

Afterward, the scheduler stops automatic progression and does not hand off to another civilization.

Pause must not abruptly interrupt the LLM.

### Suspend

The active civilization is interrupted at a safe boundary.

Its context and pending work are preserved as far as possible, and the runtime slot is released.

The civilization remains awake but inactive.

### Terminate

Termination should occur only after pausing or suspending.

The simulation saves its complete state and shuts down the runtime.

The system should avoid silently discarding unfinished work.

## 12.4 Uncertain tool execution

A tool call that has already begun executing may have side effects.

If the process stops before recording its completion, the engine must not blindly repeat it.

The tool-call journal should distinguish:

- Pending.
- Executing.
- Completed.
- Failed.
- Uncertain.

Uncertain operations require explicit recovery handling.

---

# 13. Persistence and Fresh-Process Continuation

Persistence is a core simulation requirement, not a later convenience.

A saved world must be loadable in a fresh process and continue operating.

## 13.1 Required persistent state

Persistence should cover:

- World state.
- Simulation time.
- Civilization state.
- Civilization-local time.
- Domain state.
- Active projects.
- Events and event queue.
- Scheduler state.
- Civilization knowledge.
- Agent state.
- Random generator states.
- Simulation configuration.
- Universe generation seed.
- Tool-call journal.
- Relevant execution and recovery state.

The exact schema should be versioned.

## 13.2 Save and load lifecycle

The required test is:

1. Create a simulation.
2. Advance it.
3. Save it.
4. Destroy the runtime and process.
5. Start a fresh process.
6. Load the saved simulation.
7. Restore the scheduler and domain state.
8. Recover interrupted work safely.
9. Resume the simulation.
10. Verify that it continues correctly.

A simple deserialize-and-inspect test is insufficient.

## 13.3 LLM continuation

An active coroutine or HTTP request cannot simply be serialized.

If an LLM request is interrupted, the system should preserve the available conversation context and execution information.

It must not pretend that an unfinished response completed.

Recovery should explicitly represent interrupted work.

## 13.4 Determinism

Persistence should preserve enough information to reproduce future stochastic decisions under the same simulation version and configuration.

Version upgrades may change numerical behavior, so deterministic compatibility across arbitrary software versions should not be assumed without an explicit compatibility mechanism.

---

# 14. Civilization-Facing Summaries

The simulation should maintain detailed internal models while presenting compact information to the LLM.

A civilization should not receive a giant table of hundreds of independent statistics every turn.

## 14.1 Default summary

The normal civilization context should prioritize:

- Current overall condition.
- Population trend.
- Energy condition.
- Important material constraints.
- Industrial and infrastructure condition.
- Major technological capabilities.
- Environmental and ecological pressures.
- Important social or political developments.
- Active projects.
- Relevant external observations.
- Immediate opportunities and threats.

The exact format and amount of information should be tuned through testing.

## 14.2 Drill-down

When a civilization needs more detail, it should use inspection tools.

For example:

A summary might report that energy reserves are declining.

The civilization can then inspect:

- Generation.
- Consumption.
- Storage.
- Fuel availability.
- Distribution constraints.
- Active power projects.

This avoids micro-splitting every statistic into the default context while preserving access to useful information.

## 14.3 Forecasts and hypothetical scenarios

Forecasts must be distinguished from authoritative simulation state.

A civilization may ask what would happen if it built a particular facility.

The engine can calculate a hypothetical result without modifying the actual world.

Similarly, predictions should not be confused with the civilization's existing beliefs or guaranteed future outcomes.

---

# 15. Narrator and Human Operator

The narrator is a separate actor from civilization agents.

It has access to the simulation's authoritative state and provides a mechanism for managing the world.

## 15.1 Narrator responsibilities

The narrator may:

- Inspect the world.
- Inspect civilizations.
- Modify world conditions through authorized tools.
- Create or modify simulation events.
- Advance or control time.
- Inspect calculations.
- Review civilization activity.
- Manage simulation-level settings.

Its tools should be separated into:

**World Modification:** Tools that change authoritative simulation state.

**Mathematics and Data:** Read-only calculations, inspection, and analysis.

## 15.2 Narrator and civilization information

The narrator can inspect the authoritative world.

Civilization agents cannot inherit narrator permissions.

The narrator's action log should remain narrator-facing unless a civilization has independently observed the relevant event.

The same information-boundary rules apply even when a narrator has modified the world.

---

# 16. Logging and Observability

The simulation should support both detailed technical records and readable human-facing activity.

These are different purposes and should not be forced into one representation.

## 16.1 Structured logs

Structured logs should record relevant execution information, including:

- Timestamps.
- Simulation time.
- Civilization identity.
- Event identity.
- Tool calls.
- Tool arguments.
- Results.
- Errors.
- State changes.
- Runtime transitions.
- Persistence operations.

Structured records should be suitable for debugging, auditing, and later analysis.

## 16.2 Human-readable live log

The live log should provide a concise, understandable view of simulation activity.

It should not simply display raw JSON.

## 16.3 Live execution stream

The control room should eventually display:

- LLM thinking where available.
- Assistant responses.
- Tool calls.
- Arguments.
- Results.
- Errors.
- Action proposals.
- Runtime events.
- Suspension and resume.
- Civilization handoffs.

The stream should preserve enough detail for debugging without making the interface unusable.

---

# 17. Scientific Fidelity and Model Selection

The simulation should be scientifically grounded without attempting to reproduce every physical phenomenon at maximum resolution.

Each model should document its chosen fidelity.

A model specification should define:

1. What it represents.
2. What it does not represent.
3. Its governing equations or mechanisms.
4. Its assumptions.
5. Its input variables.
6. Its output variables.
7. Its units.
8. Its update frequency.
9. Its stochastic behavior.
10. Its limitations.

## 17.1 Avoid false precision

A model should not expose highly precise-looking results when its underlying assumptions do not justify that precision.

For example, an estimated resource deposit should not be displayed as an exact quantity simply because the engine stores a floating-point number.

## 17.2 Unsupported conditions

The human operator should be able to modify authoritative values, including physically unusual or extreme values.

The engine should distinguish:

- Structurally representable state.
- Physically plausible state.
- Computationally operable state.

It should not silently clamp or correct unusual values.

If a calculation becomes undefined or unsupported, the engine should report the problem explicitly.

For example, a negative gravitational parameter may be representable as an operator-specified value, but an orbital calculation that assumes ordinary positive gravitational attraction must report that its assumptions are violated.

This preserves the distinction between editing the world and calculating its consequences.

---

# 18. Implementation Roadmap

Implementation should proceed in stages.

The objective is to establish the architecture before expanding individual domain models.

## Stage 1 — Civilization Representation

**Goal:** Build the authoritative civilization model.

Work:

- Review the current civilization state.
- Define the domain boundaries.
- Establish the authoritative data model.
- Design population, resources, energy, and other foundational state.
- Define units and accounting rules.
- Separate internal detail from civilization-facing summaries.
- Ensure operator modification does not silently clamp values.

Acceptance criteria:

- Civilization state has a documented structure.
- Core variables have defined units and meanings.
- State changes use explicit mechanisms.
- Physically unusual values can be represented.
- Unsupported calculations fail clearly.
- Tests cover accounting and state validation.

## Stage 2 — Civilization Switching and Runtime Mechanics

**Goal:** Make multiple civilizations operate safely through one active LLM runtime.

Work:

- Complete scheduler integration.
- Implement civilization context switching.
- Enforce runtime identity.
- Finalize turn lifecycle.
- Implement pause, suspend, and termination behavior.
- Handle interrupted tool calls.
- Preserve unfinished work.

Acceptance criteria:

- Multiple civilizations can take turns.
- Only one civilization is active in the LLM runtime.
- Stale tool calls cannot execute under a different civilization.
- Pause and suspend behave differently.
- Interrupted side effects are not blindly repeated.

## Stage 3 — Civilization Tools and Domain Access

**Goal:** Give civilizations access to useful information and actions.

Work:

- Review existing MCP tools.
- Separate inspection, calculation, knowledge, and action tools.
- Add domain-specific tools as the models become available.
- Enforce knowledge boundaries.
- Implement structured action proposals.
- Provide useful validation feedback.
- Add detailed inspection through drill-down tools.

Acceptance criteria:

- Civilizations can inspect their own state.
- External information respects discovery and uncertainty.
- Calculations do not silently modify authoritative state.
- Actions are validated by the engine.
- Tool access is correctly scoped to the active civilization.

## Stage 4 — Shared Simulation Mechanics

**Goal:** Build the reusable foundation for domain simulation.

Work:

- Stock-and-flow accounting.
- Capacity and constraint mechanisms.
- Network foundation.
- Project/process system.
- Uncertainty and knowledge representation.
- Stochastic engine.
- Event scheduling.
- Domain update interfaces.

Acceptance criteria:

- Shared mechanics can be reused across domains.
- Conservation accounting is testable.
- Events execute at the correct simulation time.
- Independent random streams behave independently.
- Project progress responds to actual constraints.

## Stage 5 — Domain Simulation

**Goal:** Implement the 19 domains through the shared architecture.

Suggested implementation order:

1. Demographics.
2. Energy.
3. Materials.
4. Industry.
5. Infrastructure.
6. Biology and health.
7. Food and agriculture.
8. Ecology and environment.
9. Thermodynamics.
10. Astronomy and planetary systems.
11. Technology and science.
12. Economy and trade.
13. Logistics and transportation.
14. Information and communication.
15. Exploration and expansion.
16. Governance and institutions.
17. Society and culture.
18. Military and security.
19. Risk and resilience.

This is a proposed order, not a requirement that each domain be completed entirely before the next begins.

Some domains should be developed together because they have strong dependencies.

For example, energy, materials, and industry should be developed as a connected foundation.

Astronomy and planetary environments should establish the physical context for ecology, agriculture, and exploration.

Information and communication should be developed before relying on interstellar intelligence and strategic interactions.

Acceptance criteria:

- Each domain has documented assumptions and limitations.
- Domain interactions use shared mechanisms.
- Physical constraints are enforced.
- Civilization-facing information is appropriately summarized.
- Tests cover individual systems and cross-domain consequences.

## Stage 6 — Persistence and Continuation

**Goal:** Make long-running simulations reliable.

Work:

- Review existing persistence.
- Persist complete authoritative state.
- Persist random generator states.
- Persist scheduler and event queue.
- Persist knowledge and agent state.
- Implement recovery of interrupted work.
- Support fresh-process continuation.

Acceptance criteria:

- A simulation can be saved.
- Its original process can be destroyed.
- A fresh process can load it.
- The simulation can continue.
- Random streams continue from saved states.
- Uncertain tool execution is handled safely.

## Stage 7 — GUI Overhaul

**Goal:** Provide a complete interface for operating and inspecting the simulation.

The GUI should have five major pages.

### Main Control Room

- Live execution stream.
- Civilization list and status.
- Civilization inspection and modification.
- 2D map of the 3D universe.
- Contextual object inspection.
- Simulation controls.
- Direct tool-call responses.

### Calculator

- Categorized mathematical and physical tools.
- Read-only calculations.
- Clear input and output presentation.

### Device Usage Monitor

- Hardware usage.
- Model/runtime usage.
- Resource consumption.

### File Viewer

- Graphical file picker.
- Markdown and LaTeX rendering.
- Syntax-highlighted code.
- JSON and plain text viewing.

### Live Log

- Human-readable event stream.
- Separate structured JSON persistence.

Acceptance criteria:

- GUI operations use the simulation's actual backend state.
- Human modifications are explicit.
- Runtime controls behave correctly.
- Inspection respects object permissions and information boundaries.
- The map accurately represents 3D positions through its chosen projection.

## Stage 8 — Final Review and Completion

**Goal:** Verify the complete simulation before its first serious run.

Work:

- Review architecture consistency.
- Audit information boundaries.
- Audit conservation rules.
- Test cross-domain interactions.
- Test long time advances.
- Test fresh-process persistence.
- Test runtime interruption and recovery.
- Test stochastic reproducibility.
- Review GUI behavior.
- Document known limitations.

Acceptance criteria:

- All tests pass.
- Critical interactions are covered.
- No known information leaks exist.
- Persistence continuation works.
- Runtime recovery works.
- The simulation can run for extended periods without corrupting its state.

## Stage 9 — First Simulation Run

Only after the previous stages are complete should the first serious simulation run begin.

The first run should be treated as a validation exercise.

Observe:

- Whether civilizations make meaningful decisions.
- Whether the engine enforces constraints.
- Whether systems interact naturally.
- Whether time advancement behaves correctly.
- Whether the LLM receives appropriate information.
- Whether emergent behavior is interesting and coherent.
- Whether performance remains manageable.

The results should guide later model improvements.

---

# 19. Testing Strategy

Testing must cover more than individual functions.

The simulation needs several layers of validation.

## 19.1 Unit tests

Test individual calculations and mechanisms.

Examples:

- Population accounting.
- Energy accounting.
- Material flows.
- Signal propagation.
- Travel calculations.
- Project progress.
- Random stream behavior.

## 19.2 Domain tests

Test complete domain behavior.

Examples:

- Energy shortages reduce available industrial operation.
- Resource extraction changes deposits and inventories.
- Infrastructure degradation reduces capacity.
- Agricultural production responds to environmental conditions.
- Population changes reflect demographic processes.

## 19.3 Integration tests

Test interactions between domains.

Examples:

- Energy shortage → industrial slowdown.
- Material shortage → construction delay.
- Drought → agricultural disruption.
- Communication delay → delayed information.
- Exploration → discovery → updated civilization knowledge.

## 19.4 Information-boundary tests

Verify that a civilization cannot access:

- Undiscovered objects.
- Another civilization's private state.
- Unobserved intentions.
- Unreceived communications.
- Narrator-only information.

These should be explicit security-style tests, not merely assumed from normal operation.

## 19.5 Runtime tests

Verify:

- Scheduling.
- Civilization switching.
- Pause.
- Suspend.
- Termination.
- Stale tool-call rejection.
- Interrupted operation recovery.

## 19.6 Persistence tests

Test actual continuation in a fresh process.

Round-trip serialization alone is insufficient.

## 19.7 Long-duration tests

Advance simulations across extended periods.

Look for:

- Numerical instability.
- Resource-accounting errors.
- Unbounded event queues.
- Stochastic anomalies.
- Performance degradation.
- State corruption.

---

# 20. Decisions Still Requiring Explicit Specification

The architecture establishes the overall direction, but several parameters should not be guessed.

## 20.1 Universe scale

We must decide whether the initial simulation represents:

- A local stellar neighborhood.
- A substantial portion of a galaxy.
- An entire galaxy.
- An abstract universe with galaxy-like properties.

This affects astronomical generation, spatial resolution, event scheduling, and performance.

## 20.2 Initial civilization complexity

We should establish how much detail a civilization starts with.

For example:

- Is its population represented through a small number of cohorts or more detailed demographic groups?
- Are ordinary industrial facilities aggregated?
- Which infrastructure assets are represented individually?
- How much internal social structure is needed initially?

The guiding principle remains: retain useful internal detail without unnecessarily splitting every exposed statistic.

## 20.3 Simulation performance budget

We need to determine reasonable limits for:

- Number of civilizations.
- Number of stellar systems.
- Number of active events.
- Number of projects.
- Number of detailed physical objects.
- Domain update frequency.

These should be measured rather than chosen arbitrarily.

## 20.4 Species and biology abstraction

The architecture should remain species-independent.

However, the initial biological model needs a defined level of generality.

We should avoid designing a universal biological engine before establishing which capabilities are actually necessary.

## 20.5 Economic and social abstraction

The simulation should support different civilization structures without assuming all civilizations resemble modern human states.

The initial implementation should focus on mechanisms that can be generalized.

---

# 21. Final Architectural Rules

The following rules should guide future development.

1. The engine is the authority on physical reality.
2. LLMs make decisions; the engine determines consequences.
3. Civilization knowledge is separate from authoritative world state.
4. No civilization receives information it has not legitimately acquired.
5. Physical quantities must obey applicable accounting and conservation rules.
6. Shared mechanisms should be implemented once and reused.
7. Domains must interact through causal mechanisms.
8. Different domains may operate at different temporal resolutions.
9. Randomness must be reproducible and independently managed.
10. The simulation must support fresh-process continuation.
11. Interrupted operations must never be silently treated as completed.
12. Operator modifications must not silently clamp unusual values.
13. Hypothetical forecasts must remain separate from authoritative state.
14. Civilization-facing summaries should prioritize decision-relevant information.
15. Detailed information should be available through investigation tools.
16. Models must document their assumptions and limitations.
17. Scientific complexity should be introduced where it meaningfully improves simulation behavior.
18. Avoid arbitrary scores that hide important underlying variables.
19. Avoid building disconnected domain-specific systems.
20. Every major feature should be testable independently and in combination.

---

# Conclusion

Dark Forest Sim should be built as a unified simulation engine with shared physical, computational, and organizational mechanisms.

The 19 domains describe what the simulation needs to represent, but they should not dictate 19 separate implementations.

The foundation is:

- An authoritative 3D world.
- A structured civilization model.
- Shared stock-flow, capacity, network, project, and uncertainty mechanisms.
- A reproducible event and stochastic engine.
- Strict civilization knowledge boundaries.
- A controlled multi-civilization runtime.
- Reliable persistence and recovery.
- Decision-oriented civilization interfaces.

Once these foundations are established, individual domains can be developed and refined without compromising the consistency of the overall simulation.

The ultimate goal is not to simulate every possible detail of a civilization. It is to simulate enough of its physical and organizational reality that its decisions have meaningful, consistent, and emergent consequences.
