import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime
from autenticacao import login

st.set_page_config(
    page_title="Dashboard Comercial",
    page_icon="📊",
    layout="wide"
)

if not login():
    st.stop()
    
st.title("📊 Faturamento por Mesa")

aba_resumo, aba_grafico, aba_analise = st.tabs([
    "📋 Resumo",
    "📈 Ranking Vendedores",
    "📊 Análise Comercial"
])


#CAMINHO = r"C:\Users\layza\OneDrive\Documentos\Desenvolvimento\Python\app VBC mesa\Base de Faturamento Clave.xlsx"
CAMINHO = "Base de Faturamento Clave.xlsx"
ABA = 0

@st.cache_data
def carregar():

    df = pd.read_excel(CAMINHO, sheet_name=ABA)

    df.columns = df.columns.str.strip()

    # Agora utiliza DATA VISITA
    df["DATA VISITA"] = pd.to_datetime(
        df["DATA VISITA"],
        dayfirst=True,
        errors="coerce"
    )

    df["VALOR"] = pd.to_numeric(
        df["VALOR"],
        errors="coerce"
    ).fillna(0)

    return df


df = carregar()

st.sidebar.header("Filtros")

data_inicial = st.sidebar.date_input(
    "Data Inicial",
    value=df["DATA VISITA"].min().date(),
    format="DD/MM/YYYY"
)

data_final = st.sidebar.date_input(
    "Data Final",
    value=df["DATA VISITA"].max().date(),
    format="DD/MM/YYYY"
)

mesas = sorted(df["Mesa"].dropna().unique())

mesa = st.sidebar.selectbox(
    "Mesa",
    ["Todas"] + mesas
)

linhas = sorted(df["Linha"].dropna().unique())

linha = st.sidebar.selectbox(
    "Linha",
    ["Todas"] + linhas
)

df = df[
    (df["DATA VISITA"] >= pd.to_datetime(data_inicial))
    &
    (df["DATA VISITA"] <= pd.to_datetime(data_final))
]

if mesa != "Todas":
    df = df[df["Mesa"] == mesa]



hoje = datetime.today()

dias_mes = calendar.monthrange(
    hoje.year,
    hoje.month
)[1]

dia_atual = hoje.day

dias_restantes = max(dias_mes - dia_atual, 1)

tabela = (
    df
    .groupby(["Mesa", "VENDEDOR"], as_index=False)
    .agg(
        Acumulado=("VALOR", "sum")
    )
)

# tabela["Tendência"] = (
#     tabela["Acumulado"] / dia_atual
# ) * dias_mes

# tabela["Obj. Dia"] = (
#     (tabela["Tendência"] - tabela["Acumulado"])
#     / dias_restantes
# )

tabela = tabela.sort_values(
    ["Mesa", "Acumulado"],
    ascending=[True, False]
)

with aba_resumo:

    total_faturamento = tabela["Acumulado"].sum()
    qtd_vendedores = tabela["VENDEDOR"].nunique()

    if not tabela.empty:
        top_vendedor = tabela.loc[tabela["Acumulado"].idxmax()]
        codigo_top = int(top_vendedor["VENDEDOR"])
        valor_top = top_vendedor["Acumulado"]
    else:
        codigo_top = "-"
        valor_top = 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💰 Faturamento",
        f"R$ {total_faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    col2.metric(
        "👥 Vendedores",
        qtd_vendedores
    )

    col3.metric(
        f"🏆 Melhor Vendedor ({codigo_top})",
        f"R$ {valor_top:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    st.divider()

    tabela_exibir = tabela.copy()

    def moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")

    tabela_exibir["Acumulado"] = tabela_exibir["Acumulado"].apply(moeda)

    st.dataframe(
        tabela_exibir,
        use_container_width=True,
        hide_index=True
    )
 
with aba_grafico:

    st.subheader("📈 Faturamento por Vendedor")

    grafico = (
        tabela
        .sort_values("Acumulado", ascending=False)
        .copy()
    )

    # Formatação brasileira para os rótulos
    grafico["Rótulo"] = grafico["Acumulado"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    fig = px.bar(
        grafico,
        x="VENDEDOR",
        y="Acumulado",
        color="Mesa",
        text="Rótulo",
        title="Ranking de Faturamento por Vendedor",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        height=650,
        xaxis_title="Código do Vendedor",
        yaxis_title="Faturamento (R$)",
        xaxis=dict(type="category"),

        # Formatação brasileira do eixo Y
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True
        ),

        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=14),
        title_x=0.5
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with aba_analise:

    st.header("📊 Análise Comercial")
    total_clientes = df["CLIENTE"].nunique()

    ranking_clientes = (
        df
        .groupby(["CLIENTE", "RAZÃO"], as_index=False)
        .agg(
            Valor=("VALOR", "sum")
        )
        .sort_values("Valor", ascending=False)
    )

    maior_cliente = ranking_clientes.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💰 Faturamento",
        f"R$ {df['VALOR'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    col2.metric(
        "👥 Clientes",
        total_clientes
    )

    col3.metric(
        "🏆 Maior Cliente",
        str(maior_cliente["CLIENTE"]),
        delta=f"R$ {maior_cliente['Valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    st.divider()

    st.subheader("🥇 Top 20 Clientes")

    top20 = ranking_clientes.head(20).copy()

    top20["Cliente"] = (
        top20["CLIENTE"].astype(str)
        + " - "
        + top20["RAZÃO"]
    )

    top20["Rótulo"] = top20["Valor"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    fig_clientes = px.bar(

        top20,

        x="Valor",

        y="Cliente",

        orientation="h",

        text="Rótulo",

        color="Valor",

        color_continuous_scale="Blues"

    )

    fig_clientes.update_traces(

        textposition="outside"

    )

    fig_clientes.update_layout(

        yaxis_title="",

        xaxis_title="Valor",

        height=700,

        yaxis=dict(autorange="reversed"),

        coloraxis_showscale=False

    )

    st.plotly_chart(

        fig_clientes,

        use_container_width=True

    )