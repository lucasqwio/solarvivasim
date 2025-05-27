import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="💰 Simulador de Custos", layout="wide")
st.title("💰 Simulador de Custos com Projeção")

# --- Aba de navegação ---
aba = st.sidebar.radio("Escolha a aba", ["📊 Entrada de Dados", "🧮 Cálculo de Custos", "📈 Resultados e Simulação"])

# --- Dados fixos do sistema ---
fretes = {
    ("1", "2"): 5.00,
    ("2", "1"): 5.00,
    ("1", "3"): 13.00,
    ("3", "1"): 13.00,
    ("2", "3"): 11.00,
    ("3", "2"): 11.00,
}

custos_pessoas = {
    "Operários": {"Salário/hora": 8.5},
}

# Parâmetros de custeio
custo_mp_unit = 10.0
armazenagem_mp_unit = 1.5
armazenagem_pa_unit = 2.4
mp_por_unidade = 3
mod_horas_por_unidade = 1.5
horas_por_operario = 480  # informado pelo usuário

# Módulos e depreciação
investimento_modulo = 17500
modulo_capacidade = 500
depreciacao_percentual = 2.5 / 100
admin_por_periodo = 52000

custos_producao = {
    (0, 5000): 52000,
    (5001, 10000): 89300,
    (10001, 15000): 114330,
    (15001, 20000): 135000,
    (20001, 25000): 153660,
    (25001, float('inf')): 168300
}

# --- Aba 1: Entrada de Dados ---
if aba == "📊 Entrada de Dados":
    st.header("📊 Edição da Demanda Base (usada para cálculo de média)")
    regioes = ["1", "2", "3"]
    trimestres_hist = ["Hist 1", "Hist 2", "Hist 3", "Hist 4"]

    dados_iniciais = {
        "Região": regioes,
        "Hist 1": [2959, 5763, 6853],
        "Hist 2": [3091, 8475, 10773],
        "Hist 3": [3077, 7921, 10288],
        "Hist 4": [3108, 5703, 7305],
    }

    df_input = pd.DataFrame(dados_iniciais)
    df_editado = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
    st.session_state["df_base_media"] = df_editado

# --- Aba 2: Cálculo de Custos ---
elif aba == "🧮 Cálculo de Custos":
    st.header("🧮 Projeção de Custos para 8 Períodos")

    if "df_base_media" in st.session_state:
        df_base = st.session_state["df_base_media"].copy().set_index("Região")
        media_por_regiao = df_base.mean(axis=1).round().astype(int)
        periodos = [f"T{i+1}" for i in range(8)]

        df_proj = pd.DataFrame({p: media_por_regiao for p in periodos})
        df_total = df_proj.copy()

        total_por_trimestre = df_total.sum(axis=0)
        demanda_maxima = total_por_trimestre.max()
        demanda_total = total_por_trimestre.sum()
        num_periodos = len(periodos)

        num_modulos = int(np.ceil(demanda_maxima / modulo_capacidade))
        investimento_total = num_modulos * investimento_modulo
        depre_total = investimento_total * depreciacao_percentual
        admin_total = admin_por_periodo * num_periodos

        custo_fixo_total = 0
        custo_var_total = 0
        custo_frete_total = 0

        for periodo in periodos:
            st.markdown(f"### 📅 Período {periodo}")
            demanda = df_total[periodo].sum()
            custo_fixo_producao = next(valor for (inicio, fim), valor in custos_producao.items() if inicio <= demanda <= fim)

            # Custo variável
            mp_total = demanda * mp_por_unidade
            mod_total_horas = demanda * mod_horas_por_unidade
            num_operarios = math.ceil(mod_total_horas / horas_por_operario)
            custo_mp = mp_total * custo_mp_unit
            custo_mod = mod_total_horas * custos_pessoas["Operários"]["Salário/hora"]
            custo_armazenagem_mp = mp_total * armazenagem_mp_unit
            custo_armazenagem_pa = demanda * armazenagem_pa_unit

            custo_var = custo_mp + custo_mod + custo_armazenagem_mp + custo_armazenagem_pa

            # Frete
            frete = 0
            for regiao in df_total.index:
                if regiao != "2":
                    frete_unit = fretes.get((regiao, "2"), 0)
                    frete += df_total.loc[regiao, periodo] * frete_unit

            st.write(f"🧮 Produção: **{int(demanda)} unidades**")
            st.write(f"- MP usada: {int(mp_total)} un. → R$ {custo_mp:,.2f}")
            st.write(f"- MOD: {mod_total_horas:.1f} h → R$ {custo_mod:,.2f}")
            st.write(f"👷 Operários necessários: **{num_operarios}** (480h cada)")
            st.write(f"- Armazenagem MP: R$ {custo_armazenagem_mp:,.2f}")
            st.write(f"- Armazenagem PA: R$ {custo_armazenagem_pa:,.2f}")
            st.write(f"📦 Custo variável: R$ {custo_var:,.2f}")
            st.write(f"🚚 Frete (R1/R3 → R2): R$ {frete:,.2f}")
            st.write(f"🏭 Custo fixo produção: R$ {custo_fixo_producao:,.2f}")
            st.write("---")

            custo_fixo_total += custo_fixo_producao
            custo_var_total += custo_var
            custo_frete_total += frete

        st.session_state.update({
            "custo_fixo_total": custo_fixo_total,
            "depreciacao_total": depre_total,
            "admin_total": admin_total,
            "custo_var_total": custo_var_total,
            "custo_frete_total": custo_frete_total,
            "investimento_total": investimento_total,
            "demanda_total": demanda_total,
            "num_modulos": num_modulos,
            "num_periodos": num_periodos
        })

# --- Aba 3: Resultados e Simulação ---
elif aba == "📈 Resultados e Simulação":
    st.header("📈 Resultados Consolidados")

    campos_necessarios = [
        "custo_fixo_total", "depreciacao_total", "admin_total",
        "custo_var_total", "custo_frete_total", "demanda_total"
    ]

    if all(campo in st.session_state for campo in campos_necessarios):
        total = (
            st.session_state["custo_fixo_total"] +
            st.session_state["depreciacao_total"] +
            st.session_state["admin_total"] +
            st.session_state["custo_var_total"] +
            st.session_state["custo_frete_total"]
        )
        custo_unit = total / st.session_state["demanda_total"]

        st.metric("💵 Custo Total (Fixos + Variáveis + Frete)", f"R$ {total:,.2f}")
        st.metric("📦 Custo Médio por Unidade", f"R$ {custo_unit:,.2f}")

        with st.expander("📊 Detalhamento Final"):
            st.write(f"🔧 Investimento inicial em {st.session_state['num_modulos']} módulos: R$ {st.session_state['investimento_total']:,.2f}")
            st.write(f"🏭 Custo Fixo de Produção: R$ {st.session_state['custo_fixo_total']:,.2f}")
            st.write(f"📉 Depreciação: R$ {st.session_state['depreciacao_total']:,.2f}")
            st.write(f"🧾 Administração ({st.session_state['num_periodos']} períodos): R$ {st.session_state['admin_total']:,.2f}")
            st.write(f"🧪 Custo Variável Total: R$ {st.session_state['custo_var_total']:,.2f}")
            st.write(f"🚚 Custo de Frete Total: R$ {st.session_state['custo_frete_total']:,.2f}")
    else:
        st.warning("⚠️ Execute a aba de cálculo antes de ver os resultados.")
