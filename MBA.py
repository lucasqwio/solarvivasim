import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="💰 Simulador de Custos", layout="wide")
st.title("💰 Simulador de Custos com Upload de Demanda")

# --- Aba de navegação ---
aba = st.sidebar.radio("Escolha a aba", ["📁 Upload Demanda", "🧮 Cálculo de Custos", "📈 Resultados e Simulação"])

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
    "Operários": {
        "Salário/hora": 8.5,
        "Contratação": 3000,
        "Treinamento": 700
    }
}

# Parâmetros de custeio
custo_mp_unit = 10.0
armazenagem_mp_unit = 1.5
armazenagem_pa_unit = 2.4
mp_por_unidade = 3
mod_horas_por_unidade = 1.5
horas_por_operario = 480

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

# --- Aba 1: Upload da Demanda ---
if aba == "📁 Upload Demanda":
    st.header("📁 Upload da Planilha de Demanda")
    st.markdown("O arquivo deve conter as regiões como linhas (`1`, `2`, `3`) e colunas `T1` a `T8` com as demandas por período.")
    file = st.file_uploader("Carregue o arquivo `.xlsx` com a demanda:", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        df.set_index(df.columns[0], inplace=True)
        st.session_state["df_demandas"] = df.astype(int)
        st.success("✅ Planilha carregada com sucesso!")
        st.dataframe(st.session_state["df_demandas"], use_container_width=True)

# --- Aba 2: Cálculo de Custos ---
elif aba == "🧮 Cálculo de Custos":
    st.header("🧮 Cálculo de Custos para os 8 Períodos")

    if "df_demandas" in st.session_state:
        df_total = st.session_state["df_demandas"]
        periodos = df_total.columns.tolist()

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
        custo_contratacao_total = 0
        custo_treinamento_total = 0
        operarios_anteriores = 0

        for i, periodo in enumerate(periodos):
            st.markdown(f"### 📅 Período {periodo}")
            demanda = df_total[periodo].sum()
            custo_fixo_producao = next(valor for (inicio, fim), valor in custos_producao.items() if inicio <= demanda <= fim)

            # Custo variável
            mp_total = demanda * mp_por_unidade
            mod_total_horas = demanda * mod_horas_por_unidade
            num_operarios = math.ceil(mod_total_horas / horas_por_operario)
            novos_operarios = num_operarios if i == 0 else max(0, num_operarios - operarios_anteriores)

            custo_mp = mp_total * custo_mp_unit
            custo_mod = mod_total_horas * custos_pessoas["Operários"]["Salário/hora"]
            custo_armazenagem_mp = mp_total * armazenagem_mp_unit
            custo_armazenagem_pa = demanda * armazenagem_pa_unit
            custo_var = custo_mp + custo_mod + custo_armazenagem_mp + custo_armazenagem_pa

            # Frete
            frete = 0
            for regiao in df_total.index:
                if str(regiao) != "2":
                    frete_unit = fretes.get((str(regiao), "2"), 0)
                    frete += df_total.loc[regiao, periodo] * frete_unit

            # Contratação e treinamento
            custo_contratacao = novos_operarios * custos_pessoas["Operários"]["Contratação"]
            custo_treinamento = novos_operarios * custos_pessoas["Operários"]["Treinamento"]

            st.write(f"🧮 Produção: **{int(demanda)} unidades**")
            st.write(f"- MP usada: {int(mp_total)} un. → R$ {custo_mp:,.2f}")
            st.write(f"- MOD: {mod_total_horas:.1f} h → R$ {custo_mod:,.2f}")
            st.write(f"👷 Operários necessários: **{num_operarios}** (480h cada)")
            if novos_operarios > 0:
                st.write(f"🆕 Novos operários: {novos_operarios} → Contratação: R$ {custo_contratacao:,.2f}, Treinamento: R$ {custo_treinamento:,.2f}")
            st.write(f"- Armazenagem MP: R$ {custo_armazenagem_mp:,.2f}")
            st.write(f"- Armazenagem PA: R$ {custo_armazenagem_pa:,.2f}")
            st.write(f"📦 Custo variável: R$ {custo_var:,.2f}")
            st.write(f"🚚 Frete (R1/R3 → R2): R$ {frete:,.2f}")
            st.write(f"🏭 Custo fixo produção: R$ {custo_fixo_producao:,.2f}")
            st.write("---")

            operarios_anteriores = num_operarios
            custo_fixo_total += custo_fixo_producao
            custo_var_total += custo_var
            custo_frete_total += frete
            custo_contratacao_total += custo_contratacao
            custo_treinamento_total += custo_treinamento

        st.session_state.update({
            "custo_fixo_total": custo_fixo_total,
            "depreciacao_total": depre_total,
            "admin_total": admin_total,
            "custo_var_total": custo_var_total,
            "custo_frete_total": custo_frete_total,
            "custo_contratacao_total": custo_contratacao_total,
            "custo_treinamento_total": custo_treinamento_total,
            "investimento_total": investimento_total,
            "demanda_total": demanda_total,
            "num_modulos": num_modulos,
            "num_periodos": num_periodos
        })
    else:
        st.warning("⚠️ Faça o upload da planilha primeiro na aba 'Upload Demanda'.")

# --- Aba 3: Resultados e Simulação ---
elif aba == "📈 Resultados e Simulação":
    st.header("📈 Resultados Consolidados")

    campos_necessarios = [
        "custo_fixo_total", "depreciacao_total", "admin_total",
        "custo_var_total", "custo_frete_total", "custo_contratacao_total",
        "custo_treinamento_total", "demanda_total"
    ]

    if all(campo in st.session_state for campo in campos_necessarios):
        total = (
            st.session_state["custo_fixo_total"] +
            st.session_state["depreciacao_total"] +
            st.session_state["admin_total"] +
            st.session_state["custo_var_total"] +
            st.session_state["custo_frete_total"] +
            st.session_state["custo_contratacao_total"] +
            st.session_state["custo_treinamento_total"]
        )
        custo_unit = total / st.session_state["demanda_total"]

        st.metric("💵 Custo Total", f"R$ {total:,.2f}")
        st.metric("📦 Custo Médio por Unidade", f"R$ {custo_unit:,.2f}")

        with st.expander("📊 Detalhamento Final"):
            st.write(f"🔧 Investimento em {st.session_state['num_modulos']} módulos: R$ {st.session_state['investimento_total']:,.2f}")
            st.write(f"🏭 Custo Fixo Produção: R$ {st.session_state['custo_fixo_total']:,.2f}")
            st.write(f"📉 Depreciação: R$ {st.session_state['depreciacao_total']:,.2f}")
            st.write(f"🧾 Administração: R$ {st.session_state['admin_total']:,.2f}")
            st.write(f"🧪 Custo Variável: R$ {st.session_state['custo_var_total']:,.2f}")
            st.write(f"🚚 Frete: R$ {st.session_state['custo_frete_total']:,.2f}")
            st.write(f"👷 Contratação: R$ {st.session_state['custo_contratacao_total']:,.2f}")
            st.write(f"📘 Treinamento: R$ {st.session_state['custo_treinamento_total']:,.2f}")
    else:
        st.warning("⚠️ Execute a aba de cálculo antes de ver os resultados.")
