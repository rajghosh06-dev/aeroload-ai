"""Modern aviation engineering visual language, container geometry, and responsive styling for AeroLoad-AI."""


def get_global_css() -> str:
    return """
    <style>
    /* =========================================================================
       BASE APPLICATION SURFACES & TYPOGRAPHY
       ========================================================================= */
    html {
        font-size: 14px !important;
        height: 100%;
    }
    body {
        height: 100%;
        margin: 0;
        padding: 0;
    }
    .stApp {
        background-color: #F4F6F3;
        color: #202522;
        font-size: 14px;
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        height: 100vh;
        overflow: hidden;
    }
    section[data-testid="stMain"] {
        height: 100vh;
        max-height: 100vh;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        -webkit-overflow-scrolling: touch;
    }
    [data-testid="stMainBlockContainer"],
    .block-container {
        width: 100%;
        max-width: 1480px;
        margin-left: auto !important;
        margin-right: auto !important;
        box-sizing: border-box;
        padding-top: 0.6rem;
        padding-bottom: 2rem;
        padding-left: clamp(1rem, 2vw, 1.5rem);
        padding-right: clamp(1rem, 2vw, 1.5rem);
    }
    section[data-testid='stSidebar'] {
        display: none;
    }
    header[data-testid='stHeader'],
    header[data-testid='stHeader'] [data-testid='stToolbar'],
    .stAppToolbar {
        background: transparent !important;
        pointer-events: none !important;
    }
    header[data-testid='stHeader'] button,
    header[data-testid='stHeader'] [data-testid='stMainMenu'],
    header[data-testid='stHeader'] [data-testid='stToolbar'] button,
    .stAppToolbar button,
    .stAppToolbar [data-testid='stMainMenu'] {
        pointer-events: auto !important;
    }
    [data-testid='stAppDeployButton'] {
        display: none !important;
    }

    /* High-contrast, accessible vertical scrollbar (cross-browser Chrome, Edge, Firefox) */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #E8ECE6;
    }
    ::-webkit-scrollbar-thumb {
        background: #8F9E93;
        border-radius: 5px;
        border: 2px solid #E8ECE6;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #315C4B;
    }
    * {
        scrollbar-width: thin;
        scrollbar-color: #8F9E93 #E8ECE6;
    }

    /* =========================================================================
       TOP HEADER & TOOLBAR
       ========================================================================= */
    .st-key-app_header {
        position: relative;
        z-index: 1000;
        padding: 0.25rem 0 0.55rem 0;
        border-bottom: 1px solid #D6DBD6;
        background: transparent;
        margin-bottom: 0.5rem;
    }
    .header-left-bar {
        display: flex;
        align-items: center;
        gap: 1.1rem;
        flex-wrap: nowrap;
    }
    .header-pipe {
        width: 1px;
        height: 28px;
        background: #D6DBD6;
        flex: 0 0 auto;
    }
    .top-brand {
        display: flex;
        align-items: center;
        gap: 0.55rem;
    }
    .brand-plane {
        width: 24px;
        height: 24px;
        fill: #315C4B;
        flex: 0 0 auto;
    }
    .top-brand h1 {
        margin: 0;
        color: #202522;
        font-size: 1.22rem;
        font-weight: 650;
        line-height: 1.15;
        letter-spacing: -0.01em;
    }
    .top-brand p {
        margin: 0.05rem 0 0;
        color: #5E6761;
        font-size: 0.74rem;
    }
    .header-aircraft {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.05rem;
        line-height: 1.2;
    }
    .header-aircraft-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #808982;
        font-weight: 600;
    }
    .header-aircraft-value {
        font-size: 0.78rem;
        color: #202522;
        font-weight: 500;
        white-space: nowrap;
    }
    .header-aircraft-value strong {
        color: #202522;
        font-weight: 600;
    }

    /* Toolbar buttons */
    .st-key-app_header .stButton>button,
    .st-key-app_header [data-testid='stPopover'] button,
    .st-key-open_scenario_data button {
        cursor: pointer !important;
        min-height: 32px !important;
        border-radius: 4px !important;
        background: #FFFFFF !important;
        border: 1px solid #D6DBD6 !important;
        color: #202522 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04) !important;
        padding: 0.2rem 0.55rem !important;
        white-space: nowrap !important;
    }
    .st-key-app_header .stButton>button *,
    .st-key-app_header [data-testid='stPopover'] button *,
    .st-key-open_scenario_data button * {
        pointer-events: none !important;
    }
    .st-key-app_header .stButton>button:hover,
    .st-key-app_header [data-testid='stPopover'] button:hover,
    .st-key-open_scenario_data button:hover {
        background: #EEF1ED !important;
        border-color: #BBC4BC !important;
        color: #202522 !important;
    }
    div[data-testid='stPopover']>button {
        cursor: pointer !important;
        min-height: 32px !important;
        border-radius: 4px !important;
        white-space: nowrap !important;
    }

    /* =========================================================================
       SUMMARY AREA (Single horizontal strip with responsive 2x2 fallback)
       ========================================================================= */
    .summary-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04);
        padding: 0.5rem 0.4rem;
        margin: 0.2rem 0 0.15rem;
        box-sizing: border-box;
    }
    .summary-col {
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 0 0.75rem;
        border-right: 1px solid #E7EBE7;
    }
    .summary-col:last-child {
        border-right: none;
    }
    .summary-label {
        font-size: 0.72rem;
        color: #5E6761;
        font-weight: 500;
    }
    .summary-value {
        font-size: 1.15rem;
        color: #202522;
        font-weight: 650;
        line-height: 1.15;
        margin: 0.1rem 0 0.05rem;
        letter-spacing: -0.01em;
    }
    .summary-sub {
        font-size: 0.72rem;
        color: #808982;
    }
    .summary-status-line {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.76rem;
        color: #5E6761;
        margin: 0.2rem 0 0.45rem;
        padding: 0 0.15rem;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
        flex: 0 0 auto;
    }
    .dot-safe {
        background-color: #3E7957;
    }
    .dot-warning {
        background-color: #B9782E;
    }
    .dot-danger {
        background-color: #B34E48;
    }
    .dot-info {
        background-color: #65706A;
    }

    /* =========================================================================
       WORKFLOW INDICATOR (Plain text breadcrumb progress)
       ========================================================================= */
    .workflow-progress {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        font-size: 0.78rem;
        margin: 0.2rem 0 0.55rem;
        padding: 0 0.1rem;
    }
    .workflow-step-text {
        color: #5E6761;
    }
    .workflow-step-text.is-active {
        color: #202522;
        font-weight: 600;
    }
    .workflow-step-text.is-completed {
        color: #3E7957;
    }
    .workflow-sep {
        color: #BBC4BC;
        font-size: 0.76rem;
    }

    /* =========================================================================
       NEUTRAL INFO & NOTICE BANNERS
       ========================================================================= */
    .info-banner {
        background-color: #EEF1ED;
        border: 1px solid #D6DBD6;
        border-left: 3px solid #315C4B;
        border-radius: 4px;
        padding: 0.65rem 0.9rem;
        font-size: 0.82rem;
        color: #202522;
        line-height: 1.45;
        margin-bottom: 0.75rem;
    }
    .info-banner strong {
        color: #202522;
        font-weight: 600;
    }
    .info-banner.is-neutral {
        border-left-color: #BBC4BC;
    }
    .info-banner.is-amber {
        border-left-color: #B9782E;
        background-color: #FBF6EE;
    }

    /* =========================================================================
       ANSWER-FIRST AUTO SOLVE SUMMARY
       ========================================================================= */
    .solver-summary-banner {
        background-color: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-left: 3px solid #3E7957;
        border-radius: 4px;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04);
        padding: 0.7rem 1rem;
        margin-bottom: 0.75rem;
    }
    .solver-summary-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #202522;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .solver-summary-desc {
        font-size: 0.78rem;
        color: #5E6761;
        margin-top: 0.2rem;
    }

    /* =========================================================================
       CONTROL PANELS & CARDS
       ========================================================================= */
    .control-card {
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04);
        padding: 1rem 1.15rem;
        margin-bottom: 0.85rem;
    }
    .control-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #E7EBE7;
        padding-bottom: 0.6rem;
        margin-bottom: 0.75rem;
    }
    .control-title {
        font-size: 0.92rem;
        font-weight: 650;
        color: #202522;
        margin: 0;
    }
    .control-subtitle {
        font-size: 0.78rem;
        color: #5E6761;
        margin: 0.15rem 0 0.5rem;
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 0.15rem 0.55rem;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .status-pill.status-safe {
        background-color: rgba(62, 121, 87, 0.12);
        color: #3E7957;
        border: 1px solid rgba(62, 121, 87, 0.25);
    }
    .status-pill.status-danger {
        background-color: rgba(179, 78, 72, 0.12);
        color: #B34E48;
        border: 1px solid rgba(179, 78, 72, 0.25);
    }
    .status-pill.status-warning {
        background-color: rgba(185, 120, 46, 0.12);
        color: #B9782E;
        border: 1px solid rgba(185, 120, 46, 0.25);
    }
    .status-pill.status-neutral {
        background-color: #E7EBE7;
        color: #5E6761;
        border: 1px solid #D6DBD6;
    }

    /* Section Headings */
    .section-title {
        font-size: 1.05rem;
        font-weight: 650;
        color: #202522;
        margin: 1.1rem 0 0.25rem 0;
        letter-spacing: -0.01em;
    }
    .section-subtitle {
        font-size: 0.8rem;
        color: #5E6761;
        margin: 0 0 0.75rem 0;
    }
    .section-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #808982;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    /* =========================================================================
       AIRCRAFT SCHEMATIC DECK & CG ENVELOPE
       ========================================================================= */
    .deck-shell {
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04);
        padding: 0.65rem 0.85rem;
        margin-bottom: 0.5rem;
    }
    .deck-heading {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #E7EBE7;
        padding-bottom: 0.35rem;
        margin-bottom: 0.35rem;
    }
    .deck-eyebrow {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #808982;
        font-weight: 600;
    }
    .deck-heading h3 {
        margin: 0.05rem 0 0;
        font-size: 0.92rem;
        font-weight: 650;
        color: #202522;
    }
    .deck-legend {
        display: flex;
        gap: 0.65rem;
        font-size: 0.72rem;
        color: #5E6761;
    }
    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
    }
    .legend-item span {
        width: 8px;
        height: 8px;
        border-radius: 2px;
        display: inline-block;
    }
    .legend-general { background: #315C4B; }
    .legend-warning { background: #AD633E; }
    .legend-danger { background: #B34E48; }
    .legend-legal { background: rgba(62, 121, 87, 0.2); border: 1px solid #3E7957; }
    .legend-blocked { background: rgba(179, 78, 72, 0.2); border: 1px solid #B34E48; }
    .legend-occupied { background: #EEF1ED; border: 1px solid #BBC4BC; }

    /* Direction Indicators */
    .direction {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.3rem;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #808982;
        font-weight: 600;
        padding: 0.15rem 0;
    }
    .direction svg {
        width: 12px;
        height: 12px;
        fill: #808982;
    }
    .direction-aft {
        transform: rotate(180deg);
    }

    /* Fuselage & Deck Grid */
    .fuselage {
        position: relative;
        background: #F7F9F6;
        border: 1px solid #D6DBD6;
        border-radius: 4px;
        padding: 0.45rem 0.5rem;
    }
    .centerline {
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 1px;
        border-left: 1px dashed #D6DBD6;
        transform: translateX(-50%);
        pointer-events: none;
    }
    .deck-grid {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .deck-row {
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }
    .deck-row-label {
        width: 44px;
        font-size: 0.68rem;
        font-weight: 600;
        color: #808982;
        text-transform: uppercase;
        flex: 0 0 auto;
        text-align: right;
        padding-right: 0.25rem;
    }
    .deck-row-bays {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.45rem;
        flex: 1 1 auto;
    }

    /* Deck Bay Card */
    .deck-bay {
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 4px;
        padding: 0.35rem 0.5rem;
        min-height: 52px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.15s ease;
        box-sizing: border-box;
    }
    .deck-bay header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.72rem;
        font-weight: 700;
        color: #5E6761;
        margin-bottom: 0.1rem;
    }
    .deck-bay header i {
        font-style: normal;
        font-weight: 400;
        color: #808982;
        font-size: 0.68rem;
    }
    .deck-bay strong {
        font-size: 0.82rem;
        color: #202522;
        font-weight: 650;
        line-height: 1.15;
    }
    .deck-bay span {
        font-size: 0.72rem;
        color: #5E6761;
    }
    .deck-bay small {
        font-size: 0.68rem;
        color: #808982;
        line-height: 1.15;
    }
    .deck-bay em {
        font-style: normal;
        font-size: 0.68rem;
        color: #808982;
        margin-top: 0.05rem;
    }

    /* Bay State & Guidance Borders */
    .deck-bay.is-empty {
        background: #F7F9F6;
        border: 1px dashed #D6DBD6;
    }
    .deck-bay.bay-occupied {
        background: #EEF1ED;
        border: 1px solid #BBC4BC;
    }
    .deck-bay.bay-assigned-current {
        border: 2px solid #315C4B;
        background: #FFFFFF;
    }
    .deck-bay.bay-legal {
        border: 2px solid #3E7957;
        background: rgba(62, 121, 87, 0.06);
    }
    .deck-bay.bay-illegal {
        border: 1.5px solid #B34E48;
        background: rgba(179, 78, 72, 0.05);
    }

    /* Bay Semantic Tones */
    .deck-bay.bay-general {
        border-left: 3px solid #315C4B;
        background: rgba(49, 92, 75, 0.02);
    }
    .deck-bay.bay-food {
        border-left: 3px solid #65706A;
    }
    .deck-bay.bay-warning {
        border-left: 3px solid #AD633E;
        background: rgba(173, 99, 62, 0.03);
    }
    .deck-bay.bay-lithium {
        border-left: 3px solid #AD633E;
        background: rgba(173, 99, 62, 0.03);
    }
    .deck-bay.bay-flammable {
        border-left: 3px solid #B34E48;
        background: rgba(179, 78, 72, 0.03);
    }
    .deck-bay.bay-toxic {
        border-left: 3px solid #8E4A7D;
        background: rgba(142, 74, 125, 0.03);
    }

    .bay-guidance-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 0.08rem 0.35rem;
        border-radius: 3px;
        margin-top: 0.15rem;
        width: fit-content;
    }
    .guidance-legal {
        background: rgba(62, 121, 87, 0.15);
        color: #3E7957;
    }
    .guidance-illegal {
        background: rgba(179, 78, 72, 0.15);
        color: #B34E48;
    }
    .guidance-occupied {
        background: #E7EBE7;
        color: #5E6761;
    }
    .guidance-selected {
        background: rgba(49, 92, 75, 0.15);
        color: #315C4B;
    }

    /* CG Envelope Card */
    .cg-card {
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04);
        padding: 0.65rem 0.85rem;
        margin-bottom: 0.5rem;
    }
    .cg-heading {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #E7EBE7;
        padding-bottom: 0.35rem;
        margin-bottom: 0.5rem;
    }
    .cg-heading h3 {
        margin: 0.05rem 0 0;
        font-size: 0.92rem;
        font-weight: 650;
        color: #202522;
    }
    .cg-reading {
        font-size: 0.88rem;
        font-weight: 650;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .cg-reading span {
        font-size: 0.72rem;
        font-weight: 500;
        padding: 0.1rem 0.4rem;
        border-radius: 3px;
    }
    .cg-reading.cg-safe { color: #3E7957; }
    .cg-reading.cg-safe span { background: rgba(62, 121, 87, 0.15); color: #3E7957; }
    .cg-reading.cg-danger { color: #B34E48; }
    .cg-reading.cg-danger span { background: rgba(179, 78, 72, 0.15); color: #B34E48; }
    .cg-scale {
        position: relative;
        height: 22px;
        background: #EEF1ED;
        border: 1px solid #D6DBD6;
        border-radius: 3px;
        margin: 0.35rem 0;
    }
    .cg-safe-band {
        position: absolute;
        left: 20%;
        width: 60%;
        top: 0;
        bottom: 0;
        background: rgba(62, 121, 87, 0.12);
        border-left: 1px solid #3E7957;
        border-right: 1px solid #3E7957;
    }
    .cg-target, .cg-marker {
        position: absolute;
        top: 0;
        bottom: 0;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .cg-target i {
        width: 2px;
        height: 100%;
        background: #AD633E;
        display: block;
    }
    .cg-marker i {
        width: 2px;
        height: 100%;
        display: block;
    }
    .cg-marker.cg-safe i { background: #3E7957; }
    .cg-marker.cg-danger i { background: #B34E48; }
    .cg-target span, .cg-marker span {
        font-size: 0.62rem;
        position: absolute;
        top: -14px;
        white-space: nowrap;
        font-weight: 600;
    }
    .cg-target span { color: #AD633E; }
    .cg-marker.cg-safe span { color: #3E7957; }
    .cg-marker.cg-danger span { color: #B34E48; }
    .cg-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.68rem;
        color: #808982;
        margin-top: 0.2rem;
    }

    /* =========================================================================
       DOCUMENTATION & TECHNICAL REFERENCE COMPONENTS
       ========================================================================= */
    .st-key-docs_header_bar {
        max-width: 1020px;
        margin: 0.25rem auto 1rem auto;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid #D6DBD6;
    }
    .st-key-docs_header_bar h2 {
        margin: 0;
        color: #202522;
        font-size: 1.35rem;
        font-weight: 650;
        line-height: 1.2;
        letter-spacing: -0.01em;
    }
    .st-key-docs_header_bar p {
        margin: 0.15rem 0 0 0;
        color: #5E6761;
        font-size: 0.8rem;
    }
    .st-key-docs_header_bar div[data-testid='stSelectbox'] label {
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        color: #5E6761 !important;
        margin-bottom: 0.15rem !important;
    }
    .st-key-docs_header_bar div[data-testid='stSelectbox'] div[data-baseweb='select'] {
        min-height: 34px !important;
    }
    .st-key-docs_header_bar div[data-testid='stSelectbox'] div[data-baseweb='select'] > div {
        border-color: #D6DBD6 !important;
        border-radius: 4px !important;
        background-color: #FFFFFF !important;
        min-height: 34px !important;
        font-size: 0.84rem !important;
    }
    .st-key-docs_header_bar div[data-testid='stSelectbox'] div[data-baseweb='select']:hover > div {
        border-color: #315C4B !important;
    }

    /* Back to dashboard button */
    .st-key-docs_back_btn button {
        min-height: 34px !important;
        border-radius: 4px !important;
        background: #FFFFFF !important;
        border: 1px solid #D6DBD6 !important;
        color: #202522 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04) !important;
    }
    .st-key-docs_back_btn button:hover {
        background: #EEF1ED !important;
        border-color: #BBC4BC !important;
        color: #202522 !important;
    }

    /* Documentation reading pane: centered, technical reference document */
    .st-key-docs_reading_pane {
        max-width: 1020px;
        margin: 0 auto 2.5rem auto;
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04);
        padding: 1.75rem 2.25rem 2rem 2.25rem;
        line-height: 1.62;
        color: #202522;
        box-sizing: border-box;
    }
    .docs-topic-header {
        margin-bottom: 1.4rem;
        border-bottom: 1px solid #E7EBE7;
        padding-bottom: 0.75rem;
    }
    .docs-topic-title {
        font-size: 1.42rem;
        font-weight: 700;
        color: #202522;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.01em;
    }
    .docs-topic-subtitle {
        font-size: 0.88rem;
        color: #5E6761;
        margin: 0;
    }

    .st-key-docs_reading_pane h1 {
        font-size: 1.3rem;
        font-weight: 700;
        color: #202522;
        margin: 1.25rem 0 0.5rem 0;
    }
    .st-key-docs_reading_pane h2 {
        font-size: 1.15rem;
        font-weight: 650;
        color: #202522;
        margin: 1.15rem 0 0.45rem 0;
        border-bottom: 1px solid #E7EBE7;
        padding-bottom: 0.35rem;
    }
    .st-key-docs_reading_pane h3 {
        font-size: 1.02rem;
        font-weight: 600;
        color: #202522;
        margin: 1rem 0 0.35rem 0;
    }
    .st-key-docs_reading_pane p,
    .st-key-docs_reading_pane li {
        font-size: 0.9rem;
        line-height: 1.62;
        color: #202522;
    }
    .st-key-docs_reading_pane ul,
    .st-key-docs_reading_pane ol {
        margin: 0.4rem 0 0.8rem 1.2rem;
        padding: 0;
    }
    .st-key-docs_reading_pane table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.86rem;
        display: block;
        overflow-x: auto;
    }
    .st-key-docs_reading_pane th,
    .st-key-docs_reading_pane td {
        border: 1px solid #D6DBD6;
        padding: 0.55rem 0.85rem;
        text-align: left;
    }
    .st-key-docs_reading_pane th {
        background: #EEF1ED;
        font-weight: 600;
        color: #202522;
    }
    .st-key-docs_reading_pane pre {
        background: #F7F9F6;
        border: 1px solid #D6DBD6;
        border-radius: 4px;
        padding: 0.85rem 1.1rem;
        overflow-x: auto;
        max-width: 100%;
        font-size: 0.85rem;
    }
    .st-key-docs_reading_pane code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.88em;
    }

    /* Pagination controls */
    .docs-pagination-divider {
        border-top: 1px solid #E7EBE7;
        margin: 2rem 0 1.25rem 0;
    }
    .docs-pagination-indicator {
        text-align: center;
        font-size: 0.82rem;
        font-weight: 550;
        color: #5E6761;
        white-space: nowrap;
        line-height: 32px;
    }
    .st-key-docs_prev_btn button,
    .st-key-docs_next_btn button {
        min-height: 32px !important;
        border-radius: 4px !important;
        background: #FFFFFF !important;
        border: 1px solid #D6DBD6 !important;
        color: #202522 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04) !important;
        padding: 0.2rem 0.65rem !important;
    }
    .st-key-docs_prev_btn button:hover:not(:disabled),
    .st-key-docs_next_btn button:hover:not(:disabled) {
        background: #EEF1ED !important;
        border-color: #BBC4BC !important;
    }
    .st-key-docs_prev_btn button:disabled,
    .st-key-docs_next_btn button:disabled {
        opacity: 0.45 !important;
        cursor: not-allowed !important;
        background: #F4F6F3 !important;
        border-color: #E2E6E2 !important;
    }

    /* Presentation Viewer */
    .presentation-header {
        margin-bottom: 0.75rem;
    }
    .presentation-counter {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #808982;
        font-weight: 600;
    }
    .presentation-title {
        font-size: 1.25rem;
        color: #202522;
        font-weight: 650;
        margin: 0.15rem 0 0.4rem;
        letter-spacing: -0.01em;
    }
    .presentation-nav-wrapper {
        margin-top: 0.85rem;
        padding-top: 0.75rem;
        border-top: 1px solid #E7EBE7;
    }

    /* =========================================================================
       BUTTONS & FORM CONTROLS
       ========================================================================= */
    button[kind="primary"] {
        background-color: #315C4B !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.08) !important;
    }
    button[kind="primary"]:hover {
        background-color: #274B3E !important;
        color: #FFFFFF !important;
    }
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D6DBD6 !important;
        color: #202522 !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04) !important;
    }
    button[kind="secondary"]:hover {
        background-color: #EEF1ED !important;
        border-color: #BBC4BC !important;
    }

    /* Global Radio button / segmented control styling */
    div[data-testid='stRadio'] > label {
        color: #5E6761 !important;
        font-size: 0.8rem !important;
    }
    div[data-testid='stRadio'] label[data-baseweb='radio'] {
        background: #FFFFFF;
        border: 1px solid #D6DBD6;
        border-radius: 4px;
        padding: 0.35rem 0.75rem;
        margin-right: 0.4rem;
    }
    div[data-testid='stRadio'] label[data-baseweb='radio']:has(input:checked) {
        border-color: #315C4B !important;
    }

    /* Tabs styling */
    div[data-testid='stTabs'] [data-baseweb='tab-list'] {
        background-color: transparent !important;
        border-bottom: 1px solid #D6DBD6 !important;
        gap: 1.5rem !important;
    }
    div[data-testid='stTabs'] [data-baseweb='tab'] {
        background-color: transparent !important;
        color: #5E6761 !important;
        border: none !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.1rem !important;
    }
    div[data-testid='stTabs'] [aria-selected='true'] {
        color: #315C4B !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #315C4B !important;
    }
    div[data-testid='stTabs'] [data-baseweb='tab-highlight'] {
        background-color: #315C4B !important;
    }

    /* Expanders */
    div[data-testid='stExpander'] {
        background-color: #FFFFFF !important;
        border: 1px solid #D6DBD6 !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(24, 35, 29, 0.04) !important;
        margin-bottom: 0.5rem !important;
    }
    div[data-testid='stExpander'] summary {
        color: #202522 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }

    /* Alerts */
    div[data-testid='stAlert'] {
        border-radius: 4px !important;
        box-shadow: none !important;
        padding: 0.6rem 0.9rem !important;
        font-size: 0.85rem !important;
    }

    /* Dataframes */
    div[data-testid='stDataFrame'] {
        border: 1px solid #D6DBD6 !important;
        border-radius: 4px !important;
        background: #FFFFFF !important;
    }

    /* Popovers */
    div[data-testid='stPopoverBody'] {
        background-color: #FFFFFF !important;
        border: 1px solid #D6DBD6 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 14px rgba(24, 35, 29, 0.08) !important;
    }

    /* =========================================================================
       RESPONSIVE MEDIA QUERIES
       ========================================================================= */
    @media (max-width: 900px) {
        .summary-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem 0;
            padding: 0.85rem 0.5rem;
        }
        .summary-col:nth-child(2) {
            border-right: none;
        }
        .summary-col:nth-child(1),
        .summary-col:nth-child(2) {
            border-bottom: 1px solid #E7EBE7;
            padding-bottom: 0.65rem;
        }
        .summary-col:nth-child(3),
        .summary-col:nth-child(4) {
            padding-top: 0.35rem;
        }
        .deck-row-bays {
            grid-template-columns: 1fr 1fr;
        }
        .st-key-docs_content_container {
            padding: 1.1rem 1.25rem;
        }
    }

    @media (max-width: 550px) {
        .summary-strip {
            grid-template-columns: 1fr;
            gap: 0.6rem 0;
        }
        .summary-col {
            border-right: none;
            border-bottom: 1px solid #E7EBE7;
            padding-bottom: 0.5rem;
        }
        .summary-col:last-child {
            border-bottom: none;
        }
        .workflow-progress {
            flex-wrap: wrap;
        }
        .deck-row-bays {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """
