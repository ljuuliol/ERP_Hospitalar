import datetime
import pandas as pd
import gradio as gr


class ServidorAssetGuard:
    def __init__(self):
        self.db = {
            'ativos': {},
            'usuarios': {
                'ana_instrumentadora': {'nome': 'Ana Souza', 'papel': 'Instrumentador'},
                'joao_auditor': {'nome': 'João Lima', 'papel': 'Auditor'}
            },
            'log_auditoria': []
        }

    def _registrar_log_auditoria(self, usuario_id, acao, detalhes):
        log_entry = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'usuario_id': usuario_id,
            'acao': acao,
            'detalhes': detalhes
        }
        self.db['log_auditoria'].append(log_entry)

    def cadastrar_ativo(self, rfid_tag, descricao, usuario_id='ana_instrumentadora'):
        if rfid_tag in self.db['ativos']:
            return
        self.db['ativos'][rfid_tag] = {
            'descricao': descricao,
            'local': 'Central de Esterilização',
            'status': 'Esterilizado ✅',
            'ultimo_movimento_por': usuario_id
        }
        self._registrar_log_auditoria(usuario_id, 'CADASTRO', f"Ativo '{rfid_tag}' criado (Esterilizado ✅).")

    def movimentar_ativo_servidor(self, rfid_tag, novo_local, usuario_id):
        if rfid_tag not in self.db['ativos']:
            return
        ativo = self.db['ativos'][rfid_tag]
        local_antigo = ativo['local']
        ativo['local'] = novo_local
        ativo['ultimo_movimento_por'] = usuario_id

        # --- Atualiza o status conforme o local ---
        if novo_local == "Central de Esterilização":
            ativo['status'] = "Esterilizado ✅"
        elif "Sala de Cirurgia" in novo_local:
            ativo['status'] = "Em Uso ⚠️"
        elif novo_local == "Sala de Pós-Operatório":
            ativo['status'] = "Aguardando Esterilização 🔄"
        else:
            ativo['status'] = "Indefinido ❓"

        detalhes = f"Ativo '{rfid_tag}' movido de '{local_antigo}' para '{novo_local}' (status: {ativo['status']})."
        self._registrar_log_auditoria(usuario_id, 'MOVIMENTAÇÃO', detalhes)

    def consultar_ativos_dataframe(self):
        if not self.db['ativos']:
            return pd.DataFrame(columns=['RFID Tag', 'Descrição', 'Local', 'Status'])

        df = pd.DataFrame.from_dict(self.db['ativos'], orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'RFID Tag', 'descricao': 'Descrição',
                           'local': 'Local', 'status': 'Status'}, inplace=True)
        return df[['RFID Tag', 'Descrição', 'Local', 'Status']]

    def consultar_auditoria(self, rfid_tag):
        logs_filtrados = [log for log in self.db['log_auditoria'] if rfid_tag in log['detalhes']]
        if not logs_filtrados:
            return f"Nenhum registro de auditoria para a tag: {rfid_tag}"

        output_str = f"--- 📖 TRILHA DE AUDITORIA PARA O ATIVO: {rfid_tag} ---\n"
        for log in logs_filtrados:
            output_str += f"- [{log['timestamp']}] {log['acao']} por '{log['usuario_id']}': {log['detalhes']}\n"
        return output_str


# --- LÓGICA DO LEITOR PORTÁTIL ---
class LeitorPortatil:
    def __init__(self, usuario_id: str):
        self.usuario_logado = usuario_id
        self.conectado = True
        self.fila_sincronizacao = []

    def desconectar(self):
        self.conectado = False

    def conectar(self):
        self.conectado = True


# --- FUNÇÕES AUXILIARES ---
def criar_estado_inicial():
    servidor_hospital = ServidorAssetGuard()
    servidor_hospital.cadastrar_ativo('TAG-001', 'Kit Cirurgia Cardíaca')
    servidor_hospital.cadastrar_ativo('TAG-002', 'Kit Ortopedia Geral')
    servidor_hospital.cadastrar_ativo('TAG-003', 'Kit Neurocirurgia')
    leitor_da_ana = LeitorPortatil('ana_instrumentadora')
    return servidor_hospital, leitor_da_ana


def _atualizar_info_leitor(leitor):
    status = "ONLINE ✅" if leitor.conectado else "OFFLINE ⚠️"
    fila = len(leitor.fila_sincronizacao)
    return f"Status: {status}<br>Ações na fila: {fila}"


# --- FUNÇÕES DE LÓGICA (BOTÕES) ---
def funcao_movimentar(servidor, leitor, rfid_tag, novo_local):
    if leitor.conectado:
        servidor.movimentar_ativo_servidor(rfid_tag, novo_local, leitor.usuario_logado)
        mensagem = "<span style='color:green;'>✅ Ativo movimentado com sucesso.</span>"
    else:
        acao_offline = {
            'funcao': 'movimentar_ativo_servidor',
            'args': [rfid_tag, novo_local, leitor.usuario_logado]
        }
        leitor.fila_sincronizacao.append(acao_offline)
        mensagem = "<span style='color:orange;'>⚠️ Leitor OFFLINE: movimentação enfileirada para sincronização.</span>"

    return servidor, leitor, servidor.consultar_ativos_dataframe(), _atualizar_info_leitor(leitor), mensagem


def funcao_ficar_offline(leitor):
    leitor.desconectar()
    return leitor, _atualizar_info_leitor(leitor), "<span style='color:orange;'>🔌 Leitor ficou OFFLINE.</span>"


def funcao_ficar_online_e_sincronizar(servidor, leitor):
    leitor.conectar()
    mensagem = "<span style='color:blue;'>🛰️ Leitor voltou ONLINE.</span>"
    if leitor.fila_sincronizacao:
        for acao in leitor.fila_sincronizacao:
            funcao_nome = acao['funcao']
            args = acao['args']
            getattr(servidor, funcao_nome)(*args)
        leitor.fila_sincronizacao.clear()
        mensagem += " <span style='color:green;'>🔄 Ações pendentes sincronizadas com sucesso!</span>"

    return servidor, leitor, servidor.consultar_ativos_dataframe(), _atualizar_info_leitor(leitor), mensagem


def funcao_consultar_auditoria(servidor, rfid_tag):
    return servidor.consultar_auditoria(rfid_tag)


# --- INTERFACE GRADIO ---
with gr.Blocks(theme=gr.themes.Soft(), title="Simulador AssetGuard") as demo:
    servidor_inicial, leitor_inicial = criar_estado_inicial()
    servidor_state = gr.State(servidor_inicial)
    leitor_state = gr.State(leitor_inicial)

    gr.Markdown("## Monitoramento de Ativos Hospitalares")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Painel de Controle")
            rfid_dropdown = gr.Dropdown(choices=['TAG-001', 'TAG-002', 'TAG-003'],
                                        label="Selecione o Ativo (RFID Tag)", value='TAG-001')
            local_dropdown = gr.Dropdown(choices=['Sala de Cirurgia 01', 'Sala de Cirurgia 02',
                                                  'Sala de Pós-Operatório', 'Central de Esterilização'],
                                         label="Selecione o Novo Local", value='Sala de Cirurgia 01')
            btn_movimentar = gr.Button("🚀 Movimentar Ativo", variant="primary")
            gr.Markdown("---")
            with gr.Row():
                btn_offline = gr.Button("🔌 Ficar Offline")
                btn_online = gr.Button("🛰️ Ficar Online e Sincronizar")
            gr.Markdown("---")
            btn_auditoria = gr.Button("📖 Consultar Auditoria do Ativo Selecionado")

        with gr.Column(scale=2):
            gr.Markdown("### Status do Sistema")
            info_leitor = gr.HTML(value=_atualizar_info_leitor(leitor_inicial))
            mensagem_alerta = gr.HTML(value="<span style='color:gray;'>Pronto para uso.</span>")
            gr.Markdown("### Posição Atual dos Ativos (Visão do Servidor)")
            tabela_ativos = gr.DataFrame(value=servidor_inicial.consultar_ativos_dataframe(),
                                         label="Banco de Dados de Ativos", interactive=False)
            log_auditoria = gr.Textbox(label="Trilha de Auditoria", lines=10,
                                       interactive=False,
                                       placeholder="Clique em 'Consultar Auditoria' para ver o histórico de um ativo aqui.")

    # Ligações dos botões
    btn_movimentar.click(fn=funcao_movimentar,
                         inputs=[servidor_state, leitor_state, rfid_dropdown, local_dropdown],
                         outputs=[servidor_state, leitor_state, tabela_ativos, info_leitor, mensagem_alerta])

    btn_offline.click(fn=funcao_ficar_offline,
                      inputs=[leitor_state],
                      outputs=[leitor_state, info_leitor, mensagem_alerta])

    btn_online.click(fn=funcao_ficar_online_e_sincronizar,
                     inputs=[servidor_state, leitor_state],
                     outputs=[servidor_state, leitor_state, tabela_ativos, info_leitor, mensagem_alerta])

    btn_auditoria.click(fn=funcao_consultar_auditoria,
                        inputs=[servidor_state, rfid_dropdown],
                        outputs=[log_auditoria])

if __name__ == "__main__":
    demo.launch(show_api=False)
