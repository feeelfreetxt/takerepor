def exibir_relatorio_individual(self, relatorio):
    """Exibe o relatório individual na interface"""
    try:
        if not relatorio:
            st.warning("Relatório vazio ou inválido")
            return
            
        # Exibir cabeçalho
        st.markdown(f"## Relatório de Desempenho: {relatorio['nome']}")
        st.markdown(f"**Grupo:** {relatorio['grupo']}")
        st.markdown(f"**Período:** {relatorio['periodo']}")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            valor = relatorio['metricas'].get('total_registros', 0)
            st.metric("Total de Registros", valor)
        
        with col2:
            valor = relatorio['metricas'].get('taxa_eficiencia', 0)
            if valor is not None:
                valor_fmt = f"{valor*100:.1f}%"
            else:
                valor_fmt = "N/A"
            st.metric("Taxa de Eficiência", valor_fmt)
        
        with col3:
            valor = relatorio['metricas'].get('tempo_medio_resolucao', 0)
            if valor is not None:
                valor_fmt = f"{valor:.1f} dias"
            else:
                valor_fmt = "N/A"
            st.metric("Tempo Médio", valor_fmt)
        
        with col4:
            tendencia = relatorio['metricas'].get('tendencia', {})
            direcao = tendencia.get('direcao', 'estável')
            st.metric("Tendência", direcao.capitalize())
        
        # Análise de desempenho
        st.subheader("Análise de Desempenho")
        
        if 'analise' in relatorio:
            analise = relatorio['analise']
            
            # Eficiência
            if 'eficiencia' in analise:
                ef = analise['eficiencia']
                valor = ef.get('valor', 0)
                nivel = ef.get('nivel', 'N/A')
                
                st.markdown(f"**Eficiência:** {valor:.1f}% - {nivel}")
            
            # Tempo de resolução
            if 'tempo_resolucao' in analise:
                tr = analise['tempo_resolucao']
                valor = tr.get('valor', 0)
                nivel = tr.get('nivel', 'N/A')
                
                if valor is not None:
                    st.markdown(f"**Tempo de Resolução:** {valor:.1f} dias - {nivel}")
                else:
                    st.markdown(f"**Tempo de Resolução:** N/A")
            
            # Volume de trabalho
            if 'volume_trabalho' in analise:
                vt = analise['volume_trabalho']
                valor = vt.get('valor', 0)
                nivel = vt.get('nivel', 'N/A')
                
                st.markdown(f"**Volume de Trabalho:** {valor} registros - {nivel}")
            
            # Taxa de conclusão
            if 'taxa_conclusao' in analise:
                tc = analise['taxa_conclusao']
                valor = tc.get('valor', 0)
                nivel = tc.get('nivel', 'N/A')
                
                st.markdown(f"**Taxa de Conclusão:** {valor:.1f}% - {nivel}")
        
        # Recomendações
        if 'recomendacoes' in relatorio and relatorio['recomendacoes']:
            st.subheader("Recomendações")
            
            for rec in relatorio['recomendacoes']:
                with st.expander(f"{rec['area']} - {rec['recomendacao']}"):
                    st.markdown(f"**Ação Recomendada:** {rec['acao']}")
        
        # Gráficos
        if 'graficos' in relatorio and relatorio['graficos']:
            st.subheader("Visualizações")
            
            graficos = relatorio['graficos']
            
            # Distribuição de status
            if 'distribuicao_status' in graficos:
                st.image(base64.b64decode(graficos['distribuicao_status']))
            
            # Tendência de eficiência
            if 'tendencia_eficiencia' in graficos:
                st.image(base64.b64decode(graficos['tendencia_eficiencia']))
            
            # Comparação com equipe
            if 'comparacao_equipe' in graficos:
                st.image(base64.b64decode(graficos['comparacao_equipe']))
    
    except Exception as e:
        st.error(f"Erro ao exibir relatório: {str(e)}")
        st.error(traceback.format_exc())