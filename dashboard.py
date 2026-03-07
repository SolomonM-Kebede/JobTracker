"""
Mobile-friendly Streamlit dashboard for Job Application Tracker
Access via Tailscale: http://<proxmox-tailscale-ip>:8501
"""

import os
import hashlib
import streamlit as st
import pandas as pd
from database import get_all_applications, get_stats, get_high_urgency, init_db


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

st.set_page_config(
    page_title="Job Applications Tracker",
    page_icon="",
    layout="centered",   #better for mobile browser view 
    initial_sidebar_state="collapsed",
)

# Mobile-first CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Stat cards */
.stat-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.stat-card {
    flex: 1; min-width: 130px;
    background: #0f172a;
    border-radius: 14px;
    padding: 16px 12px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.07);
}
.stat-card .val { font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-card .lbl { font-size: 0.72rem; color: #94a3b8; margin-top: 4px;
                  text-transform: uppercase; letter-spacing: 0.8px; }

/* Label pill badges */
.pill {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; white-space: nowrap;
}
.pill-rejection        { background:#fee2e2; color:#b91c1c; }
.pill-interview        { background:#dcfce7; color:#15803d; }
.pill-offer            { background:#fef9c3; color:#a16207; }
.pill-assessment       { background:#dbeafe; color:#1d4ed8; }
.pill-followup         { background:#fce7f3; color:#be185d; }
.pill-confirmed        { background:#ede9fe; color:#6d28d9; }
.pill-awaiting         { background:#e0f2fe; color:#0369a1; }

/* Email cards */
.email-card {
    background: #1e293b;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid #334155;
}
.email-card .company   { font-weight: 700; font-size: 1rem; }
.email-card .role      { color: #94a3b8; font-size: 0.85rem; margin: 2px 0 6px; }
.email-card .meta      { font-size: 0.78rem; color: #64748b; }
.email-card .action    { margin-top: 8px; font-size: 0.82rem;
                         color: #f59e0b; font-weight: 600; }

/* Urgency dot */
.dot-high   { color: #ef4444; }
.dot-medium { color: #f59e0b; }
.dot-low    { color: #22c55e; }

/* Report section */
.report-box {
    background: #0f172a; border-radius: 14px; padding: 20px;
    border: 1px solid #1e293b; margin-top: 8px;
}
.report-box h4 { margin: 0 0 12px; font-size: 1rem; color: #e2e8f0; }
.report-row { display:flex; justify-content:space-between;
              padding: 6px 0; border-bottom: 1px solid #1e293b;
              font-size: 0.88rem; }
.report-row:last-child { border-bottom: none; }

/* Make dataframe scroll on mobile */
div[data-testid="stDataFrame"] { overflow-x: auto; }

/* Wider tap targets on mobile */
button { min-height: 44px !important; }
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

URGENCY_DOT = {
    "High":   '<span class="dot-high">●</span>',
    "Medium": '<span class="dot-medium">●</span>',
    "Low":    '<span class="dot-low">●</span>',
}

# Load data
init_db()
apps      = get_all_applications()
stats     = get_stats()
urgent    = get_high_urgency()
df        = pd.DataFrame(apps) if apps else pd.DataFrame()

# Header
st.markdown("## Job Application Tracker")
st.caption("Frankfurt am Main · 2026 applications")

# Sync button 
if st.button("Sync Emails", use_container_width=True, type="primary"):
    with st.spinner("Fetching and classifying emails..."):
        from sync import run_sync
        run_sync()
    st.success("Done!")
    st.rerun()

st.markdown("---")

# Stat cards 
total      = len(apps)
interviews = stats.get("Interview Invite", 0)
rejections = stats.get("Rejection", 0)
offers     = stats.get("Job Offer", 0)
action     = stats.get("Follow-up Needed", 0) + stats.get("Assessment/Task", 0)

st.markdown(f"""
<div class="stat-row">
  <div class="stat-card"><div class="val"> {total}</div><div class="lbl">Total</div></div>
  <div class="stat-card"><div class="val"> {interviews}</div><div class="lbl">Interviews</div></div>
  <div class="stat-card"><div class="val"> {rejections}</div><div class="lbl">Rejections</div></div>
  <div class="stat-card"><div class="val"> {offers}</div><div class="lbl">Offers</div></div>
  <div class="stat-card"><div class="val"> {action}</div><div class="lbl">Need Action</div></div>
</div>
""", unsafe_allow_html=True)

# Report section 
with st.expander("Full Report", expanded=False):
    rows_html = ""
    for label, count in sorted(stats.items(), key=lambda x: -x[1]):
        if label == "Not Job Related":
            continue
        cls, display = LABEL_PILL.get(label, ("", label))
        rows_html += f"""
        <div class="report-row">
          <span><span class="pill {cls}">{display}</span></span>
          <span style="font-weight:700">{count}</span>
        </div>"""

    applied    = total
    reply_rate = f"{round(interviews/total*100)}%" if total else "—"
    offer_rate = f"{round(offers/total*100)}%" if total else "—"

    st.markdown(f"""
    <div class="report-box">
      <h4> Summary Report — 2026</h4>
      {rows_html}
      <div class="report-row" style="margin-top:10px">
        <span style="color:#94a3b8">Total applied</span><span style="font-weight:700">{applied}</span>
      </div>
      <div class="report-row">
        <span style="color:#94a3b8">Interview rate</span><span style="font-weight:700">{reply_rate}</span>
      </div>
      <div class="report-row">
        <span style="color:#94a3b8">Offer rate</span><span style="font-weight:700">{offer_rate}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# Urgent alerts 
if urgent:
    st.markdown("### Needs Action")
    for item in urgent[:5]:
        cls, display = LABEL_PILL.get(item.get("label",""), ("",""))
        dot = URGENCY_DOT.get(item.get("urgency","Low"), "")
        st.markdown(f"""
        <div class="email-card" style="border-left-color:#ef4444">
          <div class="company">{dot} {item.get('company','Unknown')}</div>
          <div class="role">{item.get('job_title','Unknown')}</div>
          <span class="pill {cls}">{display}</span>
          <div class="action">→ {item.get('action_needed','')}</div>
          <div class="meta">{item.get('received','')[:10]} · {item.get('folder','')}</div>
        </div>
        """, unsafe_allow_html=True)

# Filter bar 
st.markdown("### All Applications")

col1, col2 = st.columns(2)
with col1:
    label_filter = st.selectbox("Status", ["All"] + list(LABEL_PILL.keys()), label_visibility="collapsed")
with col2:
    search = st.text_input("Search", placeholder="Company or role...", label_visibility="collapsed")

# Email cards 
if not df.empty:
    filtered = df.copy()
    if label_filter != "All":
        filtered = filtered[filtered["label"] == label_filter]
    if search:
        mask = (
            filtered.get("company", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
            filtered.get("job_title", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
            filtered.get("subject", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.caption(f"{len(filtered)} of {len(df)} emails")

    for _, row in filtered.iterrows():
        cls, display = LABEL_PILL.get(row.get("label",""), ("","Unknown"))
        dot = URGENCY_DOT.get(row.get("urgency","Low"), "")
        action_html = f'<div class="action">→ {row["action_needed"]}</div>' if row.get("action_needed") and row["action_needed"] != "None" else ""
        border_color = {
            "Job Offer": "#fbbf24", "Interview Invite": "#22c55e",
            "Rejection": "#ef4444", "Assessment/Task": "#3b82f6",
        }.get(row.get("label",""), "#334155")

        st.markdown(f"""
        <div class="email-card" style="border-left-color:{border_color}">
          <div class="company">{dot} {row.get('company','Unknown')}</div>
          <div class="role">{row.get('job_title','Unknown')}</div>
          <span class="pill {cls}">{display}</span>
          {action_html}
          <div class="meta">{str(row.get('received',''))[:10]} · {row.get('folder','')} · {row.get('sender_email','')}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No emails yet — tap **Sync Emails** to start!")

# Mobile access footer 
st.markdown("---")
st.caption(" To open on phone: visit `http://<ip>:8501`")