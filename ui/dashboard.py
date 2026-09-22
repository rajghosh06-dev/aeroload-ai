"""Streamlit orchestration for the dynamic AeroLoad operations console."""

from __future__ import annotations

from html import escape
import pandas as pd
import streamlit as st

try:
    from streamlit_sortables import sort_items
except ImportError:  # pragma: no cover - graceful fallback until dependencies are installed
    sort_items = None

from engine.aircraft import Aircraft, load_aircraft_from_json
from engine.backtracking import assignment_to_cargo_assignments
from engine.cargo import load_cargo_from_csv
from engine.cg import calculate_side_weights
from engine.constraints import validate_loading_plan
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules
from engine.models import CargoCategory, HazardClass
from engine.pipeline import analyze_loading_problem
from ui.aircraft_view import render_aircraft_layout
from ui.charts import cg_envelope_figure, lateral_balance_figure
from ui.components import render_aircraft_status, render_brand, render_kpi_strip, render_status_pill
from ui.docs import render_docs_page
from ui.planning import (
    BayOptionStatus,
    assign_cargo_manually,
    clear_manual_assignments,
    evaluate_bay_options,
    reconcile_manual_assignments,
    unassign_cargo_manually,
    validate_manual_plan,
)
from ui.state import (
    MANIFEST_COLUMNS,
    cargo_rows,
    configured_aircraft,
    empty_manifest_rows,
    import_manifest,
    manifest_csv,
    manifest_from_rows,
    normalise_rows,
    reorder_rows,
    validate_manifest_for_aircraft,
)
from ui.styles import get_global_css
from ui.templates import scenario_templates


@st.cache_resource
def load_project_data():
    return (
        load_aircraft_from_json("data/aircraft.json"),
        load_cargo_from_csv("data/sample_cargo.csv"),
        load_hazard_rules("data/hazard_rules.json"),
    )


def _initialize_state(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    defaults = {
        "manifest_rows": sample_rows,
        "manifest_revision": 0,
        "enable_optimization": True,
        "optimization_iterations": 50,
        "max_payload_kg": base_aircraft.max_payload_kg,
        "cg_min_m": base_aircraft.cg_min_m,
        "cg_max_m": base_aircraft.cg_max_m,
        "target_cg_m": base_aircraft.target_cg_m,
        "lateral_limit_kg": base_aircraft.lateral_imbalance_limit_kg,
        "scenario_editor_open": False,
        "docs_open": False,
        "planning_mode": "Auto Solve",
        "manual_assignments": {},
        "selected_manual_cargo_idx": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_workspace(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    st.session_state["manifest_rows"] = sample_rows
    st.session_state["manifest_revision"] += 1
    st.session_state["enable_optimization"] = True
    st.session_state["optimization_iterations"] = 50
    st.session_state["max_payload_kg"] = base_aircraft.max_payload_kg
    st.session_state["cg_min_m"] = base_aircraft.cg_min_m
    st.session_state["cg_max_m"] = base_aircraft.cg_max_m
    st.session_state["target_cg_m"] = base_aircraft.target_cg_m
    st.session_state["lateral_limit_kg"] = base_aircraft.lateral_imbalance_limit_kg
    st.session_state["planning_mode"] = "Auto Solve"
    st.session_state["manual_assignments"] = {}
    st.session_state["selected_manual_cargo_idx"] = 0
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("analysis_csp", None)
    st.session_state.pop("analysis_fingerprint", None)


def _settings_panel(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    st.markdown("#### Solver preferences")
    st.toggle("Enable local-search optimization", key="enable_optimization")
    st.number_input("Maximum optimization iterations", min_value=1, max_value=500,
                    step=5, key="optimization_iterations")
    st.caption("Scenario cargo and aircraft limits are edited from Scenario Data, not Settings.")
    st.divider()
    if st.button("Reset workspace", use_container_width=True):
        _reset_workspace(base_aircraft, sample_rows)
        st.rerun()


def _configured_aircraft(base_aircraft: Aircraft) -> tuple[Aircraft, list[str]]:
    try:
        return configured_aircraft(
            base_aircraft,
            max_payload_kg=st.session_state["max_payload_kg"],
            cg_min_m=st.session_state["cg_min_m"],
            cg_max_m=st.session_state["cg_max_m"],
            target_cg_m=st.session_state["target_cg_m"],
            lateral_imbalance_limit_kg=st.session_state["lateral_limit_kg"],
        ), []
    except ValueError as error:
        return base_aircraft, [str(error)]


def _open_scenario_editor() -> None:
    """Create an isolated draft so Cancel never mutates the active scenario."""
    st.session_state["scenario_draft_rows"] = normalise_rows(st.session_state["manifest_rows"])
    st.session_state["scenario_draft_revision"] = st.session_state.get("scenario_draft_revision", 0) + 1
    for active_key in ("max_payload_kg", "cg_min_m", "cg_max_m", "target_cg_m", "lateral_limit_kg"):
        st.session_state[f"draft_{active_key}"] = st.session_state[active_key]
    st.session_state["scenario_editor_open"] = True
    st.session_state["docs_open"] = False


def _discard_scenario_draft() -> None:
    for key in list(st.session_state):
        if key.startswith("scenario_draft") or key.startswith("draft_"):
            st.session_state.pop(key, None)
    st.session_state["scenario_editor_open"] = False


def _open_docs() -> None:
    st.session_state["docs_open"] = True
    st.session_state["scenario_editor_open"] = False


def _close_docs() -> None:
    st.session_state["docs_open"] = False


def _draft_aircraft(base_aircraft: Aircraft) -> tuple[Aircraft, list[str]]:
    try:
        return configured_aircraft(
            base_aircraft,
            max_payload_kg=st.session_state["draft_max_payload_kg"],
            cg_min_m=st.session_state["draft_cg_min_m"],
            cg_max_m=st.session_state["draft_cg_max_m"],
            target_cg_m=st.session_state["draft_target_cg_m"],
            lateral_imbalance_limit_kg=st.session_state["draft_lateral_limit_kg"],
        ), []
    except ValueError as error:
        return base_aircraft, [str(error)]


def _scenario_data_editor(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    """Render a separate transactional editor with template, Save and Cancel semantics."""
    st.markdown("## Scenario Data")
    st.caption("Build an aircraft scenario here. The dashboard changes only after Save changes.")

    templates = scenario_templates(sample_rows)
    with st.container(border=True, key="template_gallery"):
        st.markdown("#### Start from a scenario template")
        selected_template = st.radio(
            "Scenario template",
            list(templates),
            horizontal=True,
            key="selected_scenario_template",
        )
        template_detail, apply_col = st.columns([4, 1], vertical_alignment="center")
        template_detail.caption(templates[selected_template]["description"])
        if apply_col.button("Use template", icon=":material/content_copy:", use_container_width=True):
            st.session_state["scenario_draft_rows"] = normalise_rows(templates[selected_template]["rows"])
            st.session_state["scenario_draft_revision"] += 1
            st.rerun()

    aircraft_tab, cargo_tab = st.tabs(["Aircraft limits", "Cargo manifest"])
    with aircraft_tab:
        st.markdown("### Aircraft operating envelope")
        st.caption("Bay topology, arms and adjacency remain fixed by the ALT-8 aircraft template.")
        first, second, third = st.columns(3)
        first.number_input("Maximum payload (kg)", min_value=1.0, step=100.0, key="draft_max_payload_kg")
        second.number_input("Target CG (m)", step=0.1, format="%.2f", key="draft_target_cg_m")
        third.number_input("Lateral imbalance limit (kg)", min_value=0.0, step=25.0,
                           key="draft_lateral_limit_kg")
        cg_min_col, cg_max_col = st.columns(2)
        cg_min_col.number_input("CG minimum (m)", step=0.1, format="%.2f", key="draft_cg_min_m")
        cg_max_col.number_input("CG maximum (m)", step=0.1, format="%.2f", key="draft_cg_max_m")

    with cargo_tab:
        st.markdown("### Cargo manifest builder")
        st.caption("Drag cards to set processing order, then select a cargo item and edit it with constrained controls.")
        cargo_actions, clear_actions, import_actions, export_actions = st.columns([1, 1, 1, 1])
        if cargo_actions.button("Add cargo", icon=":material/add:", use_container_width=True):
            rows = normalise_rows(st.session_state["scenario_draft_rows"])
            rows.append({"cargo_id": f"C{len(rows) + 1}", "name": "New cargo", "weight_kg": 100.0,
                         "category": "General", "hazard_class": "None", "priority": 1})
            st.session_state["scenario_draft_rows"] = rows
            st.session_state["scenario_draft_revision"] += 1
            st.rerun()

        with clear_actions.popover("Clear all", icon=":material/delete_sweep:", use_container_width=True):
            st.markdown("##### Clear manifest?")
            st.caption("Remove all cargo items from the draft manifest. This cannot be undone.")
            if st.button("Yes, clear all cargo", type="primary", use_container_width=True, icon=":material/check:"):
                st.session_state["scenario_draft_rows"] = empty_manifest_rows()
                st.session_state["scenario_draft_revision"] += 1
                st.rerun()

        with import_actions.popover("Import CSV", icon=":material/upload:", use_container_width=True):
            uploaded = st.file_uploader("Choose a manifest", type=["csv"])
            if uploaded is not None:
                rows, upload_errors = import_manifest(uploaded)
                if upload_errors:
                    for error in upload_errors:
                        st.error(error)
                elif st.button("Use imported CSV", type="primary", use_container_width=True):
                    st.session_state["scenario_draft_rows"] = rows
                    st.session_state["scenario_draft_revision"] += 1
                    st.rerun()

        export_actions.download_button(
            "Export draft CSV", manifest_csv(st.session_state["scenario_draft_rows"]),
            "aeroload_scenario_draft.csv", "text/csv", use_container_width=True,
        )

        draft_rows = normalise_rows(st.session_state["scenario_draft_rows"])
        if draft_rows:
            order_col, editor_col = st.columns([1, 2], gap="large")
            labels = [
                f"{index + 1:02d} | {row['cargo_id']} - {row['name']}"
                for index, row in enumerate(draft_rows)
            ]
            with order_col:
                st.markdown("#### Loading order")
                st.caption("Drag a card to reorder the manifest.")
                if sort_items is not None:
                    ordered_labels = sort_items(
                        labels,
                        direction="vertical",
                        key=f"cargo_order_{st.session_state['scenario_draft_revision']}",
                        custom_style="""
                        .sortable-component {background: transparent; padding: 0;}
                        .sortable-item {background: #142238; color: #e5e7eb; border: 1px solid #263244;
                            border-radius: 10px; margin: 7px 0; padding: 12px 14px; cursor: grab;}
                        .sortable-item:hover {background: #19304d; color: #f8fafc;}
                        """,
                    )
                    if ordered_labels != labels:
                        st.session_state["scenario_draft_rows"] = reorder_rows(draft_rows, ordered_labels)
                        st.session_state["scenario_draft_revision"] += 1
                        st.rerun()
                else:
                    st.warning("Install project dependencies to enable drag-and-drop ordering.")
                    st.dataframe(pd.DataFrame(draft_rows)[["cargo_id", "name"]], hide_index=True)

            with editor_col:
                st.markdown("#### Cargo details")
                selected_index = st.selectbox(
                    "Cargo item",
                    range(len(draft_rows)),
                    format_func=lambda index: labels[index],
                    key=f"selected_cargo_{st.session_state['scenario_draft_revision']}",
                )
                row = draft_rows[selected_index]
                with st.form(f"cargo_form_{st.session_state['scenario_draft_revision']}_{selected_index}"):
                    identity_col, name_col = st.columns([1, 2])
                    cargo_id = identity_col.text_input("Cargo ID", value=str(row["cargo_id"]))
                    name = name_col.text_input("Name", value=str(row["name"]))
                    weight_col, priority_col = st.columns(2)
                    weight = weight_col.number_input("Weight (kg)", min_value=0.01, value=float(row["weight_kg"]), step=10.0)
                    priority_options = list(range(1, 6))
                    current_priority = int(float(row["priority"])) if str(row["priority"]).strip() else 1
                    priority = priority_col.selectbox(
                        "Priority",
                        priority_options,
                        index=priority_options.index(current_priority) if current_priority in priority_options else 0,
                    )
                    category_col, hazard_col = st.columns(2)
                    category_options = [item.value for item in CargoCategory]
                    hazard_options = [item.value for item in HazardClass]
                    category = category_col.selectbox(
                        "Category",
                        category_options,
                        index=category_options.index(str(row["category"])) if str(row["category"]) in category_options else 0,
                    )
                    hazard = hazard_col.selectbox(
                        "Hazard class",
                        hazard_options,
                        index=hazard_options.index(str(row["hazard_class"])) if str(row["hazard_class"]) in hazard_options else 0,
                    )
                    remove_col, apply_row_col = st.columns([1, 2])
                    remove_row = remove_col.form_submit_button("Remove cargo", icon=":material/delete:", use_container_width=True)
                    apply_row = apply_row_col.form_submit_button("Apply row changes", type="primary", icon=":material/check:", use_container_width=True)
                if remove_row:
                    draft_rows.pop(selected_index)
                    st.session_state["scenario_draft_rows"] = draft_rows
                    st.session_state["scenario_draft_revision"] += 1
                    st.rerun()
                if apply_row:
                    draft_rows[selected_index] = {
                        "cargo_id": cargo_id,
                        "name": name,
                        "weight_kg": weight,
                        "category": category,
                        "hazard_class": hazard,
                        "priority": priority,
                    }
                    st.session_state["scenario_draft_rows"] = draft_rows
                    st.session_state["scenario_draft_revision"] += 1
                    st.rerun()

            st.markdown("#### Manifest preview")
            st.dataframe(
                pd.DataFrame(draft_rows, columns=MANIFEST_COLUMNS),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "cargo_id": st.column_config.TextColumn("Cargo ID"),
                    "name": st.column_config.TextColumn("Name"),
                    "weight_kg": st.column_config.NumberColumn("Weight (kg)", format="%.1f"),
                    "category": st.column_config.TextColumn("Category"),
                    "hazard_class": st.column_config.TextColumn("Hazard class"),
                    "priority": st.column_config.NumberColumn("Priority"),
                },
            )
        else:
            st.info("The draft manifest is empty. Add cargo manually or import a CSV to continue.")

    draft_aircraft, aircraft_errors = _draft_aircraft(base_aircraft)
    draft_items, manifest_errors = manifest_from_rows(st.session_state["scenario_draft_rows"], allow_empty=True)
    manifest_errors.extend(validate_manifest_for_aircraft(draft_items, draft_aircraft))
    errors = [*aircraft_errors, *manifest_errors]
    if errors:
        for error in errors:
            st.error(error)
    elif draft_items:
        st.success(f"Draft valid · {len(draft_items)} items · {sum(item.weight_kg for item in draft_items):,.0f} kg")
    else:
        st.caption("Draft is empty. Click 'Save changes' to confirm an empty manifest.")

    with st.container(key="scenario_actions"):
        summary_col, cancel_col, save_col = st.columns([3, 1, 1])
        summary_col.caption("Draft changes stay isolated until saved. Cancel restores the active scenario.")
        if cancel_col.button("Cancel", use_container_width=True, icon=":material/close:"):
            _discard_scenario_draft()
            st.rerun()
        if save_col.button("Save changes", type="primary", use_container_width=True,
                           icon=":material/check:", disabled=bool(errors)):
            st.session_state["manifest_rows"] = normalise_rows(st.session_state["scenario_draft_rows"])
            st.session_state["manifest_revision"] += 1
            for active_key in ("max_payload_kg", "cg_min_m", "cg_max_m", "target_cg_m", "lateral_limit_kg"):
                st.session_state[active_key] = st.session_state[f"draft_{active_key}"]
            # Reconcile manual assignments with newly saved cargo
            saved_ids = {str(row["cargo_id"]).strip() for row in st.session_state["manifest_rows"] if str(row["cargo_id"]).strip()}
            st.session_state["manual_assignments"] = {
                cid: bid for cid, bid in st.session_state.get("manual_assignments", {}).items() if cid in saved_ids
            }
            st.session_state.pop("analysis_result", None)
            st.session_state.pop("analysis_csp", None)
            st.session_state.pop("analysis_fingerprint", None)
            _discard_scenario_draft()
            st.rerun()


def _assignment_frame(csp: AeroLoadCSP, assignment: dict[str, str]) -> pd.DataFrame:
    rows = []
    for cargo_id, bay_id in assignment.items():
        cargo, bay = csp.get_cargo(cargo_id), csp.get_bay(bay_id)
        rows.append({"Cargo ID": cargo_id, "Name": cargo.name, "Bay": bay_id, "Side": bay.side.value,
                     "Arm (m)": bay.longitudinal_arm_m, "Weight (kg)": cargo.weight_kg,
                     "Bay use (%)": round(cargo.weight_kg / bay.max_weight_kg * 100, 1),
                     "Hazard": cargo.hazard_class.value})
    return pd.DataFrame(rows)


def run_dashboard() -> None:
    st.set_page_config(page_title="AeroLoad-AI", page_icon="✈", layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(get_global_css(), unsafe_allow_html=True)
    base_aircraft, sample_cargo, knowledge = load_project_data()
    sample_rows = cargo_rows(sample_cargo)
    _initialize_state(base_aircraft, sample_rows)
    aircraft, config_errors = _configured_aircraft(base_aircraft)

    with st.container(key="app_header"):
        brand_col, aircraft_col, scenario_col, docs_col, settings_col = st.columns(
            [2.25, 1.25, 0.72, 0.58, 0.62],
            vertical_alignment="center",
        )
        with brand_col:
            render_brand()
        with aircraft_col:
            render_aircraft_status(aircraft.name, aircraft.aircraft_id, len(aircraft.bays))
        with scenario_col:
            if st.button("Scenario", icon=":material/database:", use_container_width=True,
                         key="open_scenario_data"):
                _open_scenario_editor()
                st.rerun()
        with docs_col:
            if st.button("Docs", icon=":material/menu_book:", use_container_width=True,
                         key="open_docs"):
                _open_docs()
                st.rerun()
        with settings_col:
            with st.popover("Settings", icon=":material/settings:", use_container_width=True):
                _settings_panel(base_aircraft, sample_rows)

    if st.session_state["scenario_editor_open"]:
        _scenario_data_editor(base_aircraft, sample_rows)
        return
    if st.session_state["docs_open"]:
        render_docs_page(_close_docs)
        return

    cargo_items, manifest_errors = manifest_from_rows(st.session_state["manifest_rows"], allow_empty=True)
    manifest_errors.extend(validate_manifest_for_aircraft(cargo_items, aircraft))
    all_errors = [*config_errors, *manifest_errors]

    # Reconcile manual assignments against current cargo and bays
    current_cargo_ids = {c.cargo_id for c in cargo_items}
    current_bay_ids = {b.bay_id for b in aircraft.bays}
    st.session_state["manual_assignments"] = reconcile_manual_assignments(
        st.session_state.get("manual_assignments", {}), current_cargo_ids, current_bay_ids
    )

    fingerprint = (
        tuple((item.cargo_id, item.name, item.weight_kg, item.category.value,
               item.hazard_class.value, item.priority) for item in cargo_items),
        aircraft.max_payload_kg, aircraft.cg_min_m, aircraft.cg_max_m, aircraft.target_cg_m,
        aircraft.lateral_imbalance_limit_kg, st.session_state["enable_optimization"],
        st.session_state["optimization_iterations"],
    )
    stored_result = st.session_state.get("analysis_result")
    result_is_current = stored_result is not None and st.session_state.get("analysis_fingerprint") == fingerprint

    # KPI Strip
    kpi_slot = st.container()
    with kpi_slot:
        payload = sum(item.weight_kg for item in cargo_items)
        render_kpi_strip(
            item_count=len(cargo_items), bay_count=len(aircraft.bays), payload_kg=payload,
            max_payload_kg=aircraft.max_payload_kg, target_cg_m=aircraft.target_cg_m,
            cg_min_m=aircraft.cg_min_m, cg_max_m=aircraft.cg_max_m,
            analysis_current=result_is_current and bool(cargo_items),
        )

    # Mode Selector
    st.markdown("<div class='section-label'>Planning & Operations Mode</div>", unsafe_allow_html=True)
    mode_col, info_col = st.columns([2.2, 1], vertical_alignment="center")
    with mode_col:
        planning_mode = st.radio(
            "Planning mode",
            ["Auto Solve", "Manual Planning", "AI-Assisted Planning"],
            index=["Auto Solve", "Manual Planning", "AI-Assisted Planning"].index(
                st.session_state.get("planning_mode", "Auto Solve")
            ),
            horizontal=True,
            key="planning_mode",
            label_visibility="collapsed",
        )
    with info_col:
        if planning_mode == "Auto Solve":
            st.caption("🤖 **Auto Solve**: AC-3 propagation + MRV/LCV search + hill climbing")
        elif planning_mode == "Manual Planning":
            st.caption("🖐️ **Manual Planning**: Interactive placement with live constraint validation")
        else:
            st.caption("🧠 **AI-Assisted**: Live CSP domain inspection and guidance")

    with st.expander("🎓 How AeroLoad-AI Solves This — AI Architecture & Pipeline", expanded=False):
        st.markdown(
            """
**AeroLoad-AI** formulates aircraft cargo loading as a **Constraint Satisfaction Problem (CSP)** combined with **Local Search Optimization**, strictly adhering to classical AI foundations (Russell & Norvig, Units I–III):

- **Knowledge Base**: Stores simplified cargo-hazard incompatibility relationships separately from the solver.
- **CSP**: Models each cargo item as a variable and available bays as its domain.
- **AC-3**: Removes unsupported bay values from CSP domains before search.
- **MRV**: Selects the unassigned cargo having the fewest remaining legal bay choices (fail-first heuristic).
- **LCV**: Orders bay choices so that remaining cargo retains as many options as possible (fail-last heuristic).
- **Backtracking**: Tries assignments recursively and reverses decisions when a branch cannot produce a valid solution.
- **Hill Climbing**: Improves a complete safe solution using valid MOVE and SWAP neighboring assignments.
- **Explainability**: Converts constraint and optimization results into human-readable reasons.
            """
        )

    current_csp = AeroLoadCSP(aircraft=aircraft, cargo_items=cargo_items, knowledge_base=knowledge)
    workspace_slot = st.container()
    charts_slot = st.container()
    tabs_slot = st.container()

    # =========================================================================
    # WORKSPACE RENDERING BY MODE
    # =========================================================================
    with workspace_slot:
        st.markdown("<div class='section-label'>Aircraft load workspace</div>", unsafe_allow_html=True)

        if not cargo_items:
            st.info("No cargo has been added yet. Add cargo manually or import a CSV in Scenario Data to begin.")

        # ---------------------------------------------------------------------
        # MODE 1: AUTO SOLVE
        # ---------------------------------------------------------------------
        if planning_mode == "Auto Solve":
            deck_col, control_col = st.columns([2.1, 1])
            result = stored_result if result_is_current else None
            with deck_col:
                if result and result.final_assignment:
                    render_aircraft_layout(current_csp, result.final_assignment, mode="AUTO")
                else:
                    render_aircraft_layout(current_csp, {}, mode="AUTO")

            with control_col:
                with st.container(border=True):
                    st.markdown("### Dispatch analysis")
                    render_status_pill("Preflight", "Ready" if not all_errors and cargo_items else "Blocked")
                    st.caption("AC-3 propagation · MRV/LCV search · safety validation · optional local optimization")
                    for error in config_errors:
                        st.error(error)
                    if not result_is_current and stored_result is not None:
                        st.warning("Inputs changed. Run the solver again to refresh the plan.")
                    if not cargo_items:
                        st.caption("Add at least one cargo item to run the solver.")
                    run_solver = st.button("Run AeroLoad-AI", type="primary", use_container_width=True,
                                           disabled=bool(all_errors) or not cargo_items, icon=":material/flight_takeoff:")
                    st.caption(f"Optimization {'on' if st.session_state['enable_optimization'] else 'off'} · "
                               f"{st.session_state['optimization_iterations']} iteration limit")
                if run_solver:
                    with st.spinner("Solving placement, validating safety and evaluating balance..."):
                        current_result = analyze_loading_problem(
                            current_csp, optimize=st.session_state["enable_optimization"],
                            max_optimization_iterations=int(st.session_state["optimization_iterations"]),
                        )
                    st.session_state["analysis_result"] = current_result
                    st.session_state["analysis_csp"] = current_csp
                    st.session_state["analysis_fingerprint"] = fingerprint
                    st.rerun()

            # Show auto-solver telemetry
            if result and result.final_assignment:
                assignments = assignment_to_cargo_assignments(current_csp, result.final_assignment)
                safety_report = validate_loading_plan(aircraft, assignments)
                left_kg, right_kg = calculate_side_weights(assignments)
                initial_cg = (result.optimization_result.initial_quality.cg_m
                              if result.optimization_result else safety_report.cg_m)
                final_cg = safety_report.cg_m
                with charts_slot:
                    cg_col, lateral_col = st.columns(2)
                    cg_col.plotly_chart(cg_envelope_figure(
                        cg_min_m=aircraft.cg_min_m, cg_max_m=aircraft.cg_max_m,
                        target_m=aircraft.target_cg_m, initial_m=initial_cg, final_m=final_cg),
                        use_container_width=True, config={"displayModeBar": False})
                    lateral_col.plotly_chart(lateral_balance_figure(
                        left_kg=left_kg, right_kg=right_kg,
                        limit_kg=aircraft.lateral_imbalance_limit_kg),
                        use_container_width=True, config={"displayModeBar": False})

                assignment_frame = _assignment_frame(current_csp, result.final_assignment)
                with tabs_slot:
                    load_tab, safety_tab, optimization_tab, audit_tab, manifest_tab = st.tabs(
                        ["Load Plan", "Safety & Hazmat", "Optimization", "AI Solver Audit", "Manifest"]
                    )
                    with load_tab:
                        st.markdown("### Final aircraft load plan")
                        a, b, c, d = st.columns(4)
                        a.metric("Payload", f"{safety_report.total_payload_kg:,.0f} kg")
                        b.metric("Final CG", f"{safety_report.cg_m:+.3f} m")
                        c.metric("Lateral imbalance", f"{safety_report.lateral_imbalance_kg:,.0f} kg")
                        d.metric("Safety", "PASS" if safety_report.safe else "FAIL")
                        st.dataframe(assignment_frame, use_container_width=True, hide_index=True)
                        st.download_button("Export final plan CSV", assignment_frame.to_csv(index=False).encode("utf-8"),
                                           "aeroload_final_plan.csv", "text/csv")
                    with safety_tab:
                        if result.loading_explanation:
                            for item in result.loading_explanation.items:
                                message = f"**{item.category}:** {item.message}"
                                st.success(message) if item.status == "PASS" else st.error(message) if item.status == "FAIL" else st.info(message)
                    with optimization_tab:
                        optimization = result.optimization_result
                        if optimization is None:
                            st.info("Optimization was disabled for this run.")
                        else:
                            o1, o2, o3, o4 = st.columns(4)
                            o1.metric("Initial score", f"{optimization.initial_quality.score:.4f}")
                            o2.metric("Final score", f"{optimization.final_quality.score:.4f}")
                            o3.metric("Candidates", optimization.candidates_evaluated)
                            o4.metric("Improvements", optimization.improvements)
                            for step in optimization.steps:
                                with st.container(border=True):
                                    st.markdown(f"**Iteration {step.iteration} · {step.move_type}**")
                                    st.write(step.description)
                                    st.caption(f"Score {step.score_before:.4f} → {step.score_after:.4f} · CG {step.cg_before_m:+.3f} → {step.cg_after_m:+.3f} m")
                            if not optimization.steps:
                                st.info("The initial safe solution was already a local optimum.")
                    with audit_tab:
                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("Nodes explored", result.solver_result.nodes_explored)
                        s1.caption("CSP search states")
                        s2.metric("Backtracks", result.solver_result.backtracks)
                        s2.caption("Dead-ends recovered")
                        s3.metric("AC-3 values pruned", result.solver_result.ac3_values_pruned)
                        s3.caption("Unsupported values removed")
                        s4.metric("AC-3 arcs processed", result.solver_result.ac3_arcs_processed)
                        s4.caption("Directed constraints checked")
                        st.info("Pipeline preserved: AC-3 constraint propagation → MRV/LCV backtracking → safety validation → optional local search → explanations.")
                    with manifest_tab:
                        _render_manifest_tab()
            else:
                with charts_slot:
                    st.info("Run AeroLoad-AI to generate live CG and lateral-balance telemetry.")
                with tabs_slot:
                    _render_fallback_tabs()

        # ---------------------------------------------------------------------
        # MODE 2: MANUAL PLANNING
        # ---------------------------------------------------------------------
        elif planning_mode == "Manual Planning":
            manual_assignments = st.session_state.get("manual_assignments", {})
            manual_status = validate_manual_plan(aircraft, cargo_items, manual_assignments, knowledge)

            deck_col, control_col = st.columns([2.1, 1])
            with deck_col:
                render_aircraft_layout(current_csp, manual_assignments, mode="MANUAL")

            with control_col:
                with st.container(border=True):
                    st.markdown("### Manual Load Planning")
                    if cargo_items:
                        cargo_labels = [
                            f"{c.cargo_id} · {c.name} ({c.weight_kg:,.0f} kg, {c.hazard_class.value})"
                            + (f" → [{manual_assignments[c.cargo_id]}]" if c.cargo_id in manual_assignments else "")
                            for c in cargo_items
                        ]
                        selected_idx = st.selectbox(
                            "Select cargo to place",
                            range(len(cargo_items)),
                            format_func=lambda i: cargo_labels[i],
                            key="manual_cargo_select",
                        )
                        selected_cargo = cargo_items[selected_idx]

                        bay_options_list = [b.bay_id for b in aircraft.bays]
                        current_bay = manual_assignments.get(selected_cargo.cargo_id)
                        default_bay_idx = bay_options_list.index(current_bay) if current_bay in bay_options_list else 0
                        target_bay = st.selectbox("Target bay", bay_options_list, index=default_bay_idx, key="manual_bay_select")

                        assign_col, unassign_col = st.columns(2)
                        if assign_col.button("Place cargo", type="primary", use_container_width=True, icon=":material/done:"):
                            st.session_state["manual_assignments"] = assign_cargo_manually(
                                manual_assignments, selected_cargo.cargo_id, target_bay
                            )
                            st.rerun()

                        if unassign_col.button("Remove", use_container_width=True, icon=":material/close:",
                                               disabled=selected_cargo.cargo_id not in manual_assignments):
                            st.session_state["manual_assignments"] = unassign_cargo_manually(
                                manual_assignments, selected_cargo.cargo_id
                            )
                            st.rerun()

                        if st.button("Reset all placements", use_container_width=True, icon=":material/refresh:"):
                            st.session_state["manual_assignments"] = clear_manual_assignments()
                            st.rerun()
                    else:
                        st.caption("No cargo available to place.")

                # Manual Plan Summary
                with st.container(border=True):
                    st.markdown("#### Plan summary")
                    s1, s2 = st.columns(2)
                    s1.metric("Assigned", f"{manual_status.assigned_count}/{manual_status.total_count}")
                    s2.metric("Occupied bays", f"{manual_status.occupied_bays}/{manual_status.total_bays}")

                    if manual_status.payload_kg > 0:
                        p1, p2 = st.columns(2)
                        p1.metric("Payload", f"{manual_status.payload_kg:,.0f} kg")
                        if manual_status.cg_preview is not None:
                            p2.metric("CG position", f"{manual_status.cg_preview:+.3f} m")

                    if manual_status.is_complete:
                        render_status_pill("Plan Status", "SAFE" if manual_status.is_valid else "UNSAFE")
                    else:
                        render_status_pill("Plan", "INCOMPLETE")
                    st.caption(manual_status.message)

                    if manual_status.violations:
                        for violation in manual_status.violations:
                            st.error(violation)

            # Telemetry for complete manual plan
            if manual_status.is_complete and manual_status.safety_report:
                assignments = assignment_to_cargo_assignments(current_csp, manual_assignments)
                left_kg, right_kg = calculate_side_weights(assignments)
                with charts_slot:
                    cg_col, lateral_col = st.columns(2)
                    cg_col.plotly_chart(cg_envelope_figure(
                        cg_min_m=aircraft.cg_min_m, cg_max_m=aircraft.cg_max_m,
                        target_m=aircraft.target_cg_m, initial_m=None, final_m=manual_status.safety_report.cg_m),
                        use_container_width=True, config={"displayModeBar": False})
                    lateral_col.plotly_chart(lateral_balance_figure(
                        left_kg=left_kg, right_kg=right_kg,
                        limit_kg=aircraft.lateral_imbalance_limit_kg),
                        use_container_width=True, config={"displayModeBar": False})
            else:
                with charts_slot:
                    st.info("Assign all cargo items to view full flight envelope telemetry.")

        # ---------------------------------------------------------------------
        # MODE 3: AI-ASSISTED PLANNING
        # ---------------------------------------------------------------------
        else:
            manual_assignments = st.session_state.get("manual_assignments", {})
            manual_status = validate_manual_plan(aircraft, cargo_items, manual_assignments, knowledge)

            if cargo_items:
                cargo_labels = [
                    f"{c.cargo_id} · {c.name} ({c.weight_kg:,.0f} kg, {c.hazard_class.value})"
                    + (f" → [{manual_assignments[c.cargo_id]}]" if c.cargo_id in manual_assignments else "")
                    for c in cargo_items
                ]
                selected_idx = st.selectbox(
                    "Select cargo to inspect & place",
                    range(len(cargo_items)),
                    format_func=lambda i: cargo_labels[i],
                    key="ai_assisted_cargo_select",
                )
                selected_cargo = cargo_items[selected_idx]
                domain_analysis = evaluate_bay_options(current_csp, selected_cargo.cargo_id, manual_assignments)
            else:
                selected_cargo = None
                domain_analysis = None

            deck_col, control_col = st.columns([2.1, 1])
            with deck_col:
                render_aircraft_layout(
                    current_csp,
                    manual_assignments,
                    mode="AI_ASSISTED",
                    selected_cargo_id=selected_cargo.cargo_id if selected_cargo else None,
                    bay_options=domain_analysis.bay_options if domain_analysis else None,
                )

            with control_col:
                if selected_cargo and domain_analysis:
                    with st.container(border=True):
                        st.markdown(f"### CSP Domain Analysis · `{selected_cargo.cargo_id}`")
                        st.markdown(f"**Variable:** $X_{{{selected_cargo.cargo_id}}}$ ({escape(selected_cargo.name)})")
                        st.caption(f"Weight: {selected_cargo.weight_kg:,.0f} kg · Hazard Class: {selected_cargo.hazard_class.value}")

                        legal_str = ", ".join(domain_analysis.legal_bays) if domain_analysis.legal_bays else "\\emptyset"
                        st.markdown("**Current Legal Domain:**")
                        st.markdown(f"$$D(X_{{{selected_cargo.cargo_id}}}) = \\{{ {legal_str} \\}}$$")

                        st.markdown("**Domain values breakdown:**")
                        for bay in aircraft.bays:
                            opt = domain_analysis.bay_options[bay.bay_id]
                            if opt.status == BayOptionStatus.LEGAL:
                                st.markdown(f"- :green[**{bay.bay_id}**] — ✓ **LEGAL**: {escape(opt.reason)}")
                            elif opt.status == BayOptionStatus.ILLEGAL:
                                st.markdown(f"- :red[**{bay.bay_id}**] — ✕ **BLOCKED**: {escape(opt.reason)}")
                            else:
                                st.markdown(f"- :gray[**{bay.bay_id}**] — ● **OCCUPIED**: {escape(opt.reason)}")

                        st.divider()
                        st.caption("🎓 **Unit II CSP Concept**: Cargo items are variables ($X$) and bays are domain values ($D$). Unary capacity and binary hazard constraints prune inconsistent values from $D(X_i)$.")

                    # Placement actions
                    with st.container(border=True):
                        st.markdown("#### Direct placement")
                        if domain_analysis.legal_bays:
                            st.caption("Click any legal bay below to assign:")
                            btn_cols = st.columns(min(len(domain_analysis.legal_bays), 4))
                            for i, b_id in enumerate(domain_analysis.legal_bays):
                                col = btn_cols[i % len(btn_cols)]
                                if col.button(f"Place {b_id}", key=f"place_btn_{b_id}", type="primary", use_container_width=True):
                                    st.session_state["manual_assignments"] = assign_cargo_manually(
                                        manual_assignments, selected_cargo.cargo_id, b_id
                                    )
                                    st.rerun()
                        else:
                            st.warning("Domain wipeout! No legal bay exists for this cargo under current placements.")

                        un_col, reset_col = st.columns(2)
                        if un_col.button("Remove from bay", use_container_width=True, icon=":material/close:",
                                         disabled=selected_cargo.cargo_id not in manual_assignments):
                            st.session_state["manual_assignments"] = unassign_cargo_manually(
                                manual_assignments, selected_cargo.cargo_id
                            )
                            st.rerun()

                        if reset_col.button("Reset all", use_container_width=True, icon=":material/refresh:"):
                            st.session_state["manual_assignments"] = clear_manual_assignments()
                            st.rerun()
                else:
                    st.caption("Add cargo to inspect CSP domains.")

                # Plan status
                with st.container(border=True):
                    st.markdown("#### Plan summary")
                    s1, s2 = st.columns(2)
                    s1.metric("Assigned", f"{manual_status.assigned_count}/{manual_status.total_count}")
                    s2.metric("Occupied bays", f"{manual_status.occupied_bays}/{manual_status.total_bays}")
                    if manual_status.is_complete:
                        render_status_pill("Plan Status", "SAFE" if manual_status.is_valid else "UNSAFE")
                    else:
                        render_status_pill("Plan", "INCOMPLETE")
                    st.caption(manual_status.message)
                    if manual_status.violations:
                        for violation in manual_status.violations:
                            st.error(violation)

            if manual_status.is_complete and manual_status.safety_report:
                assignments = assignment_to_cargo_assignments(current_csp, manual_assignments)
                left_kg, right_kg = calculate_side_weights(assignments)
                with charts_slot:
                    cg_col, lateral_col = st.columns(2)
                    cg_col.plotly_chart(cg_envelope_figure(
                        cg_min_m=aircraft.cg_min_m, cg_max_m=aircraft.cg_max_m,
                        target_m=aircraft.target_cg_m, initial_m=None, final_m=manual_status.safety_report.cg_m),
                        use_container_width=True, config={"displayModeBar": False})
                    lateral_col.plotly_chart(lateral_balance_figure(
                        left_kg=left_kg, right_kg=right_kg,
                        limit_kg=aircraft.lateral_imbalance_limit_kg),
                        use_container_width=True, config={"displayModeBar": False})
            else:
                with charts_slot:
                    st.info("Assign all cargo items to view full flight envelope telemetry.")

    st.divider()
    st.caption("AeroLoad-AI is an educational simulation project. Aircraft parameters and hazardous-material rules are simplified for academic demonstration and must not be used for real-world flight dispatch or dangerous-goods compliance.")


def _render_manifest_tab() -> None:
    title_col, edit_col = st.columns([3, 1], vertical_alignment="center")
    title_col.markdown("### Active cargo manifest")
    if edit_col.button("Edit scenario data", icon=":material/edit:", use_container_width=True):
        _open_scenario_editor()
        st.rerun()
    st.dataframe(pd.DataFrame(normalise_rows(st.session_state["manifest_rows"])),
                 use_container_width=True, hide_index=True)
    st.download_button("Export manifest CSV", manifest_csv(st.session_state["manifest_rows"]),
                       "aeroload_manifest.csv", "text/csv")


def _render_fallback_tabs() -> None:
    load_tab, safety_tab, optimization_tab, audit_tab, manifest_tab = st.tabs(
        ["Load Plan", "Safety & Hazmat", "Optimization", "AI Solver Audit", "Manifest"]
    )
    with load_tab:
        st.info("No current load plan. Run the solver from the aircraft workspace.")
    with safety_tab:
        st.info("Safety and hazmat checks appear after a successful run.")
    with optimization_tab:
        st.info("Optimization metrics appear after a successful run.")
    with audit_tab:
        st.info("Solver audit statistics appear after a successful run.")
    with manifest_tab:
        _render_manifest_tab()
