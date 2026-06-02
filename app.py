import streamlit as st
import pandas as pd

# Configuração da página para parecer um App de celular
st.set_page_config(page_title="Painel de Plantio", page_icon="🚜", layout="centered")

st.title("🚜 Painel Digital de Plantio")
st.markdown("### Apoio à decisão para Safrinha, Soja e Trigo")
st.write("Desenvolvido para auxiliar na regulagem precisa de maquinários e logística de sementes.")

# Carregar os dados (os arquivos devem estar na mesma pasta do script)
@st.cache_data
def carregar_dados():
    try:
        df_milho = pd.read_csv('plantabilidade_ideal_safrinha.csv')
        df_soja = pd.read_csv('plantabilidade_ideal_soja.csv')
        df_trigo = pd.read_csv('plantabilidade_ideal_trigo.csv')
        df_maquinas = pd.read_csv('regulagem_plantadeiras.csv')
        
        # Padronizar nomes para evitar erros de busca
        for df in [df_milho, df_soja, df_trigo]:
            df['Variedade'] = df['Variedade'].str.upper().str.strip()
            
        return df_milho, df_soja, df_trigo, df_maquinas
    except Exception as e:
        st.error(f"Erro ao carregar arquivos .csv: {e}")
        return None, None, None, None

df_milho, df_soja, df_trigo, df_maquinas = carregar_dados()

if df_milho is not None:
    # 1. Seleção da Cultura
    cultura = st.selectbox("1. Selecione a Cultura:", ['Milho Safrinha', 'Soja', 'Trigo'])
    
    # Filtrar variedades com base na cultura
    if cultura == 'Milho Safrinha':
        df_atual, sem_saco = df_milho, 60000
    elif cultura == 'Soja':
        df_atual, sem_saco = df_soja, 200000
    else:
        df_atual, sem_saco = df_trigo, 400000
        
    variedades = sorted(df_atual['Variedade'].unique())
    hibrido = st.selectbox("2. Selecione a Variedade:", variedades)
    
    # 2. Seleção de Máquina e Dados da Área
    maquina_nome = st.selectbox("3. Selecione a Plantadeira:", ['John Deere 1111', 'Tatu Marchesan COP', 'Stara Princesa'])
    altitude = st.number_input("4. Altitude da área (m):", min_value=0, max_value=1500, value=400, step=50)
    area_alq = st.number_input("5. Área total (Alqueires):", min_value=0.1, max_value=5000.0, value=10.0, step=1.0)

    st.markdown("---")

    if st.button("GERAR RECOMENDAÇÃO", type="primary", use_container_width=True):
        dados = df_atual[df_atual['Variedade'] == hibrido]
        
        if not dados.empty:
            # Ajuste de altitude (5% a mais para milho/soja acima de 700m)
            ajuste = 1.05 if (altitude > 700 and cultura != 'Trigo') else 1.00
            
            pop_ha = dados['Populacao_Alvo_ha'].values[0] * ajuste
            pop_alq = pop_ha * 2.42
            total_sacos = pop_alq * area_alq / sem_saco
            sem_metro = dados['Sementes_por_Metro'].values[0] * ajuste
            
            # Container de resultados bem visual estilo Card de Site
            st.success(f"📋 RESULTADO DO PLANEJAMENTO: {cultura.upper()}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Sementes Necessárias", value=f"{total_sacos:.1f} sacos")
                st.write(f"**População Alvo:** {pop_ha:,.0f} pl/ha")
                st.write(f"**População por Alqueire:** {pop_alq:,.0f} pl/Alq")
            
            with col2:
                st.metric(label="Alvo na Linha (Sementes/m)", value=f"{sem_metro:.2f}")
                if cultura != 'Trigo':
                    st.write(f"**Distância entre Sementes:** {(100/sem_metro):.1f} cm")
                st.write(f"**Profundidade Ideal:** {dados['Profundidade_Ideal_cm'].values[0]} cm")
                st.write(f"**Velocidade Máxima:** {dados['Velocidade_Max_kmh'].values[0]} km/h")
            
            # Busca de engrenagens na tabela auxiliar
            df_maq_filtrada = df_maquinas[df_maquinas['Modelo_Plantadeira'] == maquina_nome]
            if not df_maq_filtrada.empty and cultura != 'Trigo':
                idx_proximo = (df_maq_filtrada['Sementes_por_Metro_Alvo'] - sem_metro).abs().idxmin()
                regulagem_fina = df_maq_filtrada.loc[idx_proximo]
                
                st.markdown("---")
                st.info(f"🔧 AJUSTE FÍSICO RECOMENDADO ({maquina_nome})")
                st.write(f"⚙️ **Engrenagem / Catraca:** {regulagem_fina['Configuracao_Engrenagem']}")
                st.write(f"📝 **Detalhe Técnico:** {regulagem_fina['Detalhe_Tecnico']}")
            elif cultura == 'Trigo':
                st.warning("⚠️ **Nota para o Trigo:** O ajuste do fluxo contínuo deve ser realizado diretamente no câmbio de engrenagens da Semeadeira por kg/ha, conforme o manual do fabricante do implemento.")
                
            if altitude > 700 and cultura != 'Trigo':
                st.caption("💡 *Aviso: A população foi aumentada automaticamente em 5% devido à altitude alta.*")
        else:
            st.error("Erro ao processar dados da variedade.")
else:
    st.info("Aguardando o upload dos arquivos de dados na mesma pasta para funcionar.")
