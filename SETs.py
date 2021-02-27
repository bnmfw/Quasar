from param import *
from corrente import *
import time

start = time.time()

circuito = raw_input("circuito a ser analisado: ")
tabela = circuito + ".csv"
circuito = circuito + ".txt"
vdd = float(input("vdd: "))
Definir_Tensao(vdd)
saidas = raw_input("saidas analisadas: ")
saidas = saidas.split()
entradas = Instanciar_entradas("fontes.txt")
validacao = list()

simulacoesFeitas = 0

sets_validos = []
sets_invalidos = []

nodos = Parametrar(circuito, entradas, saidas)

for nodo in nodos:
    print(nodo.nome, nodo.validacao)

if analiseManual:
    print("\nTESTE MANUAL\n i2, g1, up, up [0,0,0,1]\n")
    current = Corrente(circuito, vdd, entradas, "up", "up", "i2", "g1", [0, 0, 0, 1])
    print("Corrente final: " + str(current))

# for nodo in nodos:
#	print(nodo.nome, nodo.relacoes, nodo.validacao)

for nodo in nodos:

    if analiseManual: break
    for nodo_saida in saidas:  # Determina a saida

        for relacao in nodo.relacoes:  # Faz cada relacao com a saida
            if relacao[0] == nodo_saida:  # encontrou a relacao
                tipo = relacao[1]
                if tipo == "nao":
                    pass
                else:
                    relacao.append(3000)  # corrente up da relacao
                    relacao.append([])  # validacoes dessa corrente
                    relacao.append(3000)  # corrente down da relacao
                    relacao.append([])  # validacoes dessa corrente
                    if tipo == "com":  # Validacao completa
                        relacao.append(3000)  # corrente up da relacao
                        relacao.append([])  # validacoes dessa corrente
                        relacao.append(3000)  # corrente down da relacao
                        relacao.append([])  # validacoes dessa corrente

                    combinacoes = []
                    # identifica a relacao do nodo com a saida
                    if tipo == "inv":
                        combinacoes = [["up", "down"], ["down", "up"]]
                    elif tipo == "dir":
                        combinacoes = [["up", "up"], ["down", "down"]]
                    elif tipo == "com":
                        combinacoes = [["up", "up"], ["down", "down"], ["up", "down"], ["down", "up"]]

                    variaveis = 0

                    # Descobre quantas variaveis na entrada
                    for val in nodo.validacao:
                        if val[0] == nodo_saida:
                            validacao = list(val[1])
                            for x in range(len(val[1])):
                                if val[1][x] == "x": variaveis += 1

                    for k in range(2 ** variaveis):
                        binario = bin(k)
                        faltante = len(entradas) - len(binario) + 2
                        final = list(validacao)
                        flag = 0
                        binary = list()
                        # Transforma binario em uma lista de verdade e ajusta a validacao
                        for i in range(variaveis - (len(binario) - 2)): binary.append(0)
                        for i in range(len(binario) - 2): binary.append(int(binario[i + 2]))
                        for i in range(len(final)):
                            if final[i] == "x":
                                final[i] = binary[flag]
                                flag += 1

                        # Realiza a combinacao de up e down correta para validacao escolhida
                        for i in range(len(combinacoes)):
                            print(nodo.nome, nodo_saida, combinacoes[i][0], combinacoes[i][1], final)
                            lista = Corrente(circuito, vdd, entradas, combinacoes[i][0], combinacoes[i][1], nodo.nome,
                                             nodo_saida, final)
                            current = lista[0]
                            simulacoesFeitas += lista[1]

                            if current < relacao[2 + 2 * i]:
                                relacao[2 + 2 * i] = current
                                relacao[3 + 2 * i] = [final]
                            elif current == relacao[2 + 2 * i]:
                                relacao[3 + 2 * i].append(final)

                            if current < 1000:
                                sets_validos.append(
                                    [nodo.nome, nodo_saida, combinacoes[i][0], combinacoes[i][1], current, final])
                                break  # Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                            else:
                                sets_invalidos.append(
                                    [nodo.nome, nodo_saida, combinacoes[i][0], combinacoes[i][1], current, final])

for h in range(len(sets_validos)): print(sets_validos[h])
print("\n")
for h in range(len(sets_invalidos)): print(sets_invalidos[h])

# Retorno do numero de simulacoes feitas e de tempo de execucao
print("\n" + str(simulacoesFeitas) + " simulacoes feitas\n")
Escrever_CSV(tabela,nodos)

end = time.time()
tempoTotal = int(end - start)
print(str(int(tempoTotal / 60)) + " minutos e " + str(tempoTotal % 60) + " segundos de execucao\n")
