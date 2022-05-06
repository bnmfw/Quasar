from arquivos import escrever_atraso, definir_fontes, ler_atraso, ajustar_pulso, Entrada, Nodo
from corrente import verificar_validacao
import os

saidas = ["g1", "g2"]
entradas = [Entrada("a",0),Entrada("b",0),Entrada("c",0),Entrada("d",0),Entrada("e",0)]
vdd = 0.7
circuito = "c17v0.cir"
maior_atraso = 0
simulacoes_feitas = 0

ajustar_pulso("SETs.cir",saidas[0],0.0,saidas[0],"fall")

for entrada_analisada in entradas:
    for saida in saidas:
        for i in range(2 ** (len(entradas) - 1)):
            #Atribui o sinal das entradas que nao estao em analise
            binario = bin(i)
            binary = list()
            for j in range((len(entradas) - 1) - (len(binario) - 2)): binary.append(0)
            for j in range(len(binario) - 2): binary.append(int(binario[j + 2]))
            flag = 0
            for entrada in entradas:
                if entrada != entrada_analisada:
                    entrada.sinal = binary[flag]
                    flag += 1

            #Etapa de medicao de atraso
            entrada_analisada.sinal = "atraso"
            escrever_atraso(entrada_analisada, saida, vdd)
            definir_fontes("fontes.txt",vdd,entradas)
            os.system(f"hspice {circuito} | grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\|largura\" > output.txt")
            simulacoes_feitas += 1
            atraso = ler_atraso(vdd)
            paridade = 0
            #if entradaAnalisada.nome == "a":
            #    print(entradas[0].sinal,entradas[1].sinal,entradas[2].sinal,entradas[3].sinal,entradas[4].sinal)
            if atraso[0] > atraso[1]: paridade = 1
            maior_atraso = max(atraso[0 + paridade], atraso[2 + paridade])
            print(maior_atraso, entradas[0].sinal, entradas[1].sinal, entradas[2].sinal, entradas[3].sinal, entradas[4].sinal)
            if maior_atraso > entrada_analisada.atraso[0]:
                entrada_analisada.atraso[0] = maior_atraso
                entrada_analisada.atraso[1] = saida
                entrada_analisada.atraso[1] = [entradas[0].sinal, entradas[1].sinal, entradas[2].sinal, entradas[3].sinal, entradas[4].sinal]
        print(f"Atraso encontrado para {entrada_analisada.nome} em {saida}")

    print(f"Atraso encontrado para entrada {entrada_analisada.nome}\n")

for entrada in entradas:
    print(entrada.atraso)