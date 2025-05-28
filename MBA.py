import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="💰 Simulador de Custos", layout="wide")
st.title("💰 Simulador de Custos - Custeio Direto com Estratégias de Estoque")

# === Parâmetros fixos ===
fretes = {
    ("1", "2"): 5.00, ("2", "1"): 5.00,
    ("1", "3"): 13.00, ("3", "1"): 13.00,
    ("2", "3"): 11.00, ("3", "2"): 11.00,
}

custos_pessoas = {
    "Operários": {
        "Salário/hora": 8.5,
        "Contratação": 3000,
        "Treinamento": 700
    }
}

custo_mp_unit = 10.0
armazenagem_mp_unit = 1.5
armazenagem_pa_unit = 2.4
mp_por_unidade = 3
mod_horas_por_unidade = 1.5
horas_por_operario = 480

investimento_modulo = 17500
modulo_capacidade = 500
depreciacao_percentual = 0.025
admin_por_periodo = 52000

custos_producao = {
    (0, 5000): 52000,
    (5001, 10000): 89300,
    (10001, 15000): 114330,
    (15001, 20000): 135000,
    (20001, 25000): 153660,
    (25001, float('inf')): 168300
}

# === Upload da Planilha ===
st.header("📁 Upload da Planilha de Demanda (8 Períodos)")
file = st.file_uploader("Carregue o arquivo `.xlsx` com colunas T1 a T8 e a coluna 'Região'", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.set_index(df.columns[0], inplace=True)
    df_total = df.astype(int)
    st.success("✅ Planilha carregada com sucesso!")
    st.dataframe(df_total, use_container_width=True)

    # === Estoques de Segurança ===
    st.header("⚙️ Estoques de Segurança")
    estoque_seg_mp = st.number_input("Estoque de segurança de Matéria-Prima (unidades)", 0, 100000, 0)
    estoque_seg_pa = st.number_input("Estoque de segurança de Produto Acabado (unidades)", 0, 100000, 0)

    # === Preço de Venda ===
    preco_venda = st.number_input("💲 Preço de Venda por unidade", min_value=0.0, value=40.0, step=0.5)

    # === Cálculo Detalhado por Período ===
    st.header("🧮 Cálculo Detalhado por Período")
    periodos = df_total.columns.tolist()
    total_por_trimestre = df_total.sum(axis=0)
    demanda_total = total_por_trimestre.sum()
    num_periodos = len(periodos)

    demanda_maxima = total_por_trimestre.max()
    num_modulos = int(np.ceil(demanda_maxima / modulo_capacidade))
    investimento_total = num_modulos * investimento_modulo
    depre_total = investimento_total * depreciacao_percentual
    admin_total = admin_por_periodo * num_periodos

    detalhado = {}
    estoque_mp = 0
    estoque_pa = 0
    operarios_anteriores = 0

    total_fixo = total_var = total_frete = total_contr = total_trein = 0

    for i, periodo in enumerate(periodos):
        demanda = total_por_trimestre[periodo]
        fixo = next(v for (ini, fim), v in custos_producao.items() if ini <= demanda <= fim)

        mp = demanda * mp_por_unidade
        mod_horas = demanda * mod_horas_por_unidade
        operarios = math.ceil(mod_horas / horas_por_operario)
        novos_operarios = max(0, operarios - operarios_anteriores)

        custo_mp = mp * custo_mp_unit
        custo_mod = mod_horas * custos_pessoas["Operários"]["Salário/hora"]
        custo_arm_mp = (mp + estoque_seg_mp) * armazenagem_mp_unit if estoque_seg_mp > 0 else 0
        custo_arm_pa = (demanda + estoque_seg_pa) * armazenagem_pa_unit if estoque_seg_pa > 0 else 0
        custo_var = custo_mp + custo_mod + custo_arm_mp + custo_arm_pa

        frete = 0
        for regiao in df_total.index:
            if str(regiao) != "2":
                frete_unit = fretes.get((str(regiao), "2"), 0)
                frete += df_total.loc[regiao, periodo] * frete_unit

        contr = novos_operarios * custos_pessoas["Operários"]["Contratação"]
        trein = novos_operarios * custos_pessoas["Operários"]["Treinamento"]

        detalhado[periodo] = {
            "Demanda": demanda,
            "Operários": operarios,
            "MOD (R$)": custo_mod,
            "MP (R$)": custo_mp,
            "Armaz. MP (R$)": custo_arm_mp,
            "Armaz. PA (R$)": custo_arm_pa,
            "Frete (R$)": frete,
            "Fixos Prod. (R$)": fixo,
            "Contratação (R$)": contr,
            "Treinamento (R$)": trein,
            "Variáveis (R$)": custo_var
        }

        total_fixo += fixo
        total_var += custo_var
        total_frete += frete
        total_contr += contr
        total_trein += trein
        operarios_anteriores = operarios

    # === Tabela Detalhada ===
    st.header("📊 Tabela Consolidada por Período")
    df_detalhado = pd.DataFrame(detalhado).T
    st.dataframe(df_detalhado.T, use_container_width=True)

    # === Resultados Finais ===
    st.header("📈 Resultados Consolidados")
    total_geral = total_fixo + depre_total + admin_total + total_var + total_frete + total_contr + total_trein
    custo_unit = total_geral / demanda_total
    receita_total = preco_venda * demanda_total
    lucro_total = receita_total - total_geral

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Receita Total", f"R$ {receita_total:,.2f}")
    col2.metric("📦 Custo Unitário Médio", f"R$ {custo_unit:,.2f}")
    col3.metric("📈 Lucro Total", f"R$ {lucro_total:,.2f}")

    with st.expander("🔍 Detalhamento dos Custos"):
        st.write(f"🔧 Investimento em módulos: R$ {investimento_total:,.2f}")
        st.write(f"🏭 Custo Fixo Produção: R$ {total_fixo:,.2f}")
        st.write(f"📉 Depreciação Total: R$ {depre_total:,.2f}")
        st.write(f"🧾 Administração Total: R$ {admin_total:,.2f}")
        st.write(f"🧪 Custo Variável Total: R$ {total_var:,.2f}")
        st.write(f"🚚 Frete Total: R$ {total_frete:,.2f}")
        st.write(f"👷 Contratação: R$ {total_contr:,.2f}")
        st.write(f"📘 Treinamento: R$ {total_trein:,.2f}")

else:
    st.info("📥 Faça o upload da planilha para iniciar os cálculos.")
