from arquivos import Escrever_Atraso, Definir_Fontes, Ler_Atraso
from param import Entrada, Nodo
from corrente import Verificar_Validacao
import os

saidas = ["g1", "g2"]
entradas = [Entrada("a",0),Entrada("b",0),Entrada("c",0),Entrada("d",0),Entrada("e",0)]
vdd = 0.7
circuito = "benchmark.txt"
maiorAtraso = 0
simulacoesFeitas = 0

for entradaAnalisada in entradas:
    for saida in saidas:
        for i in range(2 ** (len(entradas) - 1)):
            #Atribui o sinal das entradas que nao estao em analise
            binario = bin(i)
            binary = list()
            for j in range((len(entradas) - 1) - (len(binario) - 2)): binary.append(0)
            for j in range(len(binario) - 2): binary.append(int(binario[j + 2]))
            flag = 0
            for entrada in entradas:
                if entrada != entradaAnalisada:
                    entrada.sinal = binary[flag]
                    flag += 1

            #Etapa de medicao de atraso
            entradaAnalisada.sinal = "atraso"
            Escrever_Atraso(entradaAnalisada, saida, vdd)
            Definir_Fontes("fontes.txt",vdd,entradas)
            os.system("hspice " + circuito + " | grep \"atraso_rr\|atraso_rf\|atraso_ff\|atraso_fr\" > texto.txt")
            simulacoesFeitas += 1
            atraso = Ler_Atraso()
            print(atraso)
            paridade = 0
            if entradaAnalisada.nome == "b":
                print(entradas[0].sinal,entradas[1].sinal,entradas[2].sinal,entradas[3].sinal,entradas[4].sinal)
            if atraso[0] > atraso[1]: paridade = 1
            maiorAtraso = max(atraso[0+paridade], atraso[2+paridade])
            print(maiorAtraso)
            if maiorAtraso > entradaAnalisada.atraso[0]:
                 entradaAnalisada.atraso[0] = maiorAtraso
                 entradaAnalisada.atraso[1] = saida

    print("Fim da analise de atraso para entrada "+entradaAnalisada.nome+"")
    print(str(simulacoesFeitas)+" simulacoes feitas ate agora\n\n")

for entrada in entradas:
    print(entrada.atraso)
