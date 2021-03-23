from arquivos import *

circuito = "c17v0.txt"
saidas = ["g1", "g2"]

nodos = Instanciar_Nodos(circuito,saidas)
entradas = Instanciar_Entradas("fontes.txt")
Ler_Validacao(circuito,nodos,saidas)
for nodo in nodos:
    print(nodo.nome, nodo.validacao)