import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os

st.set_page_config(page_title="Plano 105 - Regional Iporá", layout="wide")

st.markdown("""
<style>
    .main-title { text-align: center; color: #0f3460; font-weight: 800; font-size: 28px; margin-bottom: 2px; }
    .sub-title { text-align: center; color: #555; font-size: 15px; margin-bottom: 20px; font-weight: 500; }
    .badge-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 8px 16px;
        text-align: center;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-manutencao { border: 2px solid #ff9800; color: #b76e00; }
    .badge-concluido { border: 2px solid #4caf50; color: #2e7d32; }
    
    h3 {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #333 !important;
        margin-bottom: 10px !important;
    }
    
    /* Estilo para deixar o uploader compacto alinhado à esquerda */
    [data-testid="stFileUploader"] {
        width: 100% !important;
    }
    [data-testid="stFileUploader"] section {
        padding: 4px !important;
        min-height: 60px !important;
    }
    [data-testid="stFileUploader"] section div {
        gap: 2px !important;
    }
    [data-testid="stFileUploader"] small {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Plano 105 - Regional Iporá</div>', unsafe_allow_html=True)

# Colocando o uploader compacto na extrema esquerda usando colunas
col_up, col_vazia = st.columns([2, 5])
with col_up:
    arquivo_carregado = st.file_uploader("📂 Arquivo", type=["xlsx"], label_visibility="collapsed")

caminho_padrao = "Plano 105_2110.xlsx"
fonte_dados = arquivo_carregado if arquivo_carregado is not None else (caminho_padrao if os.path.exists(caminho_padrao) else None)

@st.cache_data(ttl=300)
def carregar_dados(file):
    try:
        df_anomalias = pd.read_excel(file, sheet_name='Geral anomalias')
        try:
            df_meta = pd.read_excel(file, sheet_name='meta')
            val_e2 = df_meta.iloc[0, 4]
            data_atualizacao = pd.to_datetime(val_e2).strftime('%d/%m/%Y') if pd.notnull(val_e2) else "21/10/2026"
        except Exception:
            data_atualizacao = "21/10/2026"
        return df_anomalias, data_atualizacao
    except Exception as e:
        return None, str(e)

if fonte_dados is not None:
    df_raw, data_atualizacao = carregar_dados(fonte_dados)
    
    if df_raw is not None:
        st.markdown(f'<div class="sub-title">atualizado a última vez {data_atualizacao}</div>', unsafe_allow_html=True)

        def opc(col):
            if col in df_raw.columns:
                vals = df_raw[col].dropna().unique().tolist()
                vals_str = [str(v) for v in vals]
                vals_str.sort()
                return ["Todos"] + vals_str
            return ["Todos"]

        with st.expander("🔍 Filtros de Pesquisa", expanded=True):
            c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
            
            with c1:
                f_sec = st.selectbox("Seccional", opc('Seccional'))
                f_car = st.selectbox("Carteira mês", opc('Mês'))
            with c2:
                f_se = st.selectbox("Subestação", opc('SE'))
                f_tax = st.selectbox("Taxonomia", opc('Taxonomia'))
            with c3:
                f_eq = st.selectbox("Equipamento", opc('Instalação'))
                f_par = st.selectbox("Parceira", opc('Empresa '))
            with c4:
                f_tre = st.selectbox("Tipo de trecho", opc('Tipo de trecho'))
                f_pos = st.selectbox("Poste", opc('Poste'))
            with c5:
                f_steq = st.selectbox("Status equipamento", opc('Status Equipamento'))
                f_sem = st.selectbox("Semana de execução", opc('Semana'))
            with c6:
                f_stan = st.selectbox("Status anomalia", opc('Execução'))
                f_tan = st.selectbox("Tipo de anomalia", opc('Tipo de anomalia'))
            with c7:
                f_ins = st.selectbox("Inspeção (OS)", opc('OS'))
                f_def = st.selectbox("Defeito", opc('Defeito'))

        # Filtragem principal (Dropdowns do topo)
        df = df_raw.copy()
        filtros_map = {
            'Seccional': f_sec, 'SE': f_se, 'Instalação': f_eq, 'Tipo de trecho': f_tre,
            'Status Equipamento': f_steq, 'Execução': f_stan, 'OS': f_ins, 'Mês': f_car,
            'Taxonomia': f_tax, 'Empresa ': f_par, 'Poste': f_pos, 'Semana': f_sem,
            'Tipo de anomalia': f_tan, 'Defeito': f_def
        }

        for col, val in filtros_map.items():
            if val != "Todos" and col in df.columns:
                df = df[df[col].astype(str) == str(val)]

        col_empresa_nome = 'Empresa ' if 'Empresa ' in df.columns else ('Empresa' if 'Empresa' in df.columns else None)

        # --- CAIXAS DE EQUIPAMENTOS LADO A LADO ---
        st.markdown("---")
        col_manut, col_conc = st.columns(2)

        df_manut = df[df['Status Equipamento'] == 'EM MANUTENÇÃO'] if 'Status Equipamento' in df.columns else pd.DataFrame()
        df_conc = df[df['Status Equipamento'] == 'CONCLUÍDO'] if 'Status Equipamento' in df.columns else pd.DataFrame()

        qtd_manut = df_manut['Instalação'].nunique() if not df_manut.empty else 0
        qtd_conc = df_conc['Instalação'].nunique() if not df_conc.empty else 0

        # Coluna Esquerda: Em Manutenção
        with col_manut:
            st.markdown(f'<div class="badge-card badge-manutencao">Equipamentos Únicos em Manutenção: {qtd_manut}</div>', unsafe_allow_html=True)
            st.subheader("Equipamentos EM MANUTENÇÃO")
            
            if not df_manut.empty:
                grp_m = df_manut.groupby(['Instalação', 'Execução'])['ID Anomalia'].nunique().reset_index()
                num_items_m = grp_m['Instalação'].nunique()
                calc_height_m = max(400, num_items_m * 28)

                fig_m = px.bar(
                    grp_m, x='ID Anomalia', y='Instalação', color='Execução',
                    color_discrete_map={'Executado': '#2e7d32', 'Pendente': '#d32f2f'},
                    barmode='stack', orientation='h', text='ID Anomalia'
                )
                fig_m.update_traces(textposition='outside')
                fig_m.update_layout(
                    height=calc_height_m,
                    margin=dict(l=10, r=30, t=20, b=10),
                    yaxis={'categoryorder':'total ascending'},
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                container_m = st.container(height=480)
                with container_m:
                    st.plotly_chart(fig_m, use_container_width=True, key="chart_manut", config={'displayModeBar': False})
            else:
                st.info("Nenhum dado encontrado.")

        # Coluna Direita: Concluídos
        with col_conc:
            st.markdown(f'<div class="badge-card badge-concluido">Equipamentos Únicos Concluídos: {qtd_conc}</div>', unsafe_allow_html=True)
            st.subheader("Equipamentos CONCLUÍDOS")
            
            if not df_conc.empty:
                grp_c = df_conc.groupby(['Instalação', 'Execução'])['ID Anomalia'].nunique().reset_index()
                num_items_c = grp_c['Instalação'].nunique()
                calc_height_c = max(400, num_items_c * 28)

                fig_c = px.bar(
                    grp_c, x='ID Anomalia', y='Instalação', color='Execução',
                    color_discrete_map={'Executado': '#2e7d32', 'Pendente': '#d32f2f'},
                    barmode='stack', orientation='h', text='ID Anomalia'
                )
                fig_c.update_traces(textposition='outside')
                fig_c.update_layout(
                    height=calc_height_c,
                    margin=dict(l=10, r=30, t=20, b=10),
                    yaxis={'categoryorder':'total ascending'},
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                container_c = st.container(height=480)
                with container_c:
                    st.plotly_chart(fig_c, use_container_width=True, key="chart_conc", config={'displayModeBar': False})
            else:
                st.info("Nenhum dado encontrado.")

        # --- GRÁFICO DE BARRA ÚNICA POR EMPRESA ---
        st.markdown("---")
        st.subheader("📊 Distribuição de Anomalias por Empresa")
        
        if col_empresa_nome and col_empresa_nome in df.columns:
            grp_emp = df.groupby(col_empresa_nome)['ID Anomalia'].nunique().reset_index()
            grp_emp['Categoria'] = 'Total'
            grp_emp['Empresa_Str'] = grp_emp[col_empresa_nome].astype(str)
            
            fig_emp = px.bar(
                grp_emp, x='ID Anomalia', y='Categoria', color='Empresa_Str',
                text='ID Anomalia', barmode='stack', orientation='h'
            )
            fig_emp.update_traces(textposition='inside')
            fig_emp.update_layout(
                height=130,
                margin=dict(l=10, r=30, t=10, b=10),
                xaxis_title="",
                yaxis_title="",
                yaxis=dict(showticklabels=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig_emp, use_container_width=True, key="chart_empresa", config={'displayModeBar': False})
        else:
            st.info("Coluna de Empresa não encontrada.")

        # --- TABELA INTERATIVA ---
        st.markdown("---")
        st.subheader(f"📋 Planilha Geral de Anomalias (Filtrada - {len(df)} registros)")
        col_indices = [0, 1, 3, 4, 7, 8, 9, 10, 11, 12, 14, 15, 16, 20, 21, 24]
        cols_existentes = [df.columns[i] for i in col_indices if i < len(df.columns)]
        df_tabela = df[cols_existentes].copy()

        for col_dt in ['Data de execução', 'DATA DE REGISTRO']:
            if col_dt in df_tabela.columns:
                df_tabela[col_dt] = pd.to_datetime(df_tabela[col_dt], errors='coerce').dt.strftime('%d/%m/%Y')

        st.dataframe(df_tabela, use_container_width=True, height=400)

        # --- BOTÃO DE DOWNLOAD EXCEL ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_tabela.to_excel(writer, index=False, sheet_name='Base Filtrada')
        
        st.download_button(
            label="📥 BAIXAR BASE EM EXCEL",
            data=buffer.getvalue(),
            file_name="Anomalias_Filtradas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("👆 Por favor, envie o arquivo 'Plano 105_2110.xlsx' no botão acima ou coloque-o na mesma pasta do código.")
