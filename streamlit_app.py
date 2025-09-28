import streamlit as st
import pandas as pd

# =====================
# Configuração da página
# =====================
st.set_page_config(page_title="PES 21", page_icon="⚽", layout="wide")

# =====================
# Estilos customizados
# =====================
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
        font-family: 'Helvetica', sans-serif;
    }
    h1, h2, h3 {
        color: #00ffcc;
        text-align: center;
        font-weight: 700;
    }
    div.stButton > button {
        background-color: #00ffcc;
        color: black;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 18px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #ff00aa;
        color: white;
        transition: 0.3s;
    }
    /* Cards grandes */
    .big-number-card {
        background: linear-gradient(135deg, #00ffcc, #0077ff);
        color: white;
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }
    /* Campo */
    .campo {
        width: 100%;
        aspect-ratio: 2 / 3;
        background: linear-gradient(#006400, #228B22);
        border: 4px solid white;
        border-radius: 15px;
        position: relative;
        margin: 20px auto;
    }
    .jogador {
        position: absolute;
        color: black;
        border-radius: 50%;
        padding: 12px;
        text-align: center;
        font-size: 12px;
        font-weight: bold;
        width: 80px;
        height: 80px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        white-space: pre-line;
    }
    </style>
""", unsafe_allow_html=True)

# =====================
# Carregar dataset
# =====================
@st.cache_data
def load_data():
    df = pd.read_csv("base_precificada.csv", sep=",")
    return df

df = load_data()

st.title("⚽ PES 2021 Fantasy")

# =====================
# Filtros (apenas lista)
# =====================
col1, col2 = st.columns(2)

with col1:
    posicoes = st.multiselect("📍 Filtrar por posição", options=df["pos"].unique())
    ranks = st.multiselect("⭐ Filtrar por rank", options=df["rank"].unique())

with col2:
    preco_min, preco_max = st.slider(
        "💰 Faixa de preço",
        min_value=int(df["preco"].min()),
        max_value=int(df["preco"].max()),
        value=(int(df["preco"].min()), 20)
    )
    nome = st.text_input("🔎 Buscar por nome")

df_filtrado = df.copy()
if posicoes:
    df_filtrado = df_filtrado[df_filtrado["pos"].isin(posicoes)]
if ranks:
    df_filtrado = df_filtrado[df_filtrado["rank"].isin(ranks)]
if nome:
    df_filtrado = df_filtrado[df_filtrado["Jogador"].str.contains(nome, case=False, na=False)]
df_filtrado = df_filtrado[(df_filtrado["preco"] >= preco_min) & (df_filtrado["preco"] <= preco_max)]
df_filtrado = df_filtrado.drop(columns=["vel", "kicking", "destruction", "creation"], errors='ignore')

st.subheader("📋 Jogadores disponíveis (filtrados)")
st.dataframe(df_filtrado, use_container_width=True)

# =====================
# Seleção de time
# =====================
formacao = st.radio("📐 Escolha a formação:", ["4-3-3", "4-4-2"])

titulares = st.multiselect(
    "Selecione 11 jogadores (titulares)",
    options=df["Jogador"].tolist(),
    max_selections=11
)

reservas = st.multiselect(
    "Selecione até 12 jogadores (reservas)",
    options=df["Jogador"].tolist()
)

# =====================
# Mostrar custo do time + métricas
# =====================
df_time = df[df["Jogador"].isin(titulares + reservas)]
budget = 185

if not df_time.empty:
    custo_titulares = df[df["Jogador"].isin(titulares)]["preco"].sum()
    custo_reservas = df[df["Jogador"].isin(reservas)]["preco"].sum()
    custo_total = custo_titulares + custo_reservas
    saldo = budget - custo_total
    overall_medio = df[df["Jogador"].isin(titulares)]["overall"].mean() if titulares else 0

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='big-number-card'>💵 Total gasto: {custo_total:.1f} moedas</div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='big-number-card'>💸 Restante: {saldo:.1f}</div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='big-number-card'>🏆 Overall do time: {overall_medio:.1f}</div>", unsafe_allow_html=True)

    if custo_total > budget:
        st.error(f"🚨 Custo total ultrapassou o limite de {budget} moedas!")

# =====================
# Visualização em campo + reservas
# =====================
if len(titulares) == 11 and len(reservas) <= 12 and df_time["preco"].sum() <= budget:
    st.subheader("📊 Time em campo")
    col_field, col_bench = st.columns([2, 1])

    # Definir cores por posição
    cores = {
        "GK": "#FFA500",  # laranja
        "CB": "#1E90FF", "LB": "#1E90FF", "RB": "#1E90FF",
        "CM": "#32CD32", "LM": "#32CD32", "RM": "#32CD32",
        "LW": "#DC143C", "RW": "#DC143C", "ST": "#DC143C"
    }

    with col_field:
        if formacao == "4-3-3":
            posicoes_formacao = [
                ("GK", 90, 50), ("LB", 70, 15), ("CB", 70, 40), ("CB", 70, 60), ("RB", 70, 85),
                ("CM", 50, 25), ("CM", 50, 50), ("CM", 50, 75),
                ("LW", 25, 20), ("ST", 20, 50), ("RW", 25, 80)
            ]
        else:  # 4-4-2
            posicoes_formacao = [
                ("GK", 90, 50), ("LB", 70, 15), ("CB", 70, 40), ("CB", 70, 60), ("RB", 70, 85),
                ("LM", 35, 20), ("CM", 50, 40), ("CM", 50, 60), ("RM", 35, 80),
                ("ST", 15, 35), ("ST", 15, 65)
            ]

        html_campo = '<div class="campo">'
        for i, (pos, top, left) in enumerate(posicoes_formacao):
            if i < len(titulares):
                jogador = titulares[i]
                overall = df.loc[df["Jogador"] == jogador, "overall"].values[0]
                cor = cores.get(pos, "#32CD32")
                jogador_text = f"{jogador}\n{overall:.0f}"
                html_campo += f'<div class="jogador" style="top:{top}%; left:{left}%; background:{cor}; transform:translate(-50%, -50%);">{jogador_text}</div>'
        html_campo += "</div>"

        st.markdown(html_campo, unsafe_allow_html=True)

    with col_bench:
        st.markdown("### 🪑 Reservas")
        if reservas:
            df_reservas = df[df["Jogador"].isin(reservas)][["Jogador","pos","preco","overall"]]
            st.dataframe(df_reservas, use_container_width=True)
            st.write(f"💰 **Custo dos reservas:** {custo_reservas:.1f} moedas")
        else:
            st.info("Nenhum reserva selecionado.")
else:
    st.warning("⚠️ Selecione exatamente 11 titulares, até 12 reservas e respeite o limite de 170 moedas.")
