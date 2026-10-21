"""Shared visual styling for the Streamlit application inspired by monday.com design language."""

import streamlit as st


def apply_app_theme() -> None:
    """Apply the modern, professional SaaS visual theme with pastel accents and pill shapes."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* ── Monday.com Design Tokens ──────────────────────────────────── */
        :root {
            /* Colors */
            --color-monday-violet: #6161ff;
            --color-monday-violet-hover: #4b4be0;
            --color-ink: #333333;
            --color-slate: #535768;
            --color-iron: #808080;
            --color-fog: #cacbcd;
            --color-mist: #d0d4e4;
            --color-pebble: #dddfeb;
            --color-cloud: #f5f6f8;
            --color-snow: #ffffff;
            --color-shadow-dust: #e6e7ea;

            /* Pastels */
            --color-mint: #bcfe90;
            --color-mint-soft: #f0fce8;
            --color-mint-dark: #1b5e20;
            --color-sky: #abf0ff;
            --color-sky-soft: #edfaff;
            --color-apricot: #ff8940;
            --color-apricot-soft: #fff2ea;
            --color-lavender: #eddff7;
            --color-lavender-soft: #f8f3fc;
            --color-periwinkle: #e7ecff;
            --color-periwinkle-wash: #dbdbff;
            --color-aqua: #d1faff;

            /* Aliases mapped to original tokens for full backward compatibility */
            --brand: #6161ff;
            --brand-dark: #4b4be0;
            --brand-soft: #f0f1ff;
            --ink: #333333;
            --muted: #535768;
            --line: #d0d4e4;
            --surface: #ffffff;
            --page: #f5f6f8;
            --success: #1b5e20;
            --success-soft: #f0fce8;
            --warning: #b45309;
            --warning-soft: #fffbeb;
            --error: #b91c1c;
            --error-soft: #fef2f2;
            --info: #0369a1;
            --info-soft: #f0f9ff;

            /* Typography */
            --font-poppins: 'Poppins', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

            /* Radii */
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 20px;
            --radius-card: 24px;
            --radius-pill: 9999px;
            --radius-button: 160px;

            /* Shadows */
            --shadow-card: rgba(205, 208, 223, 0.4) 0px 4px 32px 0px;
            --shadow-card-hover: rgba(0, 0, 0, 0.12) 0px 8px 36px 0px;
            --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.06);
            --shadow-button: 0 4px 14px rgba(97, 97, 255, 0.28);
        }

        /* ── Typography Guarantee ───────────────────────────────────────── */
        html, body, .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stSidebar"],
        [data-testid="stMainBlockContainer"],
        p, li, a, label,
        h1, h2, h3, h4, h5, h6,
        input, select, textarea,
        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a,
        .stFormSubmitButton > button,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stCaptionContainer"] p {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* ── Streamlit Material Symbols & Icon Font Protection ──────────── */
        [data-testid="stIconMaterial"],
        [data-testid*="stIcon"],
        [class*="material-symbols"],
        [class*="material-icons"],
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons,
        span[data-testid="stIconMaterial"] {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
            line-height: 1 !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-feature-settings: 'liga' !important;
            -webkit-font-smoothing: antialiased !important;
        }

        .stApp {
            background-color: var(--color-cloud) !important;
            background-image:
                radial-gradient(circle at 92% 5%, rgba(97, 97, 255, 0.06), transparent 30rem),
                radial-gradient(circle at 10% 90%, rgba(188, 254, 144, 0.08), transparent 25rem) !important;
            color: var(--color-ink);
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1140px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* ── Typography Scale & Spacing ─────────────────────────────────── */
        h1, h2, h3, h4, h5, h6 {
            color: var(--color-ink) !important;
            letter-spacing: -0.015em !important;
            line-height: 1.3 !important;
            margin-bottom: 0.5rem !important;
        }

        h1 {
            font-size: clamp(2rem, 4.5vw, 2.9rem) !important;
            font-weight: 600 !important;
        }

        h2 {
            font-size: 1.75rem !important;
            font-weight: 600 !important;
        }

        h3 {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }

        p, label, li {
            color: var(--color-ink);
            font-size: 0.96rem;
            line-height: 1.55;
        }

        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label {
            line-height: 1.45 !important;
            margin-bottom: 0.35rem !important;
            font-weight: 500 !important;
            display: inline-block !important;
        }

        [data-testid="stCaptionContainer"] p {
            color: var(--color-slate) !important;
            font-size: 0.88rem !important;
            line-height: 1.5 !important;
        }

        /* ── Hero Gradient Text (Monday.com Signature) ─────────────────── */
        .hero-gradient-text {
            background: linear-gradient(90deg, #6161ff 0%, #fe81e4 50%, #fda900 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            display: inline-block;
        }

        /* ── Professional Monday.com Style Sidebar ─────────────────────── */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {
            background-color: #ffffff !important;
            background: #ffffff !important;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid #e7ecf2 !important;
            box-shadow: 2px 0 20px rgba(0, 0, 0, 0.02) !important;
        }

        /* Navigation items in Sidebar */
        [data-testid="stSidebarNav"] {
            padding-top: 0.75rem;
            padding-bottom: 0.75rem;
        }

        [data-testid="stSidebarNavLink"],
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNavItems"] a {
            border-radius: var(--radius-pill) !important;
            padding: 0.65rem 1.15rem !important;
            margin: 0.25rem 0.4rem !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
            color: var(--color-slate) !important;
            text-decoration: none !important;
            transition: all 0.15s ease-in-out !important;
        }

        [data-testid="stSidebarNavLink"]:hover,
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNavItems"] a:hover {
            background: #f0f1ff !important;
            color: var(--color-monday-violet) !important;
            transform: translateX(2px) !important;
        }

        [data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebarNavLink"].active,
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a.active {
            background: var(--color-monday-violet) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 14px rgba(97, 97, 255, 0.35) !important;
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] *,
        [data-testid="stSidebarNav"] a[aria-current="page"] *,
        [data-testid="stSidebarNavLink"][aria-current="page"] span,
        [data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: #ffffff !important;
            fill: #ffffff !important;
        }

        /* Sidebar Brand Header */
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0.25rem 1rem 0.25rem;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid #edf0f5;
        }

        .sidebar-brand-prism {
            width: 2.25rem;
            height: 2.25rem;
            border-radius: 10px;
            background: conic-gradient(from 270deg, #8181ff 15%, #33dbdb 40%, #33d58e 55%, #ffd633 65%, #fc527d 85%, #8181ff 100%);
            display: grid;
            place-items: center;
            color: #ffffff;
            font-weight: 700;
            font-size: 1.15rem;
            box-shadow: 0 3px 12px rgba(129, 129, 255, 0.4);
            flex-shrink: 0;
        }

        .sidebar-brand-name {
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--color-ink);
            line-height: 1.2;
        }

        .sidebar-brand-tag {
            font-size: 0.72rem;
            color: var(--color-slate);
            font-weight: 500;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        /* Sidebar User Card */
        .sidebar-user-card {
            background: #ffffff;
            border: 1px solid var(--color-mist);
            border-radius: 18px;
            padding: 1.1rem;
            margin: 0.75rem 0;
            box-shadow: 0 4px 20px rgba(97, 97, 255, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .sidebar-user-card:hover {
            box-shadow: 0 6px 24px rgba(97, 97, 255, 0.09);
        }

        .sidebar-user-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.6rem;
        }

        .sidebar-user-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6161ff 0%, #3ac9ff 100%);
            display: grid;
            place-items: center;
            color: #ffffff;
            font-weight: 700;
            font-size: 1rem;
            box-shadow: 0 3px 10px rgba(97, 97, 255, 0.28);
            border: 2px solid #ffffff;
            flex-shrink: 0;
        }

        .sidebar-user-meta {
            overflow: hidden;
        }

        .sidebar-user-name {
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--color-ink);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
        }

        .sidebar-user-handle {
            font-size: 0.8rem;
            color: var(--color-slate);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .sidebar-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #edfbe6;
            color: #166534;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: var(--radius-pill);
            margin-bottom: 0.75rem;
            border: 1px solid #d4f7c5;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
        }

        /* Sidebar Guest Card */
        .sidebar-guest-card {
            background: var(--color-periwinkle);
            border: 1px solid var(--color-mist);
            border-radius: 18px;
            padding: 1.1rem;
            margin: 0.75rem 0;
            text-align: left;
        }

        .sidebar-guest-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--color-monday-violet);
            margin-bottom: 0.35rem;
        }

        .sidebar-guest-text {
            font-size: 0.82rem;
            color: var(--color-slate);
            line-height: 1.45;
            margin-bottom: 0.5rem;
        }

        /* ── Pill Buttons (Monday.com Signature 160px Radius) ──────────── */
        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a,
        .stFormSubmitButton > button {
            border-radius: var(--radius-button) !important;
            min-height: 2.85rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 0.65rem 1.6rem !important;
            transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
            border: 1.5px solid transparent !important;
            letter-spacing: -0.01em !important;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background-color: var(--color-monday-violet) !important;
            background: var(--color-monday-violet) !important;
            border-color: var(--color-monday-violet) !important;
            color: #ffffff !important;
            box-shadow: var(--shadow-button) !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {
            background-color: var(--color-monday-violet-hover) !important;
            background: var(--color-monday-violet-hover) !important;
            border-color: var(--color-monday-violet-hover) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(97, 97, 255, 0.38) !important;
        }

        .stButton > button[kind="secondary"],
        .stFormSubmitButton > button[kind="secondary"],
        .stDownloadButton > button[kind="secondary"],
        .stDownloadButton > button,
        .stLinkButton > a {
            background-color: #ffffff !important;
            background: #ffffff !important;
            border: 1.5px solid var(--color-mist) !important;
            color: var(--color-ink) !important;
        }

        .stButton > button[kind="secondary"]:hover,
        .stFormSubmitButton > button[kind="secondary"]:hover,
        .stDownloadButton > button[kind="secondary"]:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover {
            border-color: var(--color-monday-violet) !important;
            color: var(--color-monday-violet) !important;
            background-color: #fbfbfe !important;
            background: #fbfbfe !important;
            transform: translateY(-1.5px) !important;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05) !important;
        }

        .stButton > button:disabled,
        .stFormSubmitButton > button:disabled {
            background: #eef0f5 !important;
            border-color: #eef0f5 !important;
            color: #9ba0af !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }

        /* ── Cards & Containers (24px Radius with Soft Shadow) ─────────── */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: var(--color-snow) !important;
            background: var(--color-snow) !important;
            border: 1px solid var(--color-mist) !important;
            border-radius: var(--radius-card) !important;
            box-shadow: var(--shadow-card) !important;
            padding: 0.6rem !important;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: var(--shadow-card-hover) !important;
        }

        /* ── File Uploader & Inputs ─────────────────────────────────────── */
        [data-testid="stFileUploader"] {
            width: 100% !important;
            margin-bottom: 1rem !important;
        }

        [data-testid="stFileUploader"] section {
            background-color: #ffffff !important;
            border: 1.5px dashed #b9bed5 !important;
            border-radius: 18px !important;
            padding: 1.6rem 1.25rem !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            gap: 0.5rem !important;
            min-height: 140px !important;
        }

        [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzoneInstructions"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 0.35rem !important;
            line-height: 1.45 !important;
        }

        [data-testid="stFileUploader"] section small {
            display: block !important;
            font-size: 0.84rem !important;
            color: var(--color-slate) !important;
            line-height: 1.4 !important;
            margin-top: 0.2rem !important;
        }

        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] {
            border-radius: 12px !important;
            border: 1px solid var(--color-mist) !important;
            background-color: #ffffff !important;
            color: var(--color-ink) !important;
            font-size: 0.95rem !important;
        }

        [data-testid="stTextArea"] textarea:focus,
        [data-testid="stTextInput"] input:focus {
            border-color: var(--color-monday-violet) !important;
            box-shadow: 0 0 0 3px rgba(97, 97, 255, 0.15) !important;
        }

        /* ── Tabs (Monday.com Pill Subnav Style) ────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem !important;
            background: #eef0f7 !important;
            padding: 0.4rem !important;
            border-radius: var(--radius-pill) !important;
            border-bottom: none !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-pill) !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
            padding: 0.5rem 1.35rem !important;
            color: var(--color-slate) !important;
            border: none !important;
            background: transparent !important;
            transition: all 0.15s ease !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--color-monday-violet) !important;
        }

        .stTabs [aria-selected="true"],
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #ffffff !important;
            background: #ffffff !important;
            color: var(--color-monday-violet) !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        }

        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* ── Radio & Checkbox ───────────────────────────────────────────── */
        div[role="radiogroup"] {
            gap: 0.65rem !important;
        }

        div[role="radiogroup"] label {
            background-color: #ffffff !important;
            border: 1px solid var(--color-mist) !important;
            border-radius: var(--radius-pill) !important;
            padding: 0.5rem 1.1rem !important;
            transition: all 0.15s ease !important;
        }

        div[role="radiogroup"] label:hover {
            border-color: var(--color-monday-violet) !important;
            background-color: #f0f1ff !important;
        }

        /* ── Expanders ─────────────────────────────────────────────────── */
        [data-testid="stExpander"] {
            border-radius: 16px !important;
            border: 1px solid var(--color-mist) !important;
            background-color: #ffffff !important;
            overflow: hidden !important;
            margin-bottom: 0.75rem !important;
        }

        [data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: var(--color-ink) !important;
        }

        /* ── Progress Bar (Violet to Cyan Gradient) ─────────────────────── */
        [data-testid="stProgress"] > div > div > div > div {
            background: linear-gradient(90deg, #6161ff 0%, #3ac9ff 100%) !important;
            border-radius: var(--radius-pill) !important;
        }

        [data-testid="stProgress"] > div > div {
            background-color: #eef0f7 !important;
            border-radius: var(--radius-pill) !important;
        }

        /* ── Brand Wordmark & Hero ─────────────────────────────────────── */
        .app-brand {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            color: var(--color-monday-violet) !important;
            font-size: 0.92rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 1.2rem;
        }

        .app-brand-mark {
            display: grid;
            place-items: center;
            width: 2.25rem;
            height: 2.25rem;
            border-radius: 10px;
            background: conic-gradient(from 270deg, #8181ff 15%, #33dbdb 40%, #33d58e 55%, #ffd633 65%, #fc527d 85%, #8181ff 100%);
            color: white;
            font-size: 1.15rem;
            font-weight: 700;
            box-shadow: 0 3px 12px rgba(129, 129, 255, 0.4);
            flex-shrink: 0;
        }

        .hero-kicker {
            color: var(--color-monday-violet);
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }

        .hero-copy {
            max-width: 720px;
            color: var(--color-slate);
            font-size: 1.12rem;
            line-height: 1.7;
            margin-top: 0.75rem;
        }

        /* ── Step Tracker ──────────────────────────────────────────────── */
        .step-track {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
            padding: 0.85rem 1.2rem;
            margin: 1.5rem 0 1.2rem;
            background: #ffffff;
            border: 1px solid var(--color-mist);
            border-radius: var(--radius-pill);
            box-shadow: var(--shadow-subtle);
        }

        .step-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--color-slate);
            font-size: 0.92rem;
        }

        .step-number {
            display: grid;
            place-items: center;
            width: 1.7rem;
            height: 1.7rem;
            border-radius: 50%;
            background: var(--color-cloud);
            color: var(--color-slate);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .step-item.active {
            color: var(--color-monday-violet);
            font-weight: 600;
        }

        .step-item.active .step-number {
            background: var(--color-monday-violet);
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(97, 97, 255, 0.35);
        }

        .step-item.done .step-number {
            background: var(--color-mint);
            color: var(--color-mint-dark);
            font-weight: 700;
        }

        .step-divider {
            color: var(--color-pebble);
        }

        /* ── Eyebrow ───────────────────────────────────────────────────── */
        .section-eyebrow {
            color: var(--color-monday-violet) !important;
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.1em !important;
            text-transform: uppercase !important;
            margin-bottom: 0.35rem !important;
        }

        /* ── Pastel Feature Cards (What You'll Get) ────────────────────── */
        .value-card {
            background: #ffffff;
            border: 1px solid var(--color-mist);
            border-radius: var(--radius-card);
            padding: 1.5rem 1.2rem;
            text-align: center;
            height: 100%;
            box-shadow: var(--shadow-card);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .value-card:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-card-hover);
        }

        .value-card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--color-ink);
            margin-bottom: 0.4rem;
        }

        .value-card-desc {
            font-size: 0.88rem;
            color: var(--color-slate);
            line-height: 1.55;
        }

        /* ── Skill Chips & Status Pills (Pastel Crayon Palette) ────────── */
        .skill-chip {
            display: inline-block;
            margin: 0.2rem 0.3rem 0.2rem 0;
            padding: 0.38rem 0.85rem;
            color: var(--color-monday-violet);
            background: var(--color-periwinkle);
            border: 1px solid var(--color-periwinkle-wash);
            border-radius: var(--radius-pill);
            font-size: 0.88rem;
            font-weight: 500;
        }

        .skill-chip-match {
            color: var(--color-mint-dark);
            background: var(--color-mint);
            border-color: #a4f56f;
            font-weight: 600;
        }

        .skill-chip-gap {
            color: #636674;
            background: #eef1f6;
            border-color: var(--color-pebble);
        }

        /* ── Match-Strength Chips ──────────────────────────────────────── */
        .match-strength-chip {
            display: inline-block;
            padding: 0.35rem 0.85rem;
            border-radius: var(--radius-pill);
            font-size: 0.82rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .match-chip-strong {
            background: var(--color-mint);
            color: var(--color-mint-dark);
            border: 1px solid #a4f56f;
        }

        .match-chip-moderate {
            background: var(--color-sky);
            color: #0369a1;
            border: 1px solid #8be4f7;
        }

        .match-chip-exploratory {
            background: var(--color-periwinkle);
            color: var(--color-monday-violet);
            border: 1px solid var(--color-pebble);
        }

        /* ── Quality checks & Alert Containers ─────────────────────────── */
        .quality-disclaimer {
            background: var(--color-sky-soft);
            border: 1px solid #c2f0f8;
            border-radius: 14px;
            padding: 0.85rem 1.15rem;
            font-size: 0.9rem;
            color: #0369a1;
            margin-bottom: 1rem;
        }

        .check-suggestion {
            background: #fbfbfd;
            border-radius: 10px;
            padding: 0.6rem 0.9rem;
            font-size: 0.88rem;
            color: var(--color-ink);
            margin-top: 0.4rem;
            border: 1px solid #edf0f5;
        }

        /* ── Metric Snapshot Card ──────────────────────────────────────── */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            background: #ffffff !important;
            border: 1px solid var(--color-mist) !important;
            border-radius: 20px !important;
            padding: 1rem 1.25rem !important;
            box-shadow: rgba(205, 208, 223, 0.3) 0px 2px 16px 0px !important;
        }

        [data-testid="stMetricLabel"] p {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            color: var(--color-slate) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }

        [data-testid="stMetricValue"] div {
            font-size: 1.85rem !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            letter-spacing: -0.02em !important;
        }

        /* ── Footer ─────────────────────────────────────────────────────── */
        .app-footer {
            margin-top: 3.5rem;
            padding: 1.8rem 0 1.2rem;
            border-top: 1px solid var(--color-mist);
        }

        .app-footer-brand {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 0.45rem;
        }

        .app-footer-mark {
            display: grid;
            place-items: center;
            width: 1.75rem;
            height: 1.75rem;
            border-radius: 8px;
            background: conic-gradient(from 270deg, #8181ff 15%, #33dbdb 40%, #33d58e 55%, #ffd633 65%, #fc527d 85%, #8181ff 100%);
            color: white;
            font-size: 0.85rem;
            font-weight: 700;
        }

        .app-footer-name {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--color-ink);
        }

        .app-footer-tagline {
            font-size: 0.84rem;
            color: var(--color-slate);
            font-style: italic;
            margin-bottom: 0.85rem;
        }

        .app-footer-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            font-size: 0.8rem;
            color: var(--color-slate);
            line-height: 1.5;
        }

        .app-footer-meta span {
            flex: 1 1 260px;
        }

        /* ── Mobile Responsive ─────────────────────────────────────────── */
        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1.2rem 1rem 3rem;
            }
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.6rem !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                flex: 1 1 calc(50% - 0.3rem) !important;
                min-width: calc(50% - 0.3rem) !important;
            }
            .step-track {
                gap: 0.45rem;
            }
            .step-item {
                font-size: 0.78rem;
            }
            .step-divider {
                display: none;
            }
            .value-card {
                padding: 1rem 0.8rem;
            }
            .app-footer-meta {
                flex-direction: column;
                gap: 0.5rem;
            }
            .match-strength-chip {
                font-size: 0.75rem;
                padding: 0.25rem 0.55rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
