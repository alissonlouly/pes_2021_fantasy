import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import unicodedata
import plotly.graph_objects as go

# =====================
# Configuração da página
# =====================
st.set_page_config(page_title="PES 21", page_icon="⚽", layout="wide")

# =====================
# Estilos customizados
# =====================
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; font-family: 'Helvetica', sans-serif; }
    h1, h2, h3 { color: #00ffcc; text-align: center; font-weight: 700; }
    div.stButton > button { background-color: #18a558; color: black; border-radius: 10px; height: 3em; width: 100%; font-size: 18px; font-weight: bold; }
    div.stButton > button:hover { background-color: #148847; color: white; transition: 0.3s; }
    .big-number-card { background: linear-gradient(135deg, #00ffcc, #0077ff); color: white; padding: 20px; border-radius: 20px; text-align: center; font-size: 28px; font-weight: bold; box-shadow: 0px 4px 12px rgba(0,0,0,0.4); margin-bottom: 15px; }
    .campo { width: 100%; aspect-ratio: 2 / 3; background: linear-gradient(#006400, #228B22); border: 4px solid white; border-radius: 15px; position: relative; margin: 20px auto; }
    .jogador { position: absolute; color: black; border-radius: 50%; padding: 12px; text-align: center; font-size: 12px; font-weight: bold; width: 80px; height: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); white-space: pre-line; }
    </style>
""", unsafe_allow_html=True)

# =====================
# Carregar dataset
# =====================
@st.cache_data
def load_data():
    # Tenta encodings comuns para preservar acentos em diferentes origens de CSV.
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            df = pd.read_csv("base_precificada_2026_s3.csv", sep=",", encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        df = pd.read_csv("base_precificada_s3.csv", sep=",")

    # Normaliza tipos para evitar exibição de inteiros como 94.0
    df["Preço"] = pd.to_numeric(df["Preço"], errors="coerce")
    df["Overall"] = pd.to_numeric(df["Overall"], errors="coerce").round().astype("Int64")

    return df


def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

df = load_data()

# Dicionário com cores por grupo (Movido para cá para ser acessado por ambas as páginas)
cores_colunas = {
    'Off. Awareness': '#990000',   
    'Finishing': '#990000',
    'Kicking Power': '#990000',
    
    'Ball Control': '#008080',          
    'Dribbling': '#008080',
    'Tight Possession': '#008080',
    'Balance': '#008080',
    
    'Heading': '#000080',               
    'Jump': '#000080',
    'Defensive Awarenes': '#000080',
    'Ball Winning': '#000080',
    'Aggression': '#000080',
    
    'Low Pass': '#556B2F',              
    'Lofted Pass': '#556B2F',
    'Place Kicking': '#556B2F',
    'Curl': '#556B2F',
    
    'Speed': '#8B4513',                  
    'Acceleration': '#8B4513',
    'Physical Contact': '#8B4513',
    'Stamina': '#8B4513',
    
    'GK Awareness': '#4B0082',           
    'GK Catching': '#4B0082',
    'GK Clearing': '#4B0082',
    'GK Reflexes': '#4B0082',
    'GK Reach': '#4B0082',
}


# =====================
# Navegação Lateral
# =====================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Montar Time"

st.sidebar.subheader("Navegação")

if st.sidebar.button("⚽ Montar Time", use_container_width=True):
    st.session_state.pagina = "Montar Time"

if st.sidebar.button("⚖️ Comparar Jogadores", use_container_width=True):
    st.session_state.pagina = "Comparar Jogadores"

pagina = st.session_state.pagina
st.sidebar.caption(f"Página atual: **{pagina}**")

if pagina == "Montar Time":
    # ========================================================
    # PÁGINA 1: MONTAR TIME (Seu código original)
    # ========================================================
    st.title("⚽ PES 2021 Fantasy")

    # =====================
    # Filtros
    # =====================
    col1, col2 = st.columns(2)

    with col1:
        posicoes = st.multiselect("📍 Filtrar por posição", options=df["Posição"].unique())
        ranks = st.multiselect("⭐ Filtrar por rank", options=df["Rank"].unique())

    with col2:
        preco_min, preco_max = st.slider(
            "💰 Faixa de preço",
            min_value=int(df["Preço"].min()),
            max_value=int(df["Preço"].max()),
            value=(int(df["Preço"].min()), int(df["Preço"].max())+1)
        )
        nome_input = st.text_input("🔎 Buscar por nome (separar múltiplos por vírgula)")

    df_filtrado = df.copy()
    if posicoes:
        df_filtrado = df_filtrado[df_filtrado["Posição"].isin(posicoes)]
    if ranks:
        df_filtrado = df_filtrado[df_filtrado["Rank"].isin(ranks)]
    if nome_input:
        nomes = [n.strip() for n in nome_input.split(",")]
        nomes_normalizados = [normalize_text(n) for n in nomes if n.strip()]
        mask = df_filtrado["Jogador"].apply(
            lambda x: any(nome in normalize_text(x) for nome in nomes_normalizados)
        )
        df_filtrado = df_filtrado[mask]

    df_filtrado = df_filtrado[(df_filtrado["Preço"] >= preco_min) & (df_filtrado["Preço"] <= preco_max)]


    ordem_inicial = ["Jogador", "Preço", "Posição", "Overall", "Rank"]
    resto = [c for c in df_filtrado.columns if c not in ordem_inicial]

    df_filtrado = df_filtrado[ordem_inicial + resto]

    st.subheader("📋 Jogadores disponíveis")

    # Função para aplicar cor às colunas
    def color_cols(col):
        if col.name in cores_colunas:
            return [f'background-color: {cores_colunas[col.name]}' for _ in col]
        else:
            return ['']*len(col)

    # Aplica o estilo
    styled_df = df_filtrado.style.apply(color_cols)
    styled_df = styled_df.format({
        'Preço': '{:.2f}'
    })

    st.dataframe(styled_df, use_container_width=True, height=600)

    # =====================
    # Seleção de time
    # =====================
    formacao = st.radio("📐 Escolha a formação:", ["4-3-3", "4-4-2"])

    # Pergunta pelo orçamento individual
    budget = st.number_input("💵 Qual o orçamento do seu time?", min_value=0.0, value=200.0, step=10.0)

    titulares = st.multiselect(
        "Selecione 11 jogadores (titulares)",
        options=df["Jogador"].tolist(),
        max_selections=11
    )

    reservas = st.multiselect(
        "Selecione 12 jogadores (reservas)",
        options=df["Jogador"].tolist()
    )

    # =====================
    # Mostrar custo do time + métricas
    # =====================
    df_time = df[df["Jogador"].isin(titulares + reservas)]

    if not df_time.empty:
        custo_titulares = df[df["Jogador"].isin(titulares)]["Preço"].sum()
        custo_reservas = df[df["Jogador"].isin(reservas)]["Preço"].sum()
        custo_total = custo_titulares + custo_reservas
        saldo = budget - custo_total
        overall_medio = df[df["Jogador"].isin(titulares)]["Overall"].mean() if titulares else 0
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='big-number-card'>💵 Total gasto: {custo_total:.1f} moedas</div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='big-number-card'>💸 Restante: {saldo:.1f}</div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='big-number-card'>🏆 Overall do time: {overall_medio:.1f}</div>", unsafe_allow_html=True)

        if custo_total > budget:
            st.error(f"🚨 Custo total ultrapassou o limite de {budget} moedas!")

    # =====================
    # Download do time completo
    # =====================
    if not df_time.empty:
        csv = df_time.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Baixar time completo (titulares + reservas)", data=csv, file_name="time_completo.csv", mime="text/csv")

    # =====================
    # Visualização em campo + reservas
    # =====================
    if len(titulares) == 11 and len(reservas) <= 12 and df_time["Preço"].sum() <= budget:
        st.subheader("📊 Time em campo")
        col_field, col_bench = st.columns([2, 1])

        # --- Campo HTML/CSS ---
        with col_field:
            cores = {
                "GK": "#FFA500", "CB": "#1E90FF", "LB": "#1E90FF", "RB": "#1E90FF",
                "CM": "#32CD32", "LM": "#32CD32", "RM": "#32CD32",
                "LW": "#DC143C", "RW": "#DC143C", "ST": "#DC143C"
            }

            if formacao == "4-3-3":
                posicoes_formacao = [
                    ("GK", 90, 50), ("LB", 70, 15), ("CB", 70, 40), ("CB", 70, 60), ("RB", 70, 85),
                    ("CM", 50, 25), ("CM", 50, 50), ("CM", 50, 75),
                    ("LW", 25, 20), ("ST", 20, 50), ("RW", 25, 80)
                ]
            else:
                posicoes_formacao = [
                    ("GK", 90, 50), ("LB", 70, 15), ("CB", 70, 40), ("CB", 70, 60), ("RB", 70, 85),
                    ("LM", 35, 20), ("CM", 50, 40), ("CM", 50, 60), ("RM", 35, 80),
                    ("ST", 15, 35), ("ST", 15, 65)
                ]

            html_campo = '<div class="campo">'
            for i, (pos, top, left) in enumerate(posicoes_formacao):
                if i < len(titulares):
                    jogador = titulares[i]
                    overall = df.loc[df["Jogador"] == jogador, "Overall"].values[0]
                    cor = cores.get(pos, "#32CD32")
                    jogador_text = f"{jogador}\n{int(overall)}"
                    html_campo += f'<div class="jogador" style="top:{top}%; left:{left}%; background:{cor}; transform:translate(-50%, -50%);">{jogador_text}</div>'
            html_campo += "</div>"

            st.markdown(html_campo, unsafe_allow_html=True)

        # --- Reservas ---
        with col_bench:
            st.markdown("### 🪑 Reservas")
            if reservas:
                df_reservas = df[df["Jogador"].isin(reservas)][["Jogador","Posição","Preço","Overall"]]
                st.dataframe(df_reservas, use_container_width=True)
                st.write(f"💰 **Custo dos reservas:** {custo_reservas:.1f} moedas")
            else:
                st.info("Nenhum reserva selecionado.")
    else:
        st.warning("⚠️ Selecione exatamente 11 titulares, e no mínimo 12 reservas e respeite o limite do seu orçamento.")


elif pagina == "Comparar Jogadores":
    # ========================================================
    # PÁGINA 2: COMPARAÇÃO DE JOGADORES
    # ========================================================
    st.title("⚖️ Comparação de Jogadores")

    # Dropdowns lado a lado para escolher os jogadores
    col1, col2 = st.columns(2)
    with col1:
        jogador1 = st.selectbox("Selecione o Jogador 1", options=df["Jogador"].unique())
    with col2:
        jogador2 = st.selectbox("Selecione o Jogador 2", options=df["Jogador"].unique())

    if jogador1 and jogador2:
        # Extraindo os dados dos dois jogadores
        d1 = df[df["Jogador"] == jogador1].iloc[0]
        d2 = df[df["Jogador"] == jogador2].iloc[0]

        # --- GRÁFICO DE RADAR ---
        st.subheader("Comparação dos stats")
        
        categorias = ['Attacking', 'Passing', 'Dribbling', 'Physical', 'Defending']
        
        # Calculando a média dos macro-atributos
        stats_p1 = [
            d1[['Off. Awareness', 'Finishing', 'Kicking Power']].mean(),
            d1[['Low Pass', 'Lofted Pass', 'Place Kicking', 'Curl']].mean(),
            d1[['Ball Control', 'Dribbling', 'Tight Possession', 'Balance']].mean(),
            d1[['Speed', 'Acceleration', 'Physical Contact', 'Stamina']].mean(),
            d1[['Heading', 'Jump', 'Defensive Awarenes', 'Ball Winning', 'Aggression']].mean()
        ]
        
        stats_p2 = [
            d2[['Off. Awareness', 'Finishing', 'Kicking Power']].mean(),
            d2[['Low Pass', 'Lofted Pass', 'Place Kicking', 'Curl']].mean(),
            d2[['Ball Control', 'Dribbling', 'Tight Possession', 'Balance']].mean(),
            d2[['Speed', 'Acceleration', 'Physical Contact', 'Stamina']].mean(),
            d2[['Heading', 'Jump', 'Defensive Awarenes', 'Ball Winning', 'Aggression']].mean()
        ]

        # Desenhando o gráfico com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=stats_p1, theta=categorias, fill='toself', name=jogador1, line_color='#1e90ff'))
        fig.add_trace(go.Scatterpolar(r=stats_p2, theta=categorias, fill='toself', name=jogador2, line_color='#ff00aa'))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            paper_bgcolor='rgba(0,0,0,0)',  
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            margin=dict(l=20, r=20, t=60, b=20)
        )
        col_esq, col_centro, col_dir = st.columns([2, 4, 2])
        with col_centro:
            st.plotly_chart(fig, use_container_width=True)

        # --- TABELA DE COMPARAÇÃO ---
        st.subheader("📊 Stats Detalhadas")
        
        # Usando as chaves do seu dicionário 'cores_colunas' para puxar todas as stats
        colunas_stats = list(cores_colunas.keys())
        
        # Adicionando Overall, Preço e Posição no topo, caso não estejam
        if 'Overall' not in colunas_stats: colunas_stats.insert(0, 'Overall')
        if 'Preço' not in colunas_stats: colunas_stats.insert(1, 'Preço')
        if 'Posição' not in colunas_stats: colunas_stats.insert(2, 'Posição')

        # Criando o DataFrame base da tabela
        df_comp = pd.DataFrame({
            "Atributo": colunas_stats,
            jogador1: [d1[col] for col in colunas_stats],
            jogador2: [d2[col] for col in colunas_stats]
        })

        # Função para calcular quem venceu na stat e pintar a seta
        def comparar_stats(row):
            v1, v2 = row[jogador1], row[jogador2]
            
            # Se for texto (ex: Posição), não tem como calcular diferença matemática
            if isinstance(v1, str) or isinstance(v2, str):
                return "➖ Sem comparação"
                
            try:
                diff = float(v1) - float(v2)
                if diff > 0:
                    return f"🟢 {jogador1} +{int(round(diff))} ⬆"
                elif diff < 0:
                    return f"🟢 {jogador2} +{int(round(abs(diff)))} ⬆"
                else:
                    return "⬛ Empate ↔"
            except:
                return "N/A"

        # Aplicando a lógica da terceira coluna
        df_comp["Vantagem"] = df_comp.apply(comparar_stats, axis=1)

        # Exibindo no Streamlit (hide_index esconde os números laterais da tabela)
        st.dataframe(df_comp, use_container_width=True, hide_index=True)