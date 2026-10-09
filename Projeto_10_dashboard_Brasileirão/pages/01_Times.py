import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard de Clubes",
    page_icon="⚽",
    layout="wide"
)

# ------------------------------
# CARREGAMENTO E TRATAMENTO DOS DADOS
# ------------------------------
@st.cache_data
def carregar_dados():
    dados = pd.read_csv("Tabela_Clubes.csv")

    # Remove a coluna de índice que veio salva no CSV, se existir.
    dados = dados.loc[:, ~dados.columns.str.startswith("Unnamed")]

    # Converte números que possam estar escritos com vírgula decimal.
    dados["Idade_Media"] = pd.to_numeric(
        dados["Idade_Media"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )
    dados["Valor_total"] = pd.to_numeric(dados["Valor_total"], errors="coerce")
    dados["Media_Valor"] = pd.to_numeric(dados["Media_Valor"], errors="coerce")

    # Divide a coluna de gols, por exemplo "30:47", em duas colunas numéricas.
    gols = dados["GolsF/S"].astype(str).str.split(":", expand=True)
    dados["Gols_Feitos"] = pd.to_numeric(gols[0], errors="coerce")
    dados["Gols_Sofridos"] = pd.to_numeric(gols[1], errors="coerce")

    return dados

try:
    df_original = carregar_dados()
except FileNotFoundError:
    st.error("Não encontrei o arquivo Tabela_Clubes.csv. Coloque-o na mesma pasta de Geral_corrigido.py.")
    st.stop()

# ------------------------------
# SIDEBAR: FILTROS
# ------------------------------
st.sidebar.title("Filtros")
anos = sorted(df_original["Ano"].dropna().unique().tolist())
anos_selecionados = st.sidebar.multiselect(
    "Ano / temporada",
    options=anos,
    default=anos
)

clubes_disponiveis = sorted(df_original["Clubes"].dropna().unique().tolist())
clubes_selecionados = st.sidebar.multiselect(
    "Clubes",
    options=clubes_disponiveis,
    default=clubes_disponiveis
)

# Filtra os dados de acordo com as seleções.
df = df_original[
    df_original["Ano"].isin(anos_selecionados)
    & df_original["Clubes"].isin(clubes_selecionados)
].copy()

st.title("⚽ Dashboard de Clubes")
st.caption("Visão geral de desempenho, elenco e valor de mercado dos clubes (dados do arquivo CSV).")

if df.empty:
    st.warning("Nenhum registro corresponde aos filtros selecionados. Escolha outro ano ou clube.")
    st.stop()

# ------------------------------
# INDICADORES PRINCIPAIS
# ------------------------------
col1, col2, col3, col4 = st.columns(4)

quantidade_clubes = df["Clubes"].nunique()
quantidade_estrangeiros = int(df["Estrangeiros"].fillna(0).sum())
idade_media = df["Idade_Media"].mean()
valor_medio = df["Valor_total"].mean()

col1.metric("Clubes selecionados", f"{quantidade_clubes}")
col2.metric("Quantidade de estrangeiros", f"{quantidade_estrangeiros:,}".replace(",", "."))
col3.metric("Idade média dos jogadores", f"{idade_media:.1f}" if pd.notna(idade_media) else "N/D")
col4.metric("Valor médio dos times", f"R$ {valor_medio:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(valor_medio) else "N/D")

st.divider()

# ------------------------------
# GRÁFICOS
# ------------------------------
col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("Gols marcados e sofridos")
    gols_clubes = df.groupby("Clubes", as_index=False)[["Gols_Feitos", "Gols_Sofridos"]].sum()
    gols_longos = gols_clubes.melt(
        id_vars="Clubes",
        value_vars=["Gols_Feitos", "Gols_Sofridos"],
        var_name="Tipo de gol",
        value_name="Quantidade"
    )
    gols_longos["Tipo de gol"] = gols_longos["Tipo de gol"].replace({
        "Gols_Feitos": "Gols marcados",
        "Gols_Sofridos": "Gols sofridos"
    })
    fig_gols = px.bar(
        gols_longos,
        x="Clubes",
        y="Quantidade",
        color="Tipo de gol",
        barmode="group",
        labels={"Clubes": "Clube", "Quantidade": "Gols"}
    )
    fig_gols.update_layout(legend_title_text="")
    st.plotly_chart(fig_gols, use_container_width=True)

with col_dir:
    st.subheader("Valor total dos clubes ao longo dos anos")
    valor_ano = df.groupby(["Ano", "Clubes"], as_index=False)["Valor_total"].mean()
    fig_valor = px.line(
        valor_ano,
        x="Ano",
        y="Valor_total",
        color="Clubes",
        markers=True,
        labels={"Ano": "Ano", "Valor_total": "Valor total (R$)", "Clubes": "Clube"}
    )
    fig_valor.update_layout(legend_title_text="")
    st.plotly_chart(fig_valor, use_container_width=True)

col_esq2, col_dir2 = st.columns(2)

with col_esq2:
    st.subheader("Vitórias, empates e derrotas")
    resultados = df.groupby("Clubes", as_index=False)[["Vitorias", "Empates", "Derrotas"]].sum()
    resultados_longos = resultados.melt(
        id_vars="Clubes",
        value_vars=["Vitorias", "Empates", "Derrotas"],
        var_name="Resultado",
        value_name="Quantidade"
    )
    resultados_longos["Resultado"] = resultados_longos["Resultado"].replace({
        "Vitorias": "Vitórias", "Empates": "Empates", "Derrotas": "Derrotas"
    })
    fig_resultados = px.bar(
        resultados_longos,
        x="Clubes",
        y="Quantidade",
        color="Resultado",
        barmode="group",
        labels={"Clubes": "Clube", "Quantidade": "Jogos"}
    )
    fig_resultados.update_layout(legend_title_text="")
    st.plotly_chart(fig_resultados, use_container_width=True)

with col_dir2:
    st.subheader("Idade média x valor do elenco")
    fig_idade = px.scatter(
        df,
        x="Idade_Media",
        y="Valor_total",
        color="Clubes",
        size="Qtd_Jogadores",
        hover_data=["Ano", "Pos."],
        labels={
            "Idade_Media": "Idade média",
            "Valor_total": "Valor total (R$)",
            "Clubes": "Clube",
            "Qtd_Jogadores": "Quantidade de jogadores"
        }
    )
    st.plotly_chart(fig_idade, use_container_width=True)

# ------------------------------
# TABELA DE CLASSIFICAÇÃO
# ------------------------------
st.subheader("Classificação por ano")
colunas_tabela = [
    "Ano", "Pos.", "Clubes", "Vitorias", "Empates", "Derrotas",
    "GolsF/S", "Saldo", "Qtd_Jogadores", "Idade_Media", "Estrangeiros", "Valor_total"
]
colunas_tabela = [c for c in colunas_tabela if c in df.columns]
tabela = df[colunas_tabela].sort_values(["Ano", "Pos."])
st.dataframe(tabela, use_container_width=True, hide_index=True)

# ------------------------------
# PÓDIOS: TOP 5 EM CADA ANO SELECIONADO
# ------------------------------
st.subheader("Top 5 de cada ano")
podio = df[df["Pos."] <= 5][["Ano", "Pos.", "Clubes"]].sort_values(["Ano", "Pos."])
st.dataframe(podio, use_container_width=True, hide_index=True)

st.caption("Nota: os indicadores somam ou calculam médias dos registros selecionados. Confira o significado de cada coluna na fonte dos dados.")
