from arquivos import SpiceManager, analise_manual
from codificador import JsonManager, alternar_combinacao
from matematica import converter_binario, converter_binario_lista, ajustar_valor
from corrente import definir_corrente
from components import Nodo, Entrada, LET
import os

barra_comprida = "---------------------------"

class Circuito():
    def __init__(self):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = "nome"
        self.arquivo = "nome.txt"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0.0
        self.atrasoCC: float = 9999.9

        ##### RELATORIO DO CIRCUITO #####
        self.simulacoes_feitas: int = 0
        self.sets_validos = []
        self.sets_invalidos = []

        ##### MANEJADORES DE ARQUIVOS #####
        self.SM = SpiceManager()
        self.JM = JsonManager()

        ##### CONFIGURACOES PADRAO #####
        self.SM.set_monte_carlo(0)

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
        self.arquivo = self.nome + ".txt"
        try:
            tensao = 0.0
            with open(circuito+".json","r") as teste:
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
        elif acao == 1:
            self.__escrever_csv_total()
        elif acao == 2:
            self.analise_manual()
        elif acao == 3:
            self.analise_monte_carlo()
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

    def analise_monte_carlo(self):
        pulso_out = self.__configurar_LET()
        num_analises: int = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        self.SM.set_monte_carlo(num_analises)
        os.system(f"hspice {self.arquivo}| grep \"minout\|maxout\" > texto.txt")
        self.SM.get_monte_carlo_results(self, num_analises, pulso_out)
        print("Analise monte carlo realizada com sucesso")
        self.SM.set_monte_carlo(0)

    def __get_atrasoCC(self):
        simulacoes_feitas = 0
        maior_atraso = 0
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
                    atraso = self.SM.get_delay()
                    # Magia Negra
                    paridade = 0
                    if atraso[0] > atraso[1]: paridade = 1
                    print(atraso)
                    maior_atraso = max(atraso[0 + paridade], atraso[2 + paridade])
                    # Salvamento do Maior Atraso
                    print(maior_atraso, self.entradas)
                    if maior_atraso > self.atrasoCC: self.atrasoCC = maior_atraso

                print(f"Atraso encontrado para {entrada_analisada.nome} em {saida.nome}")
        print("Atraso CC do arquivo: ", self.atrasoCC)
        return maior_atraso

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
        if len(validacao) != len(self.entradas): raise IndexError("Numero de entradas eh diferente do tamanho de vetor validacao")
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = validacao[indice]

    def __configurar_LET(self) -> str:
        # Configuracao de pulso
        nodo_nome, saida_nome = input("nodo e saida do LET: ").split()
        nodo = self.encontrar_nodo(nodo_nome)
        print("Orientacoes disponiveis: ")
        for let_disponivel in nodo.LETs:
            if let_disponivel.saida_nome == saida_nome:
                print(alternar_combinacao(let_disponivel.orientacao))
        pulso_in, pulso_out = input("pulsos na entrada e saida do LET: ").split()
        let = self.encontrar_let(nodo, self.encontrar_nodo(saida_nome), alternar_combinacao([pulso_in, pulso_out]))
        corrente = let.corrente
        self.__escolher_validacao(let.validacoes[0])
        self.SM.set_signals(self.vdd, self.entradas)
        self.SM.set_pulse(nodo_nome, corrente, saida_nome, pulso_in)
        self.SM.set_pulse_width_param(nodo_nome, saida_nome, self.vdd, pulso_in, pulso_out)
        print("LET configurado com sucesso")
        return pulso_out # Eu uso isso na analise monte carlo, se tirar vai dar pau

    def __resetar_LETths(self):
        for nodo in self.nodos:
            nodo.validacao = {}
            nodo.LETs = []
            for saida in self.saidas:
                nodo.validacao[saida.nome] = []
                for entrada in self.entradas:
                    nodo.validacao[saida.nome].append("x")

    def __determinar_LETths(self):
        self.__instanciar_nodos()
        self.__resetar_LETths()
        self.simulacoes_feitas = 0
        self.sets_validos = []
        self.sets_invalidos = []
        ##### BUSCA DO LETs DO CIRCUITO #####
        for nodo in self.nodos:
            for saida in self.saidas:
                ##### FAZ A CONTAGEM DE VARIAVEIS NUMA VALIDACAO  #####
                variaveis = 0
                val = list(nodo.validacao[saida.nome])
                for x in range(len(val)):
                    if val[x] == "x": variaveis += 1
                if variaveis:
                    for k in range(2 ** variaveis):  # PASSA POR TODAS AS COMBINACOES DE ENTRADA

                        final = converter_binario(bin(k), val, variaveis)
                        ##### DECOBRE OS LETs PARA TODAS AS COBINACOES DE rise E fall #####
                        for combinacao in [["rise", "rise"], ["rise", "fall"], ["fall", "fall"], ["fall", "rise"]]:

                            ##### ENCONTRA O LET PARA AQUELA COMBINACAO #####
                            chave = alternar_combinacao(combinacao)  # Faz coisa tipo ["rise","fall"] virar "rf"
                            let_analisado = LET(9999, self.vdd, nodo.nome, saida.nome, chave)
                            print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                            self.simulacoes_feitas += definir_corrente(self, let_analisado, final)

                            for let in nodo.LETs:
                                if let_analisado == let: #encontrou a combinacao correta
                                    if let_analisado.corrente == let.corrente:
                                        let.adicionar_entrada(final)
                                    elif let_analisado.corrente < let.corrente:
                                        nodo.LETs.remove(let)
                                        nodo.LETs.append(let_analisado)
                                    break
                            else:
                                if let_analisado.corrente < 1111:
                                    nodo.LETs.append(let_analisado)

                            if let_analisado.corrente < nodo.LETth:
                                nodo.LETth = let_analisado.corrente

                            if let_analisado.corrente < 1111: break
                            # #### ADMINISTRACAO DE SETS VALIDOS E INVALIDOS PRA DEBUG
                            # if let_analisado.corrente < 1000:
                            #     self.sets_validos.append(
                            #         [nodo.nome, saida.nome, combinacao[0], combinacao[1], let_analisado.corrente, final])
                            #     break  # Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                            # else:
                            #     self.sets_invalidos.append(
                            #         [nodo.nome, saida.nome, combinacao[0], combinacao[1], let_analisado.corrente, final])

    def __atualizar_LETths(self):
        simulacoes_feitas = 0
        ##### BUSCA DO LETs DO CIRCUITO #####
        print(self.nodos)
        for nodo in self.nodos:
            for let in nodo.LETs:
                ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                simulacoes_feitas += definir_corrente(self, let, let.validacoes[0])
        print(f"{simulacoes_feitas} simulacoes feitas na atualizacao")
        self.JM.codificar(self)

    def __escrever_csv_total(self):
        linha = 2
        tabela = self.nome + ".csv"
        with open(tabela, "w") as sets:
            sets.write("Nodo,Saida,Pulso,Pulso,Corrente,LETs,Num Val,Validacoes->\n")
            for nodo in self.nodos:
                # print(nodo.LETs)
                for saida in nodo.LETs:
                    for chave, combinacao in zip(["rr", "ff", "rf", "fr"],
                                                 [["rise", "rise"],
                                                  ["fall", "fall"],
                                                  ["rise", "fall"],
                                                  ["fall", "rise"]]):
                        # print(saida, comb, nodo.LETs[saida])
                        if nodo.LETs[saida][chave][0] < 1111:
                            sets.write(nodo.nome + "," + saida + "," + combinacao[0] + "," + combinacao[1] + ",")
                            sets.write(str(nodo.LETs[saida][chave][0]) + ",")
                            sets.write('{:.2e}'.format(
                                (nodo.LETs[saida][chave][0] * 10 ** -6) * (0.000000000164 - (5 * 10 ** -11)) / (
                                        (1.08 * 10 ** -14) * 0.000000021)))
                            sets.write("," + str(len(nodo.LETs[saida][chave][1])))  # Numero de validacoes
                            for validacao in nodo.LETs[saida][chave][1]:
                                sets.write(",'")
                                for num in validacao:
                                    sets.write(str(num))
                            sets.write("\n")
                            linha += 1
        print(f"\nTabela {tabela} gerada com sucesso\n")

    def __escrever_csv_comparativo(self, lista_comparativa):
        with open(f"{self.nome}_compara.csv", "w") as tabela:
            for chave in lista_comparativa:
                tabela.write(chave + "," + "{:.2f}".format(lista_comparativa[chave]) + "\n")

        print(f"\nTabela {self.nome}_compara.csv" + " gerada com sucesso\n")

if __name__ == "__main__":

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.txt"
    circuito_teste.vdd = 0.7

    circuito_teste.teste()