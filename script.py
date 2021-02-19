import os

#Converte os valores em inteiros ajustando as casas decimais
def ajustar_valor(tensao):
	grandeza = 0
        if tensao[-1] == "m": grandeza = -3
        elif tensao[-1] == "u": grandeza = -6
        elif tensao[-1] == "n": grandeza = -9
        elif tensao[-1] == "p": grandeza = -12
        elif tensao[-1] == "f": grandeza = -15
        tensao = tensao[:-1]
        tensao = float(tensao)
        tensao = tensao * 10**grandeza
        return tensao

radiacao = "SETs.txt"
texto = "texto.txt"

linha_texto = list(range(2))

vdd = 0.7
precisao = 0.001

#variaveis da busca binaria da corrente
corrente_sup = 500
corrente = 250
corrente_inf = 0

tensao_pico = 0
max_tensao = 0
max_tempo = 0
min_tensao = 0
min_tempo = 0

#entradas sobre os nodos e SETs
pulso = raw_input("direcao do pulso no nodo (up/down): ")
saida = raw_input("direcao do pulso na saida (up/down): ")

tempo = int(input("tempo do pulso em nano seg: "))
tempo_precisao = 0.5

nodo = raw_input("nodo do pulso: ")
nodo_saida = raw_input("saida analisada: ")

#Reseta os valores no arquivo de radiacao. (Se nao fizer isso o algoritmo vai achar a primeira coisa como certa)
with open(radiacao, "w") as sets:
        sets.write("*SETs para serem usados nos benchmarks\n")
        if pulso == "down": sets.write("*")
        sets.write("Iseu gnd "+nodo+" EXP(0 "+str(corrente)+"u "+str(tempo)+"n 10p 10p 200p) //up\n")
        if pulso == "up": sets.write("*")
        sets.write("Iseu "+nodo+" gnd EXP(0 "+str(corrente)+"u "+str(tempo)+"n 10p 10p 200p) //down\n")
        sets.write(".meas tran minout min V("+nodo_saida+") from="+str(tempo - tempo_precisao)+"n to="+str(tempo + tempo_precisao)+"n\n")
        sets.write(".meas tran maxout max V("+nodo_saida+") from="+str(tempo - tempo_precisao)+"n to="+str(tempo + tempo_precisao)+"n\n")

while not((1-precisao)*vdd/2 < tensao_pico < (1+precisao)*vdd/2):

	#print(corrente_inf, corrente, corrente_sup)
	#print("tensao_pico:",tensao_pico)
	#print("\n")
	#print(max_tensao, min_tensao)
	#Roda o HSPICE e salva os valores no arquivo de texto
	os.system('hspice c17v0.txt | grep "minout\|maxout" > texto.txt')
	
	#Le os valores dos pontos maximos e minimos do intervalo analisado no arquivo de texto
	with open(texto, "r") as text:
		linha_texto[0] = text.readline()
		tensao,tempo1 = linha_texto[0].split('    ')
		if tensao[7] == "=": a,min_tensao = tensao.split('=')
		else: a,min_tensao = tensao.split()
		
		linha_texto[1] = text.readline()
		tensao,tempo1 = linha_texto[1].split('    ')
		if tensao[7] == "=": a,max_tensao = tensao.split('=')
		else: a,max_tensao = tensao.split()

	#Converte as strings lidas em floats
	max_tensao = ajustar_valor(max_tensao)
	min_tensao = ajustar_valor(min_tensao)

	#Identifica se o pico procurado e do tipo up ou down
	if saida == "up": tensao_pico = max_tensao
	elif saida == "down": tensao_pico = min_tensao
	else: print("ERRO: O TIPO DE PULSO NAO FOI IDENTIFICADO")

	#Converge o valor da corrente pro valor correto atraves de uma busca binaria
	if saida == "down":
		if tensao_pico <= (1-precisao)*vdd/2: corrente_sup = corrente
		elif tensao_pico >= (1+precisao)*vdd/2: corrente_inf = corrente
		else: print("corrente encontrada: "+str(corrente)+"uA\n")
	elif saida == "up":
		if tensao_pico <= (1-precisao)*vdd/2: corrente_inf = corrente
                elif tensao_pico >= (1+precisao)*vdd/2: corrente_sup = corrente
                else: print("corrente encontrada: "+str(corrente)+"uA\n")
	
	corrente = float((corrente_sup + corrente_inf)/2)

	#Escreve as coisas no arquivo com os SETs
	with open(radiacao, "w") as sets:
		sets.write("*SETs para serem usados nos benchmarks\n\n")
		if pulso == "down": sets.write("*")
		sets.write("Iseu gnd "+nodo+" EXP(0 "+str(corrente)+"u "+str(tempo)+"n 10p 10p 200p) //up\n")
		if pulso == "up": sets.write("*")
		sets.write("Iseu "+nodo+" gnd EXP(0 "+str(corrente)+"u "+str(tempo)+"n 10p 10p 200p) //down\n")
		sets.write(".meas tran minout min V("+nodo_saida+") from="+str(tempo - tempo_precisao)+"n to="+str(tempo + tempo_precisao)+"n\n")
		sets.write(".meas tran maxout max V("+nodo_saida+") from="+str(tempo - tempo_precisao)+"n to="+str(tempo + tempo_precisao)+"n\n")
