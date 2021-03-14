from arquivos import Escrever_Atraso
from param import Entrada, Nodo

saidas = ["g1", "g2"]
entradas = ["a","b","c","d","e"]
vdd = 0.7

for entrada in entrada:
    for saida in saida:
	Escrever_Atraso(entrada, saida, vdd, direcaoNodo, direcaoSaida)
