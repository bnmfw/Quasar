from arquivos import *
from time import time

tempo_inicial = time()

if analise_manual: print("-----------EM ANALISE MANUAL-----------")

circuito = Circuito(input("circuito: "))
for vdd in [0.4,0.45,0.5,0.55,0.6,0.65,0.7]:
	circuito.analise_total(vdd)

##### ANALISE MANUAL #####
if analise_manual:
    circuito = input("circuito a ser analisado: ")
    vdd = input("vdd: ")
    nodo_manual, saida_manual = input("nodo e saida analisados: ").split()
    pulso_in, pulso_out = input("pulsos na entrada e saida: ").split()
    nodo_manual = Nodo(nodo_manual)
    saida_manual = Nodo(saida_manual)
    vetor_manual = input("vetor analisado: ").split()
    for i in range(len(vetor_manual)):
        vetor_manual[i] = int(vetor_manual[i])
    print("")
    current, simulacoes_feitas = definir_corrente(circuito, vdd, entradas, pulso_in, pulso_out, nodo_manual, saida_manual,
                                                  vetor_manual)
    print("Corrente final: " + str(current))
    # pulso = largura_pulso(circuito, nodo_manual, saida_manual, vdd, atraso)

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
