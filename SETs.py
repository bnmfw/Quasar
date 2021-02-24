from param import *
from corrente import *
import time

start = time.time()

circuito = raw_input("circuito a ser analisado: ")
tabela = circuito+".csv"
circuito = circuito+".txt"
saidas = raw_input("saidas analisadas: ")
saidas = saidas.split()
#saidas = ["g1","g2"]
entradas = Instanciar_entradas("fontes.txt")
validacao = list()

ciclos = 0

sets_validos = []
sets_invalidos = []

nodos = Parametrar(circuito, entradas, saidas)

#print("TESTE MANUAL")
#current = Corrente(circuito,entradas,"up","down","i3","g1",[0,0,1,0,0])
#print("i3","g1","up","down",[0,0,1,0,0],current)
#print("\n\n")

#for nodo in nodos:
#	print(nodo.nome, nodo.relacoes, nodo.validacao)

for nodo in nodos:
	for nodo_saida in saidas: #Determina a saida
		
		for relacao in nodo.relacoes: #Faz cada relacao com a saida
			if relacao[0] == nodo_saida: #encontrou a relacao
				tipo = relacao[1]
				if tipo == "nao": pass
				else: 
					relacao.append(3000) #corrente up da relacao
					relacao.append([])#validacoes dessa corrente
					relacao.append(3000) #corrente down da relacao
					relacao.append([])#validacoes dessa corrente
					if tipo == "com": #Validacao completa
						relacao.append(3000) #corrente up da relacao
                	                        relacao.append([])#validacoes dessa corrente
        	                                relacao.append(3000) #corrente down da relacao
	                                        relacao.append([])#validacoes dessa corrente

					combinacoes = []
					p = 0
					#identifica a relacao do nodo com a saida
					if tipo == "inv": 
						p = 1
						combinacoes = [["up","down"],["down","up"]]
					elif tipo == "dir": 
						p = 0
						combinacoes = [["up","up"],["down","down"]]
					elif tipo == "com": 
						p = 2
						combinacoes = [["up","up"],["down","down"],["up","down"],["down","up"]]
					pulsos = ["up","down"]
					
					variaveis = 0
					
					#Descobre quantas variaveis na entrada
					for val in nodo.validacao:
						if val[0] == nodo_saida:
							validacao = list(val[1])
							for x in range(len(val[1])):
								if val[1][x] == "x": variaveis += 1
					
					for k in range(2**variaveis):
						binario = bin(k)
						faltante = len(entradas) - len(binario)+2
						final = list(validacao)
						flag = 0
						binary = list()
						#Transforma binario em uma lista de verdade e ajusta a validacao
						for b in range(variaveis - (len(binario)-2)): binary.append(0)
						for c in range(len(binario)-2): binary.append(int(binario[c+2]))
						for a in range(len(final)):
							if final[a] == "x":
								final[a] = binary[flag]
								flag += 1
						
						#Realiza a combinacao de up e down correta para validacao escolhida
						for i in range(len(combinacoes)):
							print(nodo.nome,nodo_saida,combinacoes[i][0],combinacoes[i][1],final)
							lista = Corrente(circuito,entradas,combinacoes[i][0],combinacoes[i][1],nodo.nome,nodo_saida,final)
							current = lista[0]
							ciclos += lista[1]
							
							if current < relacao[2+2*i]:
                                                        	relacao[2+2*i] = current
                                                        	relacao[3+2*i] = [final]
                                                	elif current == relacao[2+2*i]:
                                                        	relacao[3+2*i].append(final)
	
							if current < 1000:
                                                        	sets_validos.append([nodo.nome,nodo_saida,combinacoes[i][0],combinacoes[i][1],current,final])
								break #Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                                                	else: sets_invalidos.append([nodo.nome,nodo_saida,combinacoes[i][0],combinacoes[i][1],current,final])

for h in range(len(sets_validos)): print(sets_validos[h])
print("\n")
for h in range(len(sets_invalidos)): print(sets_invalidos[h])

print("\n"+str(ciclos)+" simulacoes feitas\n")

end = time.time()
print(str(end-start)+" segundos de execucao\n")

#Escreve as saidas obtidas em csv
linha = 2
with open(tabela,"w") as sets:
	sets.write("nodo,saida,pulso,pulso,corrente,set,validacoes->\n")
	for nodo in nodos:
		for relacao in nodo.relacoes:
			if relacao[1] == "nao": pass
			elif relacao[1] == "inv":
				sets.write(nodo.nome+","+relacao[0]+","+"up"+","+"down"+","+str(relacao[2])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021),")
				for validacao in relacao[3]: sets.write("'"+str(validacao[0])+str(validacao[1])+str(validacao[2])+str(validacao[3])+str(validacao[4])+",")
				sets.write("\n")
				linha+=1
				sets.write(nodo.nome+","+relacao[0]+","+"down"+","+"up"+","+str(relacao[4])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021),")
				for validacao in relacao[5]: sets.write("'"+str(validacao[0])+str(validacao[1])+str(validacao[2])+str(validacao[3])+str(validacao[4])+",")
				sets.write("\n")
				linha+=1
			else:
				sets.write(nodo.nome+","+relacao[0]+","+"up"+","+"up"+","+str(relacao[2])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021),")
				for validacao in relacao[3]: sets.write("'"+str(validacao[0])+str(validacao[1])+str(validacao[2])+str(validacao[3])+str(validacao[4])+",")
				sets.write("\n")
				linha+=1
				sets.write(nodo.nome+","+relacao[0]+","+"down"+","+"down"+","+str(relacao[4])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021),")
				for validacao in relacao[5]: sets.write("'"+str(validacao[0])+str(validacao[1])+str(validacao[2])+str(validacao[3])+str(validacao[4])+",")
				sets.write("\n")
				linha+=1
