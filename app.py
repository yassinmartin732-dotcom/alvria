import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.genai as genai
import requests
from PIL import Image

# 1. Configuración de la página
st.set_page_config(
    page_title="Alvria - Asistente Financiero",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de CSS (Corregido con unsafe_allow_html=True)
st.markdown("""
<style>
    .stApp { 
        background-color: #0e1117; 
        color: #e3e3e3; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
    } 
    [data-testid="stSidebar"] { 
        background-color: #161b22; 
        border-right: 1px solid #30363d; 
    } 
    #MainMenu { visibility: hidden; } 
    footer { visibility: hidden; } 
    
    /* LOGOTIPO TRANSPARENTE EN BARRA LATERAL */
    [data-testid="stSidebar"] [data-testid="stImage"] { 
        background: transparent !important; 
        border: none !important; 
        padding: 5px 0px !important; 
    } 
    [data-testid="stSidebar"] [data-testid="stImage"] img { 
        background: transparent !important; 
        box-shadow: none !important; 
    } 
    
    /* Métricas para PC */
    [data-testid="stMetric"] { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 10px 14px; 
        border-radius: 12px; 
    } 
    [data-testid="stMetricValue"] { 
        font-size: 1.3rem !important; 
        font-weight: 600 !important; 
        color: #2f81f7 !important; 
    } 
    [data-testid="stMetricLabel"] { 
        font-size: 0.75rem !important; 
        color: #8b949e !important; 
    } 
    
    .mobile-kpi-row { display: none; } 
    
    @media (max-width: 768px) { 
        .block-container { padding-top: 0.4rem !important; padding-bottom: 1rem !important; } 
        #desktop-kpis, div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) { display: none !important; } 
        .mobile-kpi-row { 
            display: flex !important; 
            justify-content: space-around; 
            align-items: center; 
            background-color: #161b22; 
            border: 1px solid #30363d; 
            padding: 8px 6px; 
            border-radius: 12px; 
            margin-bottom: 10px; 
            font-size: 0.8rem; 
            color: #8b949e; 
        } 
        .mobile-kpi-row span { color: #2f81f7; font-weight: 600; } 
    } 
    
    .stTabs [data-baseweb="tab-list"] { 
        gap: 4px; 
        background-color: #161b22; 
        padding: 3px; 
        border-radius: 8px; 
        border: 1px solid #30363d; 
        justify-content: center; 
        margin-bottom: 8px; 
    } 
    .stTabs [data-baseweb="tab"] { 
        background: transparent; 
        border-radius: 6px; 
        padding: 4px 10px; 
        color: #8b949e; 
        font-weight: 500; 
        border: none; 
        font-size: 0.85rem; 
    } 
    .stTabs [aria-selected="true"] { 
        background: #2f81f7 !important; 
        color: #ffffff !important; 
    } 
</style>
""", unsafe_allow_html=True)

# 3. Barra Lateral (Sidebar)
with st.sidebar:
    try:
        logo = Image.open("logo_completo.png")
        st.image(logo, use_container_width=True)
    except:
        st.title("Alvria")
    
    st.markdown("---")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("### 💬 Recent chats")
    chat_option = st.selectbox("Seleccionar chat", ["Chat Principal"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuración & Datos")
    capital = st.number_input("Capital Total ($ USD)", min_value=0.0, value=0.0, step=100.0)
    perfil = st.selectbox("Perfil de Riesgo", ["Conservador", "Moderado", "Agresivo"])
    
    st.markdown("---")
    st.caption("🌐 Tasa FED: 3.88% | Bono 10Y: 5.13%")

# 4. KPIs visuales
st.markdown("""
<div class="mobile-kpi-row">
    <div>Capital: <span>$0.00</span></div>
    <div>Libre: <span>$0.00</span></div>
    <div>Activos: <span>$0.00</span></div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Capital", f"${capital:,.2f}")
with col2:
    st.metric("💵 Libre", f"${capital:,.2f}")
with col3:
    st.metric("📊 Activos", "$0.00")

# 5. Navegación Principal
tab_chat, tab_portafolio, tab_mercado = st.tabs(["💬 Chat", "📊 Portafolio", "📈 Mercado"])

with tab_chat:
    st.markdown("### ✨ Where should we start?")
    st.write("Hola, soy **Alvria**. Estoy lista para ayudarte con tus inversiones, estructurar metas financieras o resolver tus dudas de forma clara.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Escribe tu consulta financiera..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = f"Procesando tu consulta sobre: *'{prompt}'* considerando un perfil **{perfil}**."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

with tab_portafolio:
    st.info("Sección de portafolio en construcción. Pronto podrás vincular tus activos.")

with tab_mercado:
    st.info("Sección de mercado en construcción. Consultando cotizaciones en tiempo real.")
