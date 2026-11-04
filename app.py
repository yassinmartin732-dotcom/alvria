import streamlit as st

# Configuración de la página (Debe ser lo primero)
st.set_page_config(
    page_title="Alvria - Asistente Financiero",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales personalizados e Inyección de metadatos SEO / Google Analytics
st.markdown("""
    <head>
        <meta name="google-site-verification" content="i8Lmkk4heGKxUsSaGrSh7-HrKS9KkDmdJfQHyVxiwNE" />
        <script async src="https://www.googletagmanager.com/gtag/js?id=GTM-P46CVH99"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('get', 'GTM-P46CVH99', 'config', 'GTM-P46CVH99');
        </script>
    </head>
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

# Título y cabecera principal
st.title("💎 Alvria — Asistente Financiero Inteligente")

# Barra lateral (Sidebar) para configuración financiera
st.sidebar.header("⚙️ Configuración & Datos")
capital_total = st.sidebar.number_input("Capital Total ($ USD)", min_value=0.0, value=0.0, step=100.0)
perfil_riesgo = st.sidebar.selectbox("Perfil de Riesgo", ["Conservador", "Moderado", "Agresivo"])

# Pestañas principales de la aplicación
tab_chat, tab_portafolio, tab_mercado = st.tabs(["💬 Chat", "📊 Portafolio", "📈 Mercado"])

with tab_chat:
    st.subheader("✨ Where should we start?")
    st.write(f"Hola, soy **Alvria**. Estoy lista para ayudarte con tus inversiones, estructurar tu capital de **${capital_total:,.2f} USD** bajo un perfil **{perfil_riesgo}**.")

    # Inicializar el historial del chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar mensajes previos
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada del usuario para el chat
    if prompt := st.chat_input("Escribe tu consulta financiera..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Respuesta inteligente adaptada al perfil
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
    st.info("Buscador y cotizador de acciones y criptomonedas integrado.")
