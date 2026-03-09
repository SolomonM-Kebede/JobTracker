"""
Mobile-friendly Job Application Tracker Dashboard
Access via Tailscale: http://<proxmox-tailscale-ip>:8501 or any other prefereable seure tunnel 
"""

import os
import hashlib
import streamlit as st
import pandas as pd
from database import (get_all_applications, get_stats, get_high_urgency,
                      init_db, update_notes, update_fields)

# Page config
st.set_page_config(
    page_title="Job Applications Tracker",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Password protection 
def check_password():
    if st.session_state.get("authenticated"):
        return
    st.markdown("## Job Applications Tracker")
    pwd = st.text_input("Password", type="password", placeholder="Enter dashboard password")
    if pwd:
        expected = hashlib.sha256(os.getenv("DASHBOARD_PASSWORD", "").encode()).hexdigest()
        entered  = hashlib.sha256(pwd.encode()).hexdigest()
        if entered == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

check_password()

# CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stat-row { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; }
.stat-card {
    flex:1; min-width:120px; background:#0f172a;
    border-radius:14px; padding:14px 10px; text-align:center;
    border:1px solid rgba(255,255,255,0.07);
}
.stat-card .val { font-size:1.8rem; font-weight:700; line-height:1; }
.stat-card .lbl { font-size:0.7rem; color:#94a3b8; margin-top:4px;
                  text-transform:uppercase; letter-spacing:0.8px; }

.pill { display:inline-block; padding:3px 10px; border-radius:20px;
        font-size:0.75rem; font-weight:600; white-space:nowrap; }
.pill-rejection  { background:#fee2e2; color:#b91c1c; }
.pill-interview  { background:#dcfce7; color:#15803d; }
.pill-offer      { background:#fef9c3; color:#a16207; }
.pill-assessment { background:#dbeafe; color:#1d4ed8; }
.pill-followup   { background:#fce7f3; color:#be185d; }
.pill-confirmed  { background:#ede9fe; color:#6d28d9; }
.pill-awaiting   { background:#e0f2fe; color:#0369a1; }

.app-card {
    background:#1e293b; border-radius:14px; padding:16px;
    margin-bottom:10px; border-left:4px solid #334155;
}
.app-card .title  { font-weight:700; font-size:1rem; }
.app-card .role   { color:#94a3b8; font-size:0.85rem; margin:2px 0 6px; }
.app-card .grid   { display:grid; grid-template-columns:1fr 1fr;
                    gap:6px; margin-top:8px; }
.app-card .field  { font-size:0.78rem; }
.app-card .flabel { color:#64748b; font-size:0.72rem; text-transform:uppercase;
                    letter-spacing:0.5px; }
.app-card .action { margin-top:8px; font-size:0.82rem;
                    color:#f59e0b; font-weight:600; }
.dot-high   { color:#ef4444; }
.dot-medium { color:#f59e0b; }
.dot-low    { color:#22c55e; }
</style>
""", unsafe_allow_html=True)

LABEL_PILL = {
    "Rejection":             ("pill-rejection",  "Rejection"),
    "Interview Invite":      ("pill-interview",  "Interview"),
    "Job Offer":             ("pill-offer",       "Offer"),
    "Assessment/Task":       ("pill-assessment",  "Assessment"),
    "Follow-up Needed":      ("pill-followup",    "Follow-up"),
    "Application Confirmed": ("pill-confirmed",   "Confirmed"),
    "Awaiting Response":     ("pill-awaiting",    "Waiting"),
}

BORDER_COLOR = {
    "Job Offer":        "#fbbf24",
    "Interview Invite": "#22c55e",
    "Rejection":        "#ef4444",
    "Assessment/Task":  "#3b82f6",
    "Follow-up Needed": "#f472b6",
}

URGENCY_DOT = {
    "High":   '<span class="dot-high">●</span>',
    "Medium": '<span class="dot-medium">●</span>',
    "Low":    '<span class="dot-low">●</span>',
}

# Load data 
init_db()
apps   = get_all_applications()
stats  = get_stats()
urgent = get_high_urgency()
df     = pd.DataFrame(apps) if apps else pd.DataFrame()

# Header 
st.markdown("## Job Apllication Tracker")
st.caption("Frankfurt am Main · 2026 applications")

if st.button("Sync Emails", use_container_width=True, type="primary"):
    with st.spinner("Fetching and classifying emails..."):
        from sync import run_sync
        run_sync()
    st.success("Done!")
    st.rerun()

st.markdown("---")

# Stats 
total      = len(apps)
interviews = stats.get("Interview Invite", 0)
rejections = stats.get("Rejection", 0)
offers     = stats.get("Job Offer", 0)
action     = stats.get("Follow-up Needed", 0) + stats.get("Assessment/Task", 0)

st.markdown(f"""
<div class="stat-row">
  <div class="stat-card"><div class="val">{total}</div><div class="lbl">Total</div></div>
  <div class="stat-card"><div class="val">{interviews}</div><div class="lbl">Interviews</div></div>
  <div class="stat-card"><div class="val">{rejections}</div><div class="lbl">Rejections</div></div>
  <div class="stat-card"><div class="val">{offers}</div><div class="lbl">Offers</div></div>
  <div class="stat-card"><div class="val">{action}</div><div class="lbl">Action</div></div>
</div>
""", unsafe_allow_html=True)

# Report 
with st.expander("Full Report", expanded=False):
    rows = ""
    for label, count in sorted(stats.items(), key=lambda x: -x[1]):
        if label == "Not Job Related":
            continue
        cls, display = LABEL_PILL.get(label, ("", label))
        rows += f"""<div style="display:flex;justify-content:space-between;padding:6px 0;
                    border-bottom:1px solid #1e293b;font-size:0.88rem">
                    <span><span class="pill {cls}">{display}</span></span>
                    <span style="font-weight:700">{count}</span></div>"""
    ir = f"{round(interviews/total*100)}%" if total else "—"
    st.markdown(f"""
    <div style="background:#0f172a;border-radius:14px;padding:20px;border:1px solid #1e293b">
      <h4 style="margin:0 0 12px;font-size:1rem"> 2026 Summary</h4>
      {rows}
      <div style="display:flex;justify-content:space-between;padding:8px 0 4px;font-size:0.88rem;margin-top:4px">
        <span style="color:#94a3b8">Interview rate</span>
        <span style="font-weight:700">{ir}</span>
      </div>
    </div>""", unsafe_allow_html=True)

# Urgent 
if urgent:
    st.markdown("### Needs Action")
    for item in urgent[:3]:
        cls, display = LABEL_PILL.get(item.get("label",""), ("",""))
        bc = BORDER_COLOR.get(item.get("label",""), "#334155")
        dot = URGENCY_DOT.get(item.get("urgency","Low"), "")
        st.markdown(f"""
        <div class="app-card" style="border-left-color:{bc}">
          <div class="title">{dot} {item.get('company','Unknown')}</div>
          <div class="role">{item.get('job_title','Unknown')} · {item.get('department','')}</div>
          <span class="pill {cls}">{display}</span>
          <div class="action">→ {item.get('action_needed','')}</div>
          <div class="grid">
            <div><div class="flabel">Sent</div>
                 <div class="field">{item.get('sent_date','—')}</div></div>
            <div><div class="flabel">Deadline</div>
                 <div class="field">{item.get('deadline','—') or '—'}</div></div>
          </div>
        </div>""", unsafe_allow_html=True)

# Filters 
st.markdown("---")
st.markdown("### All Applications")

col1, col2 = st.columns(2)
with col1:
    label_filter = st.selectbox("Status", ["All"] + list(LABEL_PILL.keys()),
                                label_visibility="collapsed")
with col2:
    dept_options = ["All Departments"]
    if not df.empty and "department" in df.columns:
        dept_options += sorted(df["department"].dropna().unique().tolist())
    dept_filter = st.selectbox("Department", dept_options, label_visibility="collapsed")

search = st.text_input("Search", placeholder="Company, role, or department...",
                       label_visibility="collapsed")

# Application cards
if not df.empty:
    filtered = df.copy()
    if label_filter != "All":
        filtered = filtered[filtered["label"] == label_filter]
    if dept_filter != "All Departments":
        filtered = filtered[filtered.get("department", pd.Series()) == dept_filter]
    if search:
        mask = (
            filtered.get("company",    pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
            filtered.get("job_title",  pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
            filtered.get("department", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.caption(f"{len(filtered)} of {len(df)} applications")

    for _, row in filtered.iterrows():
        cls, display = LABEL_PILL.get(row.get("label",""), ("",""))
        bc  = BORDER_COLOR.get(row.get("label",""), "#334155")
        dot = URGENCY_DOT.get(row.get("urgency","Low"), "")
        ad  = row.get("ad_link","") or ""
        ad_html = f'<a href="{ad}" target="_blank" style="color:#38bdf8;font-size:0.78rem">View Ad</a>' if ad else ""
        action_html = f'<div class="action">→ {row["action_needed"]}</div>' \
                      if row.get("action_needed") and row["action_needed"] != "None" else ""

        st.markdown(f"""
        <div class="app-card" style="border-left-color:{bc}">
          <div class="title">{dot} {row.get('company','Unknown')}</div>
          <div class="role">{row.get('job_title','Unknown')}</div>
          <span class="pill {cls}">{display}</span>
          {action_html}
          <div class="grid">
            <div><div class="flabel">Department</div>
                 <div class="field">{row.get('department','—')}</div></div>
            <div><div class="flabel">Sent</div>
                 <div class="field">{row.get('sent_date','—') or '—'}</div></div>
            <div><div class="flabel">Deadline</div>
                 <div class="field">{row.get('deadline','—') or '—'}</div></div>
            <div><div class="flabel">Documents</div>
                 <div class="field">{row.get('documents','—')}</div></div>
          </div>
          <div style="margin-top:6px">{ad_html}</div>
          <div style="margin-top:4px;font-size:0.75rem;color:#475569">
             {row.get('notes','') or 'No notes'}
          </div>
        </div>""", unsafe_allow_html=True)

        # Inline edit panel 
        with st.expander(f"Edit — {row.get('company','?')} · {row.get('job_title','?')}"):
            e1, e2 = st.columns(2)
            with e1:
                new_deadline = st.text_input("Deadline", value=row.get("deadline","") or "",
                                             key=f"dl_{row.get('email_id','')}")
                new_ad = st.text_input("Ad Link", value=row.get("ad_link","") or "",
                                       key=f"ad_{row.get('email_id','')}")
                new_dept = st.text_input("Department", value=row.get("department","") or "",
                                         key=f"dept_{row.get('email_id','')}")
            with e2:
                new_company = st.text_input("Company", value=row.get("company","") or "",
                                            key=f"co_{row.get('email_id','')}")
                new_title = st.text_input("Job Title", value=row.get("job_title","") or "",
                                          key=f"jt_{row.get('email_id','')}")
                new_docs = st.text_input("Documents", value=row.get("documents","") or "",
                                         key=f"docs_{row.get('email_id','')}")

            new_notes = st.text_area("Notes / Details", value=row.get("notes","") or "",
                                     placeholder="Add any notes about this application...",
                                     key=f"notes_{row.get('email_id','')}")

            new_label = st.selectbox("Status", list(LABEL_PILL.keys()),
                                     index=list(LABEL_PILL.keys()).index(row.get("label","Awaiting Response"))
                                     if row.get("label") in LABEL_PILL else 6,
                                     key=f"lbl_{row.get('email_id','')}")

            if st.button("Save Changes", key=f"save_{row.get('email_id','')}",
                         use_container_width=True):
                update_fields(row.get("email_id"), {
                    "deadline":   new_deadline,
                    "ad_link":    new_ad,
                    "department": new_dept,
                    "company":    new_company,
                    "job_title":  new_title,
                    "documents":  new_docs,
                    "label":      new_label,
                    "notes":      new_notes,
                })
                st.success("Saved!")
                st.rerun()
else:
    st.info("No applications yet — tap **Sync Emails** to start!")

st.markdown("---")
st.caption("http://<tailscale-ip>:8501 · Auto-syncs every 6h")