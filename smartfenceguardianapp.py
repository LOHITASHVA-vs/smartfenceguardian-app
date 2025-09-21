import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Smart Fence Guardian", layout="wide")

st.title("⚡ Smart Fence Guardian – Simulation Demo")
st.markdown("**SIH 2025 | Voltage Vikings**")

# Sidebar mode selector
mode = st.sidebar.radio("Select Mode", ["Live Simulation", "CSV Dataset"])

# =========================
# 1. Live Simulation Section
# =========================
event = st.sidebar.selectbox(
    "Choose Event (for Live Simulation)",
    ["Normal", "Voltage Drop", "Leakage Rise", "Wire Cut", "Grounding", "Box Open", "Energizer Off"]
)

speed = st.sidebar.slider("Simulation Speed (CSV & Live)", 0.1, 2.0, 1.0)

def simulate(event_type, n=200):
    data = []
    for i in range(n):
        t = i / 10.0
        if event_type == "Normal":
            V = 700 + np.sin(t) * 5
            I = 0.8 + np.sin(t/2) * 0.05
            L = 0.02 + np.random.randn() * 0.002
            box = 0
        elif event_type == "Voltage Drop":
            V = 300 + np.random.randn() * 10
            I = 0.5 + np.random.randn() * 0.05
            L = 0.03 + np.random.randn() * 0.01
            box = 0
        elif event_type == "Leakage Rise":
            V = 680 + np.random.randn() * 5
            I = 0.7 + np.random.randn() * 0.05
            L = 0.7 + np.random.randn() * 0.05
            box = 0
        elif event_type == "Wire Cut":
            V = 50 + np.random.randn() * 5
            I = 0.05 + np.random.randn() * 0.01
            L = 0.0 + np.random.randn() * 0.002
            box = 0
        elif event_type == "Grounding":
            V = 300 + np.random.randn() * 20
            I = 1.0 + np.random.randn() * 0.05
            L = 0.8 + np.random.randn() * 0.05
            box = 0
        elif event_type == "Box Open":
            V = 700 + np.random.randn() * 5
            I = 0.8 + np.random.randn() * 0.05
            L = 0.02 + np.random.randn() * 0.002
            box = 1
        elif event_type == "Energizer Off":
            V, I, L, box = 0, 0, 0, 0
        data.append([i, V, I, L, box])
    df = pd.DataFrame(data, columns=["t", "Voltage", "Current", "Leakage", "Box"])
    return df

# =========================
# 2. Detection Logic with SMS Panel
# =========================
tamper_count = st.session_state.get("tamper_count", 0)
lockout = st.session_state.get("lockout", False)

def detect(df, event_type):
    global tamper_count, lockout
    sms_message = ""

    if lockout:
        sms_message = "CRITICAL ALERT: Fence system LOCKED OUT. Reset required."
        return "🔒 CRITICAL: System Locked Out! Needs Authorized Reset", sms_message

    if event_type == "Normal":
        return "✅ Normal Condition – Logging only", "No SMS sent. System stable."
    elif event_type in ["Voltage Drop", "Leakage Rise"]:
        sms_message = f"⚠️ WARNING: Abnormal condition detected ({event_type}). Please check fence."
        return "⚠️ Warning – SMS + Buzzer Activated", sms_message
    elif event_type in ["Wire Cut", "Grounding", "Box Open"]:
        tamper_count += 1
        st.session_state["tamper_count"] = tamper_count
        if tamper_count >= 3:
            st.session_state["lockout"] = True
            sms_message = "🚨 CRITICAL: Multiple Tamper attempts! Fence LOCKED until reset."
            return "🔒 CRITICAL: Multiple Tampering – Lockout until Reset", sms_message
        else:
            sms_message = f"🚨 TAMPER ALERT: {event_type} detected! Siren + Cutoff triggered."
            return "🚨 Tamper Detected – Siren + Cutoff Relay", sms_message
    elif event_type == "Energizer Off":
        st.session_state["lockout"] = True
        sms_message = "🚨 CRITICAL: Energizer OFF. System locked until authorized reset."
        return "🔒 CRITICAL: Energizer Off – Lockout until Reset", sms_message
    else:
        return "Unknown Condition", "Unknown SMS Event"

# =========================
# 3. CSV Dataset Mode
# =========================
if mode == "CSV Dataset":
    uploaded_file = st.file_uploader("📂 Upload CSV Dataset", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        st.subheader("📊 CSV Data Playback (Live Feed)")
        placeholder = st.empty()

        for i, row in df.iterrows():
            with placeholder.container():
                st.write(f"Time {i} | Voltage={row['V']} | Current={row['I']} | Leakage={row['L']}")
            time.sleep(0.1 / speed)

        # Plot CSV data
        st.subheader("📈 Sensor Graphs from CSV")
        fig, axs = plt.subplots(3, 1, figsize=(12, 8))
        axs[0].plot(df["V"]); axs[0].set_title("Voltage")
        axs[1].plot(df["I"]); axs[1].set_title("Current")
        axs[2].plot(df["L"]); axs[2].set_title("Leakage")
        plt.tight_layout(pad=3.0)
        st.pyplot(fig)

else:
    # Live Simulation Mode
    df = simulate(event)
    decision, sms_message = detect(df, event)

    st.subheader("📈 Sensor Readings (Live Simulation)")
    fig, axs = plt.subplots(4, 1, figsize=(12, 10))
    axs[0].plot(df["t"], df["Voltage"]); axs[0].set_title("Voltage")
    axs[1].plot(df["t"], df["Current"]); axs[1].set_title("Current")
    axs[2].plot(df["t"], df["Leakage"]); axs[2].set_title("Leakage")
    axs[3].plot(df["t"], df["Box"]); axs[3].set_title("Box Status (0=Closed, 1=Open)")
    plt.tight_layout(pad=3.0)
    st.pyplot(fig)

    # Decision Display
    st.subheader("🔍 System Decision")
    if "Normal" in decision:
        st.success(decision)
    elif "Warning" in decision:
        st.warning(decision)
    elif "Tamper" in decision:
        st.error(decision)
    elif "CRITICAL" in decision:
        st.error(decision)

    # SMS Panel
    st.subheader("📱 SMS / Alert Log")
    st.info(sms_message)

    # Reset button
    if st.button("🔄 Authorized Reset"):
        st.session_state["tamper_count"] = 0
        st.session_state["lockout"] = False
        st.success("System Reset Successful – Monitoring Resumed")
