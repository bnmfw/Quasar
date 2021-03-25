from arquivos import *

circuito = "c17v0.txt"
saidas = ["g1", "g2"]
entradas = ["a","b","c","d","e"]

nodos = Instanciar_Nodos(circuito,saidas,entradas)
entradas = Instanciar_Entradas(entradas)
Ler_Validacao(circuito,nodos,saidas)
for nodo in nodos:
    print(nodo.nome, nodo.validacao)
