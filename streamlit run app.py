import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Dimensionamento de Drenagem Pluvial",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ Dimensionamento e Verificação de Drenagem Pluvial")
st.markdown("---")

# --- BARRA LATERAL: PARÂMETROS DE ENTRADA ---
st.sidebar.header("⚙️ 1. Dados da Rua e Chuva")

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

inclinacao_rua_pct = st.sidebar.number_input(
    "Inclinação Longitudinal da Rua (%):",
    min_value=0.1,
    max_value=20.0,
    value=2.0,
    step=0.1,
    help="Exemplo: 2.0% de caimento ao longo do comprimento da rua."
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

st.sidebar.header("📐 2. Geometria da Sarjeta e Meio-Fio")

altura_guia_cm = st.sidebar.number_input(
    "Altura Real do Meio-Fio / Guia (cm):", 
    min_value=5.0, 
    max_value=30.0, 
    value=15.0, 
    step=1.0,
    help="Altura física construída do meio-fio para contenção da água."
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

st.sidebar.header("🕳️ 3. Configuração das Bocas de Lobo")

qtd_bocas_projetadas = st.sidebar.number_input(
    "Quantidade de Bocas de Lobo Instaladas:",
    min_value=1,
    value=4,
    step=1
)

espacamento_bocas_m = st.sidebar.number_input(
    "Espaçamento Lido/Adotado entre Bocas (m):",
    min_value=5.0,
    value=50.0,
    step=5.0
)

capacidade_boca_lobo_ls = st.sidebar.number_input(
    "Capacidade Máxima por Boca de Lobo (L/s):", 
    min_value=5.0, 
    value=25.0, 
    step=5.0
)

st.sidebar.header("🚰 4. Escolha da Manilha")

opcoes_manilha_mm = [300, 500, 600, 800, 1000]

dn_selecionado_mm = st.sidebar.selectbox(
    "Diâmetro Nominal da Manilha:",
    options=opcoes_manilha_mm,
    index=0,
    format_func=lambda x: f"DN {x} mm"
)

material_tubo = st.sidebar.selectbox(
    "Material do Tubo:",
    options=["Concreto (n = 0.013)", "PVC / PEAD (n = 0.010)"],
    index=0
)

n_manilha = 0.013 if "Concreto" in material_tubo else 0.010

limite_folga_pct = st.sidebar.slider(
    "Alerta de Enchimento do Tubo (%):",
    min_value=50,
    max_value=100,
    value=85,
    step=5
)

# --- CÁLCULOS HIDROLÓGICOS DA CHUVA ---
volume_litros_hora = area_rua_m2 * intensidade_mm_h * coef_c
vazao_m3_s = volume_litros_hora / (1000.0 * 3600.0)
vazao_litros_segundo = volume_litros_hora / 3600.0

# --- CÁLCULOS HIDRÁULICOS ---
S_rua = inclinacao_rua_pct / 100.0  # Declividade m/m
y_limite_m = altura_guia_cm / 100.0
Z = 1.0 / (decliv_transversal_pct / 100.0)

# 1. CÁLCULO DA ALTURA REAL DA LÂMINA D'ÁGUA NA SARJETA (Fórmula de Izard Invertida)
# Considera a vazão que chega até a primeira boca de lobo com base no espaçamento adotado
vazao_por_metro = vazao_litros_segundo / comprimento_rua_m
vazao_trecho_sarjeta_ls = vazao_por_metro * espacamento_bocas_m

# Cálculo da altura da lâmina d'água (em m e cm)
if vazao_trecho_sarjeta_ls > 0 and S_rua > 0:
    y_calculado_m = ((vazao_trecho_sarjeta_ls * n_sarjeta) / (375.0 * Z * np.sqrt(S_rua)))**(3.0 / 8.0)
else:
    y_calculado_m = 0.0

altura_lamina_cm = y_calculado_m * 100.0
largura_espelho_agua_m = y_calculado_m * Z

# Capacidade máxima absoluta da sarjeta considerando a altura limite do meio-fio
Q_sarjeta_max_ls = (375.0 / n_sarjeta) * Z * (y_limite_m**(8.0/3.0)) * np.sqrt(S_rua)

# Distância limite que a água pode andar antes de estourar o meio-fio
espacamento_critico_m = Q_sarjeta_max_ls / vazao_por_metro if vazao_por_metro > 0 else comprimento_rua_m

# 2. BOCAS DE LOBO
capacidade_total_bocas_ls = qtd_bocas_projetadas * capacidade_boca_lobo_ls

# 3. MANILHA (Fórmula de Manning)
D_m = dn_selecionado_mm / 1000.0
A_tubo = (np.pi * (D_m**2)) / 4.0
Rh_tubo = D_m / 4.0

Q_cap_max_manilha_m3s = (1.0 / n_manilha) * A_tubo * (Rh_tubo**(2/3)) * np.sqrt(S_rua)
Q_cap_max_manilha_lh = Q_cap_max_manilha_m3s * 1000.0 * 3600.0

ocupacao_manilha_pct = (vazao_m3_s / Q_cap_max_manilha_m3s) * 100.0
v_escoamento_manilha = vazao_m3_s / A_tubo

# --- EXIBIÇÃO DE PAINEL DE MÉTRICAS PRINCIPAIS ---
st.subheader("📌 Resumo das Condições Digitadas")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Área da Rua", f"{area_rua_m2:,.0f} m²".replace(",", "."))
c2.metric("Inclinação da Via", f"{inclinacao_rua_pct:.1f}%")
c3.metric("Volume de Chuva", f"{volume_litros_hora:,.0f} L/h".replace(",", "."))
c4.metric("Altura Meio-Fio", f"{altura_guia_cm:.1f} cm")
c5.metric("Lâmina D'água Calculada", f"{altura_lamina_cm:.2f} cm")

st.markdown("---")

# --- QUADRO DE DIAGNÓSTICO DO SISTEMA DE DRENAGEM ---
st.subheader("🔍 Diagnóstico do Sistema de Drenagem")

col_left, col_mid, col_right = st.columns(3)

# 1. Diagnóstico do Meio-Fio e Sarjeta
with col_left:
    st.markdown("### 🛣️ Meio-Fio e Sarjeta")
    st.write(f"**Altura do Meio-Fio:** {altura_guia_cm:.1f} cm")
    st.write(f"**Lâmina D'água no Trecho:** {altura_lamina_cm:.2f} cm")
    st.write(f"**Largura na Pista:** {largura_espelho_agua_m:.2f} m")
    st.write(f"**Espaçamento Limite Seguro:** {min(espacamento_critico_m, comprimento_rua_m):.1f} m")
    
    if altura_lamina_cm <= altura_guia_cm:
        folga_cm = altura_guia_cm - altura_lamina_cm
        st.success(f"✅ **Meio-Fio Suporta:** A água atinge {altura_lamina_cm:.2f} cm, deixando uma folga de {folga_cm:.2f} cm no meio-fio.")
    else:
        excesso_cm = altura_lamina_cm - altura_guia_cm
        st.error(f"❌ **Transbordo no Meio-Fio:** A água subirá {altura_lamina_cm:.2f} cm, estourando o meio-fio em {excesso_cm:.2f} cm. Reduza o espaçamento entre bocas de lobo ou aumente o meio-fio.")

# 2. Diagnóstico das Bocas de Lobo
with col_mid:
    st.markdown("### 🕳️ Engolidoras (Bocas de Lobo)")
    st.write(f"**Qtd. Instalada:** {qtd_bocas_projetadas} un")
    st.write(f"**Capacidade Total de Engolimento:** {capacidade_total_bocas_ls:.1f} L/s")
    st.write(f"**Vazão Chegando da Chuva:** {vazao_litros_segundo:.1f} L/s")
    
    if capacidade_total_bocas_ls >= vazao_litros_segundo:
        st.success("✅ **Engolimento Aprovado:** As bocas de lobo captam toda a água da rua.")
    else:
        qtd_necessaria = int(np.ceil(vazao_litros_segundo / capacidade_boca_lobo_ls))
        st.error(f"❌ **Falta de Bocas de Lobo:** As engolidoras vão empoçar. Instale no mínimo {qtd_necessaria} unidades.")

# 3. Diagnóstico da Manilha
with col_right:
    st.markdown(f"### 🚰 Manilha (DN {dn_selecionado_mm} mm)")
    st.write(f"**Capacidade do Tubo:** {Q_cap_max_manilha_lh:,.0f} L/h".replace(",", "."))
    st.write(f"**Taxa de Ocupação:** {ocupacao_manilha_pct:.1f}% do diâmetro")
    st.write(f"**Velocidade na Manilha:** {v_escoamento_manilha:.2f} m/s")
    
    if ocupacao_manilha_pct <= limite_folga_pct:
        st.success(f"✅ **Manilha Aprovada:** Tubo trabalha dentro da folga de segurança ({ocupacao_manilha_pct:.1f}% cheio).")
    elif ocupacao_manilha_pct <= 100.0:
        st.warning(f"⚠️ **Manilha no Limite:** Tubo comporta a chuva ({ocupacao_manilha_pct:.1f}% cheio), mas supera a folga desejada.")
    else:
        st.error(f"❌ **Manilha Sobrecarregada:** {ocupacao_manilha_pct:.1f}% cheio. O tubo vai escoar sob pressão/refluxo. Escolha um diâmetro maior.")

st.markdown("---")

# --- TABELA DE RESUMO EXECUTIVO ---
st.subheader("📋 Tabela Consolidada do Projeto")

df_consolidado = pd.DataFrame([{
    "Inclinação Rua (%)": f"{inclinacao_rua_pct:.1f}%",
    "Comprimento Rua (m)": f"{comprimento_rua_m:.0f} m",
    "Volume Chuva (L/h)": f"{volume_litros_hora:,.0f}".replace(",", "."),
    "Altura Meio-Fio (cm)": f"{altura_guia_cm:.1f} cm",
    "Lâmina D'água (cm)": f"{altura_lamina_cm:.2f} cm",
    "Espaçamento Bocas (m)": f"{espacamento_bocas_m:.1f} m",
    "Qtd. Bocas de Lobo": f"{qtd_bocas_projetadas} un",
    "Manilha Selecionada": f"DN {dn_selecionado_mm} mm ({material_tubo.split()[0]})",
    "Ocupação Manilha (%)": f"{ocupacao_manilha_pct:.1f}%",
    "Velocidade Fluxo (m/s)": f"{v_escoamento_manilha:.2f} m/s"
}])

st.dataframe(df_consolidado, use_container_width=True)
