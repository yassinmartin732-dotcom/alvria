import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Alvria — Asistente Financiero Inteligente",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales personalizados
st.markdown("""
    <style>
        .stApp {
            background-color: #0b0f19;
            color: #ffffff;
        }
        sidebar .stSidebar {
            background-color: #111827;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BARRA LATERAL (LOGOTIPO Y CONFIGURACIÓN)
# ==========================================
with st.sidebar:
    col_v1, col_img, col_v2 = st.columns([1, 6, 1])
    with col_img:
        try:
            st.image("logo_completo.png", width=220)
        except:
            st.subheader("💎 Alvria")
    
    st.markdown("---")
    st.header("⚙️ Configuración & Datos")
    capital_total = st.number_input("Capital Total ($ USD)", min_value=0.0, value=0.0, step=100.0)
    perfil_riesgo = st.selectbox("Perfil de Riesgo", ["Conservador", "Moderado", "Agresivo"])

# ==========================================
# 3. CUERPO PRINCIPAL Y PESTAÑAS DE ALVRIA
# ==========================================
st.title("Alvria — Asistente Financiero Inteligente")

# Pestañas principales de la aplicación
tab_chat, tab_portafolio, tab_mercado = st.tabs(["💬 Chat", "📊 Portafolio", "📈 Mercado"])

with tab_chat:
    st.subheader("✨ Where should we start?")
    st.write(f"Hola, soy **Alvria**. Estoy lista para ayudarte con tus inversiones, estructurar tu capital de **${capital_total:,.2f} USD** bajo un perfil **{perfil_riesgo}**.")

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
            if capital_total == 0:
                respuesta = "Para darte una recomendación precisa, por favor define primero tu **Capital Total** en la barra lateral de la izquierda."
            else:
                respuesta = f"Analizando tu consulta bajo tu perfil **{perfil_riesgo}** y tu capital disponible de **${capital_total:,.2f} USD**:\n\n"
                if perfil_riesgo == "Conservador":
                    respuesta += "- Te sugiero destinar un 70% a renta fija de bajo riesgo y 30% a fondos indexados estables."
                elif perfil_riesgo == "Moderado":
                    respuesta += "- Te sugiero una distribución equilibrada: 50% en acciones sólidas, 30% en renta fija y 20% en criptoactivos o activos de crecimiento."
                else:
                    respuesta += "- Al ser un perfil agresivo, puedes enfocar un 60% en oportunidades de alto crecimiento (acciones tecnológicas/innovación) y 40% en diversificación táctica."
            
            st.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})

with tab_portafolio:
    st.subheader("📊 Rastreador de Portafolio")
    st.info("Aquí podrás registrar tus activos y visualizar el rendimiento de tu capital en tiempo real.")
    st.write(f"**Capital asignado al portafolio:** ${capital_total:,.2f} USD")

with tab_mercado:
    st.subheader("📈 Mercado en Tiempo Real")
    st.write("Consulta el precio actual y el historial de acciones o criptomonedas (ej. `AAPL`, `TSLA`, `BTC-USD`, `NVDA`).")
    
    # Buscador de tickers
    ticker_symbol = st.text_input("Símbolo del Activo (Ticker):", value="AAPL").upper()
    
    if ticker_symbol:
        try:
            ticker_data = yf.Ticker(ticker_symbol)
            hist = ticker_data.history(period="1mo")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((current_price - prev_price) / prev_price) * 100
                
                col1, col2 = st.columns(2)
                col1.metric(label=f"Precio Actual ({ticker_symbol})", value=f"${current_price:,.2f} USD", delta=f"{change:.2f}%")
                
                # Gráfico de la cotización
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Cierre', line=dict(color='#00d26a', width=2)))
                fig.update_layout(
                    title=f"Comportamiento Histórico (Último Mes) - {ticker_symbol}",
                    xaxis_title="Fecha",
                    yaxis_title="Precio (USD)",
                    plot_bgcolor='#0b0f19',
                    paper_bgcolor='#0b0f19',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No se encontraron datos para este símbolo. Intenta con otro (ej. AAPL, MSFT, TSLA).")
        except Exception as e:
            st.error(f"Error al obtener los datos del mercado: {e}")
