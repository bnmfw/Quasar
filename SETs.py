from param import *
from corrente import *
from arquivos import *
from time import time

tempoInicial = time()

circuito = raw_input("circuito a ser analisado: ")
tabela = circuito + ".csv"
circuito = circuito + ".txt"
vdd = float(input("vdd: "))
Definir_Tensao(vdd)
saidas = raw_input("saidas analisadas: ")
saidas = saidas.split()
entradas = Instanciar_Entradas("fontes.txt")
validacao = list()

simulacoesFeitas = 0

sets_validos = []
sets_invalidos = []

nodos = Instanciar_Nodos(circuito,saidas)
Ler_Validacao(circuito,nodos,saidas)

for nodo in nodos:
    print(nodo.nome, nodo.validacao)

if analiseManual:
    print("\nTESTE MANUAL\n i2, g1, rise, rise [0,0,0,1]\n")
    current = Corrente(circuito, vdd, entradas, "rise", "rise", "i2", "g1", [0, 0, 0, 1])
    print("Corrente final: " + str(current))

for nodo in nodos:
    if analiseManual: break
    for nodo_saida in saidas:  # Determina a saida
        for relacao in nodo.relacoes:
            for i in range(4):
                relacao.append(3000)  # correntes da relacao
                relacao.append([])  # validacoes dessa corrente
                #[g1,corrente,[vals],corrente,[vals],corrente,[vals],corrente,[vals]

            combinacoes = [["rise", "rise"], ["fall", "fall"], ["rise", "fall"], ["fall", "rise"]]

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

                # Realiza a combinacao de rise e fall correta para validacao escolhida
                for i in range(len(combinacoes)):
                    print(nodo.nome, nodo_saida, combinacoes[i][0], combinacoes[i][1], final)
                    current, simulacoesFeitas = Corrente(circuito, vdd, entradas, combinacoes[i][0], combinacoes[i][1], nodo.nome,
                                     nodo_saida, final)

                    #print(relacao)
		    if current < relacao[1 + 2 * i]:
                        relacao[1 + 2 * i] = current
                        relacao[2 + 2 * i] = [final]
                    elif current == relacao[1 + 2 * i]:
                        relacao[2 + 2 * i].append(final)

                    if current < 1000:
                        sets_validos.append(
                            [nodo.nome, nodo_saida, combinacoes[i][0], combinacoes[i][1], current, final])
                        break  # Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                    else:
                        sets_invalidos.append(
                            [nodo.nome, nodo_saida, combinacoes[i][0], combinacoes[i][1], current, final])
	    print(relacao)

if not analiseManual:
    for sets in sets_validos: print(sets)
    print("\n")
    for sets in sets_invalidos: print(sets)

    # Retorno do numero de simulacoes feitas e de tempo de execucao
    print("\n" + str(simulacoesFeitas) + " simulacoes feitas\n")
    Escrever_CSV(tabela, nodos)

tempoFinal = time()
tempoTotal = int(tempoFinal - tempoInicial)
print(str(int(tempoTotal / 60)) + " minutos e " + str(tempoTotal % 60) + " segundos de execucao\n")
