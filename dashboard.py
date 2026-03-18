"""
Job Application Tracker Dashboard
Clean separation: components.py handles all HTML rendering.
"""

import os
import hashlib
import streamlit as st
from database import (get_stats, get_high_urgency, init_db,
                      get_applications_by_label, get_total_count,
                      get_departments, update_fields, get_sent_stats)
import components as ui

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

# Inject styles 
ui.inject_styles()

# Constants 
PAGE_SIZE = 10

LABEL_PILL = {
    "Rejection":             ("pill-rejection",  "Rejection"),
    "Interview Invite":      ("pill-interview",  "Interview"),
    "Job Offer":             ("pill-offer",      "Offer"),
    "Assessment/Task":       ("pill-assessment", "Assessment"),
    "Follow-up Needed":      ("pill-followup",   "Follow-up"),
    "Application Confirmed": ("pill-confirmed",  "Confirmed"),
    "Awaiting Response":     ("pill-awaiting",   "Waiting"),
}

STAT_CARDS = [
    ("All",                   "", "All"),
    ("Interview Invite",      "", "Interviews"),
    ("Assessment/Task",       "", "Assessments"),
    ("Follow-up Needed",      "", "Follow-ups"),
    ("Application Confirmed", "", "Confirmed"),
    ("Awaiting Response",     "", "Waiting"),
    ("Rejection",             "", "Rejections"),
    ("Job Offer",             "", "Offers"),
]

BORDER_COLOR = {
    "Job Offer":        "#fbbf24",
    "Interview Invite": "#22c55e",
    "Rejection":        "#ef4444",
    "Assessment/Task":  "#3b82f6",
    "Follow-up Needed": "#f472b6",
}

# Session state defaults 
for key, default in [("active_label", "All"), ("page", 0),
                      ("search", ""),         ("dept", "All Departments")]:
    if key not in st.session_state:
        st.session_state[key] = default

# Load data (stats only — lightweight) 
init_db()
stats       = get_stats()
urgent      = get_high_urgency()
sent_stats  = get_sent_stats()
total_all   = sum(v for k, v in stats.items() if k != "Not Job Related")
departments = ["All Departments"] + get_departments()

# Header 
st.markdown("## Job Application Tracker")
st.caption("Frankfurt am Main · 2026")

# Sync button 
if st.button(" Sync Emails", use_container_width=True, type="primary"):
    status   = st.empty()
    progress = st.progress(0)

    def update(msg):
        status.caption(f" {msg}")

    update("Connecting to Microsoft...")
    progress.progress(10)

    from fetch_emails import fetch_all_job_emails
    from classify import classify_batch
    from database import save_emails

    emails = fetch_all_job_emails(progress_cb=update)
    progress.progress(50)

    update(f"Classifying {len(emails)} emails...")
    classified = classify_batch(emails)
    progress.progress(80)

    update("Saving to MongoDB...")
    save_emails(classified)
    progress.progress(100)

    status.empty()
    progress.empty()
    st.success(f"Sync complete — {len(classified)} emails processed!")
    st.rerun()

st.markdown("---")

# Category filter buttons 
st.markdown("#### Select Category")

for row_cards in [STAT_CARDS[:4], STAT_CARDS[4:]]:
    cols = st.columns(4)
    for i, (label, emoji, name) in enumerate(row_cards):
        count  = total_all if label == "All" else stats.get(label, 0)
        active = st.session_state.active_label == label
        with cols[i]:
            if st.button(f"{emoji}\n**{count}**\n{name}",
                         key=f"cat_{label}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.active_label = label
                st.session_state.page = 0
                st.rerun()

st.markdown("---")

# Applications sent counter 
ui.sent_counter(sent_stats)

# Urgent alerts 
if urgent and st.session_state.active_label == "All":
    st.markdown("### Needs Action Now")
    for item in urgent[:3]:
        ui.urgent_card(item, LABEL_PILL, BORDER_COLOR)
    st.markdown("---")

# Search & department filter 
active_label  = st.session_state.active_label
label_display = {l: n for l, _, n in STAT_CARDS}.get(active_label, active_label)
st.markdown(f"### {label_display}")

c1, c2 = st.columns([2, 1])
with c1:
    search = st.text_input("Search", placeholder="🔍 Company or role...",
                           value=st.session_state.search,
                           label_visibility="collapsed", key="search_input")
with c2:
    dept = st.selectbox("Dept", departments,
                        index=departments.index(st.session_state.dept)
                        if st.session_state.dept in departments else 0,
                        label_visibility="collapsed")

if search != st.session_state.search or dept != st.session_state.dept:
    st.session_state.page   = 0
    st.session_state.search = search
    st.session_state.dept   = dept

# Fetch current page 
page        = st.session_state.page
apps        = get_applications_by_label(active_label, page, PAGE_SIZE, search, dept)
total       = get_total_count(active_label, search, dept)
total_pages = max(1, -(-total // PAGE_SIZE))

st.caption(f"{total} applications · Page {page+1} of {total_pages}")

# Application cards + edit panels
if apps:
    for row in apps:
        ui.app_card(row, LABEL_PILL, BORDER_COLOR)

        with st.expander(f"Edit — {row.get('company', '?')}"):
            ui.edit_panel(row, LABEL_PILL, update_fields)
else:
    st.info("No applications in this category yet.")

# Pagination 
if total_pages > 1:
    st.markdown("---")
    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("← Prev", disabled=page == 0, use_container_width=True):
            st.session_state.page -= 1
            st.rerun()
    with p2:
        st.markdown(f'<p style="text-align:center;color:#64748b;font-size:0.82rem">'
                    f'Page {page+1} / {total_pages}</p>', unsafe_allow_html=True)
    with p3:
        if st.button("Next →", disabled=page >= total_pages - 1, use_container_width=True):
            st.session_state.page += 1
            st.rerun()

st.markdown("---")
st.caption("Mobile Version Tailscale · Auto-syncs every 6h")