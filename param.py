#Classe nodo e entrada
class Entrada():
	def __init__(self, nome, sinal):
		self.nome = nome
		self.sinal = sinal

class Nodo():
	def __init__(self,nome,entradas,logica,relacoes,sinal,validacao):
		self.nome = nome
		self.entradas = entradas
		self.logica = logica
		self.relacoes = relacoes
		self.sinal = sinal
		self.validacao = validacao

#Recursao que encontra a relacao de um nodo com uma saida
def Relacionar(saida_global, saida, nodos, entradas ,relacao_acumulada):
	
	#Finaliza a recursao quando chega nas entradas
	if saida in entradas: return 0	
	else:
		for relacao in saida.relacoes:
			if relacao[0] == saida_global.nome and relacao[1] == "nao":
				relacao[1] = relacao_acumulada #Salva a relacao do nodo com a global
		#Atualiza as relacoes
		if saida.logica == "NAND" or saida.logica == "NOR" or saida.logica == "NOT":
			if relacao_acumulada == "dir": relacao_acumulada = "inv"
			elif relacao_acumulada == "inv": relacao_acumulada = "dir"
			else: print("ERRO RELACAO NAO ENCONTRADA PARA:", nodos[i].nome, relacao_acumulada)
		
		for entrada in saida.entradas:
			Relacionar(saida_global, entrada, nodos, entradas, relacao_acumulada)

#Funcao que define sinais para entradas nao relevantes ao sinal analisado
def Fixar(saida, entradas):
        #Escolhe as paridades das entradas fixas
        if saida.sinal == 1:
                if saida.logica == "NAND" or saida.logica == "NOR" or saida.logica == "NOT": paridade = 0
                elif saida.logica == "AND" or saida.logica == "OR": paridade = 1 #Pra realmente fixar todas as entradas tem que ser 1
                else: print("PORTA LOGICA DE SAIDA "+saida.nome+"NAO REGISTRADA")
        elif saida.sinal == 0:
                if saida.logica == "NAND" or saida.logica == "NOR" or saida.logica == "NOT": paridade = 1
                elif saida.logica == "AND" or saida.logica == "OR": paridade = 0 #Pra realmente fixar todas as entradas tem que ser 0
                else: print("PORTA LOGICA "+saida.nome+" NAO REGISTRADA (FIX)")

        #Altera os valores das entradas quando possivel
	for entrada in saida.entradas:
                if saida.sinal == "x":
			if entrada.sinal == "t": entrada.sinal = "x"
                elif saida.sinal == "t": #t significa tanto faz kkkkkk
                        pass
                elif saida.sinal == 0 or saida.sinal == 1:
                        if entrada.sinal == "t": entrada.sinal = paridade
                else: print("ERRO TIPO DE SINAL NAO REGISTRADO: "+str(saida.sinal))

                #Repete a funcao pra entradas nao elementares
                if not entrada in entradas: 
			Fixar(entrada, entradas)


#Funcao que recursivamente corre do nodo pra saida neutralizando entradas paralelas
def Neutralizar(saida,alvo,nodos,saidas):
	
	alvo.sinal = "x"
	for i in range(len(nodos)):	
		for entrada in nodos[i].entradas:
			if entrada.nome == alvo.nome: #Achou uma porta que tem o alvo como entrada
				paridade = -1
				if nodos[i].logica == "NAND" or nodos[i].logica == "AND": paridade = 1
				elif nodos[i].logica == "NOR" or nodos[i].logica == "OR": paridade = 0
				elif nodos[i].logica == "NOT": pass
				else: print("PORTA LOGICA "+nodos[i].logica+" NAO REGISTRADA (NEU)")
				
				for outra_entrada in nodos[i].entradas:
					if outra_entrada.nome != alvo.nome: #Achou uma outra entrada e atribuiu o sinal
						if outra_entrada.sinal == "t": outra_entrada.sinal = paridade
                                                elif outra_entrada.sinal == "x": pass
						elif outra_entrada.sinal == paridade: pass
						else: print("ERRO CONFLITO DE PARADIDADE PARA: "+outra_entrada.nome+" ATUAL: "+str(outra_entrada.sinal)+" NOVA: "+str(paridade))
				
				#Repete o processo se nao eh saida global
				if nodos[i].nome in saidas: pass
				else: Neutralizar(saida,nodos[i], nodos,saidas)

#Finaliza as entradas logicas para ter apenas uma variavel
def Finalizar(entradas):
	for i in range(len(entradas)):
		if entradas[i].sinal == "t": entradas[i].sinal = 0

#Gera as validacoes logicas de uma entrada para uma saida
def Validar(alvo,entradas,nodos,saida,saidas):
	
	logica_entrada = []
		
	#Zera a validacao se nao ha relacao, o que impede que a validacao logica seja feita mais pra frente
	for relacao in alvo.relacoes:
		if relacao[0] == saida and relacao[1] == "nao":
			for i in range(len(entradas)):
				logica_entrada.append(0)
			
	#Reseta todos os sinais
        for i in range(len(entradas)):
		entradas[i].sinal = "t"
	for i in range(len(nodos)):
		nodos[i].sinal = "t"
	
	#Altera a saida de string para objeto
	for i in range(len(nodos)):
        	if nodos[i].nome == saida:
                	saida = nodos[i] 

	#Realiza as validacoes logicas
	alvo.sinal = "x"
	if not len(logica_entrada):
		
		Fixar(alvo, entradas) #Declara como X todas as entradas que tem influencia no nivel logico do nodo
        	
		Neutralizar(saida, alvo, nodos, saidas)#Limpa o caminho do nodo ate a saida
        	
		Fixar(saida, entradas)#Fixa entradas ainda nao determinadas que tem influencia na saida
        	
		Finalizar(entradas)#Coloca em 0 entradas sem influencia na saida analisada
		
		#Salva a validacao logica em um vetor
		logica_entrada = list()
		for i in range(len(entradas)):
			logica_entrada.append(entradas[i].sinal)

	alvo.validacao.append([saida.nome, logica_entrada])

def Instanciar_entradas(fontes):
	entradas = list()
        with open(fontes, "r") as fonte:
                for linha in fonte:
                        if "V" in linha:
                                a,nome,b,c = linha.split()
                                entrada = Entrada(nome,"t")
                                entradas.append(entrada)

	return entradas

#Funcao que recebe o circuito e retorna os parametros	
def Parametrar(circuito, entradas, saidas):

	#Instanciacao de todos os nodos que nao entradas
	nodos = list()
	with open(circuito,"r") as circ:
		for linha in circ:
			if "X" in linha:
				a,b,c,info = linha.split(' ', 3)
				lista = list()
				lista = info.split()
				nodo = Nodo(lista[-2], lista[:-2], lista[-1], [], "t", [])
				for output in saidas:
					nodo.relacoes.append([output,"nao"])
				nodos.append(nodo)

	#Agrega os nodos a outros nodos por que orientacao a objeto arrebenta
	for i in range(len(nodos)):
		for j in nodos[i].entradas:
			for k in range(len(nodos)):
				if nodos[k].nome == nodos[i].entradas[0]:
					nodos[i].entradas.append(nodos[k])
					nodos[i].entradas.remove(nodos[i].entradas[0])
			for k in range(len(entradas)):
				if entradas[k].nome == nodos[i].entradas[0]:
					nodos[i].entradas.append(entradas[k])
					nodos[i].entradas.remove(nodos[i].entradas[0])

	#Define o relacionamento de cada nodo com cada saida
	for saida in saidas:
		for nodo in nodos:
			if nodo.nome == saida:	
				Relacionar(nodo,nodo,nodos,entradas,"dir")
	
	#Realiza a validacao logica de cada nodo para cada entrada
	for nodo in nodos:
		for saida in saidas:
			Validar(nodo, entradas, nodos, saida, saidas)
	return nodos
