from arquivos import alternar_combinacao, JManager, CManager
from runner import HSRunner
from matematica import bin2list
from circuitManager import CircMan
from components import Nodo, Entrada, LET
from time import time
from interface import UserInterface
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
    def __init__(self):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = "nome"
        self.path = "circuitos/nome/"
        self.arquivo = "nome.cir"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0
        self.atrasoCC: float = 0
        self.LETth: LET = None

        ##### RELATORIO DO CIRCUITO #####
        self.sets_validos = []
        self.sets_invalidos = []

    def run(self):
        self.__tela_inicial()
        while True:
            self.__tela_principal()

    def __tela_inicial(self):
        # Escolha de dados do circuito
        circuito = UserInterface.requisitar_circuito()
        self.nome: str = circuito
        self.path: str = f"circuitos/{circuito}/"
        self.arquivo: str = f"{circuito}.cir"
        self.vdd = UserInterface.requisitar_vdd()
        HSRunner.default(self.vdd)

        if os.path.exists(f"{self.path}{circuito}.json"):
            JManager.decodificar(self)
            self.__get_atrasoCC()
            self.__atualizar_LETths(None, None)

        else:
            cadastro = UserInterface.requisitar_cadastro()
            if cadastro:
                self.__instanciar_nodos()
                self.__get_atrasoCC()
                self.__determinar_LETths()
                JManager.codificar(self)
            else:
                exit()

        ### INICIALIZACAO DO LETth DO CIRCUITO ###
        menor = 9999999999999
        for nodo in self.nodos:
            if nodo.LETth.corrente < menor:
                menor = nodo.LETth.corrente
                self.LETth = nodo.LETth

    def __tela_principal(self):
        
        acao = UserInterface.requisitar_menu(self.nome, self.vdd)
        if not acao:
            self.__atualizar_LETths(None, None)
        elif acao == 1:
            CManager.escrever_csv_total(self)
        elif acao == 2:
            self.analise_manual()
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
        let: LET = self.__configurar_LET()
        _, pulso_out = alternar_combinacao(let.orientacao)

        with HSRunner.SET(let):
            num_analises = UserInterface.requisitar_num_analises()
            faults = HSRunner.run_simple_MC(self.path, self.nome, let.nodo_nome, let.saida_nome, num_analises, pulso_out, self.vdd)
        
        print(f"Proporcao de falhas: {100 * faults/num_analises}%")
        print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_progressiva(self):

        # Configuracao do LETth do circuito no Hspice
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = self.LETth.validacoes[0][indice]
        HSRunner.configure_input(self.vdd, self.entradas)
        _, pulso_out = alternar_combinacao(self.LETth.orientacao)

        num_analises = UserInterface.requisitar_num_analises()

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
        num_analises = UserInterface.requisitar_num_analises()
        
        print("Gerando instancias MC")
        var: dict = HSRunner.run_MC_var(self.path, self.arquivo, self.nome, num_analises)

        saida: dict = {"indice": ("pmos", "nmos", "nodo", "saida", "corrente", "LETth")}

        print("Encontrando LETth para cada instancia")

        with open("erros.txt", "a") as erro:
            erro.write(f"\nErros do circuito: {self.nome}\n")
                

        for i in var:
            print(f"index: {i} pmos: {var[i][0]} nmos: {var[i][1]}")
            with HSRunner.MC_Instance(var[i][0], var[i][1]):
                self.__atualizar_LETths(var[i][0], var[i][1])
                saida[i] = (var[i][0], var[i][1], self.LETth.nodo_nome, self.LETth.saida_nome, self.LETth.corrente, self.LETth.valor)
            if i > num_analises: break

        CManager.tup_dict_to_csv(self.path,f"{self.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

    @relatorio_de_tempo
    def __get_atrasoCC(self):
        self.__verificar_tensoes()
        self.atrasoCC: float = 0
        simulacoes: int = 0

        # Todas as entradas em todas as saidas com todas as combinacoes
        for entrada_analisada in self.entradas:
            for saida in self.saidas:
                for i in range(2 ** (len(self.entradas) - 1)):

                    # Atribui o Sinal das Entradas que Nao Estao em Analise
                    sinais_entrada = bin2list(i, len(self.entradas)-1)
                    index = 0
                    for entrada in self.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = sinais_entrada[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # Etapa de medicao de atraso
                    atraso: float = HSRunner.run_delay(self.path, self.arquivo, entrada_analisada.nome, saida.nome, self.vdd, self.entradas)

                    simulacoes += 1

                    if atraso > self.atrasoCC:
                        self.atrasoCC = atraso
        # if self.atrasoCC == 0: exit()
        print(f"Atraso CC do arquivo: {self.atrasoCC} simulacoes: {simulacoes}")

    def __instanciar_nodos(self):
        ##### SAIDAS #####
        entradas, saidas = UserInterface.requisitar_entradas_e_saidas()
        self.saidas = [Nodo(saida) for saida in saidas]

        ##### ENTRADAS #####
        self.entradas = [Entrada(entrada) for entrada in entradas]

        ##### OUTROS NODOS #####
        self.nodos = [Nodo(nodo) for nodo in HSRunner.get_nodes(self.nome) if "f" not in nodo and nodo not in {"vdd", "gnd"}]

    def __configurar_LET(self) -> str:
        # Configuracao de pulso
        nodo_nome, saida_nome = UserInterface.requisitar_nodo_e_saida()
        nodo: Nodo = next(nodo for nodo in self.nodos if nodo.nome == nodo_nome)
        saida: Nodo = next(saida for saida in self.saidas if saida.nome == saida_nome)
        
        print("Orientacoes disponiveis: ")
        
        for let_disponivel in nodo.LETs:
            if let_disponivel.saida_nome == saida_nome:
                print(alternar_combinacao(let_disponivel.orientacao), let_disponivel.corrente)
        
        pulso_in, pulso_out = UserInterface.requisitar_pulsos()
        let: LET = next(let for let in nodo.LETs if let.saida_nome == saida.nome and let.orientacao == alternar_combinacao([pulso_in, pulso_out]))
        
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = let.validacoes[0][indice]

        return let # Eu uso isso na analise monte carlo, se tirar vai dar pau

    @relatorio_de_tempo
    def __determinar_LETths(self):
        for nodo in self.nodos:
            nodo.LETs = []
        simulacoes: int = 0
        
        ##### BUSCA DO LETs DO CIRCUITO #####
        for nodo in self.nodos:
            for saida in self.saidas:
                for k in range(2 ** len(self.entradas)):  # PASSA POR TODAS AS COMBINACOES DE ENTRADA

                    final = bin2list(k, len(self.entradas))
                    ##### DECOBRE OS LETs PARA TODAS AS COBINACOES DE rise E fall #####
                    for combinacao in [a+b for a in "rf" for b in "rf"]:

                        ##### ENCONTRA O LETth PARA AQUELA COMBINACAO #####
                        let_analisado = LET(9999, self.vdd, nodo.nome, saida.nome, combinacao)

                        print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                        simulacoes += CircMan.definir_corrente(self, let_analisado, final)

                        for let in nodo.LETs:
                            if let_analisado == let: #encontrou a combinacao correta
                                if let_analisado.corrente == let.corrente:
                                    let.append(final)
                                elif let_analisado.corrente < let.corrente:
                                    nodo.LETs.remove(let)
                                    nodo.LETs.append(let_analisado)
                                break
                        else:
                            if let_analisado.corrente < 1111:
                                nodo.LETs.append(let_analisado)

                        # LETth do circuito
                        if let_analisado.corrente < nodo.LETth.corrente:
                            nodo.LETth = let_analisado

                        if let_analisado.corrente < 1111: break
            
    def __verificar_tensoes(self):
        for saida in self.saidas:
            for i in range(2 ** len(self.entradas)):

                # Atribui o Sinal das Entradas que Nao Estao em Analise
                sinais_entrada = bin2list(i, len(self.entradas))
                for entrada, sinal in zip(self.entradas, sinais_entrada):
                    entrada.sinal = sinal

                HSRunner.configure_input(self.vdd, self.entradas)
                tensao = CircMan.verificar_nivel_logico(self.path, self.arquivo, self.vdd, saida)
                print(f"{[entrada.sinal for entrada in self.entradas]} resultam em {tensao}")
    
    @relatorio_de_tempo
    def __atualizar_LETths(self, pmos, nmos):
        HSRunner.default(self.vdd)
        # self.__get_atrasoCC()
        simulacoes: int = 0
        self.LETth = None
        ##### BUSCA DO LETs DO CIRCUITO #####
        for nodo in self.nodos:
            for let in nodo.LETs:
                try: 
                    ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                    print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                    simulacoes += CircMan.atualizar_corrente(self, let, let.validacoes[0])
                    print(f"corrente: {let.corrente}\n")
                    if not self.LETth:
                        self.LETth = let
                    elif let < self.LETth: 
                        self.LETth = let
                except KeyboardInterrupt:
                    exit() 
                except (ValueError, KeyError):
                    with open("erros.txt", "a") as erro:
                        erro.write(f"pmos {pmos} nmos {nmos} {let.nodo_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
        print(f"{simulacoes} simulacoes feitas na atualizacao")
        JManager.codificar(self)

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.cir"
    circuito_teste.vdd = 0.7
