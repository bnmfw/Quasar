from utils.arquivos import CManager, JManager
from utils.circuitManager import CircuitManager
from utils.mcManager import MCManager
from utils.letFinder import LetFinder
from utils.circuito import Circuito
from utils.components import LET
from utils.spiceInterface import HSRunner
from utils.matematica import Time

barra_comprida = "---------------------------"

delay = False

class InterfaceComponentes:

    def __init__(self) -> None:
        pass

    def requisitar_circuito(self) -> str:
        return input(barra_comprida+"\nEscolha o circuito: ")

    def requisitar_vdd(self) -> float:
        return float(input(f"{barra_comprida}\nVdd da simulacao: "))

    def requisitar_menu(self, circuito_nome: str, vdd: float) -> int:
        return int(input(f"{barra_comprida}\n"
                     f"Trabalhando com o {circuito_nome} em {vdd} volts\n"
                     "O que deseja fazer?\n"
                     "0. Atualizar LETs\n"
                     "1. Gerar CSV de LETs\n"
                     "2. Analisar LET Unico\n"
                     "3. Analise Monte Carlo\n"
                     "4. Analise Monte Carlo Unica\n"
                     "5. Analise Monte Carlo Total\n"
                     "6. Sair\n"
                     "Resposta: "))

    def requisitar_num_analises(self) -> int:
        return int(input(f"{barra_comprida}\nQuantidade de analises: "))

    def requisitar_entradas_e_saidas(self) -> tuple:
        return (input("entradas: ").split() , input("saidas: ").split())

    def requisitar_nodo_e_saida(self) -> list:
        return input("nodo e saida do LET: ").split()

    def requisitar_pulsos(self) -> list:
        return input("pulsos na entrada e saida do LET: ").split()

    def requisitar_cadastro(self) -> bool:
        cadastro = None
        while not cadastro in {"y","n"}:
            cadastro: bool = input(f"{barra_comprida}\nCadastro do circuito nao encontrado\nDeseja gera-lo? (y/n) ")
        return cadastro == "y"

class GUI:
    def __init__(self) -> None:
        self.circuito = None
        self.circ_man = None
        HSRunner.default(0.7)
        self.__tela_inicial()
        while True:
            self.__tela_principal()

    def __tela_inicial(self):
        nome = GUIComponents.requisitar_circuito()
        self.circuito = Circuito(nome)
        self.circuito.vdd = GUIComponents.requisitar_vdd()
        self.circ_man = CircuitManager(self.circuito)
        with HSRunner.Vdd(self.circuito.vdd):
            if delay: self.circ_man.get_atrasoCC()
            if not self.circuito.iniciado:
                self.circ_man.determinar_LETths(delay=delay)
                self.circuito.iniciado = True
            # else:
            #     self.circ_man.atualizar_LETths()
    
    def __tela_principal(self):
        acao = GUIComponents.requisitar_menu(self.circuito.nome, self.circuito.vdd)
        if not acao:
            with Time():
                if delay: self.circ_man.get_atrasoCC()
                self.circ_man.atualizar_LETths(delay=delay)
            JManager.codificar(self.circuito)
        elif acao == 1:
            CManager.escrever_csv_total(self.circuito)
        elif acao == 2:
            LetFinder(self.circuito, self.circuito.path_to_circuits True).definir_corrente(LET(None))
        elif acao == 3:
            self.circuito.analise_monte_carlo_progressiva()
        elif acao == 4:
            self.circuito.analise_monte_carlo()
        elif acao == 5:
            MCManager(self.circuito).analise_monte_carlo_total(delay=delay)
        elif acao == 6:
            exit()
        else:
            print("Comando invalido")

    def _get_pulse_config(self):
        nodo_nome, saida_nome = GUIComponents.requisitar_nodo_e_saida()


GUIComponents = InterfaceComponentes()
# tela = GUI()