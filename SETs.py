from arquivos import *
from time import time

tempo_inicial = time()

circuito = Circuito(input("circuito: "))
analise = None
while not analise in ["t","c","u"]:
    analise = input("Total [t]\n"
                "Comparativa [c]\n"
                "Unica [u]\n"
                "Analise desejada:")
    if analise == "t":
        circuito.analise_total(float(input("vdd: ")))
    elif analise == "c":
        vddmin = float(input("vdd min: "))
        vddmax = float(input("vdd max: "))
        circuito.analise_tensao_comparativa(vddmin,vddmax)
    elif analise == "u":
        circuito.analise_manual()
    else:
        print("Entrada invalida")

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
