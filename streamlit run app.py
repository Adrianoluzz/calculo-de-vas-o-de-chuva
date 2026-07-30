import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Dimensionamento Completo de Drenagem Pluvial",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ Dimensionamento: Sarjeta, Bocas de Lobo e Manilha")
st.markdown("---")

# --- BARRA LATERAL: PARÂMETROS DE ENTRADA ---
st.sidebar.header("⚙️ 1. Geometria da Rua e Chuva")

comprimento_rua_m = st.sidebar.number_input(
    "Comprimento Total da Rua (m):", 
    min_value=10.0, 
    value=200.0, 
    step=10.0
)

largura_rua_m = st.sidebar.number_input(
    "Largura da Rua (m):", 
    min_value=3.0, 
    value=10.0, 
    step=0.5
)

area_rua_m2 = comprimento_rua_m * largura_rua_m
st.sidebar.caption(f"📐 Área calculada da rua: **{area_rua_m2:,.0f} m²**".replace(",", "."))

coef_c = st.sidebar.slider(
    "Coeficiente de Runoff (C):", 
    min_value=0.10, 
    max_value=0.95, 
    value=0.85, 
    step=0.05
)

intensidade_mm_h = st.sidebar.number_input(
    "Intensidade da Chuva (mm/h):", 
    min_value=1.0, 
    value=80.0, 
    step=5.0
)

st.sidebar.header("📐 2. Sarjeta e Meio-Fio")

altura_guia_cm = st.sidebar.number_input(
    "Altura do Meio-Fio / Lâmina Máx. (cm):", 
    min_value=5.0, 
    max_value=25.0, 
    value=15.0, 
    step=1.0
)

decliv_transversal_pct = st.sidebar.slider(
    "Declividade Transversal (%):", 
    min_value=1.0, 
    max_value=10.0, 
    value=2.0, 
    step=0.5
)

n_sarjeta = st.sidebar.number_input(
    "Rugosidade da Sarjeta (n):", 
    min_value=0.010, 
    max_value=0.025, 
    value=0.015, 
    step=0.001
)

st.sidebar.header("🕳️ 3. Boca de Lobo")

capacidade_boca_lobo_ls = st.sidebar.number_input(
    "Capacidade Média da Boca de Lobo (L/s):", 
    min_value=5.0, 
    value=25.0, 
    step=5.0,
    help="Uma boca de lobo de grelha padrão capta tipicamente de 20 a 30 L/s."
)

# --- CÁLCULOS HIDROLÓGICOS GERAIS ---
volume_litros_hora = area_rua_m2 * intensidade_mm_h * coef_c
vazao_m3_s = volume_litros_hora / (1000.0 * 3600.0)
vazao_litros_segundo = volume_litros_hora / 3600.0

# Exibição de Métricas Principais
c1, c2, c3, c4 = st.columns(4)
c1.metric("Comprimento da Via", f"{comprimento_rua_m:.0f} m")
c2.metric("Volume Gerado", f"{volume_litros_hora:,.0f} L/h".replace(",", "."))
c3.metric("Vazão Total da Rua", f"{vazao_litros_segundo:.2f} L/s")
c4.metric("Vazão em m³/s", f"{vazao_m3_s:.4f} m³/s")

st.markdown("---")

# --- SEÇÃO DE ANÁLISE COMPLETA ---
st.subheader("📊 Tabela de Dimensionamento Integrado por Inclinação")

inclinacoes_pct = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0]
diametros_comerciais = [0.30, 0.40, 0.50, 0.60, 0.80, 1.00, 1.20]
n_manilha = 0.013

# Conversões da Sarjeta (Izard)
y_m = altura_guia_cm / 100.0
Z = 1.0 / (decliv_transversal_pct / 100.0)
largura_espelho_agua = y_m * Z

dados_tabela = []

for inc in inclinacoes_pct:
    S = inc / 100.0  # Declividade em m/m
    
    # 1. CAPACIDADE MÁXIMA DA SARJETA (Fórmula de Izard em L/s)
    Q_sarjeta_ls = (375.0 / n_sarjeta) * Z * (y_m**(8.0/3.0)) * np.sqrt(S)
    
    # 2. CÁLCULO DE BOCAS DE LOBO E ESPAÇAMENTO
    # Se a vazão total da rua for maior que a capacidade da sarjeta:
    if vazao_litros_segundo > Q_sarjeta_ls:
        # Distância na qual a água atinge o topo da sarjeta
        vazao_por_metro = vazao_litros_segundo / comprimento_rua_m
        espacamento_m = Q_sarjeta_ls / vazao_por_metro if vazao_por_metro > 0 else comprimento_rua_m
        
        # Quantidade necessária de bocas de lobo
        qtd_bocas = int(np.ceil(vazao_litros_segundo / capacidade_boca_lobo_ls))
    else:
        espacamento_m = comprimento_rua_m
        qtd_bocas = 1  # Apenas 1 no ponto mais baixo ao final da rua

    # 3. MANILHA IDEAL (Manning a 85% da capacidade)
    dn_recomendado = "DN > 1200mm"
    v_escoamento = 0.0
    
    for D in diametros_comerciais:
        A_tubo = (np.pi * (D**2)) / 4.0
        Rh_tubo = D / 4.0
        Q_cap_max = (1.0 / n_manilha) * A_tubo * (Rh_tubo**(2/3)) * np.sqrt(S)
        
        if (Q_cap_max * 0.85) >= vazao_m3_s:
            dn_recomendado = f"DN {int(D*1000)} mm"
            v_escoamento = vazao_m3_s / A_tubo
            break

    dados_tabela.append({
        "Inclinação (%)": f"{inc:.1f}%",
        "Capac. Sarjeta (L/s)": f"{Q_sarjeta_ls:.1f}",
        "Espaçamento Máx. Entre Bocas (m)": f"{min(espacamento_m, comprimento_rua_m):.1f} m",
        "Qtd. Mínima de Bocas de Lobo": f"{qtd_bocas} un",
        "Veloc. Manilha (m/s)": f"{v_escoamento:.2f}" if v_escoamento > 0 else "N/A",
        "Manilha Mínima": dn_recomendado
    })

df_resultado = pd.DataFrame(dados_tabela)
st.dataframe(df_resultado, use_container_width=True)

# --- RECOMENDAÇÕES PRÁTICAS ---
with st.expander("📌 Como aplicar os resultados no projeto executivo"):
    st.markdown(f"""
    * **Espaçamento das Bocas de Lobo:** Indica a distância máxima que a água pode percorrer na sarjeta antes de estourar a altura limite do meio-fio ({altura_guia_cm} cm).
    * **Bocas de Lobo Intermediárias:** Se a quantidade de bocas for maior que 1, instale as engolidoras ao longo dos **{comprimento_rua_m:.0f} metros** respeitando o espaçamento indicado.
    * **Ponto Mais Baixo:** Garanta sempre a instalação de pelo menos um par de bocas de lobo no ponto mais baixo (*ponto de selha*) da via para evitar empoçamento terminal.
    """)
