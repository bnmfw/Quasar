from arquivos import JManager, CManager
from runner import HSRunner
from circuitManager import CircMan
from components import Nodo, Entrada, LET
from time import time
from interface import GUIComponents
import os

def relatorio_de_tempo(func):
    def wrapper(*args, **kwargs):
        start = time()
        rv = func(*args, **kwargs)
        end = time()
        tempo = int(end - start)
        dias: int = tempo // 86400
        horas: int = (tempo % 86400) // 3600
        minutos: int = (tempo % 3600) // 60
        if dias: print(f"{dias} dias, ", end='')
        if horas: print(f"{horas} horas, ", end='')
        if minutos: print(f"{minutos} minutos e ", end='')
        print(f"{tempo % 60} segundos de execucao")
        return rv
    return wrapper

class Circuito():
    def __init__(self, nome):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = nome
        self.path = f"circuitos/{nome}/"
        self.arquivo = f"{nome}.cir"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0
        self.atrasoCC: float = 0
        self.LETth: LET = None
        self.__iniciado = False

        # Decodifica do Json caso exista, se nao existir tenta criar a partir do arquivo
        if os.path.exists(f"{self.path}{self.nome}.json"):
            JManager.decodificar(self)
            self.__iniciado = True
        else:
            self.__instanciar_nodos()

    @property
    def iniciado(self):
        return self.__iniciado

    @iniciado.setter
    def iniciado(self, iniciado):
        if not self.__iniciado and iniciado:
            JManager.codificar(self)
        self.__iniciado = iniciado

    def run(self):
        while True:
            self.__tela_principal()

    def __tela_principal(self):
        
        acao = GUIComponents.requisitar_menu(self.nome, self.vdd)
        if not acao:
            CircMan.atualizar_LETths(self, None, None)
        elif acao == 1:
            CManager.escrever_csv_total(self)
        # elif acao == 2:
            # self.analise_manual()
        elif acao == 3:
            self.__analise_monte_carlo_progressiva()
        elif acao == 4:
            self.__analise_monte_carlo()
        elif acao == 5:
            self.__analise_monte_carlo_total()
        elif acao == 6:
            exit()
        else:
            print("Comando invalido")
   
    @relatorio_de_tempo
    def __analise_monte_carlo(self):

        nodo_nome, saida_nome = GUIComponents.requisitar_nodo_e_saida()

        nodo: Nodo = next(nodo for nodo in self.nodos if nodo.nome == nodo_nome)
        saida: Nodo = next(saida for saida in self.saidas if saida.nome == saida_nome)
        
        print("Orientacoes disponiveis: ")
        
        for let_disponivel in nodo.LETs:
            if let_disponivel.saida_nome == saida_nome:
                print(let_disponivel.orientacao, let_disponivel.corrente)
        
        pulso_in, pulso_out = GUIComponents.requisitar_pulsos()
        let: LET = next(let for let in nodo.LETs if let.saida_nome == saida.nome and let.orientacao == [pulso_in, pulso_out])
        
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = let.validacoes[0][indice]
        
        with HSRunner.SET(let):
            num_analises = GUIComponents.requisitar_num_analises()
            faults = HSRunner.run_simple_MC(self.path, self.nome, let.nodo_nome, let.saida_nome, num_analises, pulso_out, self.vdd)
        
        print(f"Proporcao de falhas: {100 * faults/num_analises}%")
        print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_progressiva(self):

        # Configuracao do LETth do circuito no Hspice
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = self.LETth.validacoes[0][indice]
        
        with HSRunner.Inputs(self.vdd, self.entradas), HSRunner.Vdd(self.vdd):
            _, pulso_out = self.LETth.orientacao

            num_analises = GUIComponents.requisitar_num_analises()

            mc_dict: dict = {"analises": [num_analises]}

            step: float = 0.05
            for frac in [round(num*step,2) for num in range(1, int(1/step)+1)]:

                with HSRunner.SET(self.LETth, self.LETth.corrente * frac):

                    falhas: int = HSRunner.run_simple_MC(self.path, self.nome, self.LETth.nodo_nome, self.LETth.saida_nome, num_analises, pulso_out, self.vdd)
                    mc_dict[frac] = [falhas]

            print(mc_dict)
            CManager.tup_dict_to_csv(self.path,f"{self.nome}_mc.csv",mc_dict)

            print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_total(self):
        # Gera as instancias de nmos e pmos da analise MC
        num_analises = GUIComponents.requisitar_num_analises()
        
        print("Gerando instancias MC")
        var: dict = HSRunner.run_MC_var(self.path, self.arquivo, self.nome, num_analises)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        saida: dict = {"indice": ("pmos", "nmos", "nodo", "saida", "corrente", "LETth")}

        print("Encontrando LETth para cada instancia")

        with open("erros.txt", "a") as erro:
            erro.write(f"\nErros do circuito: {self.nome}\n")

        for i in var:
            print(f"index: {i} pmos: {var[i][0]} nmos: {var[i][1]}")
            with HSRunner.MC_Instance(var[i][0], var[i][1]):
                CircMan.get_atrasoCC(self)
                CircMan.atualizar_LETths(self,var[i][0], var[i][1])
                saida[i] = (var[i][0], var[i][1], self.LETth.nodo_nome, self.LETth.saida_nome, self.LETth.corrente, self.LETth.valor)
            if i > num_analises: break

        CManager.tup_dict_to_csv(self.path,f"{self.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

    def __instanciar_nodos(self):
        entradas, saidas = GUIComponents.requisitar_entradas_e_saidas()
        ##### SAIDAS #####
        self.saidas = [Nodo(saida) for saida in saidas]
        ##### ENTRADAS #####
        self.entradas = [Entrada(entrada) for entrada in entradas]
        ##### OUTROS NODOS #####
        self.nodos = [Nodo(nodo) for nodo in HSRunner.get_nodes(self.nome) if "f" not in nodo and "t" not in nodo and nodo not in {"vdd", "gnd"}]

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.cir"
    circuito_teste.vdd = 0.7
