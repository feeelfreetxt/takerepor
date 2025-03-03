import pandas as pd
import json
from datetime import datetime
import logging
from typing import Dict, Any, List

# Configuração do logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnalisadorExcel:
    def __init__(self):
        self.arquivos = [
            r"F:\okok\(JULIO) LISTAS INDIVIDUAIS.xlsx",
            r"F:\okok\(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
        ]
        
        # Mapeamento de colunas (nome lógico -> possíveis nomes no Excel)
        self.COLUNAS = {
            'DATA_CRIACAO': ['DATA', 'Data', 'DATA CRIACAO', 'Data Criação'],
            'DATA_RESOLUCAO': ['RESOLUÇÃO', 'RESOLUCAO', 'Data Resolução', 'Data Resolucao'],
            'BANCO': ['BANCO', 'Banco'],
            'NEGOCIACAO': ['NEGOCIAÇÃO', 'NEGOCIACAO', 'Negociacao', 'Negociação'],
            'STATUS': ['SITUAÇÃO', 'SITUACAO', 'Status', 'Situacao']
        }
    
    def validate_columns(self, df):
        """Verifica se todas as colunas necessárias estão presentes"""
        colunas_presentes = set(df.columns)
        colunas_mapeadas = {}
        
        # Para cada coluna lógica, procurar uma correspondente no Excel
        for col_logica, possiveis_nomes in self.COLUNAS.items():
            coluna_encontrada = None
            for nome in possiveis_nomes:
                if nome in colunas_presentes:
                    coluna_encontrada = nome
                    break
            
            if coluna_encontrada:
                colunas_mapeadas[col_logica] = coluna_encontrada
            else:
                logger.warning(f"Coluna ausente: {possiveis_nomes[0]}")
                return False, {}
        
        return True, colunas_mapeadas
    
    def analisar_arquivo(self, caminho: str) -> Dict[str, Any]:
        """Analisa um arquivo Excel e retorna os dados processados"""
        try:
            logger.info(f"Analisando: {caminho}")
            excel_file = pd.ExcelFile(caminho)
            resultados = {}
            
            for nome in excel_file.sheet_names:
                if nome.upper() == 'RELATÓRIO GERAL':
                    continue
                    
                df = excel_file.parse(nome)
                
                # Validar e obter mapeamento de colunas
                valido, colunas = self.validate_columns(df)
                if not valido:
                    logger.error(f"Estrutura inválida na aba {nome}")
                    continue
                
                # Processar datas
                df['data_criacao'] = pd.to_datetime(
                    df[colunas['DATA_CRIACAO']], 
                    format='mixed', 
                    errors='coerce'
                )
                df['data_resolucao'] = pd.to_datetime(
                    df[colunas['DATA_RESOLUCAO']], 
                    format='mixed', 
                    errors='coerce'
                )
                
                # Registrar datas inválidas
                for col in ['data_criacao', 'data_resolucao']:
                    invalid_dates = df[col].isna().sum()
                    if invalid_dates > 0:
                        logger.warning(f"{invalid_dates} datas inválidas na coluna {col.upper()}")
                
                # Calcular tempo de resolução
                df['tempo_resolucao'] = None
                mask = ~df['data_criacao'].isna() & ~df['data_resolucao'].isna()
                if mask.any():
                    df.loc[mask, 'tempo_resolucao'] = (
                        df.loc[mask, 'data_resolucao'] - df.loc[mask, 'data_criacao']
                    ).dt.days
                
                # Converter status para string
                df[colunas['STATUS']] = df[colunas['STATUS']].astype(str)
                
                # Calcular estatísticas
                total_registros = len(df)
                concluidos = df[df[colunas['STATUS']].str.upper() == 'CONCLUÍDO'].shape[0]
                taxa_sucesso = round((concluidos / total_registros * 100), 2) if total_registros > 0 else 0
                tempo_medio = round(df['tempo_resolucao'].mean(), 2) if df['tempo_resolucao'].notna().any() else None
                
                # Contar bancos
                banco_col = colunas['BANCO']
                bancos = df[banco_col].value_counts().head(3).to_dict() if banco_col in df.columns else {}
                
                # Últimas negociações
                ultimas_negociacoes = []
                if not df.empty and 'data_criacao' in df.columns:
                    ultimas = df.sort_values('data_criacao', ascending=False).head(5)
                    for _, row in ultimas.iterrows():
                        data = row['data_criacao']
                        if pd.isna(data):
                            continue
                        ultimas_negociacoes.append({
                            'data': data.strftime('%Y-%m-%d') if isinstance(data, pd.Timestamp) else str(data),
                            'status': str(row[colunas['STATUS']])
                        })
                
                resultados[nome] = {
                    'total_registros': total_registros,
                    'taxa_sucesso': taxa_sucesso,
                    'tempo_medio': tempo_medio,
                    'bancos': bancos,
                    'ultimas_negociacoes': ultimas_negociacoes
                }
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro ao analisar arquivo {caminho}: {str(e)}")
            return {}
    
    def gerar_relatorio_json(self, dados: Dict[str, Any]) -> None:
        """Salva os dados processados em um arquivo JSON formatado"""
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type %s not serializable" % type(obj))
        
        try:
            with open('relatorio_analise.json', 'w', encoding='utf-8') as f:
                json.dump(dados, f, default=serialize_datetime, ensure_ascii=False, indent=2)
            logger.info("Relatório JSON gerado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao gerar relatório JSON: {str(e)}")
    
    def imprimir_resumo(self, dados: Dict[str, Any]) -> None:
        """Exibe um resumo organizado dos dados processados"""
        for colaborador, info in dados.items():
            print(f"\n{'='*50}")
            print(f"Colaborador: {colaborador}")
            print(f"Total de registros: {info['total_registros']}")
            print(f"Tempo médio de resolução: {info['tempo_medio']} dias")
            print(f"Taxa de sucesso: {info['taxa_sucesso']}%")
            
            print("\nTop 3 Bancos:")
            for banco, qtd in sorted(info['bancos'].items(), 
                                   key=lambda x: x[1], reverse=True)[:3]:
                print(f"- {banco}: {qtd}")
            
            print("\nDistribuição de Situações:")
            for sit, qtd in sorted(info['situacoes'].items()):
                print(f"- {sit}: {qtd}")
            
            print("\nÚltimas Negociações:")
            for neg in info['ultimas_negociacoes']:
                print(f"- {neg}")
    
    def gerar_insights(self, dados):
        """Gera insights baseados nos dados analisados"""
        insights = []
        
        for colaborador, info in dados.items():
            if not isinstance(info, dict):
                continue
                
            # Taxa de sucesso
            taxa_sucesso = info.get('taxa_sucesso')
            if taxa_sucesso is not None and taxa_sucesso > 80:
                insights.append(f"Parabéns! {colaborador} mantém uma alta taxa de sucesso de {taxa_sucesso}%")
            
            # Tempo médio de resolução
            tempo_medio = info.get('tempo_medio')
            if tempo_medio is not None and tempo_medio > 7:
                insights.append(f"Atenção: {colaborador} tem um tempo médio de resolução de {tempo_medio} dias")
            
            # Volume de registros
            total_registros = info.get('total_registros')
            if total_registros is not None and total_registros < 10:
                insights.append(f"Nota: {colaborador} tem poucos registros ({total_registros})")
        
        if not insights:
            insights.append("Nenhum insight significativo encontrado nos dados atuais")
        
        return insights
    
    def gerar_relatorio_html(self, dados):
        """Gera um relatório HTML com visualização moderna dos dados"""
        html_template = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Análise</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .card { margin-bottom: 1rem; }
        .success-rate { font-size: 1.5rem; font-weight: bold; }
        .alert-custom { margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="mb-4">Relatório de Análise de Negociações</h1>
        <div class="row">
            {cards}
        </div>
        <div class="mt-4">
            <h2>Insights Importantes</h2>
            {insights}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

        colaborador_cards = []
        for colaborador, info in dados.items():
            success_rate = info.get('taxa_sucesso', 0)
            card_class = 'success' if success_rate >= 80 else ('warning' if success_rate >= 50 else 'danger')
            
            card_html = f'''<div class="col-md-6">
    <div class="card">
        <div class="card-header bg-{card_class} text-white">
            <h5 class="card-title mb-0">{colaborador}</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h6>Métricas Gerais</h6>
                    <ul class="list-unstyled">
                        <li>Total de Registros: {info.get('total_registros', 0)}</li>
                        <li>Taxa de Sucesso: <span class="success-rate">{info.get('taxa_sucesso', 0)}%</span></li>
                        <li>Tempo Médio: {info.get('tempo_medio', 'N/A')} dias</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Bancos Mais Frequentes</h6>
                    <ul class="list-unstyled">
                        {self._format_bank_list(info.get('bancos', {}))}
                    </ul>
                </div>
            </div>
            <div class="mt-3">
                <h6>Últimas Negociações</h6>
                <ul class="list-group">
                    {self._format_negotiations(info.get('ultimas_negociacoes', []))}
                </ul>
            </div>
        </div>
    </div>
</div>'''
            colaborador_cards.append(card_html)
        
        insights = self.gerar_insights(dados)
        insights_html = '<div class="list-group">'
        for insight in insights:
            alert_type = 'success' if 'parabéns' in insight.lower() else 'warning'
            insights_html += f'<div class="alert alert-{alert_type}">{insight}</div>'
        insights_html += '</div>'
        
        # Replace placeholders with actual content
        html_content = html_template.format(
            cards='\n'.join(colaborador_cards),
            insights=insights_html
        )
        
        try:
            with open('relatorio_analise.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("Relatório HTML gerado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao gerar relatório HTML: {str(e)}")
    
    def _format_bank_list(self, bancos):
        """Formata a lista de bancos para HTML"""
        if not bancos:
            return "<li>Sem dados de bancos</li>"
        
        html = []
        for banco, count in bancos.items():
            if banco and isinstance(banco, str):
                html.append(f"<li>{banco}: {count}</li>")
        return "\n".join(html) if html else "<li>Sem dados de bancos</li>"
    
    def _format_negotiations(self, negociacoes):
        """Formata a lista de negociações para HTML"""
        if not negociacoes:
            return "<li class='list-group-item'>Sem negociações recentes</li>"
        
        html = []
        for neg in negociacoes:
            if isinstance(neg, dict) and all(key in neg for key in ['data', 'status']):
                data = neg['data'].strftime('%d/%m/%Y') if isinstance(neg['data'], pd.Timestamp) else str(neg['data'])
                status = str(neg['status'])
                html.append(f"<li class='list-group-item'>{data} - {status}</li>")
        return "\n".join(html) if html else "<li class='list-group-item'>Sem negociações recentes</li>"

def main() -> None:
    """Função principal que coordena a execução do programa"""
    try:
        logger.info("Iniciando análise dos arquivos Excel")
        analisador = AnalisadorExcel()
        
        # Processa cada arquivo
        resultados_totais = {}
        for arquivo in analisador.arquivos:
            resultados = analisador.analisar_arquivo(arquivo)
            resultados_totais.update(resultados)
        
        # Gera relatórios
        analisador.gerar_relatorio_json(resultados_totais)
        analisador.gerar_relatorio_html(resultados_totais)
        
        # Gera insights
        insights = analisador.gerar_insights(resultados_totais)
        print("\nInsights Importantes:")
        for insight in insights:
            print(f"- {insight}")
        
        logger.info("Análise concluída com sucesso")
        
    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}")
        raise

if __name__ == "__main__":
    main()