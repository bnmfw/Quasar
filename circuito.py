from logging.config import valid_ident
from arquivos import SpiceManager, CSVManager, JsonManager, alternar_combinacao, HSRunner
from matematica import bin2list
from corrente import definir_corrente
from components import Nodo, Entrada, LET
from time import time
import os

barra_comprida = "---------------------------"

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


class Monte_Carlo(object):
    def __init__ (self, num_testes):
        self.num = num_testes
        self.MCManager = SpiceManager()

    def __enter__(self):
        self.MCManager.set_monte_carlo(self.num)

    def __exit__(self, type, value, traceback):
        self.MCManager.set_monte_carlo(0)

class MC_Instance(object):
    def __init__ (self, pmos = None, nmos = None):
        self.pmos = pmos
        self.nmos = nmos
        self.MCManager = SpiceManager()

    def __enter__(self):
        self.MCManager.set_variability(self.pmos, self.nmos)

    def __exit__(self, type, value, traceback):
        self.MCManager.set_variability(None, None)

class Circuito():
    def __init__(self):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = "nome"
        self.arquivo = "nome.cir"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0
        self.atrasoCC: float = 0
        self.LETth: LET

        ##### RELATORIO DO CIRCUITO #####
        self.sets_validos = []
        self.sets_invalidos = []

        ##### MANEJADORES DE ARQUIVOS #####
        self.SM = SpiceManager()
        self.JM = JsonManager()
        self.CM = CSVManager()

    def run(self):
        self.__tela_inicial()
        while True:
            self.__tela_principal()

    def teste(self):
        print("Teste de analise total")
        self.analise_total()

    def __tela_inicial(self):
        # Escolha de dados do circuito
        circuito = input(barra_comprida+"\nEscolha o circuito: ")
        self.nome = circuito
        self.arquivo: str = self.nome + ".cir"
        try:
            tensao: float = 0.0
            with open(circuito+".json","r"):
                tensao = float(input(f"{barra_comprida}\nCadastro encontrado\nQual vdd deseja analisar: "))
                self.vdd = tensao
            try:
                with open(f"{circuito}_{tensao}.json","r") as cadastro:
                    print(f"{barra_comprida}\nCadastro com essa tensao encontrado")
                    self.JM.decodificar(self, tensao, True) # LEITURA SIMPLES DO CIRCUITO
            except FileNotFoundError:
                print(f"{barra_comprida}\nCadastro com essa tensao nao encontrado\nGeracao sendo feita")
                self.JM.decodificar(self, tensao, False)
                self.__atualizar_LETths() # ATUALIZACAO DO CIRCUITO

        except FileNotFoundError:
            cadastro = "0"
            while not cadastro in ["y", "n"]:
                cadastro = input(f"{barra_comprida}\nCadastro do circuito nao encontrado\nDeseja gera-lo? (y/n) ")
            if cadastro == "y":
                self.analise_total() # GERA TODOS OS DADOS DO CIRCUITO
            else:
                print(f"{barra_comprida}\nPrograma encerrado")
                exit()

        ### INICIALIZACAO DO LETth DO CIRCUITO ###
        menor = 9999999999999
        for nodo in self.nodos:
            if nodo.LETth.corrente < menor:
                menor = nodo.LETth.corrente
                self.LETth = nodo.LETth

    def __tela_principal(self):
        
        acao = int(input(f"{barra_comprida}\n"
                     f"Trabalhando com o {self.nome} em {self.vdd} volts\n"
                     "O que deseja fazer?\n"
                     "0. Atualizar LETs\n"
                     "1. Gerar CSV de LETs\n"
                     "2. Analisar LET Unico\n"
                     "3. Analise Monte Carlo\n"
                     "4. Analise Monte Carlo Unica\n"
                     "5. Analise Monte Carlo Total\n"
                     "6. Sair\n"
                     "Resposta: "))
        if not acao:
            self.__atualizar_LETths()
            # self.__get_atrasoCC()
        elif acao == 1:
            self.CM.escrever_csv_total(self)
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

    def analise_total(self):
        self.vdd = float(input("vdd: "))
        self.SM.set_vdd(self.vdd)
        self.SM.set_monte_carlo(0)
        self.__instanciar_nodos()
        self.__get_atrasoCC()
        while not self.atrasoCC < 1e-10:
            print("Errei o atraso")
            self.__get_atrasoCC()
        self.__determinar_LETths()
        self.JM.codificar(self)

    def analise_tensao_comparativa(self, minvdd, maxvdd):
        lista_comparativa = {}
        while minvdd <= maxvdd + 0.0001:
            LETth_critico = 9999
            self.vdd = minvdd
            self.SM.set_vdd(minvdd)
            self.__determinar_LETths()
            for nodo in self.nodos:
                if nodo.LETth < LETth_critico:
                    LETth_critico = nodo.LETth
            lista_comparativa[str(minvdd)] = LETth_critico
            minvdd += 0.05
        #self.__escrever_csv_comparativo(lista_comparativa)

    def analise_manual(self):
        analise_manual = True
        self.vdd = input("vdd: ")
        self.SM.set_vdd(float(self.vdd))
        nodo, saida = input("nodo e saida analisados: ").split()
        pulso_in, pulso_out = input("pulsos na entrada e saida: ").split()
        nodo = Nodo(nodo)
        saida = Nodo(saida)
        vetor = [int(sinal) for sinal in input("vetor analisado: ").split()]
        let_analisado = LET(9999, float(self.vdd), nodo.nome, saida.nome, alternar_combinacao([pulso_in,pulso_out]))
        definir_corrente(self, let_analisado, vetor)
        print(f"Corrente final: {let_analisado.corrente}")

    @relatorio_de_tempo
    def __analise_monte_carlo(self):
        pulso_out = self.__configurar_LET()
        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        with Monte_Carlo(num_analises):
            os.system(f"hspice {self.arquivo}| grep \"minout\|maxout\" > output.txt")
            self.SM.get_monte_carlo_results(self, num_analises, pulso_out)
            print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_progressiva(self):

        # Configuracao do LETth do circuito no Hspice
        self.__escolher_validacao(self.LETth.validacoes[0])
        _, pulso_out = alternar_combinacao(self.LETth.orientacao)
        self.SM.set_pulse(self.LETth)
        self.SM.set_pulse_width_measure(self.LETth)

        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        with Monte_Carlo(num_analises):
            corrente = self.SM.change_pulse_value(1)
            mc_dict: dict = {"analises":num_analises}
            for frac in [1]:#, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05]:

                print(f"{100*frac}% do LETth:")

                self.SM.change_pulse_value(corrente * frac)

                os.system(f"hspice {self.arquivo}| grep \"minout\|maxout\" > output.txt")

                falhas: int = self.SM.get_monte_carlo_results(self, num_analises, pulso_out)
                mc_dict[frac] = (falhas)

            self.CM.tup_dict_to_csv(f"{self.nome}_mc.csv",mc_dict)

            print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_total(self):
        # Configuracao do LETth do circuito no Hspice
        self.__escolher_validacao(self.LETth.validacoes[0])
        self.SM.set_pulse(self.LETth)
        self.SM.set_pulse_width_measure(self.LETth)
        
        # Gera as instancias de nmos e pmos da analise MC
        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        print("Gerando instancias MC")

        with Monte_Carlo(num_analises):
            os.system(f"hspice {self.arquivo} > output.txt")

        # Retira as instancias individuais
        var: dict = self.SM.get_mc_instances(self.nome, num_analises)

        saida: dict = {"indice": ("pmos", "nmos", "nodo", "saida", "corrente", "LETth")}

        print("Encontrando LETth para cada instancia")
        for i in var:
            print(var[i][0], var[i][1])
            with MC_Instance(var[i][0], var[i][1]):
                self.__atualizar_LETths()
                saida[i] = (var[i][0], var[i][1], self.LETth.nodo_nome, self.LETth.saida_nome, self.LETth.corrente, self.LETth.valor)

        self.CM.tup_dict_to_csv(f"{self.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

    @relatorio_de_tempo
    def __get_atrasoCC(self):
        self.atrasoCC: float = 0
        simulacoes: int = 0

        self.SM.set_pulse(LET(0, 0.7, self.entradas[0].nome, self.saidas[0].nome, "ff"))

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
                    atraso: float = HSRunner.run_delay(self.arquivo, entrada_analisada.nome, saida.nome, self.vdd, self.entradas)

                    simulacoes += 1

                    if atraso > self.atrasoCC:
                        self.atrasoCC = atraso

        print(f"Atraso CC do arquivo: {self.atrasoCC} simulacoes: {simulacoes}")

    ##### METODOS PARA ENCONTRAR INSTANCIAS #####
    def encontrar_nodo(self, nome):
        for nodo in self.nodos:
            if nodo.nome == nome:
                return nodo
        #Eu nem sei se essa funcao passa dessa linha, mas se nao passar nem importa tambem
        for nodo in self.saidas:
            if nodo.nome == nome:
                return nodo
        for nodo in self.entradas:
            if nodo.nome == nome:
                return nodo
        raise RuntimeError(f"Nodo nao encontrado: {nome}")

    def encontrar_let(self, nodo: Nodo, saida: Nodo, orientacao: str) -> LET:
        if type(nodo)!= Nodo or type(saida)!= Nodo or type(orientacao) != str: raise TypeError
        let_equivalente = LET(9999, self.vdd, nodo.nome, saida.nome, orientacao)
        for let in nodo.LETs:
            if let_equivalente == let:
                return let
        raise RuntimeError("Let nao encontrado")

    def __instanciar_nodos(self):
        ##### SAIDAS #####
        saidas = input("saidas: ").split()
        self.saidas = [Nodo(saida) for saida in saidas]

        ##### ENTRADAS #####
        entradas = input("entradas: ").split()
        self.entradas = [Entrada(entrada) for entrada in entradas]

        ##### OUTROS NODOS #####
        nodos_nomes = list()
        ignorados_true = ["t" + entrada.nome for entrada in self.entradas]
        ignorados_false = ["f" + entrada.nome for entrada in self.entradas]
        with open(self.arquivo, "r") as circuito:
            for linha in circuito:
                if "M" in linha:
                    _, coletor, base, emissor, _, _, _ = linha.split()
                    for nodo in [coletor, base, emissor]:
                        if nodo not in ["vdd", "gnd", *nodos_nomes, *ignorados_true, *ignorados_false]:
                            nodo = Nodo(nodo)
                            nodos_nomes.append(nodo.nome)
                            for saida in self.saidas:
                                nodo.atraso[saida.nome] = 1111
                            self.nodos.append(nodo)

    def __escolher_validacao(self, validacao:list):
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = validacao[indice]
        self.SM.set_signals(self.vdd, self.entradas)

    def __configurar_LET(self, fracao: float = 1) -> str:
        # Configuracao de pulso
        nodo_nome, saida_nome = input("nodo e saida do LET: ").split()
        nodo = self.encontrar_nodo(nodo_nome)
        print("Orientacoes disponiveis: ")
        for let_disponivel in nodo.LETs:
            if let_disponivel.saida_nome == saida_nome:
                print(alternar_combinacao(let_disponivel.orientacao), let_disponivel.corrente)
        pulso_in, pulso_out = input("pulsos na entrada e saida do LET: ").split()
        let = self.encontrar_let(nodo, self.encontrar_nodo(saida_nome), alternar_combinacao([pulso_in, pulso_out]))
        corrente = let.corrente * fracao
        self.__escolher_validacao(let.validacoes[0])
        fake_let = LET(corrente, self.vdd, nodo_nome, saida_nome, alternar_combinacao(pulso_in, pulso_out))
        self.SM.set_pulse(fake_let)
        self.SM.set_pulse_width_measure(fake_let)
        print("LET configurado com sucesso")
        return pulso_out # Eu uso isso na analise monte carlo, se tirar vai dar pau

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
                        simulacoes += definir_corrente(self, let_analisado, final)

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
            
    @relatorio_de_tempo
    def __atualizar_LETths(self):
        simulacoes: int = 0
        ##### BUSCA DO LETs DO CIRCUITO #####
        self.LETth = LET(9999, self.vdd, "setup", "setup", "setup")
        for nodo in self.nodos:
            for let in nodo.LETs:
                ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                simulacoes += definir_corrente(self, let, let.validacoes[0])
                if let < self.LETth:
                    self.LETth = let
        print(f"{simulacoes} simulacoes feitas na atualizacao")
        self.JM.codificar(self)

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.cir"
    circuito_teste.vdd = 0.7

    circuito_teste.teste()
