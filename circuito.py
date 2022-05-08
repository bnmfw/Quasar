from arquivos import alternar_combinacao, JManager, CManager
from runner import HSRunner
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
        self.LETth: LET

        ##### RELATORIO DO CIRCUITO #####
        self.sets_validos = []
        self.sets_invalidos = []

    def run(self):
        self.__tela_inicial()
        while True:
            self.__tela_principal()

    def __tela_inicial(self):
        # Escolha de dados do circuito
        circuito = input(barra_comprida+"\nEscolha o circuito: ")
        self.nome: str = circuito
        self.path: str = f"circuitos/{circuito}/"
        self.arquivo: str = f"{circuito}.cir"
        if os.path.exists(f"{self.path}{circuito}.json"):
            tensao: float = float(input(f"{barra_comprida}\nCadastro encontrado\nQual vdd deseja analisar: "))
            self.vdd = tensao    
            JManager.decodificar(self, tensao)
            self.__atualizar_LETths() # ATUALIZACAO DO CIRCUITO

        else:
            cadastro = "0"
            while not cadastro in ["y", "n"]:
                cadastro = input(f"{barra_comprida}\nCadastro do circuito nao encontrado\nDeseja gera-lo? (y/n) ")
            if cadastro == "y":
                self.vdd = float(input("vdd: "))
                HSRunner.default(self.vdd)
                self.__instanciar_nodos()
                self.__get_atrasoCC()
                self.__determinar_LETths()
                JManager.codificar(self)
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
        pulso_out, nodo_nome, saida_nome = self.__configurar_LET()
        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        faults: int = HSRunner.run_simple_MC(self.path, self.nome, nodo_nome, saida_nome, num_analises, pulso_out, self.vdd)
        print(f"Proporcao de falhas: {100 * faults/num_analises}%")
        print("Analise monte carlo realizada com sucesso")

    @relatorio_de_tempo
    def __analise_monte_carlo_progressiva(self):

        # Configuracao do LETth do circuito no Hspice
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = self.LETth.validacoes[0][indice]
        HSRunner.configure_input(self.vdd, self.entradas)
        _, pulso_out = alternar_combinacao(self.LETth.orientacao)

        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))

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
        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        
        print("Gerando instancias MC")
        var: dict = HSRunner.run_MC_var(self.path, self.arquivo, self.nome, num_analises)

        saida: dict = {"indice": ("pmos", "nmos", "nodo", "saida", "corrente", "LETth")}

        print("Encontrando LETth para cada instancia")
        for i in var:
            print(f"index: {i} pmos: {var[i][0]} nmos: {var[i][1]}")
            with HSRunner.MC_Instance(var[i][0], var[i][1]):
                self.__atualizar_LETths()
                saida[i] = (var[i][0], var[i][1], self.LETth.nodo_nome, self.LETth.saida_nome, self.LETth.corrente, self.LETth.valor)

        CManager.tup_dict_to_csv(self.path,f"{self.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

    @relatorio_de_tempo
    def __get_atrasoCC(self):
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

        print(f"Atraso CC do arquivo: {self.atrasoCC} simulacoes: {simulacoes}")

    def __instanciar_nodos(self):
        ##### SAIDAS #####
        self.saidas = [Nodo(saida) for saida in input("saidas: ").split()]

        ##### ENTRADAS #####
        self.entradas = [Entrada(entrada) for entrada in input("entradas: ").split()]

        ##### OUTROS NODOS #####
        nodos_nomes = list()
        ignorados_true = ["t" + entrada.nome for entrada in self.entradas]
        ignorados_false = ["f" + entrada.nome for entrada in self.entradas]
        with open(f"{self.path}{self.arquivo}", "r") as circuito:
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

    def __configurar_LET(self, fracao: float = 1) -> str:
        # Configuracao de pulso
        nodo_nome, saida_nome = input("nodo e saida do LET: ").split()
        nodo: Nodo = next(nodo for nodo in self.nodos if nodo.nome == nodo_nome)
        saida: Nodo = next(saida for saida in self.saidas if saida.nome == saida_nome)
        
        print("Orientacoes disponiveis: ")
        
        for let_disponivel in nodo.LETs:
            if let_disponivel.saida_nome == saida_nome:
                print(alternar_combinacao(let_disponivel.orientacao), let_disponivel.corrente)
        
        pulso_in, pulso_out = input("pulsos na entrada e saida do LET: ").split()
        let: LET = next(let for let in nodo.LETs if let.saida_nome == saida.nome and let.orientacao == alternar_combinacao([pulso_in, pulso_out]))
        
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = let.validacoes[0][indice]

        HSRunner.configure_SET(let, self.vdd, self.entradas, let.corrente * fracao)

        return (pulso_out, nodo_nome, saida_nome) # Eu uso isso na analise monte carlo, se tirar vai dar pau

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
        HSRunner.default(self.vdd)
        self.__get_atrasoCC()
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
        JManager.codificar(self)

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.cir"
    circuito_teste.vdd = 0.7
