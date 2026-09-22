# Getting Started with AeroLoad-AI

**AeroLoad-AI** is an intelligent aircraft cargo weight-and-balance and hazard-placement planning system designed for B.Tech 3rd-year Artificial Intelligence Project-Based Learning (AI-PBL).

It helps students and loadmasters solve the challenging problem of placing cargo packages into aircraft cargo bays while satisfying structural weight limits, dangerous-goods separation rules, and aerodynamic balance envelopes.

---

## The 4-Step Planning Workflow

AeroLoad-AI organizes cargo operations into four intuitive steps:

```
[ Step 1: Prepare Scenario ] ──> [ Step 2: Choose Mode ] ──> [ Step 3: Plan Cargo ] ──> [ Step 4: Review Results ]
```

### Step 1: Prepare Scenario
- Review the active cargo manifest and aircraft limits shown on the dashboard.
- Click **Edit Scenario** in the top header to add, edit, or remove cargo items, change aircraft limits, or load a pre-configured template (such as *Relief and medical mission* or *Hazmat separation exercise*).

### Step 2: Choose Planning Mode
Select one of the three planning modes using the mode selector:
- **Auto Solve**: Let AeroLoad-AI autonomously compute a complete, safe, and balance-optimized load plan.
- **Manual Planning**: Place cargo items into bays yourself with instant constraint validation.
- **AI-Assisted Planning**: Place cargo interactively with live AI guidance showing which bays are legal or blocked.

### Step 3: Plan Cargo
- In **Auto Solve**: Click **Run AeroLoad-AI** to solve the placement.
- In **Manual Planning**: Select a cargo item, choose a target bay, and click **Place cargo**.
- In **AI-Assisted**: Select a cargo item, inspect its legal bays on the aircraft deck, and click a legal bay to place it.

### Step 4: Review Results
- Inspect the visual aircraft cargo deck to verify which items occupy each bay.
- Review the Center of Gravity (CG) position and lateral roll balance figures.
- Check the safety validation report and solver audit statistics.
