"""
 Optimized Job Tracker: loads only selected category, paginated.
"""

import os
import hashlib
import streamlit as st
from database import (get_stats, get_high_urgency, init_db,
                      get_applications_by_label, get_total_count,
                      get_departments, update_fields)

# Page config 
st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Password protection 
def check_password():
    if st.session_state.get("authenticated"):
        return
    st.markdown("## Job Application Tracker")
    pwd = st.text_input("Password", type="password", placeholder="Enter dashboard password")
    if pwd:
        expected = hashlib.sha256(os.getenv("DASHBOARD_PASSWORD", "").encode()).hexdigest()
        if hashlib.sha256(pwd.encode()).hexdigest() == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

check_password()

#  CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stat-row { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.stat-card {
    flex:1; min-width:100px; background:#0f172a; border-radius:14px;
    padding:12px 8px; text-align:center; border:1px solid rgba(255,255,255,0.07);
    cursor:pointer; transition: border-color 0.2s;
}
.stat-card.active { border-color:#38bdf8 !important; }
.stat-card .val { font-size:1.6rem; font-weight:700; line-height:1; }
.stat-card .lbl { font-size:0.68rem; color:#94a3b8; margin-top:4px;
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
.app-card .grid   { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:10px; }
.app-card .flabel { color:#64748b; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px; }
.app-card .fval   { font-size:0.8rem; margin-top:1px; }
.app-card .action { margin-top:8px; font-size:0.82rem; color:#f59e0b; font-weight:600; }
.app-card .notes  { margin-top:6px; font-size:0.75rem; color:#64748b; font-style:italic; }

.dot-high   { color:#ef4444; }
.dot-medium { color:#f59e0b; }
.dot-low    { color:#22c55e; }

.page-info { text-align:center; color:#64748b; font-size:0.82rem; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

PAGE_SIZE = 10

LABEL_PILL = {
    "Rejection":             ("pill-rejection",  "Rejection"),
    "Interview Invite":      ("pill-interview",  "Interview"),
    "Job Offer":             ("pill-offer",       "Offer"),
    "Assessment/Task":       ("pill-assessment",  "Assessment"),
    "Follow-up Needed":      ("pill-followup",    "Follow-up"),
    "Application Confirmed": ("pill-confirmed",   "Confirmed"),
    "Awaiting Response":     ("pill-awaiting",    "Waiting"),
}

STAT_CARDS = [
    ("All",                  "", "All"),
    ("Interview Invite",     "", "Interviews"),
    ("Assessment/Task",      "", "Assessments"),
    ("Follow-up Needed",     "", "Follow-ups"),
    ("Application Confirmed","", "Confirmed"),
    ("Awaiting Response",    "", "Waiting"),
    ("Rejection",            "", "Rejections"),
    ("Job Offer",            "", "Offers"),
]

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

# Session state defaults 
if "active_label" not in st.session_state:
    st.session_state.active_label = "All"
if "page" not in st.session_state:
    st.session_state.page = 0
if "search" not in st.session_state:
    st.session_state.search = ""
if "dept" not in st.session_state:
    st.session_state.dept = "All Departments"

# Load lightweight data (stats only)
init_db()
stats      = get_stats()
urgent     = get_high_urgency()
total_all  = sum(v for k, v in stats.items() if k != "Not Job Related")
departments = ["All Departments"] + get_departments()

# Header
st.markdown("## Job Application Tracker")
st.caption("Frankfurt am Main · 2026")

if st.button("Sync Emails", use_container_width=True, type="primary"):
    with st.spinner("Fetching and classifying emails..."):
        from sync import run_sync
        run_sync()
    st.success("Done!")
    st.rerun()

st.markdown("---")

#  Category cards 
st.markdown("#### Select Category")

# Row 1 — 4 cards
cols1 = st.columns(4)
for i, (label, emoji, name) in enumerate(STAT_CARDS[:4]):
    count = total_all if label == "All" else stats.get(label, 0)
    active = "active" if st.session_state.active_label == label else ""
    with cols1[i]:
        if st.button(f"{emoji}\n**{count}**\n{name}",
                     key=f"cat_{label}",
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.active_label = label
            st.session_state.page = 0
            st.rerun()

# Row 2 — 4 cards
cols2 = st.columns(4)
for i, (label, emoji, name) in enumerate(STAT_CARDS[4:]):
    count = stats.get(label, 0)
    active = "active" if st.session_state.active_label == label else ""
    with cols2[i]:
        if st.button(f"{emoji}\n**{count}**\n{name}",
                     key=f"cat_{label}",
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.active_label = label
            st.session_state.page = 0
            st.rerun()

st.markdown("---")

# Urgent alerts (only on All view) 
if urgent and st.session_state.active_label == "All":
    st.markdown("### Needs Action Now")
    for item in urgent[:3]:
        cls, display = LABEL_PILL.get(item.get("label",""), ("",""))
        bc  = BORDER_COLOR.get(item.get("label",""), "#334155")
        dot = URGENCY_DOT.get(item.get("urgency","Low"), "")
        st.markdown(f"""
        <div class="app-card" style="border-left-color:{bc}">
          <div class="title">{dot} {item.get('company','Unknown')}</div>
          <div class="role">{item.get('job_title','Unknown')} · {item.get('department','')}</div>
          <span class="pill {cls}">{display}</span>
          <div class="action">→ {item.get('action_needed','')}</div>
          <div class="grid">
            <div><div class="flabel">Sent</div>
                 <div class="fval">{item.get('sent_date','—') or '—'}</div></div>
            <div><div class="flabel">Deadline</div>
                 <div class="fval">{item.get('deadline','—') or '—'}</div></div>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")

# Search & department filter
active_label = st.session_state.active_label
label_display = dict([(l, n) for l, _, n in STAT_CARDS]).get(active_label, active_label)
st.markdown(f"### {label_display}")

c1, c2 = st.columns([2, 1])
with c1:
    search = st.text_input("Search", placeholder="🔍 Company or role...",
                           value=st.session_state.search,
                           label_visibility="collapsed",
                           key="search_input")
with c2:
    dept = st.selectbox("Dept", departments,
                        index=departments.index(st.session_state.dept)
                        if st.session_state.dept in departments else 0,
                        label_visibility="collapsed")

# Reset page if filters changed
if search != st.session_state.search or dept != st.session_state.dept:
    st.session_state.page = 0
    st.session_state.search = search
    st.session_state.dept = dept

# Fetch only this page of this category 
page      = st.session_state.page
apps      = get_applications_by_label(active_label, page, PAGE_SIZE, search, dept)
total     = get_total_count(active_label, search, dept)
total_pages = max(1, -(-total // PAGE_SIZE))  # ceiling division

st.caption(f"{total} applications · Page {page+1} of {total_pages}")

# Application cards
if apps:
    for row in apps:
        cls, display = LABEL_PILL.get(row.get("label",""), ("","📧"))
        bc  = BORDER_COLOR.get(row.get("label",""), "#334155")
        dot = URGENCY_DOT.get(row.get("urgency","Low"), "")
        ad  = row.get("ad_link","") or ""
        ad_html = f'<a href="{ad}" target="_blank" style="color:#38bdf8;font-size:0.78rem">🔗 Ad Link</a>' if ad else ""
        action_html = f'<div class="action">→ {row["action_needed"]}</div>' \
                      if row.get("action_needed") and row["action_needed"] != "None" else ""
        notes_html = f'<div class="notes">📝 {row["notes"]}</div>' \
                     if row.get("notes") else ""

        st.markdown(f"""
        <div class="app-card" style="border-left-color:{bc}">
          <div class="title">{dot} {row.get('company','Unknown')}</div>
          <div class="role">{row.get('job_title','Unknown')}</div>
          <span class="pill {cls}">{display}</span>
          {action_html}
          <div class="grid">
            <div><div class="flabel">Department</div>
                 <div class="fval">{row.get('department','—') or '—'}</div></div>
            <div><div class="flabel">Sent</div>
                 <div class="fval">{row.get('sent_date','—') or '—'}</div></div>
            <div><div class="flabel">Deadline</div>
                 <div class="fval">{row.get('deadline','—') or '—'}</div></div>
            <div><div class="flabel">Documents</div>
                 <div class="fval">{row.get('documents','—') or '—'}</div></div>
          </div>
          <div style="margin-top:6px">{ad_html}</div>
          {notes_html}
        </div>""", unsafe_allow_html=True)

        # Edit panel
        with st.expander(f"Edit — {row.get('company','?')}"):
            e1, e2 = st.columns(2)
            eid = row.get("email_id","")
            with e1:
                new_company  = st.text_input("Company",    value=row.get("company","") or "",    key=f"co_{eid}")
                new_title    = st.text_input("Job Title",  value=row.get("job_title","") or "",  key=f"jt_{eid}")
                new_dept     = st.text_input("Department", value=row.get("department","") or "", key=f"dp_{eid}")
                new_deadline = st.text_input("Deadline",   value=row.get("deadline","") or "",   key=f"dl_{eid}")
            with e2:
                new_docs  = st.text_input("Documents", value=row.get("documents","") or "", key=f"dc_{eid}")
                new_ad    = st.text_input("Ad Link",   value=row.get("ad_link","") or "",   key=f"ad_{eid}")
                new_label = st.selectbox("Status", list(LABEL_PILL.keys()),
                                         index=list(LABEL_PILL.keys()).index(row.get("label","Awaiting Response"))
                                         if row.get("label") in LABEL_PILL else 6,
                                         key=f"lb_{eid}")

            new_notes = st.text_area("Notes / Details",
                                     value=row.get("notes","") or "",
                                     placeholder="Add notes, contact name, salary, anything...",
                                     key=f"nt_{eid}")

            if st.button("Save", key=f"sv_{eid}", use_container_width=True):
                update_fields(eid, {
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
else:
    st.info("No applications in this category yet.")

#  Pagination 
if total_pages > 1:
    st.markdown("---")
    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("← Prev", disabled=page == 0, use_container_width=True):
            st.session_state.page -= 1
            st.rerun()
    with p2:
        st.markdown(f'<div class="page-info">Page {page+1} / {total_pages}</div>',
                    unsafe_allow_html=True)
    with p3:
        if st.button("Next →", disabled=page >= total_pages - 1, use_container_width=True):
            st.session_state.page += 1
            st.rerun()

st.markdown("---")
st.caption("Tailscale · Auto-syncs every 6h")