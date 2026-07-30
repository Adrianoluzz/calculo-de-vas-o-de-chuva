import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Dimensionamento de Drenagem Pluvial",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ Calculadora de Drenagem: Sarjeta, Bocas de Lobo e Manilhas")
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
    step=0.05,
    help="Asfalto/Concreto: 0.85"
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

capacidade_boca_lobo_ls = st.sidebar.number_input(
    "Capacidade Média por Boca de Lobo (L/s):", 
    min_value=5.0, 
    value=25.0, 
    step=5.0
)

# --- CAIXA DE SELEÇÃO FIXA DE MANILHA ---
st.sidebar.header("🚰 3. Escolha da Manilha")

opcoes_manilha_mm = [300, 500, 600, 800, 1000]

dn_selecionado_mm = st.sidebar.selectbox(
    "Selecione o Diâmetro Nominal da Manilha:",
    options=opcoes_manilha_mm,
    index=0,  # Padrão: 300 mm
    format_func=lambda x: f"DN {x} mm"
)

material_tubo = st.sidebar.selectbox(
    "Material do Tubo:",
    options=["Concreto (n = 0.013)", "PVC / PEAD (n = 0.010)"],
    index=0
)

# Define o coeficiente de Manning do tubo escolhido
n_manilha = 0.013 if "Concreto" in material_tubo else 0.010

limite_folga_pct = st.sidebar.slider(
    "Alerta de Enchimento do Tubo (%):",
    min_value=50,
    max_value=100,
    value=85,
    step=5,
    help="Define a porcentagem máxima tolerada de ocupação do tubo antes de emitir alerta."
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
c4.metric("Manilha Selecionada", f"DN {dn_selecionado_mm} mm")

st.markdown("---")

# --- SEÇÃO DE ANÁLISE PARA A MANILHA ESCOLHIDA ---
st.subheader(f"📊 Avaliação do Desempenho para Manilha de DN {dn_selecionado_mm} mm")

inclinacoes_pct = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0]

# Variáveis Geométricas da Sarjeta (Izard)
y_m = altura_guia_cm / 100.0
Z = 1.0 / (decliv_transversal_pct / 100.0)

# Propriedades do Tubo Selecionado
D_m = dn_selecionado_mm / 1000.0  # Converte mm para m
A_tubo = (np.pi * (D_m**2)) / 4.0
Rh_tubo = D_m / 4.0

dados_tabela = []

for inc in inclinacoes_pct:
    S = inc / 100.0  # Declividade em m/m
    
    # 1. CAPACIDADE DA SARJETA (L/s)
    Q_sarjeta_ls = (375.0 / n_sarjeta) * Z * (y_m**(8.0/3.0)) * np.sqrt(S)
    
    # 2. ESPAÇAMENTO E BOCAS DE LOBO
    if vazao_litros_segundo > Q_sarjeta_ls:
        vazao_por_metro = vazao_litros_segundo / comprimento_rua_m
        espacamento_m = Q_sarjeta_ls / vazao_por_metro if vazao_por_metro > 0 else comprimento_rua_m
        qtd_bocas = int(np.ceil(vazao_litros_segundo / capacidade_boca_lobo_ls))
    else:
        espacamento_m = comprimento_rua_m
        qtd_bocas = 1

    # 3. CÁLCULO DA MANILHA ESCOLHIDA (Manning)
    # Vazão máxima teórica da manilha a seção cheia
    Q_cap_max_m3s = (1.0 / n_manilha) * A_tubo * (Rh_tubo**(2/3)) * np.sqrt(S)
    Q_cap_max_lh = Q_cap_max_m3s * 1000.0 * 3600.0
    
    # Percentual de Ocupação da Manilha com a água da chuva
    ocupacao_pct = (vazao_m3_s / Q_cap_max_m3s) * 100.0
    v_escoamento = vazao_m3_s / A_tubo
    
    # Status da manilha
    if ocupacao_pct <= limite_folga_pct:
        status_manilha = f"✅ Atende ({ocupacao_pct:.1f}% cheio)"
    elif ocupacao_pct <= 100.0:
        status_manilha = f"⚠️ Atenção ({ocupacao_pct:.1f}% cheio)"
    else:
        status_manilha = f"❌ Sobrecarga ({ocupacao_pct:.1f}% - Sobrecarregado)"

    dados_tabela.append({
        "Inclinação (%)": f"{inc:.1f}%",
        "Capac. Sarjeta (L/s)": f"{Q_sarjeta_ls:.1f}",
        "Espaçamento Bocas (m)": f"{min(espacamento_m, comprimento_rua_m):.1f} m",
        "Qtd. Bocas": f"{qtd_bocas} un",
        f"Capacidade Máx. DN{dn_selecionado_mm} (L/h)": f"{Q_cap_max_lh:,.0f}".replace(",", "."),
        "Ocupação do Tubo (%)": f"{ocupacao_pct:.1f}%",
        "Velocidade (m/s)": f"{v_escoamento:.2f}",
        "Avaliação do Tubo": status_manilha
    })

df_resultado = pd.DataFrame(dados_tabela)
st.dataframe(df_resultado, use_container_width=True)

# --- RECOMENDAÇÕES PRÁTICAS ---
with st.expander("📌 Orientações de Leitura do Resultado"):
    st.markdown(f"""
    * **Manilha Testada:** **DN {dn_selecionado_mm} mm** em material **{material_tubo}**.
    * **Status ✅ Atende:** O volume de água preenche menos do que **{limite_folga_pct}%** do diâmetro do tubo, estando seguro contra refluxos.
    * **Status ⚠️ Atenção:** O tubo comporta a água, porém trabalha muito cheio (acima de {limite_folga_pct}% da seção).
    * **Status ❌ Sobrecarga:** A vazão gerada pela chuva é superior à capacidade física do diâmetro **DN {dn_selecionado_mm} mm** para aquela declividade. Escolha um diâmetro maior na caixa lateral.
    """)
