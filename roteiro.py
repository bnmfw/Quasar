from param import *
from corrente import *

circuito = raw_input("circuito a ser analisado: ")
circuito = circuito+".txt"
saidas = ["g1","g2"]
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
	
					p = 0
					#identifica a relacao do nodo com a saida
					if tipo == "inv": p = 1
					elif tipo == "dir": p = 0
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
						#Transforma binario em uma lista de verdade
						for b in range(variaveis - (len(binario)-2)): binary.append(0)
						for c in range(len(binario)-2): binary.append(int(binario[c+2]))
						for a in range(len(final)):
							if final[a] == "x":
								final[a] = binary[flag]
								flag += 1
						
						#PULSO DE SUBIDA NO NODO						
						print("up", pulsos[p],nodo.nome,nodo_saida,final)
						lista = Corrente(circuito,entradas,"up",pulsos[p],nodo.nome,nodo_saida,final)
						current = lista[0]
						ciclos += lista[1]
						if current < relacao[2]:
							relacao[2] = current
							relacao[3] = [final]
						elif current == relacao[2]:
							relacao[3].append(final)
						#print(nodo.nome,nodo_saida,"up",pulsos[p],current,final)
						
						if current < 1000:
							sets_validos.append([nodo.nome,nodo_saida,"up",pulsos[p],current,final])
						else: sets_invalidos.append([nodo.nome,nodo_saida,"up",pulsos[p],current,final])
						
						
						if current >= 1000:
							#PULSO DE DESCIDA NO NODO
							pd = int((p+1)%2)
							print("down", pulsos[pd],nodo.nome,nodo_saida,final)
							lista  = Corrente(circuito,entradas,"down",pulsos[pd],nodo.nome,nodo_saida,final)
							current = lista[0]
							ciclos += lista[1]
							if current < relacao[4]:
								relacao[4] = current
								relacao[5] = [final]
							elif current == relacao[4]:
								relacao[5].append(final)
							#print(nodo.nome,nodo_saida,"down",pulsos[pd],current,final)
							if current < 1000:
                        	                                sets_validos.append([nodo.nome,nodo_saida,"down",pulsos[pd],current,final])
							else: sets_invalidos.append([nodo.nome,nodo_saida,"down",pulsos[pd],current,final])

for nodo in nodos:
	print(nodo.nome, nodo.relacoes)
for h in range(len(sets_validos)): print(sets_validos[h])
print("\n")
for h in range(len(sets_invalidos)): print(sets_invalidos[h])

print(str(ciclos)+" simulacoes feitas")

#Escreve as saidas obtidas em csv
linha = 2
with open("SETs.csv","w") as sets:
	sets.write("nodo,saida,pulso,pulso,corrente,set\n")
	for nodo in nodos:
		for relacao in nodo.relacoes:
			if relacao[1] == "nao": pass
			elif relacao[1] == "inv":
				sets.write(nodo.nome+","+relacao[0]+","+"up"+","+"down"+","+str(relacao[2])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021)\n")
				linha+=1
				sets.write(nodo.nome+","+relacao[0]+","+"down"+","+"up"+","+str(relacao[4])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021)\n")
				linha+=1
			else:
				sets.write(nodo.nome+","+relacao[0]+","+"up"+","+"up"+","+str(relacao[2])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021)\n")
				linha+=1
                                sets.write(nodo.nome+","+relacao[0]+","+"down"+","+"down"+","+str(relacao[4])+"E-6,=E"+str(linha)+"*0.00000000019/(1.08E-14*0.000000021)\n")
				linha+=1
