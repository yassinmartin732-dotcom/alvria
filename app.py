import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import requests
import re
from datetime import datetime, timedelta
import plotly.graph_objects as go
from google import genai
import os

# --- CONFIGURACIÓN DE PÁGINA (Pestaña del Navegador) ---
favicon_path = "favicon.png"
page_icon = favicon_path if os.path.exists(favicon_path) else "⚡"

st.set_page_config(
    page_title="Alvria - Asistente Financiero",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS INTELIGENTE Y ESTILO GEMINI ---
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

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- LOGOTIPO TRANSPARENTE EN BARRA LATERAL (ESTILO GEMINI) --- */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        background: transparent !important;
        border: none !important;
        padding: 5px 0px !important;
    }
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Métricas normales para PC */
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

    .mobile-kpi-row {
        display: none;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 1rem !important;
        }
        
        #desktop-kpis, div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) {
            display: none !important;
        }
        
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
        .mobile-kpi-row span {
            color: #2f81f7;
            font-weight: 600;
        }
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
        background-color: transparent;
        border-radius: 6px;
        padding: 4px 10px;
        color: #8b949e;
        font-weight: 500;
        border: none;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2f81f7 !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS Y CONFIGURACIONES ---
def init_db():
    conn = sqlite3.connect('portafolio.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, ticker TEXT, categoria TEXT, tipo TEXT,
            cantidad REAL, precio REAL, total REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT, fecha TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversacion_id INTEGER, role TEXT, content TEXT,
            FOREIGN KEY (conversacion_id) REFERENCES conversaciones (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

GEMINI_API_KEY = "AQ.Ab8RN6L9BPs7guukpVSuGag9z9nf5rZcM9rj1vzOwpR0a9wW7Q"
FINNHUB_API_KEY = "db9hg7hr01qjv8c5dqfgdb9hg7hr01qjv8c5d q g0".replace(" ", "")
FRED_API_KEY = "9d6a4faa5b8d2d16f0213659397123b8"

@st.cache_data(ttl=3600)
def obtener_datos_fred_cached(series_id):
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            obs = res.json().get('observations', [])
            if obs:
                return obs[0].get('value', 'N/A')
        return "N/A"
    except Exception:
        return "N/A"

@st.cache_data(ttl=1800)
def obtener_noticias_finnhub_cached(ticker):
    try:
        hasta_fecha = datetime.now().strftime('%Y-%m-%d')
        desde_fecha = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={desde_fecha}&to={hasta_fecha}&token={FINNHUB_API_KEY}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()[:3]
        return []
    except Exception:
        return []

def corregir_ticker_inteligente(texto_entrada):
    if not texto_entrada or not texto_entrada.strip():
        return ""
    texto_limpio = texto_entrada.strip().upper()
    mapa_comun = {
        "GOOGLLE": "GOOGL", "GOOGLE": "GOOGL", "NVIDIA": "NVDA", "NVIDIAM": "NVDA",
        "APPLE": "AAPL", "APLE": "AAPL", "TESLA": "TSLA", "AMAZON": "AMZN",
        "MICROSOFT": "MSFT", "BITCOIN": "BTC-USD", "BITCOING": "BTC-USD", "ETHEREUM": "ETH-USD"
    }
    if texto_limpio in mapa_comun:
        return mapa_comun[texto_limpio]
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt_corr = f"El usuario escribió '{texto_entrada}'. Devuelve ÚNICAMENTE el ticker oficial de bolsa correspondiente (ej: GOOGL, NVDA, AAPL, BTC-USD). No expliques nada, solo el ticker en mayúsculas."
        res = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt_corr
        )
        ticker_sugerido = res.text.strip().upper()
        t_check = yf.Ticker(ticker_sugerido)
        if not t_check.history(period="1d").empty:
            return ticker_sugerido
    except Exception:
        pass
    return texto_limpio

# --- BARRA LATERAL (LOGOTIPO COMPLETO TRANSPARENTE) ---
logo_completo_path = "logo_completo.png"
if os.path.exists(logo_completo_path):
    st.sidebar.image(logo_completo_path, width="stretch")
else:
    st.sidebar.markdown("### ⚡ Alvria")

if st.sidebar.button("➕ New chat", use_container_width=True):
    conn = sqlite3.connect('portafolio.db')
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO conversaciones (titulo, fecha) VALUES (?, ?)", ("Nueva Conversación", fecha_actual))
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    st.session_state.chat_activo = nuevo_id
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Recent chats")

conn = sqlite3.connect('portafolio.db')
cursor = conn.cursor()
cursor.execute("SELECT id, titulo, fecha FROM conversaciones ORDER BY id DESC")
lista_chats = cursor.fetchall()
conn.close()

bienvenida_amigable = (
    "✨ **Where should we start?**\n\n"
    "Hola, soy **Alvria**. Estoy lista para ayudarte con tus inversiones, estructurar metas financieras o resolver tus dudas de forma clara."
)

if not lista_chats:
    conn = sqlite3.connect('portafolio.db')
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO conversaciones (titulo, fecha) VALUES (?, ?)", ("Chat Principal", fecha_actual))
    conn.commit()
    chat_inicial_id = cursor.lastrowid
    cursor.execute("INSERT INTO mensajes (conversacion_id, role, content) VALUES (?, ?, ?)",
                   (chat_inicial_id, "assistant", bienvenida_amigable))
    conn.commit()
    conn.close()
    conn = sqlite3.connect('portafolio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, fecha FROM conversaciones ORDER BY id DESC")
    lista_chats = cursor.fetchall()
    conn.close()

if "chat_activo" not in st.session_state:
    st.session_state.chat_activo = lista_chats[0][0]

opciones_chats = {f"{chat[1]}": chat[0] for chat in lista_chats}
chat_seleccionado_nombre = st.sidebar.selectbox(
    "Seleccionar conversación:",
    options=list(opciones_chats.keys()),
    index=0 if st.session_state.chat_activo not in opciones_chats.values() else list(opciones_chats.values()).index(st.session_state.chat_activo),
    label_visibility="collapsed"
)
st.session_state.chat_activo = opciones_chats[chat_seleccionado_nombre]

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configuración & Datos")
capital_input_str = st.sidebar.text_input("Capital Total ($ USD)", "0")
perfil_input = st.sidebar.selectbox("Perfil de Riesgo", ["Conservador", "Moderado", "Agresivo"])

try:
    capital_inicial = float(capital_input_str.replace(",", ""))
except ValueError:
    capital_inicial = 0.0

fed_rate = obtener_datos_fred_cached("FEDFUNDS")
treasury_10y = obtener_datos_fred_cached("GS10")
st.sidebar.caption(f"🌐 Tasa FED: {fed_rate}% | Bono 10Y: {treasury_10y}%")

# --- ÁREA PRINCIPAL ---
conn = sqlite3.connect('portafolio.db')
df_kpi = pd.read_sql_query("SELECT * FROM transacciones", conn)
conn.close()

total_inversion_calculado = 0.0
if not df_kpi.empty:
    total_inversion_calculado = df_kpi.apply(lambda row: row['total'] if row['tipo'] == 'COMPRA' else -row['total'], axis=1).sum()

efectivo_disponible = capital_inicial - total_inversion_calculado

# 1. RECUADRO HORIZONTAL ÚNICO (Exclusivo para celular)
st.markdown(f"""
    <div class="mobile-kpi-row">
        <div>Capital: <span>${capital_inicial:,.2f}</span></div>
        <div>Libre: <span>${efectivo_disponible:,.2f}</span></div>
        <div>Activos: <span>${total_inversion_calculado:,.2f}</span></div>
    </div>
""", unsafe_allow_html=True)

# 2. TARJETAS COMPLETAS (Exclusivas para PC)
st.markdown('<div id="desktop-kpis">', unsafe_allow_html=True)
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1:
    st.metric(label="💰 Capital", value=f"${capital_inicial:,.2f}")
with col_kpi2:
    st.metric(label="💵 Libre", value=f"${efectivo_disponible:,.2f}")
with col_kpi3:
    st.metric(label="📊 Activos", value=f"${total_inversion_calculado:,.2f}")
st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑAS DE NAVEGACIÓN ---
tab_chat, tab_cartera, tab_mercado = st.tabs([
    "💬 Chat", 
    "📊 Portafolio", 
    "📈 Mercado"
])

# 1. PESTAÑA: CHAT
with tab_chat:
    conn = sqlite3.connect('portafolio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM mensajes WHERE conversacion_id = ?", (st.session_state.chat_activo,))
    mensajes_db = cursor.fetchall()
    conn.close()

    for role, content in mensajes_db:
        with st.chat_message(role):
            st.markdown(content)

    user_prompt = st.chat_input("Type @ or ask Alvria anything...")

    if user_prompt:
        conn = sqlite3.connect('portafolio.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mensajes (conversacion_id, role, content) VALUES (?, ?, ?)",
                       (st.session_state.chat_activo, "user", user_prompt))

        cursor.execute("SELECT titulo FROM conversaciones WHERE id = ?", (st.session_state.chat_activo,))
        titulo_actual = cursor.fetchone()[0]
        if titulo_actual == "Nueva Conversación":
            nuevo_titulo = user_prompt[:22] + "..." if len(user_prompt) > 22 else user_prompt
            cursor.execute("UPDATE conversaciones SET titulo = ? WHERE id = ?", (nuevo_titulo, st.session_state.chat_activo))

        conn.commit()
        conn.close()

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    resumen_transacciones = df_kpi.to_string(index=False) if not df_kpi.empty else "Sin transacciones."

                    system_instruction = (
                        f"Te llamas Alvria. Eres una IA financiera con motor cuantitativo avanzado, pero con una interfaz humana, natural y amigable.\n\n"
                        f"REGLAS INTELIGENTES DE COMPORTAMIENTO:\n"
                        f"1. ADAPTACIÓN DE TONO Y TOLERANCIA A ERRATAS: Entiende la intención del usuario aunque escriba nombres con faltas de ortografía (ej: 'googlle', 'nvidiam').\n"
                        f"2. PLANIFICACIÓN DE METAS: Si menciona una meta (viaje, auto, ahorro), calcula montos mensuales y activos sugeridos.\n"
                        f"3. EVALUACIÓN DE RIESGO: Si pregunta sobre el riesgo de su dinero, usa un diagnóstico visual con semáforo (🟢 RIESGO BAJO, 🟡 RIESGO MODERADO, 🔴 RIESGO ALTO).\n"
                        f"4. MODO DIDÁCTICO: Si pide explicaciones sencillas, usa peras y manzanas sin lenguaje técnico.\n\n"
                        f"Datos del usuario: Capital Total: ${capital_inicial:,.2f} USD, Efectivo Libre: ${efectivo_disponible:,.2f} USD, Perfil: {perfil_input}.\n"
                        f"Datos Macroeconómicos: Tasa FED: {fed_rate}%, Bono 10Y: {treasury_10y}%.\n"
                        f"Movimientos del usuario:\n{resumen_transacciones}"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=user_prompt,
                        config={'system_instruction': system_instruction}
                    )
                    ai_response = response.text
                    st.markdown(ai_response)

                    conn = sqlite3.connect('portafolio.db')
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO mensajes (conversacion_id, role, content) VALUES (?, ?, ?)",
                                   (st.session_state.chat_activo, "assistant", ai_response))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    st.error(f"Error: {e}")

# 2. PESTAÑA: PORTAFOLIO
with tab_cartera:
    st.subheader("📊 Gestión de Portafolio")
    with st.form("form_transaccion"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            t_ticker_input = st.text_input("Ticker", value="", placeholder="Ej: AAPL, NVDA")
            t_categoria = st.selectbox("Categoría", ["Tecnología", "Criptomonedas", "ETFs / Índices", "Otros"])
        with col_f2:
            t_tipo = st.selectbox("Operación", ["COMPRA", "VENTA"])
            t_cantidad = st.number_input("Cantidad", min_value=0.01, value=1.0)
        
        t_precio = st.number_input("Precio por unidad ($ USD)", min_value=0.01, value=100.0)
        submitted = st.form_submit_button("➕ Registrar Inversión")

        if submitted:
            if not t_ticker_input.strip():
                st.warning("Ingresa un símbolo.")
            else:
                t_ticker = corregir_ticker_inteligente(t_ticker_input)
                total_operacion = t_cantidad * t_precio
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect('portafolio.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transacciones (fecha, ticker, categoria, tipo, cantidad, precio, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (fecha_actual, t_ticker, t_categoria, t_tipo, t_cantidad, t_precio, total_operacion))
                conn.commit()
                conn.close()
                st.success(f"¡Registrado {t_ticker} con éxito!")
                st.rerun()

    conn = sqlite3.connect('portafolio.db')
    df_transacciones = pd.read_sql_query("SELECT * FROM transacciones ORDER BY id DESC", conn)
    conn.close()

    if not df_transacciones.empty:
        st.markdown("### Historial de Movimientos")
        st.dataframe(df_transacciones, use_container_width=True)

# 3. PESTAÑA: MERCADO
with tab_mercado:
    st.subheader("📈 Análisis de Mercado")
    ticker_input_plot = st.text_input("Buscar Ticker", value="", placeholder="Escribe un activo (ej. nvda, tesla)")
    
    if st.button("🔍 Consultar Activo"):
        if not ticker_input_plot.strip():
            st.warning("Escribe un símbolo válido.")
        else:
            try:
                with st.spinner("Buscando datos..."):
                    ticker_plot = corregir_ticker_inteligente(ticker_input_plot)
                    df_ticker = yf.Ticker(ticker_plot).history(period="3mo")
                    if not df_ticker.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_ticker.index, y=df_ticker['Close'], line=dict(color='#2f81f7', width=2), name=ticker_plot))
                        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No se encontraron datos.")

                    noticias = obtener_noticias_finnhub_cached(ticker_plot)
                    if noticias:
                        st.markdown("### 📰 Noticias Recientes")
                        for n in noticias:
                            st.markdown(f"• [{n.get('headline')}]({n.get('url')})")
            except Exception as e:
                st.error(f"Error: {e}")
