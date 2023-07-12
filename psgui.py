import PySimpleGUI as sg
from tkinter import TclError, Tk
from utils.runner import HSRunner
import os

# Testa para ver se o tkinter esta funcionando
sg.theme('DarkAmber')

psgui_is_working = None
gui_error = None
try:
    janela_teste = Tk()
    janela_teste.destroy()
except TclError as erro:
    gui_error = erro
    psgui_is_working = False
else:
    psgui_is_working = True

def progress_report(progress: int):
    print(f"progress report: {progress}")

class PSGUI:
    class SimpleInputScreen:
        def __init__(self, label: str, tipo: type, tooltip: str = None):
            self.warning_text = sg.Text("")
            self.tipo = tipo
            layout = [[sg.Text(label),sg.InputText(tooltip=tooltip)],
                    [self.warning_text],
                    [sg.Button("Ok")]]
            
            self.janela = sg.Window("Quasar", layout)

        def run(self):
            ret: float = None

            while True:
                event, values = self.janela.read()

                if event == "Ok":
                    
                    # Tenta ler vdd
                    try:
                        ret = self.tipo(values[0].strip())
                    except ValueError:
                        self.warning_text.update("Entrada inadequada")
                        continue
                    self.janela.close()
                    return ret

    class SimpleProgressBar:
        def __init__(self, label: str) -> None:
            self.max  = 1000
            self.progresso = sg.ProgressBar(self.max, orientation='h', expand_x=True, size=(20, 20))
            layout = [
                [sg.Text(label)],
                [self.progresso],
                ]
            self.window = sg.Window('Progress Bar', layout, size=(715, 100), finalize=True)

        def progress(self, progress: float):
            self.progresso.update(current_count=int(progress*self.max))
            if int(progress) >= 1:
                self.window.close()

    # Tela inicial onde um circuito é escolhido
    def tela_inicial(self):
        # Inputs do usuario que serao retornados
        next_screen = None
        inputs = {"vdd": None, "circ": None, "cadastro": None}

        # Retorna uma lista de circuitos disponiveis no diretorio "circuitos"
        def get_circuits():
            not_circuits = {"dis", "include", "output.txt", "include.cir"}
            available_circuits = [circ for circ in os.listdir("circuitos") if not circ in not_circuits]
            available_circuits.sort()
            return available_circuits

        # All the stuff inside your window.
        file_exists = sg.Text(" ", justification="center")
        warning_text = sg.Text(" ", justification="center")
        start_layout = [  [sg.Text("Quasar", justification="center")],
                    [sg.Text("Escolha um Circuito"), sg.Combo(get_circuits(), enable_events=True)],
                    [file_exists],
                    [sg.Text("Vdd (V)"),sg.InputText(tooltip=" Use virgula como separador decimal ")],
                    [warning_text],
                    [sg.Button("Ok"), sg.Button("Sair")]]
        # Cria a Janela
        start_window = sg.Window("Quasar", start_layout)


        # Loop principal
        while True:
            event, values = start_window.read()
            print(event, values)
            
            # Escolhe um circuito
            if event == 0:
                inputs["circ"] = values[0]
                if os.path.exists(f"circuitos/{inputs['circ']}/{inputs['circ']}.json"):
                    file_exists.update("Cadastro encontrado")
                    inputs["cadastro"] = True
                else:
                    file_exists.update("Cadastro nao encontrado")
                    inputs["cadastro"] = False

            # Fecha a aba
            if event == sg.WIN_CLOSED or event == 'Sair':
                next_screen = None
                start_window.close()
                break
            
            # Seleciona de fato o circuito
            if event == "Ok":
                # Ok sem circuito selecionado
                if inputs["circ"] is None:
                    file_exists.update("Circuito nao selecionado")
                    continue

                # Ok com vdd ruim
                try:
                    inputs["vdd"] = float(values[1].strip())
                except ValueError:
                    warning_text.update("Vdd inadequado")
                    continue
                # Fim
                start_window.close()
                next_screen = "main" if inputs["cadastro"] else "cadastro"
                break
                
        # Retorno da tela
        return next_screen, inputs

    # Tela de cadastro do circuito
    def tela_cadastro(self, circuito_nome):
        next_screen = "main"
        inputs = {"nodos": None, "entradas": None, "saidas": None}

        # Barra de Progresso
        self.progress_max = 1000
        self.progresso = sg.ProgressBar(self.progress_max, orientation='h', expand_x=True, size=(10,10))
        def progress(progress: float):
            self.progresso.update(current_count=int(progress*self.progress_max))

        # Carrega os nodos disponiveis
        nodos = [nodo for nodo in HSRunner.get_nodes(circuito_nome)]
        nodos.sort()
        inputs["nodos"] = nodos
        nodo_dict = {index: nodo for index, nodo in enumerate([None]+nodos)}

        # Cria um frame com todos os nodos como opcao
        output_layout = []
        current_row = []
        columns = 5
        for i, nodo in enumerate(nodos):
            current_row.append(sg.CBox(nodo, default = False))
            if i % columns == columns-1 or i == len(nodos) - 1:
                output_layout.append(current_row)
                current_row = []
        output_frame = sg.Frame(title="Saidas", layout=output_layout)
        
        warning_text = sg.Text("")
        layout = [[sg.Text("Cadastre o circuito")],
                  [sg.Text("Entradas"), sg.InputText(tooltip="Nomes separados por virgulas")],
                  [output_frame],
                  [warning_text],
                  [sg.Button("Ok")],
                  [self.progresso]
                  ]

        janela = sg.Window("Quasar", layout)

        # Loop principal da tela
        while True:
            event, values = janela.read()
            
            # Retorna as entradas e saidas cadastradas
            if event == "Ok":
                
                inputs["entradas"] = [nodo.strip() for nodo in values[0].split(",")]
                inputs["saidas"] = [nodo for id, nodo in nodo_dict.items() if values[id] is True]
                
                if inputs["entradas"] == [''] and inputs["saidas"] == []:
                    warning_text.update("Deve haver pelo menos uma entrada e saida")
                    continue
                elif inputs["entradas"] == ['']:
                    warning_text.update("Deve haver pelo menos uma entrada")
                    continue
                elif inputs["saidas"] == []:
                    warning_text.update("Deve haver pelo menos uma saida")
                    continue
                
                # Cria o circuito
                break      
        
        janela.close()
        return next_screen, inputs
        
    # Tela principal
    def tela_principal(self, circuito):
        inputs = {"acao": None}
        layout = [[sg.Text(f"Circuito {circuito.nome} operando em {circuito.vdd}V")],
                  [sg.Button("Atualizar LETs do circuito")],
                  [sg.Button("Gerar CSV com LETs do circuito")],
                  [sg.Button("Analise Monte Carlo do LETth")],
                  [sg.Button("Sair")]]
        
        janela = sg.Window("Quasar", layout)

        while True:
            event, values = janela.read()
            janela.close()

            # Encerra o Quasar
            if event == "Sair":
                return None, inputs
            
            # Atualiza os LETs do circuito
            if event == "Atualizar LETs do circuito":
                inputs["acao"] = "atualizar"
                return "main", inputs

            # Escreve um CSV com os LETs do circuito
            elif event == "Gerar CSV com LETs do circuito":
                inputs["acao"] = "csv"
                return "main", inputs

            # Analise Monte Carlo
            elif event == "Analise Monte Carlo do LETth":
                return "mc", inputs

    # Tela backup
    def tela_mc(self, circuito):
        next_screen = "main"
        inputs = {"progress": None, "n_sim": None, "continue": None, "window": None}

        ha_backup = os.path.exists(f"circuitos/{circuito.nome}/MC_jobs.json")
        
        self.progress_max = 1000
        self.progresso = sg.ProgressBar(self.progress_max, orientation='h', expand_x=True, size=(10,10))

        def progress(progress: float):
            self.progresso.update(current_count=int(progress*self.progress_max))

        iniciar = sg.Button("Iniciar")
        warning_text = sg.Text("")

        layout_bc = [[sg.Text("Existe uma simulacao Monte Carlo em andamento")],
                     [sg.Text("Se deseja iniciar uma nova simulação Insira o numero de simulacoes")],
                     [sg.Text("Numero de Simulacoes:")],
                     [sg.InputText()],
                     [warning_text],
                     [iniciar, sg.Button("Continuar")],
                     [self.progresso]
                     ]
        
        layout_nbc = [[sg.Text("Quantidade de analises a analisar:")],
                      [sg.InputText()],
                      [warning_text],
                      [iniciar],
                      [self.progresso]
                      ]

        layout = layout_bc if ha_backup else layout_nbc

        # Cria a Janela
        janela = sg.Window("Quasar", layout)
        inputs["window"] = janela
        inputs["progress"] = progress

        # Loop de Escolha
        n_simu = None
        while True:
            event, values = janela.read()
            inputs["continue"] = event == "Continuar"

            # Nova simulacao pra rodar do 0
            if event == "Iniciar":

                # Tenta ler o numero de simulacoes
                try:
                    inputs["nsim"] = int(values[0].strip())
                except ValueError:
                    warning_text.update("Numero de simulacoes indadequado")
                    continue
                warning_text.update("Realizando as simulacoes...")
                break

            # Continuar simulacao ja existente
            if event == "Continuar":
                warning_text.update("Realizando as simulacoes...")
                break
        return next_screen, inputs