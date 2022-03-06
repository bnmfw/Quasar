from arquivos import SpiceManager, CSVManager, JsonManager, alternar_combinacao, analise_manual
from matematica import converter_binario_lista
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

class Circuito():
    def __init__(self):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = "nome"
        self.arquivo = "nome.txt"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0
        self.atrasoCC: float = 0

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
        self.arquivo: str = self.nome + ".txt"
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
                self.__get_atrasoCC()
            else:
                print(f"{barra_comprida}\nPrograma encerrado")
                exit()

    def __tela_principal(self):
        acao = int(input(f"{barra_comprida}\n"
                     f"Trabalhando com o {self.nome} em {self.vdd} volts\n"
                     "O que deseja fazer?\n"
                     "0. Atualizar LETs\n"
                     "1. Gerar CSV de LETs\n"
                     "2. Analisar LET unico\n"
                     "3. Analise Monte Carlo\n"
                     "5. Sair\n"
                     "Resposta: "))
        if not acao:
            self.__atualizar_LETths()
            self.__get_atrasoCC()
        elif acao == 1:
            self.CM.escrever_csv_total(self)
        elif acao == 2:
            self.analise_manual()
        elif acao == 3:
            self.__analise_monte_carlo_progressiva()
        #elif acao == 4:
        elif acao == 5:
            exit()
        else:
            print("Comando invalido")

    def analise_total(self):
        self.vdd = float(input("vdd: "))
        self.SM.set_vdd(self.vdd)
        self.SM.set_monte_carlo(0)
        #self.__get_atrasoCC()
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
            os.system(f"hspice {self.arquivo}| grep \"minout\|maxout\" > texto.txt")
            self.SM.get_monte_carlo_results(self, num_analises, pulso_out)
            print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_progressiva(self):
        pulso_out = self.__configurar_LET()
        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        with Monte_Carlo(num_analises):
            corrente = self.SM.change_pulse_value(1)
            for frac in [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]:
                self.SM.change_pulse_value(corrente * frac)
                os.system(f"hspice {self.arquivo}| grep \"minout\|maxout\" > texto.txt")
                self.SM.get_monte_carlo_results(self, num_analises, pulso_out)
            print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __get_atrasoCC(self):
        self.atrasoCC = 0
        simulacoes_feitas = 0
        for entrada_analisada in self.entradas:
            for saida in self.saidas:
                for i in range(2 ** (len(self.entradas) - 1)):

                    # Atribui o Sinal das Entradas que Nao Estao em Analise
                    sinais_entrada = converter_binario_lista(i, len(self.entradas)-1)
                    index = 0
                    for entrada in self.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = sinais_entrada[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # VERIFICACAO DE ERRO
                    for entrada in self.entradas:
                        if not entrada.sinal in [0, 1, "atraso"]:
                            raise ValueError(f"Sinais de entrada nao identificado: {entrada.sinal}")

                    # Etapa de medicao de atraso
                    self.SM.set_delay_param(entrada_analisada.nome, saida.nome, self.vdd)
                    self.SM.set_signals(self.vdd, self.entradas)
                    os.system(
                        f"hspice {self.arquivo}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\|largura\" > texto.txt")
                    simulacoes_feitas += 1
                    atraso: float = self.SM.get_delay()

                    if atraso > self.atrasoCC:
                        self.atrasoCC = atraso

                #print(f"Atraso encontrado para {entrada_analisada.nome} em {saida.nome}")
        print("Atraso CC do arquivo: ", self.atrasoCC)

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
        if type(nodo)!= Nodo and type(saida)!= Nodo and type(orientacao) != str: raise TypeError
        let_equivalente = LET(9999, self.vdd, nodo.nome, saida.nome, orientacao)
        for let in nodo.LETs:
            if let_equivalente == let:
                return let
        raise RuntimeError("Let nao encontrado")

    def __instanciar_nodos(self):
        ##### SAIDAS #####
        saidas = input("saidas: ").split()
        for saida in saidas:
            self.saidas.append(Nodo(saida))

        ##### ENTRADAS #####
        entradas = input("entradas: ").split()
        for entrada in entradas:
            self.entradas.append(Entrada(entrada, "t"))

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
        ##### ERROS #####
        if len(validacao) != len(self.entradas):
            raise IndexError("Numero de entradas eh diferente do tamanho de vetor validacao")

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
                print(alternar_combinacao(let_disponivel.orientacao), let_disponivel.valor)
        pulso_in, pulso_out = input("pulsos na entrada e saida do LET: ").split()
        let = self.encontrar_let(nodo, self.encontrar_nodo(saida_nome), alternar_combinacao([pulso_in, pulso_out]))
        corrente = let.corrente * fracao
        self.__escolher_validacao(let.validacoes[0])
        self.SM.set_pulse(nodo_nome, corrente, saida_nome, pulso_in)
        self.SM.set_pulse_width_param(nodo_nome, saida_nome, self.vdd, pulso_in, pulso_out)
        print("LET configurado com sucesso")
        return pulso_out # Eu uso isso na analise monte carlo, se tirar vai dar pau

    @relatorio_de_tempo
    def __determinar_LETths(self):
        self.__instanciar_nodos()
        for nodo in self.nodos:
            nodo.LETs = []
        simulacoes_feitas: int = 0
        ##### BUSCA DO LETs DO CIRCUITO #####
        for nodo in self.nodos:
            for saida in self.saidas:
                for k in range(2 ** len(self.entradas)):  # PASSA POR TODAS AS COMBINACOES DE ENTRADA

                    final = converter_binario_lista(k, len(self.entradas))
                    ##### DECOBRE OS LETs PARA TODAS AS COBINACOES DE rise E fall #####
                    for combinacao in [["rise", "rise"], ["rise", "fall"], ["fall", "fall"], ["fall", "rise"]]:

                        ##### ENCONTRA O LET PARA AQUELA COMBINACAO #####
                        chave = alternar_combinacao(combinacao)  # Faz coisa tipo ["rise","fall"] virar "rf"
                        let_analisado = LET(9999, self.vdd, nodo.nome, saida.nome, chave)
                        print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                        simulacoes_feitas += definir_corrente(self, let_analisado, final)

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

                        if let_analisado.corrente < nodo.LETth.corrente:
                            nodo.LETth = let_analisado

                        if let_analisado.corrente < 1111: break
                        # #### ADMINISTRACAO DE SETS VALIDOS E INVALIDOS PRA DEBUG
                        # if let_analisado.corrente < 1000:
                        #     self.sets_validos.append(
                        #         [nodo.nome, saida.nome, combinacao[0], combinacao[1], let_analisado.corrente, final])
                        #     break  # Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                        # else:
                        #     self.sets_invalidos.append(
                        #         [nodo.nome, saida.nome, combinacao[0], combinacao[1], let_analisado.corrente, final])

    @relatorio_de_tempo
    def __atualizar_LETths(self):
        simulacoes_feitas = 0
        ##### BUSCA DO LETs DO CIRCUITO #####
        print(self.nodos)
        for nodo in self.nodos:
            if nodo.LETth.corrente > 1000:
                break #TEM QUE VER ISSO AQUI
            simulacoes_feitas += definir_corrente(self, nodo.LETth, nodo.LETth.validacoes[0])
            for let in nodo.LETs:
                ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                simulacoes_feitas += definir_corrente(self, let, let.validacoes[0])
        print(f"{simulacoes_feitas} simulacoes feitas na atualizacao")
        self.JM.codificar(self)

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.txt"
    circuito_teste.vdd = 0.7

    circuito_teste.teste()
