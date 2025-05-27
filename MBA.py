import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="💰 Simulador de Custos", layout="wide")
st.title("💰 Simulador de Custos por Região e Trimestre")

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

# Módulos e depreciação
investimento_modulo = 17500
modulo_capacidade = 500  # capacidade por trimestre
depreciacao_percentual = 2.5 / 100
admin = 52000  # custo administrativo total por ano

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
    st.header("📊 Edição da Demanda por Região e Trimestre")
    regioes = ["1", "2", "3"]
    trimestres = ["1º", "2º", "3º", "4º"]

    dados_iniciais = {
        "Região": regioes,
        "1º": [2959, 5763, 6853],
        "2º": [3091, 8475, 10773],
        "3º": [3077, 7921, 10288],
        "4º": [3108, 5703, 7305],
    }

    df_input = pd.DataFrame(dados_iniciais)
    df_editado = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
    st.session_state["df_vendas"] = df_editado

# --- Aba 2: Cálculo de Custos ---
elif aba == "🧮 Cálculo de Custos":
    st.header("🧮 Detalhamento dos Custos por Trimestre")
    if "df_vendas" in st.session_state:
        df = st.session_state["df_vendas"].copy()
        df_total = df.set_index("Região")
        total_por_trimestre = df_total.sum(axis=0)
        demanda_maxima = total_por_trimestre.max()
        demanda_total = total_por_trimestre.sum()

        # Módulos fixos baseados na demanda máxima
        num_modulos = int(np.ceil(demanda_maxima / modulo_capacidade))
        investimento_total = num_modulos * investimento_modulo
        depre_total = investimento_total * depreciacao_percentual

        custo_fixo_total = 0
        custo_var_total = 0
        custo_frete_total = 0

        for trimestre in total_por_trimestre.index:
            st.markdown(f"### 📅 Trimestre {trimestre}")
            demanda_trim = df_total[trimestre].sum()
            custo_fixo_producao = next(valor for (inicio, fim), valor in custos_producao.items() if inicio <= demanda_trim <= fim)
            
            # Custo variável detalhado
            mp_total = demanda_trim * mp_por_unidade
            mod_total_horas = demanda_trim * mod_horas_por_unidade
            custo_mp = mp_total * custo_mp_unit
            custo_mod = mod_total_horas * custos_pessoas["Operários"]["Salário/hora"]
            custo_armazenagem_mp = mp_total * armazenagem_mp_unit
            custo_armazenagem_pa = demanda_trim * armazenagem_pa_unit

            custo_var_total_trim = custo_mp + custo_mod + custo_armazenagem_mp + custo_armazenagem_pa

            # Frete
            frete_trim = 0
            for regiao in df_total.index:
                if regiao != "2":  # fábrica na região 2
                    frete_unit = fretes.get((regiao, "2"), 0)
                    frete_trim += df_total.loc[regiao, trimestre] * frete_unit

            st.write(f"🧮 Produção: {int(demanda_trim)} unidades")
            st.write(f"- Matéria-prima usada: {int(mp_total)} unidades (R$ {custo_mp:,.2f})")
            st.write(f"- MOD (1,5h/un): {mod_total_horas:.1f} h (R$ {custo_mod:,.2f})")
            st.write(f"- Armazenagem MP: R$ {custo_armazenagem_mp:,.2f}")
            st.write(f"- Armazenagem PA: R$ {custo_armazenagem_pa:,.2f}")
            st.write(f"📦 Custo variável total: **R$ {custo_var_total_trim:,.2f}**")
            st.write(f"🚚 Custo de frete (de R1/R3 para R2): **R$ {frete_trim:,.2f}**")
            st.write(f"🏭 Custo fixo produção: **R$ {custo_fixo_producao:,.2f}**")
            st.write("---")

            custo_fixo_total += custo_fixo_producao
            custo_var_total += custo_var_total_trim
            custo_frete_total += frete_trim

        st.session_state["custo_fixo_total"] = custo_fixo_total
        st.session_state["depreciacao_total"] = depre_total
        st.session_state["admin"] = admin
        st.session_state["custo_var_total"] = custo_var_total
        st.session_state["custo_frete_total"] = custo_frete_total
        st.session_state["investimento_total"] = investimento_total
        st.session_state["demanda_total"] = demanda_total
        st.session_state["num_modulos"] = num_modulos

# --- Aba 3: Resultados e Simulação ---
elif aba == "📈 Resultados e Simulação":
    st.header("📈 Resultados Consolidados")
    if "custo_fixo_total" in st.session_state:
        total = (
            st.session_state["custo_fixo_total"] +
            st.session_state["depreciacao_total"] +
            st.session_state["admin"] +
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
            st.write(f"🧾 Administrativo: R$ {st.session_state['admin']:,.2f}")
            st.write(f"🧪 Custo Variável Total: R$ {st.session_state['custo_var_total']:,.2f}")
            st.write(f"🚚 Custo de Frete Total: R$ {st.session_state['custo_frete_total']:,.2f}")
    else:
        st.warning("⚠️ Calcule os custos antes de visualizar os resultados.")
