#Classe responsavel por manejar todos os arquivos spice
class SPICEHandler():
    def __init__(self):
        pass



class Nodo():
    def __init__(self, nome, relacoes = None, sinal = 0, validacao = None):
        if relacoes == None: relacoes = []
        if validacao == None: validacao = []
        self.nome = nome
        self.relacoes = relacoes  # Tipo de relacao com cada saida: inv, dir, nao, com
        self.sinal = sinal  # Sinal logico (usado apenas na validacao)
        self.validacao = validacao  # Lista que contem 1 lista pra cara saida contendo: [nome da saida, validacao generica]
        self.LETth = 1111

class Circuito():
    def __init__(self, arquivo, saidas, entradas, vdd):
        self.nodos = [] #Nodos compoe um circuito
        self.arquivo = arquivo #Nome do arquivo HSPICE
        self.entradas = entradas #Entradas do circuito
        self.saidas = saidas #Saidas do circuito
        self.vdd = vdd

        self.criar_nodos()
        self.definir_vdd(vdd)

    def criar_nodos(self):
        #Cria todos os nodos do circuito
        nodos_encontrados = list() #strings
        ignorados = ["ta","tb","tc","td","te","fa","fb","fc","fd","fd"]
        with open(self.arquivo, "r") as circ:
            for linha in circ:
                if "M" in linha: #Encontra um Finfet na linha, ou seja possivelmente um novo nodo
                    transistor, coletor, base, emissor, bulk, modelo, nfin = linha.split() #Desmonta
                    for nodo in [coletor, base, emissor]:
                        if nodo not in ["vdd","gnd", *ignorados, *nodos_encontrados]:
                            #Encontra um nodo novo que nao eh uma entrada ou alimentacao
                            nodo = Nodo(nodo)
                            self.nodos.append(nodo)
                            nodos_encontrados.append(nodo.nome)

        #                     for saida in self.saidas:
        #                         nodo.relacoes.append([saida])
        #                     nodos.append(nodo)

    def definir_vdd(self, vdd):
        with open("vdd.txt", "w") as arquivo_vdd:
            arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
            arquivo_vdd.write("Vvdd vdd gnd " + str(vdd) + "\n")
            arquivo_vdd.write("Vvcc vcc gnd " + str(vdd) + "\n")
            arquivo_vdd.write("Vclk clk gnd PULSE(0 " + str(vdd) + " 1n 0.01n 0.01n 1n 2n)")

    def definir_sinais(self, sinais_de_entrada):
        with open("fontes.txt", "w") as sinais:
            sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")
            for sinal in sinais_de_entrada:
                sinais.write("V" + entradas[i].nome + " " + entradas[i].nome + " gnd ")
                if entradas[i].sinal == 1:
                    sinais.write(str(vdd) + "\n")
                elif entradas[i].sinal == 0:
                    sinais.write("0.0\n")
                elif entradas[i].sinal == "atraso":
                    sinais.write("PWL(0n 0 1n 0 1.01n " + str(vdd) + " 3n " + str(vdd) + " 3.01n 0)\n")
                else:
                    print("ERRO SINAL NAO IDENTIFICADO RECEBIDO: ", entradas[i].sinal)