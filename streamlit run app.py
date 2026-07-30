import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Dimensionamento de Drenagem Pluvial",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ Dimensionamento Integrado: Sarjeta, Bocas de Lobo e Manilhas")
st.markdown("---")

# --- BANCO DE DADOS DE MATERIAIS DE MANILHA (COM DIÂMETROS CUSTOMIZADOS) ---
MATERIAIS_MANILHA = {
    "Manilha Padrão do Projeto (300mm a 1000mm)": {
        "n": 0.013,
        "diametros_mm": [300, 500, 600, 800, 1000]
    },
    "Concreto Armado (Linha Completa)": {
        "n": 0.013,
        "diametros_mm": [300, 400, 500, 600, 800, 1000, 1200, 1500]
    },
    "PVC / PEAD Corrugado": {
        "n": 0.010,
        "diametros_mm": [300, 500, 600, 800, 1000]
    }
}

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

st.sidebar.header("🚰 3. Especificação das Manilhas")

material_selecionado = st.sidebar.selectbox(
    "Opção de Manilhas:",
    options=list(MATERIAIS_MANILHA.keys()),
    index=0
)

# Permitir ao usuário personalizar os diâmetros diretamente na interface se quiser
usar_custom = st.sidebar.checkbox("Personalizar diâmetros manualmente", value=False)

if usar_custom:
    diametros_comerciais_mm = st.sidebar.multiselect(
        "Selecione os Diâmetros Permitidos (mm):",
        options=[200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1500],
        default=[300, 500, 600, 800, 1000]
    )
    diametros_comerciais_mm.sort()
else:
    diametros_comerciais_mm = MATERIAIS_MANILHA[material_selecionado]["diametros_mm"]

folga_seguranca = st.sidebar.slider(
    "Limite do Nível de Enchimento do Tubo (%):",
    min_value=50,
    max_value=100,
    value=85,
    step=5,
    help="Determina o percentual máximo da área da manilha que pode ser ocupado pela água."
)

n_manilha = MATERIAIS_MANILHA[material_selecionado]["n"]

st.sidebar.info(
    f"ℹ️ **Rugosidade Utilizada:** Manning n = **{n_manilha}**\n\n"
    f"**Diâmetros Avaliados:** {', '.join([f'DN{d}' for d in diametros_comerciais_mm])} mm"
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

# --- SEÇÃO DE ANÁLISE INTEGRADA ---
st.subheader("📊 Tabela de Dimensionamento (Foco nas Manilhas de 300mm a 1000mm)")

inclinacoes_pct = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0]

# Conversões da Sarjeta (Fórmula de Izard)
y_m = altura_guia_cm / 100.0
Z = 1.0 / (decliv_transversal_pct / 100.0)

dados_tabela = []
fator_folga = folga_seguranca / 100.0

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

    # 3. SELEÇÃO DA MANILHA DENTRE AS OPÇÕES DA LISTA
    dn_recomendado = f"DN > {max(diametros_comerciais_mm) if diametros_comerciais_mm else 0} mm (Requer Galeria/Aumento)"
    v_escoamento = 0.0
    ocupacao_pct = 0.0
    
    for d_mm in diametros_comerciais_mm:
        D = d_mm / 1000.0  # Converte mm para m
        A_tubo = (np.pi * (D**2)) / 4.0
        Rh_tubo = D / 4.0
        
        # Fórmula de Manning (Vazão máxima com tubo cheio)
        Q_cap_max = (1.0 / n_manilha) * A_tubo * (Rh_tubo**(2/3)) * np.sqrt(S)
        
        # Aplica o limite de segurança
        if (Q_cap_max * fator_folga) >= vazao_m3_s:
            dn_recomendado = f"DN {d_mm} mm"
            v_escoamento = vazao_m3_s / A_tubo
            ocupacao_pct = (vazao_m3_s / Q_cap_max) * 100.0
            break

    dados_tabela.append({
        "Inclinação (%)": f"{inc:.1f}%",
        "Capac. Sarjeta (L/s)": f"{Q_sarjeta_ls:.1f}",
        "Espaçamento Bocas (m)": f"{min(espacamento_m, comprimento_rua_m):.1f} m",
        "Qtd. Bocas": f"{qtd_bocas} un",
        "Manilha Mínima": dn_recomendado,
        "Ocupação do Tubo (%)": f"{ocupacao_pct:.1f}%" if ocupacao_pct > 0 else "N/A",
        "Veloc. Tubo (m/s)": f"{v_escoamento:.2f}" if v_escoamento > 0 else "N/A"
    })

df_resultado = pd.DataFrame(dados_tabela)
st.dataframe(df_resultado, use_container_width=True)

# --- RECOMENDAÇÕES PRÁTICAS ---
with st.expander("📌 Regras de Seleção das Manilhas"):
    st.markdown("""
    * **Lista de Diâmetros Padrão:** As bitolas testadas são **300 mm, 500 mm, 600 mm, 800 mm e 1000 mm**.
    * **Ocupação (%)**: Mostra a porcentagem de água dentro do tubo. O ideal é que fique **abaixo do limite selecionado** (padrão de 85%) para deixar espaço de ar livre dentro do tubo.
    * **Personalização:** Ative a caixa *"Personalizar diâmetros manualmente"* na barra lateral caso queira incluir ou remover algum tamanho específico de tubo da lista de verificação.
    """)
