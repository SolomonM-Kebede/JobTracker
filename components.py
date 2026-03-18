"""
 All HTML rendering for the Job Tracker dashboard.
Keep all inline HTML/CSS here — dashboard.py stays clean Python logic.
"""

import streamlit as st


# Styles 

def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    /* ── Pills ── */
    .pill { display:inline-block; padding:3px 10px; border-radius:20px;
            font-size:0.75rem; font-weight:600; white-space:nowrap; }
    .pill-rejection  { background:#fee2e2; color:#b91c1c; }
    .pill-interview  { background:#dcfce7; color:#15803d; }
    .pill-offer      { background:#fef9c3; color:#a16207; }
    .pill-assessment { background:#dbeafe; color:#1d4ed8; }
    .pill-followup   { background:#fce7f3; color:#be185d; }
    .pill-confirmed  { background:#ede9fe; color:#6d28d9; }
    .pill-awaiting   { background:#e0f2fe; color:#0369a1; }

    /* ── Application card ── */
    .app-card {
        background:#1e293b; border-radius:14px; padding:16px;
        margin-bottom:10px; border-left:4px solid #334155;
    }
    .app-card .title  { font-weight:700; font-size:1rem; }
    .app-card .role   { color:#94a3b8; font-size:0.85rem; margin:2px 0 6px; }
    .app-card .grid   { display:grid; grid-template-columns:1fr 1fr;
                        gap:6px; margin-top:10px; }
    .app-card .flabel { color:#64748b; font-size:0.7rem;
                        text-transform:uppercase; letter-spacing:0.5px; }
    .app-card .fval   { font-size:0.8rem; margin-top:1px; }
    .app-card .action { margin-top:8px; font-size:0.82rem;
                        color:#f59e0b; font-weight:600; }
    .app-card .notes  { margin-top:6px; font-size:0.75rem;
                        color:#64748b; font-style:italic; }

    /* ── Sent counter ── */
    .sent-card {
        background:#0f172a; border-radius:14px; padding:16px;
        border:1px solid rgba(255,255,255,0.07); margin-bottom:16px;
        display:flex; justify-content:space-between; align-items:center;
    }
    .sent-card .total  { font-size:2.2rem; font-weight:700; line-height:1.2; }
    .sent-card .label  { font-size:0.7rem; color:#94a3b8;
                         text-transform:uppercase; letter-spacing:0.8px; }
    .sent-card .month  { font-size:0.78rem; color:#64748b; text-align:right; }
    .sent-card .month b { color:#e2e8f0; }

    /* ── Urgency dots ── */
    .dot-high   { color:#ef4444; }
    .dot-medium { color:#f59e0b; }
    .dot-low    { color:#22c55e; }
    </style>
    """, unsafe_allow_html=True)


# Helper renderers

def _dot(urgency: str) -> str:
    css = {"High": "dot-high", "Medium": "dot-medium", "Low": "dot-low"}.get(urgency, "dot-low")
    return f'<span class="{css}">●</span>'


def _pill(label: str, label_pill: dict) -> str:
    cls, display = label_pill.get(label, ("", label))
    return f'<span class="pill {cls}">{display}</span>'


def _field(label: str, value: str) -> str:
    v = value or "—"
    return f'<div><div class="flabel">{label}</div><div class="fval">{v}</div></div>'


# Components

def sent_counter(sent_stats: dict):
    """Applications sent counter card with monthly breakdown."""
    total    = sent_stats.get("total", 0)
    by_month = sent_stats.get("by_month", {})

    months_html = "".join(
        f'<div class="month">{m}: <b>{c}</b></div>'
        for m, c in sorted(by_month.items())[-3:]
    )

    st.markdown(f"""
    <div class="sent-card">
      <div>
        <div class="label">Applications Sent</div>
        <div class="total">{total}</div>
      </div>
      <div>{months_html}</div>
    </div>
    """, unsafe_allow_html=True)


def app_card(row: dict, label_pill: dict, border_color: dict):
    """Single application card with all tracking fields."""
    label   = row.get("label", "")
    bc      = border_color.get(label, "#334155")
    ad      = row.get("ad_link", "") or ""
    action  = row.get("action_needed", "") or ""
    notes   = row.get("notes", "") or ""

    ad_html     = f'<a href="{ad}" target="_blank" style="color:#38bdf8;font-size:0.78rem">🔗 Ad Link</a>' if ad else ""
    action_html = f'<div class="action">→ {action}</div>' if action and action != "None" else ""
    notes_html  = f'<div class="notes">📝 {notes}</div>' if notes else ""

    st.markdown(f"""
    <div class="app-card" style="border-left-color:{bc}">
      <div class="title">{_dot(row.get('urgency','Low'))} {row.get('company','Unknown')}</div>
      <div class="role">{row.get('job_title','Unknown')}</div>
      {_pill(label, label_pill)}
      {action_html}
      <div class="grid">
        {_field('Department', row.get('department',''))}
        {_field('Sent',       row.get('sent_date',''))}
        {_field('Deadline',   row.get('deadline',''))}
        {_field('Documents',  row.get('documents',''))}
      </div>
      <div style="margin-top:6px">{ad_html}</div>
      {notes_html}
    </div>
    """, unsafe_allow_html=True)


def urgent_card(item: dict, label_pill: dict, border_color: dict):
    """Compact urgent action card."""
    label = item.get("label", "")
    bc    = border_color.get(label, "#ef4444")

    st.markdown(f"""
    <div class="app-card" style="border-left-color:{bc}">
      <div class="title">{_dot(item.get('urgency','High'))} {item.get('company','Unknown')}</div>
      <div class="role">{item.get('job_title','Unknown')} · {item.get('department','')}</div>
      {_pill(label, label_pill)}
      <div class="action">→ {item.get('action_needed','')}</div>
      <div class="grid">
        {_field('Sent',     item.get('sent_date',''))}
        {_field('Deadline', item.get('deadline',''))}
      </div>
    </div>
    """, unsafe_allow_html=True)


def edit_panel(row: dict, label_pill: dict, update_fields_fn):
    """Inline edit form for a single application."""
    eid = row.get("email_id", "")

    e1, e2 = st.columns(2)
    with e1:
        new_company  = st.text_input("Company",    value=row.get("company","")    or "", key=f"co_{eid}")
        new_title    = st.text_input("Job Title",  value=row.get("job_title","")  or "", key=f"jt_{eid}")
        new_dept     = st.text_input("Department", value=row.get("department","") or "", key=f"dp_{eid}")
        new_deadline = st.text_input("Deadline",   value=row.get("deadline","")   or "", key=f"dl_{eid}")
    with e2:
        new_docs  = st.text_input("Documents", value=row.get("documents","") or "", key=f"dc_{eid}")
        new_ad    = st.text_input("Ad Link",   value=row.get("ad_link","")   or "", key=f"ad_{eid}")
        new_label = st.selectbox(
            "Status",
            list(label_pill.keys()),
            index=list(label_pill.keys()).index(row.get("label", "Awaiting Response"))
                  if row.get("label") in label_pill else 6,
            key=f"lb_{eid}"
        )

    new_notes = st.text_area(
        "Notes / Details",
        value=row.get("notes", "") or "",
        placeholder="Add notes, contact name, salary, anything...",
        key=f"nt_{eid}"
    )

    if st.button("Save", key=f"sv_{eid}", use_container_width=True):
        update_fields_fn(eid, {
            "company":    new_company,
            "job_title":  new_title,
            "department": new_dept,
            "deadline":   new_deadline,
            "documents":  new_docs,
            "ad_link":    new_ad,
            "label":      new_label,
            "notes":      new_notes,
        })
        st.success("Saved!")
        st.rerun()