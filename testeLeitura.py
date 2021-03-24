from arquivos import *
saidas = ["g1","g2"]
entradas = ["a","b","c","d","e"]
vdd = 0.7
circuito = "benchmark.txt"

nodos = Instanciar_Nodos(circuito,saidas,entradas)
Ler_Validacao(circuito,nodos,saidas)

for nodo in nodos:
    print(nodo.nome, nodo.relacoes, nodo.validacao)