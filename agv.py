import streamlit as st
import requests
import json
import os
import pathlib
import random
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib.parse

# =====================================================================
# 🎨 STREAMLIT APPLICATION ROUTING & CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="Dynamic Fault Recovery System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mock user info for the sidebar since authentication is removed
user = {
    "name": "Console Operator",
    "email": "operator@warehouse.internal",
    "picture": "https://img.icons8.com/color/96/user-male-circle--v1.png"
}

st.sidebar.image(user["picture"], width=60)
st.sidebar.success(f"👋 Active Session: {user['name']}")
st.sidebar.caption(user["email"])

# --- Custom Styling Engine for Modern UI Canvas ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .metric-container {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        padding: 24px;
        border-radius: 20px;
        margin: 15px 0;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.15);
    }
    
    .metric-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        border-radius: 20px 20px 0 0;
    }
    
    .status-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 4px solid;
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .critical-alert {
        background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
        border-left-color: #dc2626;
        color: #991b1b;
    }
    
    .warning-alert {
        background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
        border-left-color: #d97706;
        color: #92400e;
    }
    
    .success-alert {
        background: linear-gradient(135deg, #d1fae5 0%, #f0fdf4 100%);
        border-left-color: #059669;
        color: #065f46;
    }
    
    .info-alert {
        background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
        border-left-color: #2563eb;
        color: #1d4ed8;
    }
    
    div.stButton > button, 
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
    }
    
    .stSelectbox > div > div > div,
    .stSelectbox label,
    .stSelectbox div[role="button"] {
        color: #1f2937 !important;
    }
    
    .fleet-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-available { background: #d1fae5; color: #065f46; }
    .status-working { background: #dbeafe; color: #1e40af; }
    .status-failed { background: #fee2e2; color: #991b1b; }
    .status-charging { background: #fef3c7; color: #92400e; }
    
    .pulse-animation {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: .7; }
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# ⚙️ SYSTEM CORE ARCHITECTURE MODELING (AGV, Task, Warehouse)
# =====================================================================
class AGV:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.batterylevel = random.uniform(60, 100)
        self.failed = False
        self.faulttype = None
        self.faultseverity = 0
        self.task = None
        self.losttask = None
        self.taskcompletioncount = 0
        self.totaldistance = 0
        self.lastmaintenance = time.time()
        self.operatinghours = random.uniform(0, 1000)
        self.intercept_info = None  
        
    def move(self):
        if self.failed or not self.task:
            return None
            
        dx = self.task.x - self.x
        dy = self.task.y - self.y
        
        if abs(dx) > 0: self.x += 1 if dx > 0 else -1
        if abs(dy) > 0: self.y += 1 if dy > 0 else -1
            
        self.totaldistance += 1
        self.batterylevel -= 0.1
        
        if self.x == self.task.x and self.y == self.task.y:
            completed_task = self.task
            self.task = None
            self.taskcompletioncount += 1
            completed_task.completed = True
            
            if hasattr(self, 'intercept_info'):
                self.intercept_info = None
                
            return completed_task
            
        return None
    
    def inducefault(self, log, tasks, fleet, assignment_system):
        if not self.failed and random.random() < 0.02:
            self.failed = True
            self.faulttype = random.choice(["LiDAR Error", "Battery Crit", "Motor Jam"])
            self.faultseverity = random.choice([1, 2, 3])
        
        if self.failed:
            if self.task:
                self.losttask = self.task
                log.append(f"🚨 AGV-{self.id:03d} FAILED ({self.faulttype}) while on T-{self.losttask.id}")
                assignment_system.trigger_immediate_takeover(self, fleet, log)
                self.task = None 
            else:
                log.append(f"🚨 AGV-{self.id:03d} FAILED ({self.faulttype})")
    
    def autorecover(self, log):
        if self.failed and self.faultseverity <= 2 and random.random() < 0.15:
            self.failed = False
            log.append(f"✅ AGV-{self.id:03d} AUTO-RECOVERY: {self.faulttype} fault resolved")
            self.faulttype = None
            self.faultseverity = 0
            self.losttask = None
    
    def manualrecover(self, log):
        if self.failed:
            self.failed = False
            log.append(f"🔧 AGV-{self.id:03d} MANUAL RECOVERY: {self.faulttype} fault manually resolved")
            self.faulttype = None
            self.faultseverity = 0
            self.losttask = None
    
    def gethealthscore(self):
        score = 100
        if self.failed:
            score -= self.faultseverity * 20
        score -= max(0, (100 - self.batterylevel) * 0.5)
        score -= min(30, self.operatinghours * 0.01)
        return max(0, score)

class Task:
    def __init__(self, id, x, y, priority=1, deadline=None):
        self.id = id
        self.x = x
        self.y = y
        self.priority = priority
        self.deadline = deadline or (time.time() + 1800)
        self.assignedagvid = None
        self.reassignmentcount = 0
        self.completed = False
        self.createdtime = time.time()

class TaskAssignmentSystem:
    def trigger_immediate_takeover(self, failed_agv, fleet, log):
        candidates = [a for a in fleet if not a.failed and not a.task and a.id != failed_agv.id]
        
        if candidates:
            best_backup = min(candidates, key=lambda a: abs(a.x - failed_agv.x) + abs(a.y - failed_agv.y))
            best_backup.task = failed_agv.losttask
            best_backup.task.assignedagvid = best_backup.id
            best_backup.task.reassignmentcount += 1
            best_backup.intercept_info = f"Recovering T-{best_backup.task.id} from failed AGV-{failed_agv.id:03d}"
            
            log.append(f"⚡ DYNAMIC TAKEOVER: AGV-{best_backup.id:03d} is now doing failed AGV-{failed_agv.id:03d}'s Task T-{best_backup.task.id}")
            failed_agv.losttask = None
            return True
            
        log.append(f"⚠️ TAKEOVER FAILED: No idle AGVs available to help AGV-{failed_agv.id:03d}")
        return False
        
    def smarttaskassignment(self, tasks, agvs, log):
        assignments = 0
        unassigned_tasks = [t for t in tasks if not t.assignedagvid and not t.completed]
        available_agvs = [a for a in agvs if not a.failed and not a.task]
        
        unassigned_tasks.sort(key=lambda t: (t.priority, t.deadline))
        
        for task in unassigned_tasks:
            if not available_agvs:
                break
                
            best_agv = min(available_agvs, key=lambda agv: 
                ((agv.x - task.x)**2 + (agv.y - task.y)**2) - agv.batterylevel/10)
            
            task.assignedagvid = best_agv.id
            best_agv.task = task
            available_agvs.remove(best_agv)
            assignments += 1
            
            if task.reassignmentcount > 0:
                log.append(f"🔄 REASSIGNMENT: Task T-{task.id} assigned to AGV-{best_agv.id:03d} (attempt #{task.reassignmentcount + 1})")
            else:
                log.append(f"📋 Task T-{task.id} assigned to AGV-{best_agv.id:03d}")
                
        return assignments
    
    def recoverlosttasks(self, agvs, log):
        recovered = 0
        for agv in agvs:
            if agv.losttask and not agv.failed:
                agv.task = agv.losttask
                agv.losttask.assignedagvid = agv.id
                agv.losttask = None
                recovered += 1
                log.append(f"🔄 Task T-{agv.task.id} recovered by AGV-{agv.id:03d}")
        return recovered

class WarehouseSystem:
    def __init__(self):
        self.taskassignmentsystem = TaskAssignmentSystem()
    
    def calculatekpis(self, agvs, tasks):
        total_agvs = len(agvs)
        operational_agvs = sum(1 for agv in agvs if not agv.failed)
        availability = (operational_agvs / total_agvs) * 100 if total_agvs > 0 else 0
        
        avg_battery = sum(agv.batterylevel for agv in agvs) / total_agvs if total_agvs > 0 else 0
        total_reassignments = sum(task.reassignmentcount for task in tasks)
        total_tasks = len(tasks)
        reassignment_rate = (total_reassignments / total_tasks) * 100 if total_tasks > 0 else 0
        
        completed_tasks = sum(1 for task in tasks if task.completed)
        efficiency = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        network_health = sum(1 for agv in agvs if not agv.failed and agv.faulttype != "Communication") / total_agvs * 100
        pending_tasks = sum(1 for task in tasks if not task.assignedagvid and not task.completed)
        
        return {
            'availability': availability,
            'avgbattery': avg_battery,
            'reassignmentrate': reassignment_rate,
            'efficiency': efficiency,
            'networkhealth': network_health,
            'pendingtasks': pending_tasks
        }

# =====================================================================
# INITIALIZE STATE MATRICES
# =====================================================================
GRIDSIZE = 25
NUMAGVS = 8
NUMTASKS = 15

if 'agvs' not in st.session_state:
    st.session_state.agvs = [AGV(i, random.randint(0, GRIDSIZE), random.randint(0, GRIDSIZE)) for i in range(NUMAGVS)]
    st.session_state.tasks = [Task(i, random.randint(0, GRIDSIZE), random.randint(0, GRIDSIZE), 
                                  random.choice([1,2,3]), time.time()+random.randint(300,1800)) for i in range(NUMTASKS)]
    st.session_state.warehouse = WarehouseSystem()
    st.session_state.log = ["📌 Platform Core Initialization Complete."]
    st.session_state.autorun = False
    st.session_state.GRIDSIZE = GRIDSIZE
    st.session_state.stepcount = 0
    st.session_state.kpihistory = [{'availability': 100.0, 'avgbattery': 90.0, 'networkhealth': 100.0, 'pendingtasks': NUMTASKS, 'reassignmentrate': 0.0, 'efficiency': 0.0, 'step': 0}]
    st.session_state.completedtasks = []

# --- Header Template ---
st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">🤖 Dynamic Fault Recovery System</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">Intelligent Autonomous Vehicle Fleet Operations & Real-time Monitoring</p>
    </div>
""", unsafe_allow_html=True)

# --- Sidebar Controls Layout ---
with st.sidebar:
    st.markdown("<div class='control-section'>", unsafe_allow_html=True)
    st.markdown("### 🎛️ System Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Smart Assignment", key="smart_assign"):
            assignments = st.session_state.warehouse.taskassignmentsystem.smarttaskassignment(
                st.session_state.tasks, st.session_state.agvs, st.session_state.log)
            if assignments > 0: st.success(f"✅ {assignments} tasks assigned!")
            else: st.warning("⚠️ No options")
            
    with col2:
        if st.button("🚨 Emergency Recovery", key="emergency"):
            recovered = 0
            for agv in st.session_state.agvs:
                if agv.failed:
                    agv.manualrecover(st.session_state.log)
                    recovered += 1
            if recovered > 0: st.success(f"🔧 {recovered} AGVs recovered!")
            
    if st.button("🔄 Recover Lost Tasks", key="recover"):
        recovered = st.session_state.warehouse.taskassignmentsystem.recoverlosttasks(
            st.session_state.agvs, st.session_state.log)
        if recovered > 0: st.success(f"📋 {recovered} tasks recovered!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='control-section'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Simulation")
    st.session_state.autorun = st.toggle("🔄 Auto Simulation", value=st.session_state.autorun)
    simulation_speed = st.slider("Simulation Speed", 0.5, 5.0, 2.0, 0.5)
    
    if st.button("▶️ Manual Step", key="manual_step"):
        for agv in st.session_state.agvs:
            agv.inducefault(st.session_state.log, st.session_state.tasks, st.session_state.agvs, st.session_state.warehouse.taskassignmentsystem)
            agv.autorecover(st.session_state.log)
            completed_task = agv.move()
            if completed_task:
                st.session_state.completedtasks.append(completed_task)
                st.session_state.log.append(f"✅ Task T-{completed_task.id} completed by AGV-{agv.id:03d}")
        
        st.session_state.warehouse.taskassignmentsystem.smarttaskassignment(
            st.session_state.tasks, st.session_state.agvs, st.session_state.log)
        st.session_state.stepcount += 1
        
        kpis = st.session_state.warehouse.calculatekpis(st.session_state.agvs, st.session_state.tasks)
        kpis['step'] = st.session_state.stepcount
        st.session_state.kpihistory.append(kpis)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Loop Execution Strategy (Auto-run)
if st.session_state.autorun:
    time.sleep(1.0 / simulation_speed)
    for agv in st.session_state.agvs:
        agv.inducefault(st.session_state.log, st.session_state.tasks, st.session_state.agvs, st.session_state.warehouse.taskassignmentsystem)
        agv.autorecover(st.session_state.log)
        completed_task = agv.move()
        if completed_task:
            st.session_state.completedtasks.append(completed_task)
            st.session_state.log.append(f"✅ Task T-{completed_task.id} completed by AGV-{agv.id:03d}")
            
    st.session_state.warehouse.taskassignmentsystem.smarttaskassignment(
        st.session_state.tasks, st.session_state.agvs, st.session_state.log)
    st.session_state.stepcount += 1
    
    kpis = st.session_state.warehouse.calculatekpis(st.session_state.agvs, st.session_state.tasks)
    kpis['step'] = st.session_state.stepcount
    st.session_state.kpihistory.append(kpis)
    st.rerun()

# --- Render Top Level Metric Banners ---
if st.session_state.kpihistory:
    latest_kpi = st.session_state.kpihistory[-1]
    availability = latest_kpi['availability']
    reassignment_rate = latest_kpi['reassignmentrate']
    
    if availability >= 90:
        st.markdown(f'<div class="status-card success-alert"><strong>🟢 System Status: Excellent</strong><br>Fleet Availability: {availability:.1f}% • Running Optimal</div>', unsafe_allow_html=True)
    elif availability >= 70:
        st.markdown(f'<div class="status-card warning-alert"><strong>🟡 System Status: Moderate</strong><br>Fleet Availability: {availability:.1f}% • Interventions Indicated</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-card critical-alert pulse-animation"><strong>🔴 System Status: Critical</strong><br>Fleet Availability: {availability:.1f}% • Immediate System Failures Active</div>', unsafe_allow_html=True)

# =====================================================================
# DASHBOARD TABS ENGINE RENDER
# =====================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🤖 Fleet Status", "🗺️ Live Map", "🔄 Job Recovery", "📈 Analytics"])

with tab1:
    st.markdown("### 📊 Real-time Performance Dashboard")
    if st.session_state.kpihistory:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("🎯 Fleet Availability", f"{latest_kpi['availability']:.1f}%")
        col2.metric("🔋 Avg Battery", f"{latest_kpi['avgbattery']:.1f}%")
        col3.metric("🌐 Network Health", f"{latest_kpi['networkhealth']:.0f}%")
        col4.metric("📋 Pending Tasks", latest_kpi['pendingtasks'])
        col5.metric("🔄 Reassignment Rate", f"{latest_kpi['reassignmentrate']:.1f}%")

    if len(st.session_state.kpihistory) > 1:
        df_kpi = pd.DataFrame(st.session_state.kpihistory)
        fig = make_subplots(rows=2, cols=3, subplot_titles=("🎯 Availability (%)", "🔄 Reassignments (%)", "⚡ Efficiency (%)", "🌐 Network (%)", "🔋 Avg Battery (%)", "📊 Pending"))
        
        fig.add_trace(go.Scatter(x=df_kpi['step'], y=df_kpi['availability'], mode="lines", name="Avail", line=dict(color='#10b981')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_kpi['step'], y=df_kpi['reassignmentrate'], mode="lines", name="Reassign", line=dict(color='#f59e0b')), row=1, col=2)
        fig.add_trace(go.Scatter(x=df_kpi['step'], y=df_kpi['efficiency'], mode="lines", name="Eff", line=dict(color='#3b82f6')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_kpi['step'], y=df_kpi['networkhealth'], mode="lines", name="Net", line=dict(color='#8b5cf6')), row=2, col=2)
        fig.add_trace(go.Scatter(x=df_kpi['step'], y=df_kpi['avgbattery'], mode="lines", name="Batt", line=dict(color='#06b6d4')), row=2, col=3)
        fig.add_trace(go.Bar(x=df_kpi['step'], y=df_kpi['pendingtasks'], name="Load", marker=dict(color='#ef4444')), row=1, col=3)
        
        fig.update_layout(height=450, showlegend=False, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### 🤖 Fleet Status & Health Monitoring")
    for agv in st.session_state.agvs:
        health_score = agv.gethealthscore()
        status = "Failed" if agv.failed else ("Working" if agv.task else "Available")
        s_class = "status-failed" if agv.failed else ("status-working" if agv.task else "status-available")
        
        col1, col2, col3, col4 = st.columns([2,2,2,4])
        col1.markdown(f'<div class="fleet-card"><h4>AGV-{agv.id:03d}</h4><span class="status-badge {s_class}">{status}</span></div>', unsafe_allow_html=True)
        col2.metric("Battery Status", f"{agv.batterylevel:.1f}%")
        col3.metric("Health Score", f"{health_score:.1f}/100")
        
        with col4:
            if agv.failed: st.error(f"⚠️ Fault Detected: {agv.faulttype} (Severity Level {agv.faultseverity})")
            elif agv.intercept_info: st.warning(f"⚡ {agv.intercept_info}")
            else: st.info(f"Assigned Destination: {f'Task T-{agv.task.id} ({agv.task.x}, {agv.task.y})' if agv.task else 'Standing By (Idle)'}")

with tab3:
    st.markdown("### 🗺️ Live Warehouse Operations Matrix Map")
    show_paths = st.checkbox("Show Vector Task Paths", value=True)
    
    fig_map = go.Figure()
    
    # Render Tasks Locations
    for t in st.session_state.tasks:
        if not t.completed:
            fig_map.add_trace(go.Scatter(x=[t.x], y=[t.y], mode="markers", marker=dict(symbol='diamond', size=14, color='#f59e0b'), name=f"Task T-{t.id}"))
            
    # Render Active Robotic Fleets
    for a in st.session_state.agvs:
        a_color = '#ef4444' if a.failed else ('#3b82f6' if a.task else '#10b981')
        fig_map.add_trace(go.Scatter(x=[a.x], y=[a.y], mode="markers+text", text=f"AGV-{a.id:02d}", textposition="top center", marker=dict(symbol='square', size=16, color=a_color), name=f"AGV-{a.id}"))
        
        if show_paths and a.task and not a.failed:
            fig_map.add_trace(go.Scatter(x=[a.x, a.task.x], y=[a.y, a.task.y], mode="lines", line=dict(dash='dot', color='rgba(59,130,246,0.5)', width=2)))

    fig_map.update_layout(width=None, height=550, plot_bgcolor='#f8fafc', xaxis=dict(range=[-1, GRIDSIZE+1]), yaxis=dict(range=[-1, GRIDSIZE+1]))
    st.plotly_chart(fig_map, use_container_width=True)

with tab4:
    st.markdown("### 📜 Dynamic Fault & Takeover History Logs")
    for entry in reversed(st.session_state.log[-12:]):
        if "⚡ DYNAMIC TAKEOVER" in entry:
            st.markdown(f'<div style="padding:10px; background:#fff7ed; border-left:4px solid #f97316; margin:5px 0; border-radius:4px; font-weight:600;">{entry}</div>', unsafe_allow_html=True)
        elif "🚨" in entry:
            st.markdown(f'<span style="color:#dc2626;">{entry}</span>', unsafe_allow_html=True)
        else:
            st.text(entry)

with tab5:
    st.markdown("### 📈 Machine Predictive Insights")
    if len(st.session_state.kpihistory) >= 5:
        df_kpi = pd.DataFrame(st.session_state.kpihistory)
        if df_kpi['availability'].tail(5).mean() < 85:
            st.info("🔮 Operational Trend Analysis: Cascade component wear detected. Maintain intervals soon.")
        else:
            st.success("✅ Operational Analytics: Fleet efficiency patterns remain structural and clean.")
    else:
        st.info("Data arrays processing. Performance history building metrics...")

# --- Global Expandable Logging Module ---
with st.expander("📝 Complete System Telemetry Event Logs", expanded=False):
    st.markdown("<div class='log-container'>", unsafe_allow_html=True)
    for entry in reversed(st.session_state.log):
        st.write(entry)
    st.markdown("</div>", unsafe_allow_html=True)

# Process cleanup matrices updates
st.session_state.tasks = [t for t in st.session_state.tasks if not t.completed]

# Footer Framework metrics indicators
st.markdown("---")
f_col1, f_col2, f_col3 = st.columns(3)
f_col1.metric("Current Simulation Step", st.session_state.stepcount)
f_col2.metric("Total Executed Tasks", len(st.session_state.completedtasks))
f_col3.metric("Fleet Accumulated Distance Traveled", f"{sum(a.totaldistance for a in st.session_state.agvs)}m")
