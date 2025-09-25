# Instale as bibliotecas necessárias antes de executar:
# pip install gradio pandas

import gradio as gr
import pandas as pd
from datetime import datetime

# --- 1. SIMULAÇÃO DO BANCO DE DADOS COM PANDAS ---
# Baseado no seu diagrama de classes e na planilha de exemplo.

# Tabela de Funcionários (Simulando a classe Funcionario e Papéis)
funcionarios_data = {
    'id_responsavel': ['AUX-56195840', 'ENF-28585028', 'ENF-96828591', 'ADM-00000001'],
    'nome': ['Denilson Machado Carvalho', 'José Calabreso da Silva', 'Carlinhos Pereira de Jesus', 'Gestor do Sistema'],
    'profissao': ['Auxiliar de almoxarifado', 'Enfermeiro', 'Enfermeiro', 'Administrador']
}
funcionarios_df = pd.DataFrame(funcionarios_data)

locais_hospitalares = [
    "ALMOXARIFADO-CENTRAL-01",
    "ALMOXARIFADO-CENTRAL-02",
    "CME-01",
    "CME-02",
    "CME-03",
]

# Tabela de Instrumentais (Simulando a classe Objeto)
instrumentais_data = {
    'tag_id': ['TAG-BISTURI-001', 'TAG-PINCA-007', 'TAG-TESOURA-003'],
    'nome': ['Bisturi Elétrico Alpha', 'Pinça Anatômica Beta', 'Tesoura Cirúrgica Gamma'],
    'lote': ['LOTE-2024-A', 'LOTE-2024-B', 'LOTE-2023-C'],
    'status_atual': ['Armazenado', 'Em Operação', 'Em esterilização'],
    'localizacao_atual': ['ALMOXARIFADO-CENTRAL-02', 'PS-04', 'CME-03'],
    'responsavel_atual_id': ['AUX-56195840', 'ENF-28585028', 'ENF-28585028']
}
instrumentais_df = pd.DataFrame(instrumentais_data)

# [cite_start]Tabela de Log de Eventos (Exatamente como na sua planilha PDF) [cite: 1]
log_data = {
    'tag_id': ['TAG-PINCA-007', 'TAG-PINCA-007', 'TAG-PINCA-007', 'TAG-PINCA-007', 'TAG-PINCA-007', 'TAG-PINCA-007', 'TAG-PINCA-007', 'TAG-PINCA-007'],
    'Responsável': ["Denilson Machado Carvalho", "José Calabreso da Silva", "José Calabreso da Silva", "José Calabreso da Silva", "José Calabreso da Silva", "Carlinhos Pereira de Jesus", "Carlinhos Pereira de Jesus", "Denilson Machado Carvalho"],
    'ID do responsável': ["AUX-56195840", "ENF-28585028", "ENF-28585028", "ENF-28585028", "ENF-28585028", "ENF-96828591", "ENF-96828592", "AUX-56195840"],
    'Profissão': ["Auxiliar de almoxarifado", "Enfermeiro", "Enfermeiro", "Enfermeiro", "Enfermeiro", "Enfermeiro", "Enfermeiro", "Auxiliar de almoxarifado"],
    'ID da sala': ["ALMOXARIFADO-CENTRAL-02", "ALMOXARIFADO-CENTRAL-02", "PS-04", "PS-04", "CME-03", "CME-03", "ALMOXARIFADO-CENTRAL-02", "ALMOXARIFADO-CENTRAL-02"],
    'ID da antena': [None, None, "ANT-08", "ANT-08", "ANT-10", None, "ANT-05", None],
    'ID do leitor': [None, None, "LEITOR-06", "LEITOR-06", "LEITOR-13", None, "LEITOR-02", None],
    'Data e hora': ["2025-03-28T12:07:14Z", "2025-03-30T15:10:47Z", "2025-03-30T15:13:32Z", "2025-03-30T17:40:19Z", "2025-03-30T17:45:54Z", "2025-03-30T18:52:41Z", "2025-03-30T19:04:47Z", "2025-03-30T19:15:18Z"],
    'Status': ["Armazenado", "Saída", "Operação", "Movimentação", "Em esterilização", "Esterilizado", "Movimentação", "Armazenado"]
}
log_df = pd.DataFrame(log_data)
log_df['Data e hora'] = pd.to_datetime(log_df['Data e hora'])

# Simulação de solicitações pendentes
solicitacoes_data = {
    'id_solicitacao': [101, 102],
    'solicitante_nome': ['José Calabreso da Silva', 'Dr. House'],
    'tag_id_solicitado': ['TAG-BISTURI-001', 'TAG-TESOURA-003'],
    'status': ['Pendente', 'Pendente']
}
solicitacoes_df = pd.DataFrame(solicitacoes_data)


# --- 2. FUNÇÕES DE LÓGICA DE NEGÓCIO (Backend do Protótipo) ---

def registrar_evento(tag_id, novo_status, responsavel_id, sala_id):
    """Função central para registrar qualquer movimentação no sistema."""
    global log_df, instrumentais_df

    # Pega informações do funcionário
    info_responsavel = funcionarios_df[funcionarios_df['id_responsavel'] == responsavel_id].iloc[0]

    novo_evento = {
        'tag_id': tag_id,
        'Responsável': info_responsavel['nome'],
        'ID do responsável': responsavel_id,
        'Profissão': info_responsavel['profissao'],
        'ID da sala': sala_id,
        'ID da antena': 'N/A (Manual)',
        'ID do leitor': 'N/A (Manual)',
        'Data e hora': datetime.now(),
        'Status': novo_status
    }
    log_df = pd.concat([log_df, pd.DataFrame([novo_evento])], ignore_index=True)

    # Atualiza o status atual do instrumental
    instrumentais_df.loc[instrumentais_df['tag_id'] == tag_id, 'status_atual'] = novo_status
    instrumentais_df.loc[instrumentais_df['tag_id'] == tag_id, 'localizacao_atual'] = sala_id
    instrumentais_df.loc[instrumentais_df['tag_id'] == tag_id, 'responsavel_atual_id'] = responsavel_id

    return f"Evento '{novo_status}' para o item {tag_id} registrado com sucesso."


def get_dashboard_data():
    em_uso = instrumentais_df[instrumentais_df['status_atual'] == 'Em Operação'].shape[0]
    em_esterilizacao = instrumentais_df[instrumentais_df['status_atual'] == 'Em esterilização'].shape[0]
    armazenados = instrumentais_df[instrumentais_df['status_atual'] == 'Armazenado'].shape[0]
    log_recente = log_df.sort_values(by='Data e hora', ascending=False).head(5)
    return em_uso, em_esterilizacao, armazenados, log_recente

def autorizar_saida(id_solicitacao, responsavel_id_auxiliar):
    global solicitacoes_df
    if id_solicitacao is None:
        return "Selecione uma solicitação.", solicitacoes_df[solicitacoes_df['status']=='Pendente']
        
    solicitacao = solicitacoes_df[solicitacoes_df['id_solicitacao'] == id_solicitacao].iloc[0]
    tag_id = solicitacao['tag_id_solicitado']
    
    # Atualiza status da solicitação
    solicitacoes_df.loc[solicitacoes_df['id_solicitacao'] == id_solicitacao, 'status'] = 'Aprovada'
    
    # Registra o evento de saída
    msg = registrar_evento(tag_id, "Saída", responsavel_id_auxiliar, "ALMOXARIFADO-CENTRAL-02")
    
    solicitacoes_pendentes = solicitacoes_df[solicitacoes_df['status']=='Pendente']
    return f"Solicitação {id_solicitacao} aprovada. {msg}", solicitacoes_pendentes

def get_historico(tag_id):
    if tag_id is None:
        return pd.DataFrame(), "Selecione um item para ver o histórico."
    historico = log_df[log_df['tag_id'] == tag_id].sort_values(by='Data e hora', ascending=False)
    status_atual = instrumentais_df[instrumentais_df['tag_id'] == tag_id].iloc[0]
    info_status = f"""
    **Status Atual:** {status_atual['status_atual']}
    **Localização:** {status_atual['localizacao_atual']}
    **Responsável:** {status_atual['responsavel_atual_id']}
    """
    return historico, info_status

def confirmar_etapa_manual(tag_id, novo_status, responsavel_id_enfermeiro, local):
    if tag_id is None or novo_status is None or local is None:
        return "Por favor, preencha todos os campos."
    
    msg = registrar_evento(tag_id, novo_status, responsavel_id_enfermeiro, local)
    return msg

# --- 3. CONSTRUÇÃO DA INTERFACE GRÁFICA COM GRADIO ---

with gr.Blocks(theme=gr.themes.Soft(), title="AssetGuard - Protótipo") as demo:
    
    # Simula um "login" para contextualizar as ações
    gr.Markdown("# Protótipo AssetGuard - Monitoramento de Ativos")
    usuario_logado_id = gr.Dropdown(
        label="Simular Login Como:",
        choices=list(funcionarios_df['id_responsavel']),
        value='ADM-00000001'
    )
    
    with gr.Tabs():
        # --- TELA 1: DASHBOARD ---
        with gr.TabItem("Dashboard"):
            with gr.Row():
                em_uso_box = gr.Number(label="Instrumentais em Uso")
                em_esterilizacao_box = gr.Number(label="Em Esterilização")
                armazenados_box = gr.Number(label="Armazenados")
            gr.Markdown("### Últimas Movimentações")
            log_recente_df = gr.DataFrame(column_widths=["10%", "18%", "12%", "15%", "15%", "10%", "10%", "17%", "10%"])
            
            demo.load(get_dashboard_data, outputs=[em_uso_box, em_esterilizacao_box, armazenados_box, log_recente_df])

        # --- TELA 2: GESTÃO DE SOLICITAÇÕES (ALMOXARIFADO) ---
        with gr.TabItem("Gestão de Solicitações (Almoxarifado)"):
            gr.Markdown("## Autorizar Saída de Instrumentais")
            solicitacoes_pendentes_df = gr.DataFrame(solicitacoes_df[solicitacoes_df['status']=='Pendente'])
            
            with gr.Row():
                solicitacao_selecionada = gr.Dropdown(
                    label="Selecione a Solicitação para Aprovar",
                    choices=list(solicitacoes_df[solicitacoes_df['status']=='Pendente']['id_solicitacao'])
                )
                autorizar_btn = gr.Button("Autorizar e Registrar Saída", variant="primary")
            
            msg_autorizacao = gr.Textbox(label="Status da Operação")
            autorizar_btn.click(
                autorizar_saida,
                inputs=[solicitacao_selecionada, usuario_logado_id],
                outputs=[msg_autorizacao, solicitacoes_pendentes_df]
            )

        # --- TELA 3: RASTREAMENTO E HISTÓRICO DO ATIVO ---
        with gr.TabItem("Rastreamento de Ativo (Auditoria)"):
            gr.Markdown("## Trilha de Auditoria do Instrumental")
            item_selecionado = gr.Dropdown(
                label="Selecione o Instrumental (pela TAG ID)",
                choices=list(instrumentais_df['tag_id'])
            )
            status_atual_info = gr.Markdown()
            gr.Markdown("### Histórico Completo de Eventos")
            historico_df = gr.DataFrame(column_widths=["10%", "18%", "12%", "15%", "15%", "10%", "10%", "17%", "10%"])
            
            item_selecionado.change(
                get_historico,
                inputs=item_selecionado,
                outputs=[historico_df, status_atual_info]
            )
        
        # --- TELA 4: CONFIRMAÇÃO DE ETAPAS (CME / ENFERMAGEM) ---
        with gr.TabItem("Confirmação de Etapas (Enfermagem)"):
            gr.Markdown("## Registrar Evento Manualmente")
            gr.Markdown("Use esta tela para registrar eventos importantes como a conclusão da esterilização no CME.")
            
            with gr.Row():
                item_para_atualizar = gr.Dropdown(label="Instrumental (TAG ID)", choices=list(instrumentais_df['tag_id']))
                novo_status_escolha = gr.Dropdown(label="Novo Status", choices=["Esterilizado", "Devolvido ao Almoxarifado", "Em Manutenção"])
                local_evento = gr.Dropdown(label="Local do Evento", choices=locais_hospitalares)
            
            confirmar_etapa_btn = gr.Button("Confirmar Etapa", variant="primary")
            msg_confirmacao_etapa = gr.Textbox(label="Status da Operação")
            
            confirmar_etapa_btn.click(
                confirmar_etapa_manual,
                inputs=[item_para_atualizar, novo_status_escolha, usuario_logado_id, local_evento],
                outputs=[msg_confirmacao_etapa]
            )

if __name__ == "__main__":
    demo.launch()