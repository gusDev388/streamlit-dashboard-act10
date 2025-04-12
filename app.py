import streamlit as st
import pandas as pd
import random
from openai import OpenAI
import plotly.express as px
import plotly.graph_objects as go

# Configuración general
st.set_page_config(page_title="Dashboard de Historia Mundial", layout="wide")
st.title("🌍 Dashboard Educativo de Historia Mundial")

# Cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"]["value"])

# Cargar datos
eventos_df = pd.read_csv("datos/World Important Dates.csv")
trivia_df = pd.read_csv("datos/trivia.csv")

# Limpiar y estandarizar años
def clean_year(y):
    try:
        if isinstance(y, str) and 'BC' in y:
            return -int(y.replace('BC', '').strip())
        return int(y)
    except:
        return None

eventos_df['Cleaned_Year'] = eventos_df['Year'].apply(clean_year)
eventos_df = eventos_df.dropna(subset=['Cleaned_Year'])
eventos_df = eventos_df.sort_values(by='Cleaned_Year')

# Sidebar de navegación
st.sidebar.markdown("👋 **Bienvenido(a) al dashboard histórico**")
st.sidebar.caption("Explora eventos, responde trivias y aprende con inteligencia artificial.")

menu = st.sidebar.selectbox("Selecciona una sección:", [
    "📚 Preguntas por época/región",
    "🧠 Trivia interactiva",
    "📊 Línea del tiempo de eventos",
    "🕰 Exploración histórica",
    "🤖 Asistente histórico (GPT)"
])
descripcion_secciones = {
    "📚 Preguntas por época/región": "Filtra y explora eventos según su año y región.",
    "🧠 Trivia interactiva": "Pon a prueba tus conocimientos históricos en 5 preguntas.",
    "📊 Línea del tiempo de eventos": "Visualiza cronológicamente eventos importantes por país.",
    "🕰 Exploración histórica": "Despliega información detallada y mapas por tipo de evento.",
    "🤖 Asistente histórico (GPT)": "Haz preguntas abiertas sobre historia y recibe respuestas de IA."
}
st.sidebar.markdown(f"ℹ️ {descripcion_secciones.get(menu, '')}")

# Años extremos del dataset
year_min = eventos_df['Cleaned_Year'].min()
year_max = eventos_df['Cleaned_Year'].max()
st.sidebar.markdown(f"📅 Años cubiertos: **{year_min}** a **{year_max}**")

# Botón de ayuda
if st.sidebar.button("❓ ¿Cómo usar el dashboard?"):
    st.sidebar.info("Selecciona una sección en el menú para comenzar.\nPuedes explorar eventos, responder trivias o hacer preguntas al asistente.")

# Curiosidad histórica aleatoria
curiosidades = [
    "📜 La primera civilización conocida fue la sumeria, en Mesopotamia.",
    "⚔️ El Imperio Mongol fue el imperio contiguo más grande de la historia.",
    "🗺 La Segunda Guerra Mundial involucró a más de 30 países.",
    "⏳ La imprenta revolucionó Europa en el siglo XV.",
    "🏛 Roma fue fundada, según la leyenda, en el año 753 a.C."
]
st.sidebar.markdown(random.choice(curiosidades))

# --- 1. Preguntas por época/región ---
if menu == "📚 Preguntas por época/región":
    st.subheader("📚 Consulta por época o región")
    epocas = sorted(eventos_df['Cleaned_Year'].unique())
    epoca_sel = st.selectbox("Selecciona una época o año:", epocas)

    regiones_filtradas = sorted(eventos_df[eventos_df['Cleaned_Year'] == epoca_sel]['Place Name'].dropna().unique())
    region_sel = st.selectbox("Selecciona una región o lugar:", regiones_filtradas)

    resultados = eventos_df[(eventos_df['Cleaned_Year'] == epoca_sel) & (eventos_df['Place Name'] == region_sel)]

    if not resultados.empty:
        for _, row in resultados.iterrows():
            st.markdown(f"### {row['Name of Incident']}")
            st.write(f"**Año:** {row['Year']} | **Lugar:** {row['Place Name']} | **Tipo:** {row['Type of Event']}")
            st.write(f"**Impacto:** {row['Impact']}")
            st.write(f"**Figura clave:** {row['Important Person/Group Responsible']}")
            st.write("---")
    else:
        st.warning("No se encontraron eventos con esa combinación.")

# --- 2. Trivia interactiva sin recarga ---
elif menu == "🧠 Trivia interactiva":
    st.subheader("🧠 Trivia Histórica (5 preguntas)")
    if 'respuestas_usuario' not in st.session_state:
        st.session_state.trivia_preguntas = random.sample(trivia_df.to_dict('records'), 5)
        st.session_state.respuestas_usuario = [None] * 5

    puntaje = 0
    for i, pregunta in enumerate(st.session_state.trivia_preguntas):
        st.markdown(f"**Pregunta {i+1}: {pregunta['pregunta']}**")
        opciones = eval(pregunta['opciones'])
        respuesta = st.radio("Selecciona una respuesta:", opciones, key=f"pregunta_{i}")
        st.session_state.respuestas_usuario[i] = respuesta
        if respuesta == pregunta['respuesta']:
            puntaje += 1

    if st.button("Calcular puntaje"):
        st.success(f"🎉 Has obtenido {puntaje} de 5 respuestas correctas.")
        if st.button("Volver a intentar"):
            del st.session_state.trivia_preguntas
            del st.session_state.respuestas_usuario
            st.experimental_rerun()

# --- 3. Línea del tiempo con detalles desplegables ---
elif menu == "📊 Línea del tiempo de eventos":
    st.subheader("📊 Línea del Tiempo de Eventos Clave")
    paises = sorted(eventos_df['Country'].dropna().unique())
    pais_sel = st.selectbox("Selecciona un país para ver su línea del tiempo:", paises)

    eventos_pais = eventos_df[eventos_df['Country'] == pais_sel]
    timeline_df = eventos_pais[['Name of Incident', 'Cleaned_Year']]

    fig = px.scatter(
        timeline_df,
        x='Cleaned_Year',
        y=[0] * len(timeline_df),
        hover_name='Name of Incident',
        color='Name of Incident',
        labels={'Cleaned_Year': 'Año'},
        size_max=10,
        title=f"Línea del Tiempo de Eventos - {pais_sel}"
    )
    fig.update_traces(marker=dict(size=12))
    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis=dict(visible=False),
        xaxis=dict(rangeslider=dict(visible=True), title='Año')
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Detalles de los eventos")
    for _, row in eventos_pais.iterrows():
        with st.expander(f"{row['Year']} - {row['Name of Incident']}"):
            st.write(f"**Lugar:** {row['Place Name']}")
            st.write(f"**Impacto:** {row['Impact']}")
            st.write(f"**Figura clave:** {row['Important Person/Group Responsible']}")
            st.write(f"**Resultado:** {row['Outcome']}")

# --- 4. Exploración histórica + Mapa ---
elif menu == "🕰 Exploración histórica":
    st.subheader("🕰 Modo Exploración Histórica")
    tipo_evento = st.selectbox("Filtrar por tipo de evento:", eventos_df['Type of Event'].unique())
    eventos_filtrados = eventos_df[eventos_df['Type of Event'] == tipo_evento]

    for _, row in eventos_filtrados.iterrows():
        with st.expander(f"{row['Year']} - {row['Name of Incident']}"):
            st.write(f"**Lugar:** {row['Place Name']}")
            st.write(f"**Impacto:** {row['Impact']}")
            st.write(f"**Figura clave:** {row['Important Person/Group Responsible']}")
            st.write(f"**Resultado:** {row['Outcome']}")
            st.write(f"**País:** {row['Country']}")
            if row['Country'] != 'Unknown':
                mapa = px.choropleth(
                    pd.DataFrame({'country': [row['Country']], 'value': [1]}),
                    locations='country',
                    locationmode='country names',
                    color='value',
                    range_color=[0, 1],
                    color_continuous_scale='blues',
                    title=f"Ubicación del evento: {row['Country']}"
                )
                st.plotly_chart(mapa, use_container_width=True)

# --- 5. Asistente histórico con ChatGPT ---
elif menu == "🤖 Asistente histórico (GPT)":
    st.subheader("🤖 Asistente de Historia Mundial")
    user_question = st.text_input("Haz una pregunta sobre historia mundial")

    if st.button("Consultar"):
        if user_question:
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_question}]
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Error al consultar la API: {e}")
        else:
            st.info("Por favor, ingresa una pregunta.")
