from arquivos import Escrever_Atraso, Definir_Fontes
from param import Entrada, Nodo
import os

saidas = ["g1", "g2"]
entradas = [Entrada("a",0),Entrada("b",0),Entrada("c",0),Entrada("d",0),Entrada("e",0)]
vdd = 0.7
circuito = "c17v0.txt"
transicoes = [["rise","rise"],["rise","fall"],["fall","rise"],["fall","fall"]]

for entradaAnalisada in entradas:
    for saida in saidas:
        for i in range(len(entradas) - 1):

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

            for transicao in transicoes:
		entradaAnalisada.sinal = transicao[0]
                Escrever_Atraso(entradaAnalisada, saida, vdd, transicao[0], transicao[1])
                Definir_Fontes("fontes.txt",vdd,entradas)
                os.system("hspice " + circuito + " | grep \"atraso\" > texto.txt")
		print(binary)
		with open("texto.txt","r") as texto:
			print(entradaAnalisada.nome, saida, transicao,[entradas[0].sinal,entradas[1].sinal,entradas[2].sinal,entradas[3].sinal,entradas[4].sinal])
			print(texto.readline())
