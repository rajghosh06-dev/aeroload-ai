# Academic Scope & Modeling Simplifications

To remain appropriate for a B.Tech 3rd-year Artificial Intelligence curriculum, AeroLoad-AI incorporates several deliberate engineering simplifications.

---

## 1. Discrete Bay Model vs. Continuous Loading
- **In Simulation**: Cargo is placed into discrete, indexed cargo bays (e.g., $B_1$ through $B_8$). Each bay has fixed coordinates (longitudinal arm and lateral side) and a structural weight capacity.
- **In Real-World Aviation**: Cargo compartments often support continuous palletized loading along floor tracks, requiring continuous geometric packing, running load limits (kg/m), and cumulative shear/bending moment calculations.

---

## 2. Static CG vs. In-Flight Fuel Burn
- **In Simulation**: Center of Gravity is calculated for static takeoff conditions based on cargo placement alone.
- **In Real-World Aviation**: The CG shifts dynamically during flight as fuel burns from main wing tanks and center tanks, and as passengers move about the cabin.

---

## 3. Educational Airframe Specification
- **In Simulation**: The application uses the `ALT-8` ("AeroLoad Training Aircraft"), an educational airframe model with 8 bays, a 4,000 kg payload limit, and an allowable CG envelope of $[-1.0\text{ m}, +1.0\text{ m}]$.
- **In Real-World Aviation**: Commercial freighters (such as the Boeing 737-800BCF or Airbus A330-200F) have dozens of main-deck and lower-deck positions, specialized Unit Load Devices (ULDs), and complex weight-and-balance index schedules.

---

## 4. Simplified Hazard Segregation
- **In Simulation**: The Knowledge Base models 4 primary incompatibility pairs (Lithium Batteries & Flammables, Flammables & Oxidizers, Toxics & Food, Biohazards & Food).
- **In Real-World Aviation**: The IATA Dangerous Goods Regulations (DGR) and ICAO Technical Instructions include hundreds of UN numbers, packing instructions, quantity exemptions, and multi-tier segregation requirements.

---

## 5. Educational Disclaimer

> **AeroLoad-AI is an educational simulation project.**  
> Aircraft parameters and hazardous-material rules are simplified for academic demonstration and must **not** be used for real-world flight dispatch, operational loadsheet generation, or commercial dangerous-goods compliance.
