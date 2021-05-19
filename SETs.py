from corrente import *
from arquivos import *
from time import time


def converter_binario(binario, validacao):  # Converte o binario esquisito numa lista
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
    return final


tempo_inicial = time()

##### DADOS GERAIS #####
combinacoes = [["rise", "rise"], ["fall", "fall"], ["rise", "fall"], ["fall", "rise"]]
simulacoes_feitas = 0
sets_validos = []
sets_invalidos = []

if analise_manual: print("-----------EM ANALISE MANUAL-----------")

#def raw_input(key):
#    return(input(key))

##### ENTRADAS #####
circuito = raw_input("circuito a ser analisado: ")
tabela = circuito + ".csv"
circuito = circuito + ".txt"
vdd = float(input("vdd: "))
definir_tensao(vdd)
saidas = raw_input("saidas analisadas: ").split()
lista_auxiliar = []
for saida in saidas:
    lista_auxiliar.append(Nodo(saida))
saidas = lista_auxiliar
entradas = ["a", "b", "c", "d", "e"]
validacao = list()

##### OBJETIFICACAO DOS NODOS E LEITURA DA VALIDACAO #####
nodos = instanciar_nodos(circuito, saidas)
atraso = ler_validacao(circuito, nodos, saidas)
entradas = instanciar_entradas(entradas)

##### ANALISE MANUAL #####
if analise_manual:
    nodos_analise = raw_input("nodo e saida analisados: ")
    pulsos = raw_input("pulsos na entrada e saida: ")
    pulso_in, pulso_out = pulsos.split()
    nodo_manual, saida_manual = nodos_analise.split()
    nodo_manual = Nodo(nodo_manual)
    saida_manual = Nodo(saida_manual)
    vetor_manual = raw_input("vetor analisado: ").split()
    for i in range(len(vetor_manual)):
        vetor_manual[i] = int(vetor_manual[i])
    print("")
    current = Corrente(circuito, vdd, entradas, pulso_in, pulso_out, nodo_manual, saida_manual, vetor_manual)
    print("Corrente final: " + str(nodo_manual.LETth[saida_manual.nome]))
    # pulso = largura_pulso(circuito, nodo_manual, saida_manual, vdd, atraso)

##### BUSCA DO LETth DO CIRCUITO #####
for nodo in nodos:
    if analise_manual: break

    for saida in saidas:
        ##### FAZ A CONTAGEM DE VARIAVEIS NUMA VALIDACAO  #####
        variaveis = 0
        for val in nodo.validacao:
            if val[0] == saida.nome:
                validacao = list(val[1])  # Copia a validacao
                for x in range(len(val[1])):
                    if val[1][x] == "x": variaveis += 1
        # print(variaveis)
	print(variaveis)
        if not variaveis: break

        for k in range(2 ** variaveis):  # PASSA POR TODAS AS COMBINACOES DE ENTRADA

            final = converter_binario(bin(k), validacao)
            ##### DECOBRE OS LETth PARA TODAS AS COBINACOES DE rise E fall #####
            for combinacao in combinacoes:

                ##### ENCONTRA O LETth PARA AQUELA COMBINACAO #####
                print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                current, simulacoes = Corrente(circuito, vdd, entradas, combinacao[0], combinacao[1], nodo, saida, final)
                simulacoes_feitas += simulacoes

                chave = combinacao[0][0] + combinacao[1][0]  # Faz coisa tipo ["rise","fall"] virar "rf"
                if current < nodo.LETth[saida.nome][chave][0]:  ##### SE O LETth EH MENOR DO QUE UM JA EXISTENTE
                    nodo.LETth[saida.nome][chave][0] = current
                    nodo.LETth[saida.nome][chave][1] = [final]

                elif current == nodo.LETth[saida.nome][chave][0]:  ##### SE O LETth EH IGUAL A UM JA EXISTENTE
                    nodo.LETth[saida.nome][chave][1].append(final)

                ##### VALIDACAO DE LARGURA DE PULSO #####
                # if current < 1000:
                #     pulso = largura_pulso(circuito, nodo, saida, vdd, atraso)
                #     simulacoes_feitas += 1
                #     if pulso == 4444:
                #         print("Corrente invalidada por lagura de pulso\n")
                #         current = 4444  # Invalida corrente de pulso muito pequeno
                #     else:
                #         print("Corrente validada\n")

                ##### ADMINISTRACAO DE SETS VALIDOS E INVALIDOS PRA DEBUG
                if current < 1000:
                    sets_validos.append(
                        [nodo.nome, saida.nome, combinacao[0], combinacao[1], current, final])
                    break  # Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                else:
                    sets_invalidos.append(
                        [nodo.nome, saida.nome, combinacao[0], combinacao[1], current, final])

##### RELATORIOS #####

if not analise_manual:

    for sets in sets_validos: print(sets)
    print("\n")
    for sets in sets_invalidos: print(sets)

    print("\n1111-SET invalidado em analise de tensao")
    print("2222-SET invalidado em analise de pulso")
    print("3333-SET Passou validacoes anteriores mas foi mal concluido")
    print("4444-SET invalidado em validacao de largura de pulso")

    # Retorno do numero de simulacoes feitas e de tempo de execucao
    print("\n" + str(simulacoes_feitas) + " simulacoes feitas\n")
    for nodo in nodos:
	print(nodo.nome)
	for saida in nodo.LETth:
	    print(saida, nodo.LETth[saida])
	    #for orientacao in nodo.LETth[saida]:	
	    #	print(orientacao)
    escrever_csv(tabela, nodos)

##### RELATORIO DE TEMPO DE EXECUCAO #####
tempo_final = time()
tempo_total = int(tempo_final - tempo_inicial)
dias_de_simulacao = int(tempo_total / 86400)
horas_de_simulacao = int((tempo_total % 86400) / 3600)
minutos_de_simulacao = int((tempo_total % 3600) / 60)
if dias_de_simulacao:
    print(str(dias_de_simulacao) + " dias, ")
if horas_de_simulacao:
    print(str(horas_de_simulacao) + " horas, ")
print(str(minutos_de_simulacao) + " minutos e " + str(tempo_total % 60) + " segundos de execucao\n")
