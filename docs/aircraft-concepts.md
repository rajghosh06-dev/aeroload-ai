# Aircraft Weight & Balance Concepts

Safe flight operations require an aircraft to be properly loaded within strict structural and aerodynamic limits.

AeroLoad-AI calculates physical balance using classical flight-mechanics principles implemented directly in `engine/cg.py`.

---

## Key Physical Concepts

### 1. Weight ($W$)
The gravitational force exerted by cargo mass, measured in kilograms ($\text{kg}$). Each cargo item has a defined weight, and each cargo bay has a structural maximum weight capacity ($C_{\max}$).

### 2. Longitudinal Arm ($x$)
The distance from an aircraft's reference datum along the longitudinal fuselage axis, measured in meters ($\text{m}$).
- Bays located forward of the datum have negative arm values (e.g., $-3.0\text{ m}$, $-1.0\text{ m}$).
- Bays located aft of the datum have positive arm values (e.g., $+1.0\text{ m}$, $+3.0\text{ m}$).

### 3. Moment ($M$)
The rotational force produced by a cargo item about the reference datum:
$$\text{Moment} = \text{Weight} \times \text{Arm}$$
Units: kilogram-meters ($\text{kg}\cdot\text{m}$).

### 4. Total Payload
The sum of all assigned cargo weights:
$$\text{Total Payload} = \sum_{i=1}^n \text{Weight}_i$$
This must not exceed the aircraft's configured maximum payload capacity ($\text{MaxPayload}$).

### 5. Center of Gravity (CG)
The longitudinal balance point of the loaded cargo:
$$\text{CG} = \frac{\text{Total Moment}}{\text{Total Payload}} = \frac{\sum_{i=1}^n (\text{Weight}_i \times \text{Arm}_i)}{\sum_{i=1}^n \text{Weight}_i}$$

### 6. Target CG ($\text{TargetCG}$)
The preferred aerodynamic balance position (e.g., $0.00\text{ m}$ on the ALT-8 airframe). When the actual CG aligns closely with the Target CG, the aircraft maintains neutral pitch trim.

### 7. CG Envelope ($[\text{CG}_{\min}, \text{CG}_{\max}]$)
The allowable forward and aft range within which the CG must remain. Loading an aircraft too far forward causes nose-heaviness and excessive elevator control force. Loading too far aft causes tail-heaviness and longitudinal instability.

### 8. Lateral Imbalance
The difference in cargo weight between port (left) and starboard (right) cargo bays:
$$\text{Left Weight} = \sum_{b \in \text{Left}} \text{Weight}_i, \quad \text{Right Weight} = \sum_{b \in \text{Right}} \text{Weight}_i$$
$$\text{Lateral Imbalance} = |\text{Left Weight} - \text{Right Weight}|$$
Excessive lateral imbalance induces an aerodynamic roll moment that forces the pilot or autopilot to maintain continuous aileron/rudder trim.
