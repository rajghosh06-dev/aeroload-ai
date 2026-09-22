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
from ui.components import (
    render_aircraft_status,
    render_brand,
    render_kpi_strip,
    render_status_pill,
    render_workflow_indicator,
)
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
    default_workspace_state,
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


def _to_float(value: object, default: float = 0.0) -> float:
    """Safely convert an arbitrary value to float with fallback."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _to_int(value: object, default: int = 0) -> int:
    """Safely convert an arbitrary value to int with fallback."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return default
    return default


def _initialize_state(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    defaults = default_workspace_state(base_aircraft, sample_rows)
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _apply_workspace_reset(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    """Restore the pristine default session state values before any widgets render."""
    defaults = default_workspace_state(base_aircraft, sample_rows)
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state["manifest_revision"] = _to_int(st.session_state.get("manifest_revision", 0), 0) + 1
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("analysis_csp", None)
    st.session_state.pop("analysis_fingerprint", None)
    for k in list(st.session_state):
        if isinstance(k, str) and (k.startswith("scenario_draft") or k.startswith("draft_")):
            st.session_state.pop(k, None)


def _settings_panel(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    st.markdown("#### Solver preferences")
    st.toggle("Enable local-search optimization", key="enable_optimization")
    st.number_input(
        "Maximum optimization iterations",
        min_value=1,
        max_value=500,
        step=5,
        key="optimization_iterations",
    )
    st.markdown("#### Interface")
    st.toggle(
        "Show technical AI details",
        key="show_technical_details",
        help="Expose formal CSP notation, detailed domain formulas, and algorithm audit stats across all views.",
    )
    st.caption("Cargo items and aircraft limits are edited from 'Edit Scenario', not Settings.")
    st.divider()
    if st.button("Reset workspace", width="stretch", icon=":material/restart_alt:"):
        st.session_state["pending_workspace_reset"] = True
        st.rerun()


def _configured_aircraft(base_aircraft: Aircraft) -> tuple[Aircraft, list[str]]:
    try:
        return configured_aircraft(
            base_aircraft,
            max_payload_kg=_to_float(st.session_state.get("max_payload_kg", base_aircraft.max_payload_kg), base_aircraft.max_payload_kg),
            cg_min_m=_to_float(st.session_state.get("cg_min_m", base_aircraft.cg_min_m), base_aircraft.cg_min_m),
            cg_max_m=_to_float(st.session_state.get("cg_max_m", base_aircraft.cg_max_m), base_aircraft.cg_max_m),
            target_cg_m=_to_float(st.session_state.get("target_cg_m", base_aircraft.target_cg_m), base_aircraft.target_cg_m),
            lateral_imbalance_limit_kg=_to_float(st.session_state.get("lateral_limit_kg", base_aircraft.lateral_imbalance_limit_kg), base_aircraft.lateral_imbalance_limit_kg),
        ), []
    except ValueError as error:
        return base_aircraft, [str(error)]


def _open_scenario_editor() -> None:
    """Create an isolated draft so Cancel never mutates the active scenario."""
    st.session_state["scenario_draft_rows"] = normalise_rows(st.session_state["manifest_rows"])
    st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
    for active_key in ("max_payload_kg", "cg_min_m", "cg_max_m", "target_cg_m", "lateral_limit_kg"):
        st.session_state[f"draft_{active_key}"] = st.session_state[active_key]
    st.session_state["scenario_editor_open"] = True
    st.session_state["docs_open"] = False


def _discard_scenario_draft() -> None:
    for key in list(st.session_state):
        if isinstance(key, str) and (key.startswith("scenario_draft") or key.startswith("draft_")):
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
            max_payload_kg=_to_float(st.session_state.get("draft_max_payload_kg", base_aircraft.max_payload_kg), base_aircraft.max_payload_kg),
            cg_min_m=_to_float(st.session_state.get("draft_cg_min_m", base_aircraft.cg_min_m), base_aircraft.cg_min_m),
            cg_max_m=_to_float(st.session_state.get("draft_cg_max_m", base_aircraft.cg_max_m), base_aircraft.cg_max_m),
            target_cg_m=_to_float(st.session_state.get("draft_target_cg_m", base_aircraft.target_cg_m), base_aircraft.target_cg_m),
            lateral_imbalance_limit_kg=_to_float(st.session_state.get("draft_lateral_limit_kg", base_aircraft.lateral_imbalance_limit_kg), base_aircraft.lateral_imbalance_limit_kg),
        ), []
    except ValueError as error:
        return base_aircraft, [str(error)]


def _scenario_data_editor(base_aircraft: Aircraft, sample_rows: list[dict[str, object]]) -> None:
    """Render a 3-tab transactional scenario editor with Save and Cancel semantics."""
    header_col, close_col = st.columns([4, 1], vertical_alignment="center")
    with header_col:
        st.markdown("## Edit Scenario Data")
        st.caption("Configure the cargo manifest and aircraft limits. Changes apply to the dashboard only after clicking 'Save changes'.")
    with close_col:
        if st.button("Cancel & Return", icon=":material/arrow_back:", width="stretch"):
            _discard_scenario_draft()
            st.rerun()

    manifest_tab, limits_tab, templates_tab = st.tabs([
        "1. Cargo Manifest",
        "2. Aircraft Limits",
        "3. Import & Templates",
    ])

    draft_rows = normalise_rows(st.session_state["scenario_draft_rows"])

    # -------------------------------------------------------------------------
    # TAB 1: CARGO MANIFEST
    # -------------------------------------------------------------------------
    with manifest_tab:
        st.markdown("### Cargo Manifest")
        st.caption("Manage cargo packages to be loaded onto the aircraft.")

        action_col1, action_col2, count_col = st.columns([1, 1, 2], vertical_alignment="center")
        with action_col1:
            if st.button("Add cargo item", icon=":material/add:", type="primary", width="stretch"):
                new_rows = list(draft_rows)
                new_rows.append({
                    "cargo_id": f"C{len(new_rows) + 1}",
                    "name": "New cargo",
                    "weight_kg": 100.0,
                    "category": "General",
                    "hazard_class": "None",
                    "priority": 1,
                })
                st.session_state["scenario_draft_rows"] = new_rows
                st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
                st.rerun()

        with action_col2:
            with st.popover("Clear all cargo", icon=":material/delete_sweep:", width="stretch"):
                st.markdown("##### Clear manifest?")
                st.caption("Remove all cargo items from this draft. This cannot be undone.")
                if st.button("Yes, clear all cargo", type="primary", width="stretch", icon=":material/check:"):
                    st.session_state["scenario_draft_rows"] = empty_manifest_rows()
                    st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
                    st.rerun()

        with count_col:
            total_draft_wt = sum(_to_float(r.get("weight_kg", 0.0)) for r in draft_rows)
            st.caption(f"**Manifest Summary**: {len(draft_rows)} items · {total_draft_wt:,.0f} kg total weight")

        if draft_rows:
            st.dataframe(
                pd.DataFrame(draft_rows, columns=MANIFEST_COLUMNS),
                width="stretch",
                hide_index=True,
                column_config={
                    "cargo_id": st.column_config.TextColumn("Cargo ID", width="small"),
                    "name": st.column_config.TextColumn("Name"),
                    "weight_kg": st.column_config.NumberColumn("Weight (kg)", format="%.1f"),
                    "category": st.column_config.TextColumn("Category"),
                    "hazard_class": st.column_config.TextColumn("Hazard Class"),
                    "priority": st.column_config.NumberColumn("Priority", width="small"),
                },
            )

            # Clean edit form for an item
            with st.expander("✏️ Edit or Remove an Item", expanded=False):
                labels = [
                    f"{index + 1:02d} | {row['cargo_id']} - {row['name']} ({_to_float(row.get('weight_kg', 0.0)):.0f} kg, {row['hazard_class']})"
                    for index, row in enumerate(draft_rows)
                ]
                selected_index = st.selectbox(
                    "Select item to modify",
                    range(len(draft_rows)),
                    format_func=lambda idx: labels[idx],
                    key=f"edit_cargo_sel_{st.session_state['scenario_draft_revision']}",
                )
                row = draft_rows[selected_index]
                with st.form(f"cargo_edit_form_{st.session_state['scenario_draft_revision']}_{selected_index}"):
                    c1, c2 = st.columns([1, 2])
                    c_id = c1.text_input("Cargo ID", value=str(row["cargo_id"]))
                    c_name = c2.text_input("Name", value=str(row["name"]))

                    w1, p1 = st.columns(2)
                    c_weight = w1.number_input("Weight (kg)", min_value=0.01, value=_to_float(row.get("weight_kg", 100.0), default=100.0), step=10.0)
                    priority_options = list(range(1, 6))
                    cur_p = _to_int(row.get("priority", 1), default=1)
                    c_priority = p1.selectbox(
                        "Priority (1 = standard, 5 = urgent)",
                        priority_options,
                        index=priority_options.index(cur_p) if cur_p in priority_options else 0,
                    )

                    cat_col, haz_col = st.columns(2)
                    cat_options = [item.value for item in CargoCategory]
                    haz_options = [item.value for item in HazardClass]
                    c_cat = cat_col.selectbox(
                        "Category",
                        cat_options,
                        index=cat_options.index(str(row["category"])) if str(row["category"]) in cat_options else 0,
                    )
                    c_haz = haz_col.selectbox(
                        "Hazard Class",
                        haz_options,
                        index=haz_options.index(str(row["hazard_class"])) if str(row["hazard_class"]) in haz_options else 0,
                    )

                    apply_clicked = st.form_submit_button("Save changes to item", type="primary", icon=":material/check:", width="stretch")

                del_col, _ = st.columns([1, 1])
                remove_clicked = del_col.button("Delete this item", icon=":material/delete:", width="stretch", help="Remove this cargo item from the manifest")

                if remove_clicked:
                    draft_rows.pop(selected_index)
                    st.session_state["scenario_draft_rows"] = draft_rows
                    st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
                    st.rerun()
                if apply_clicked:
                    draft_rows[selected_index] = {
                        "cargo_id": str(c_id).strip(),
                        "name": str(c_name).strip(),
                        "weight_kg": _to_float(c_weight, default=100.0),
                        "category": str(c_cat),
                        "hazard_class": str(c_haz),
                        "priority": _to_int(c_priority, default=1),
                    }
                    st.session_state["scenario_draft_rows"] = draft_rows
                    st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
                    st.rerun()
        else:
            st.info("No cargo has been added yet. Click 'Add cargo item' or import a CSV to begin.")

    # -------------------------------------------------------------------------
    # TAB 2: AIRCRAFT LIMITS
    # -------------------------------------------------------------------------
    with limits_tab:
        st.markdown("### Aircraft Operating Envelope")
        st.caption("Configure structural and aerodynamic operating limits for the current scenario.")

        r1_col1, r1_col2, r1_col3 = st.columns(3)
        r1_col1.number_input("Maximum payload (kg)", min_value=1.0, step=100.0, key="draft_max_payload_kg",
                             help="Maximum combined weight of all loaded cargo.")
        r1_col2.number_input("Target CG (m)", step=0.1, format="%.2f", key="draft_target_cg_m",
                             help="The preferred aerodynamic balance point used as optimization target.")
        r1_col3.number_input("Lateral imbalance limit (kg)", min_value=0.0, step=25.0, key="draft_lateral_limit_kg",
                             help="Maximum allowable weight difference between left and right bays.")

        r2_col1, r2_col2 = st.columns(2)
        r2_col1.number_input("CG minimum (forward limit, m)", step=0.1, format="%.2f", key="draft_cg_min_m",
                             help="Most forward allowable Center of Gravity position.")
        r2_col2.number_input("CG maximum (aft limit, m)", step=0.1, format="%.2f", key="draft_cg_max_m",
                             help="Most aft allowable Center of Gravity position.")

        with st.expander("ℹ️ Advanced Aircraft Information (Fixed Bay Topology)", expanded=False):
            st.caption("Bay layout, longitudinal arms, and physical adjacency are determined by the ALT-8 airframe model.")
            bay_data = [
                {"Bay": b.bay_id, "Row": b.row, "Side": b.side.value, "Arm (m)": b.longitudinal_arm_m,
                 "Max Capacity (kg)": b.max_weight_kg, "Adjacent Bays": ", ".join(b.adjacent_bays)}
                for b in base_aircraft.bays
            ]
            st.dataframe(pd.DataFrame(bay_data), width="stretch", hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 3: IMPORT & TEMPLATES
    # -------------------------------------------------------------------------
    with templates_tab:
        st.markdown("### Scenario Templates & CSV Transfer")
        st.caption("Quickly populate the manifest using standard teaching scenarios or external CSV files.")

        templates = scenario_templates(sample_rows)
        st.markdown("#### Load a Curated Template")
        selected_template = st.radio(
            "Select scenario template",
            list(templates),
            horizontal=True,
            key="selected_scenario_template",
        )
        t_desc_col, t_apply_col = st.columns([3.5, 1.5], vertical_alignment="center")
        t_desc_col.caption(templates[selected_template]["description"])
        if t_apply_col.button("Apply this template", icon=":material/content_copy:", width="stretch", type="primary"):
            st.session_state["scenario_draft_rows"] = normalise_rows(templates[selected_template]["rows"])
            st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
            st.rerun()

        st.divider()
        st.markdown("#### CSV Import & Export")
        csv_col1, csv_col2 = st.columns(2)
        with csv_col1:
            st.markdown("**Import from CSV**")
            uploaded = st.file_uploader("Upload manifest CSV", type=["csv"], key="draft_csv_uploader")
            if uploaded is not None:
                rows, upload_errors = import_manifest(uploaded)
                if upload_errors:
                    for error in upload_errors:
                        st.error(error)
                elif st.button("Load uploaded CSV into draft", type="primary", width="stretch"):
                    st.session_state["scenario_draft_rows"] = rows
                    st.session_state["scenario_draft_revision"] = _to_int(st.session_state.get("scenario_draft_revision", 0), 0) + 1
                    st.rerun()

        with csv_col2:
            st.markdown("**Export Draft to CSV**")
            st.caption("Download the current draft manifest to a CSV file on your local machine.")
            st.download_button(
                "Download draft CSV",
                manifest_csv(st.session_state["scenario_draft_rows"]),
                "aeroload_scenario_draft.csv",
                "text/csv",
                width="stretch",
                icon=":material/download:",
            )

    # -------------------------------------------------------------------------
    # DRAFT VALIDATION & SAVE / CANCEL ACTION BAR
    # -------------------------------------------------------------------------
    draft_aircraft, aircraft_errors = _draft_aircraft(base_aircraft)
    draft_items, manifest_errors = manifest_from_rows(st.session_state["scenario_draft_rows"], allow_empty=True)
    manifest_errors.extend(validate_manifest_for_aircraft(draft_items, draft_aircraft))
    errors = [*aircraft_errors, *manifest_errors]

    st.divider()
    if errors:
        for error in errors:
            st.error(error)
    elif draft_items:
        st.success(f"✓ Scenario is valid: {len(draft_items)} items · {sum(item.weight_kg for item in draft_items):,.0f} kg payload.")
    else:
        st.info("Scenario draft is currently empty. Click 'Save changes' to confirm an empty manifest.")

    with st.container(key="scenario_actions"):
        summary_col, cancel_col, save_col = st.columns([3, 1, 1])
        summary_col.caption("Draft changes stay isolated until saved. Cancel restores the active scenario.")
        if cancel_col.button("Cancel", width="stretch", icon=":material/close:"):
            _discard_scenario_draft()
            st.rerun()
        if save_col.button("Save changes", type="primary", width="stretch",
                           icon=":material/check:", disabled=bool(errors)):
            st.session_state["manifest_rows"] = normalise_rows(st.session_state["scenario_draft_rows"])
            st.session_state["manifest_revision"] = _to_int(st.session_state.get("manifest_revision", 0), 0) + 1
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
        rows.append({
            "Cargo ID": cargo_id,
            "Name": cargo.name,
            "Bay": bay_id,
            "Side": bay.side.value,
            "Arm (m)": bay.longitudinal_arm_m,
            "Weight (kg)": cargo.weight_kg,
            "Bay use (%)": round(cargo.weight_kg / bay.max_weight_kg * 100, 1),
            "Hazard": cargo.hazard_class.value,
        })
    return pd.DataFrame(rows)


def run_dashboard() -> None:
    st.set_page_config(
        page_title="AeroLoad-AI — Aircraft Cargo Balance Engine",
        page_icon="✈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(get_global_css(), unsafe_allow_html=True)
    base_aircraft, sample_cargo, knowledge = load_project_data()
    sample_rows = cargo_rows(sample_cargo)

    # Lifecycle bug fix: handle pending reset BEFORE any widgets are created
    if st.session_state.pop("pending_workspace_reset", False):
        _apply_workspace_reset(base_aircraft, sample_rows)
    else:
        _initialize_state(base_aircraft, sample_rows)

    aircraft, config_errors = _configured_aircraft(base_aircraft)

    # -------------------------------------------------------------------------
    # TOP HEADER
    # -------------------------------------------------------------------------
    with st.container(key="app_header"):
        brand_col, aircraft_col, scenario_col, docs_col, settings_col = st.columns(
            [2.3, 1.2, 0.9, 0.8, 0.7],
            vertical_alignment="center",
        )
        with brand_col:
            render_brand()
        with aircraft_col:
            render_aircraft_status(aircraft.name, aircraft.aircraft_id, len(aircraft.bays))
        with scenario_col:
            if st.button("Edit Scenario", icon=":material/edit_note:", width="stretch",
                         key="open_scenario_data"):
                _open_scenario_editor()
                st.rerun()
        with docs_col:
            if st.button("Help / Docs", icon=":material/help_outline:", width="stretch",
                         key="open_docs"):
                _open_docs()
                st.rerun()
        with settings_col:
            with st.popover("Settings", icon=":material/settings:", width="stretch"):
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

    # -------------------------------------------------------------------------
    # KPI METRIC STRIP
    # -------------------------------------------------------------------------
    kpi_slot = st.container()
    with kpi_slot:
        payload = sum(item.weight_kg for item in cargo_items)
        render_kpi_strip(
            item_count=len(cargo_items),
            bay_count=len(aircraft.bays),
            payload_kg=payload,
            max_payload_kg=aircraft.max_payload_kg,
            target_cg_m=aircraft.target_cg_m,
            cg_min_m=aircraft.cg_min_m,
            cg_max_m=aircraft.cg_max_m,
            analysis_current=result_is_current and bool(cargo_items),
        )

    # -------------------------------------------------------------------------
    # WORKFLOW INDICATOR (Phase 8B)
    # -------------------------------------------------------------------------
    planning_mode = st.session_state.get("planning_mode", "Auto Solve")
    manual_assignments = st.session_state.get("manual_assignments", {})
    if planning_mode == "Auto Solve":
        current_step = 4 if result_is_current else (3 if cargo_items else 1)
    else:
        current_step = 4 if (len(manual_assignments) == len(cargo_items) and cargo_items) else (3 if cargo_items else 1)

    render_workflow_indicator(current_step)

    # -------------------------------------------------------------------------
    # PLANNING MODE SELECTION (Phase 8E)
    # -------------------------------------------------------------------------
    st.markdown("<div class='section-label'>Planning & Operations Mode</div>", unsafe_allow_html=True)
    mode_descriptions = {
        "Auto Solve": "Let AeroLoad-AI generate a complete, balance-optimized loading plan.",
        "Manual Planning": "Place cargo yourself and let AeroLoad-AI validate your plan.",
        "AI-Assisted Planning": "Place cargo yourself while AeroLoad-AI shows legal and blocked bays.",
    }

    mode_col, info_col = st.columns([2.0, 1.2], vertical_alignment="center")
    with mode_col:
        planning_mode = st.radio(
            "Planning mode",
            ["Auto Solve", "Manual Planning", "AI-Assisted Planning"],
            index=["Auto Solve", "Manual Planning", "AI-Assisted Planning"].index(planning_mode),
            horizontal=True,
            key="planning_mode",
            label_visibility="collapsed",
        )
    with info_col:
        st.caption(f"💡 **{planning_mode}**: {mode_descriptions[planning_mode]}")

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
            st.info("No cargo has been added yet. Click 'Edit Scenario' in the header or import a CSV to begin.")

        # ---------------------------------------------------------------------
        # MODE 1: AUTO SOLVE (Phase 8I)
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
                    st.markdown("### Autonomous Solver")
                    render_status_pill("Pre-Solve", "Ready" if not all_errors and cargo_items else "Blocked")
                    st.caption("AC-3 domain pruning · MRV/LCV search · safety validation · local optimization")
                    for error in config_errors:
                        st.error(error)
                    if not result_is_current and stored_result is not None:
                        st.warning("Inputs changed. Run the solver again to refresh the plan.")
                    if not cargo_items:
                        st.caption("Add at least one cargo item to run the solver.")
                    run_solver = st.button(
                        "Run AeroLoad-AI",
                        type="primary",
                        width="stretch",
                        disabled=bool(all_errors) or not cargo_items,
                        icon=":material/flight_takeoff:",
                    )
                    st.caption(
                        f"Optimization {'enabled' if st.session_state['enable_optimization'] else 'disabled'} · "
                        f"{st.session_state['optimization_iterations']} max iterations"
                    )

                if run_solver:
                    with st.spinner("Solving placement, validating safety and evaluating balance..."):
                        current_result = analyze_loading_problem(
                            current_csp,
                            optimize=bool(st.session_state.get("enable_optimization", True)),
                            max_optimization_iterations=_to_int(st.session_state.get("optimization_iterations", 50), default=50),
                        )
                    st.session_state["analysis_result"] = current_result
                    st.session_state["analysis_csp"] = current_csp
                    st.session_state["analysis_fingerprint"] = fingerprint
                    st.rerun()

            # Show auto-solver results (Lead with the answer!)
            if result and result.final_assignment:
                assignments = assignment_to_cargo_assignments(current_csp, result.final_assignment)
                safety_report = validate_loading_plan(aircraft, assignments)
                left_kg, right_kg = calculate_side_weights(assignments)
                initial_cg = (result.optimization_result.initial_quality.cg_m
                              if result.optimization_result else safety_report.cg_m)
                final_cg = safety_report.cg_m

                # 1. Answer banner
                if safety_report.safe:
                    st.success("✓ Safe loading plan found — passes AeroLoad-AI simulation safety checks (structural, balance and hazard constraints satisfied).", icon=":material/check_circle:")
                else:
                    st.error("✕ Plan violates aircraft constraints.", icon=":material/error:")

                # 2. Key metrics in a clean row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Payload", f"{safety_report.total_payload_kg:,.0f} / {aircraft.max_payload_kg:,.0f} kg")
                m2.metric("Final CG", f"{safety_report.cg_m:+.3f} m")
                m3.metric("Target CG", f"{aircraft.target_cg_m:+.2f} m")
                m4.metric("Lateral Imbalance", f"{safety_report.lateral_imbalance_kg:,.0f} kg",
                          f"Limit: {aircraft.lateral_imbalance_limit_kg:,.0f} kg")

                # 3. CG and balance telemetry charts
                with charts_slot:
                    cg_col, lateral_col = st.columns(2)
                    cg_col.plotly_chart(
                        cg_envelope_figure(
                            cg_min_m=aircraft.cg_min_m,
                            cg_max_m=aircraft.cg_max_m,
                            target_m=aircraft.target_cg_m,
                            initial_m=initial_cg,
                            final_m=final_cg,
                        ),
                        width="stretch",
                        config={"displayModeBar": False},
                    )
                    lateral_col.plotly_chart(
                        lateral_balance_figure(
                            left_kg=left_kg,
                            right_kg=right_kg,
                            limit_kg=aircraft.lateral_imbalance_limit_kg,
                        ),
                        width="stretch",
                        config={"displayModeBar": False},
                    )

                # 4. Secondary technical tabs
                assignment_frame = _assignment_frame(current_csp, result.final_assignment)
                with tabs_slot:
                    load_tab, safety_tab, optimization_tab, audit_tab, manifest_tab = st.tabs(
                        ["Load Plan Table", "Safety Checks", "Optimization Details", "AI Solver Audit", "Manifest"]
                    )
                    with load_tab:
                        st.markdown("#### Aircraft Bay Assignments")
                        st.dataframe(assignment_frame, width="stretch", hide_index=True)
                        st.download_button(
                            "Export load plan CSV",
                            assignment_frame.to_csv(index=False).encode("utf-8"),
                            "aeroload_final_plan.csv",
                            "text/csv",
                            icon=":material/download:",
                        )

                    with safety_tab:
                        st.markdown("#### Safety & Constraint Evaluation")
                        if result.loading_explanation:
                            for item in result.loading_explanation.items:
                                message = f"**{item.category}:** {item.message}"
                                if item.status == "PASS":
                                    st.success(message)
                                elif item.status == "FAIL":
                                    st.error(message)
                                else:
                                    st.info(message)

                    with optimization_tab:
                        st.markdown("#### Hill-Climbing Local Search")
                        optimization = result.optimization_result
                        if optimization is None:
                            st.info("Optimization was disabled for this run.")
                        else:
                            o1, o2, o3, o4 = st.columns(4)
                            o1.metric("Initial score", f"{optimization.initial_quality.score:.4f}")
                            o2.metric("Final score", f"{optimization.final_quality.score:.4f}")
                            o3.metric("Candidates evaluated", optimization.candidates_evaluated)
                            o4.metric("Improvements accepted", optimization.improvements)
                            for step in optimization.steps:
                                with st.container(border=True):
                                    st.markdown(f"**Iteration {step.iteration} · {step.move_type}**")
                                    st.write(step.description)
                                    st.caption(f"Score {step.score_before:.4f} → {step.score_after:.4f} · CG {step.cg_before_m:+.3f} → {step.cg_after_m:+.3f} m")
                            if not optimization.steps:
                                st.info("The initial feasible solution was already a local optimum.")

                    with audit_tab:
                        st.markdown("#### Search & Propagation Statistics")
                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("Nodes explored", result.solver_result.nodes_explored, help="Total search states visited")
                        s2.metric("Backtracks", result.solver_result.backtracks, help="Dead-ends recovered")
                        s3.metric("AC-3 values pruned", result.solver_result.ac3_values_pruned, help="Unsupported bay choices eliminated before search")
                        s4.metric("AC-3 arcs processed", result.solver_result.ac3_arcs_processed, help="Directed constraint pairs evaluated")
                        st.caption("Pipeline: AC-3 constraint propagation → MRV variable selection → LCV value ordering → Backtracking search → Safety validation → Hill climbing.")

                    with manifest_tab:
                        _render_manifest_tab()
            else:
                with charts_slot:
                    st.info("Run AeroLoad-AI to generate live Center of Gravity and lateral balance telemetry.")
                with tabs_slot:
                    _render_fallback_tabs()

        # ---------------------------------------------------------------------
        # MODE 2: MANUAL PLANNING (Phase 8G)
        # ---------------------------------------------------------------------
        elif planning_mode == "Manual Planning":
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
                        selected_cargo = cargo_items[int(selected_idx)] if selected_idx is not None else cargo_items[0]

                        bay_options_list = [b.bay_id for b in aircraft.bays]
                        current_bay = manual_assignments.get(selected_cargo.cargo_id)
                        default_bay_idx = bay_options_list.index(current_bay) if current_bay in bay_options_list else 0
                        target_bay = st.selectbox("Target bay", bay_options_list, index=default_bay_idx, key="manual_bay_select")

                        assign_col, unassign_col = st.columns(2)
                        if assign_col.button("Place cargo", type="primary", width="stretch", icon=":material/done:"):
                            st.session_state["manual_assignments"] = assign_cargo_manually(
                                manual_assignments, selected_cargo.cargo_id, target_bay
                            )
                            st.rerun()

                        if unassign_col.button("Remove", width="stretch", icon=":material/close:",
                                               disabled=selected_cargo.cargo_id not in manual_assignments):
                            st.session_state["manual_assignments"] = unassign_cargo_manually(
                                manual_assignments, selected_cargo.cargo_id
                            )
                            st.rerun()

                        if st.button("Reset all placements", width="stretch", icon=":material/refresh:"):
                            st.session_state["manual_assignments"] = clear_manual_assignments()
                            st.rerun()
                    else:
                        st.caption("No cargo available to place.")

                # Plan Progress & Status
                with st.container(border=True):
                    st.markdown("#### Plan Status")
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Assigned", f"{manual_status.assigned_count}/{manual_status.total_count}")
                    s2.metric("Remaining", f"{manual_status.total_count - manual_status.assigned_count}")
                    s3.metric("Bays used", f"{manual_status.occupied_bays}/{manual_status.total_bays}")

                    if manual_status.payload_kg > 0:
                        p1, p2 = st.columns(2)
                        p1.metric("Payload", f"{manual_status.payload_kg:,.0f} kg")
                        if manual_status.cg_preview is not None:
                            p2.metric("CG position", f"{manual_status.cg_preview:+.3f} m")

                    if manual_status.is_complete:
                        render_status_pill("Status", "SAFE" if manual_status.is_valid else "UNSAFE")
                    else:
                        render_status_pill("Status", "INCOMPLETE")
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
                    cg_col.plotly_chart(
                        cg_envelope_figure(
                            cg_min_m=aircraft.cg_min_m,
                            cg_max_m=aircraft.cg_max_m,
                            target_m=aircraft.target_cg_m,
                            initial_m=None,
                            final_m=manual_status.safety_report.cg_m,
                        ),
                        width="stretch",
                        config={"displayModeBar": False},
                    )
                    lateral_col.plotly_chart(
                        lateral_balance_figure(
                            left_kg=left_kg,
                            right_kg=right_kg,
                            limit_kg=aircraft.lateral_imbalance_limit_kg,
                        ),
                        width="stretch",
                        config={"displayModeBar": False},
                    )
            else:
                with charts_slot:
                    remaining_count = manual_status.total_count - manual_status.assigned_count
                    if remaining_count > 0:
                        st.info(f"{remaining_count} cargo item{'s' if remaining_count != 1 else ''} still require placement to view full flight envelope telemetry.")
                    else:
                        st.info("Assign all cargo items to view full flight envelope telemetry.")

        # ---------------------------------------------------------------------
        # MODE 3: AI-ASSISTED PLANNING (Phase 8H)
        # ---------------------------------------------------------------------
        else:
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
                selected_cargo = cargo_items[int(selected_idx)] if selected_idx is not None else cargo_items[0]
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
                        st.markdown(f"### AI Guidance · `{selected_cargo.cargo_id}`")
                        st.write(f"**{selected_cargo.name}** · {selected_cargo.weight_kg:,.0f} kg")
                        st.caption(f"Category: {selected_cargo.category.value} · Hazard: {selected_cargo.hazard_class.value}")

                        if domain_analysis.legal_bays:
                            st.caption("Click a legal bay to place this cargo:")
                            btn_cols = st.columns(min(len(domain_analysis.legal_bays), 4))
                            for i, b_id in enumerate(domain_analysis.legal_bays):
                                col = btn_cols[i % len(btn_cols)]
                                if col.button(f"Place {b_id}", key=f"place_btn_{b_id}", type="primary", width="stretch"):
                                    st.session_state["manual_assignments"] = assign_cargo_manually(
                                        manual_assignments, selected_cargo.cargo_id, b_id
                                    )
                                    st.rerun()
                        else:
                            st.warning("No legal bays exist for this cargo under current placements.")

                        un_col, reset_col = st.columns(2)
                        if un_col.button("Remove from bay", width="stretch", icon=":material/close:",
                                         disabled=selected_cargo.cargo_id not in manual_assignments):
                            st.session_state["manual_assignments"] = unassign_cargo_manually(
                                manual_assignments, selected_cargo.cargo_id
                            )
                            st.rerun()

                        if reset_col.button("Reset all", width="stretch", icon=":material/refresh:"):
                            st.session_state["manual_assignments"] = clear_manual_assignments()
                            st.rerun()

                    # Progressive disclosure: technical CSP expander
                    with st.expander("🎓 Show CSP Domain Explanation", expanded=st.session_state.get("show_technical_details", False)):
                        st.markdown(f"**Variable:** $X_{{{selected_cargo.cargo_id}}}$")
                        legal_str = ", ".join(domain_analysis.legal_bays) if domain_analysis.legal_bays else "\\emptyset"
                        st.markdown(f"**Current Legal Domain:** $$D(X_{{{selected_cargo.cargo_id}}}) = \\{{ {legal_str} \\}}$$")
                        st.markdown("**Bay evaluation breakdown:**")
                        for bay in aircraft.bays:
                            opt = domain_analysis.bay_options[bay.bay_id]
                            if opt.status == BayOptionStatus.LEGAL:
                                st.markdown(f"- :green[**{bay.bay_id}**] — ✓ **LEGAL**: {escape(opt.reason)}")
                            elif opt.status == BayOptionStatus.ILLEGAL:
                                st.markdown(f"- :red[**{bay.bay_id}**] — ✕ **BLOCKED**: {escape(opt.reason)}")
                            else:
                                st.markdown(f"- :gray[**{bay.bay_id}**] — ● **OCCUPIED**: {escape(opt.reason)}")
                        st.caption("Cargo items are variables ($X$) and bays are domain values ($D$). Constraints prune unviable bays.")

                    # Plan status
                    with st.container(border=True):
                        st.markdown("#### Plan Status")
                        s1, s2 = st.columns(2)
                        s1.metric("Assigned", f"{manual_status.assigned_count}/{manual_status.total_count}")
                        s2.metric("Bays used", f"{manual_status.occupied_bays}/{manual_status.total_bays}")
                        if manual_status.is_complete:
                            render_status_pill("Status", "SAFE" if manual_status.is_valid else "UNSAFE")
                        else:
                            render_status_pill("Status", "INCOMPLETE")
                        st.caption(manual_status.message)
                        if manual_status.violations:
                            for violation in manual_status.violations:
                                st.error(violation)
                else:
                    st.caption("Add cargo to inspect CSP domains.")

            if manual_status.is_complete and manual_status.safety_report:
                assignments = assignment_to_cargo_assignments(current_csp, manual_assignments)
                left_kg, right_kg = calculate_side_weights(assignments)
                with charts_slot:
                    cg_col, lateral_col = st.columns(2)
                    cg_col.plotly_chart(
                        cg_envelope_figure(
                            cg_min_m=aircraft.cg_min_m,
                            cg_max_m=aircraft.cg_max_m,
                            target_m=aircraft.target_cg_m,
                            initial_m=None,
                            final_m=manual_status.safety_report.cg_m,
                        ),
                        width="stretch",
                        config={"displayModeBar": False},
                    )
                    lateral_col.plotly_chart(
                        lateral_balance_figure(
                            left_kg=left_kg,
                            right_kg=right_kg,
                            limit_kg=aircraft.lateral_imbalance_limit_kg,
                        ),
                        width="stretch",
                        config={"displayModeBar": False},
                    )
            else:
                with charts_slot:
                    st.info("Assign all cargo items to view full flight envelope telemetry.")

    st.divider()
    st.caption("AeroLoad-AI is an educational simulation project. Aircraft parameters and hazardous-material rules are simplified for academic demonstration and must not be used for real-world flight dispatch or dangerous-goods compliance.")


def _render_manifest_tab() -> None:
    title_col, edit_col = st.columns([3, 1], vertical_alignment="center")
    with title_col:
        st.markdown("### Active cargo manifest")
    with edit_col:
        if st.button("Edit scenario data", icon=":material/edit:", width="stretch"):
            _open_scenario_editor()
            st.rerun()
    st.dataframe(pd.DataFrame(normalise_rows(st.session_state["manifest_rows"])),
                 width="stretch", hide_index=True)
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
