from arquivos import Entrada, Nodo, instanciar_nodos

# Agrega os nodos a outros nodos por que orientacao a objeto arrebenta
def Agregar_Nodos(nodos, entradas):
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

# Recursao que encontra a relacao de um nodo com uma saida
def Relacionar(saida_global, saida, nodos, entradas, relacao_acumulada):
    # Finaliza a recursao quando chega nas entradas
    if type(saida) == str:
        print("ERRO: ENTRADA "+saida+" PROVAVELMENTE NAO DECLARADO NO ARQUIVO Fontes.txt")
    if saida in entradas:
        return 0
    else:
        for relacao in saida.relacoes:
            if relacao[0] == saida_global.nome:
                if relacao[1] == "nao":
                    relacao[1] = relacao_acumulada  # Salva a relacao do nodo com a global
                elif relacao[1] == relacao_acumulada:
                    print("Relacao repetida em:" + saida.nome, relacao[1])
                    pass
                else:
                    relacao[1] = "com"
                    relacao_acumulada = "com"
        # Atualiza as relacoes
        if saida.logica == "NAND" or saida.logica == "NOR" or saida.logica == "NOT":
            if relacao_acumulada == "dir":
                relacao_acumulada = "inv"
            elif relacao_acumulada == "inv":
                relacao_acumulada = "dir"
            elif relacao_acumulada == "com":
                pass
        elif saida.logica == "AND" or saida.logica == "OR":
            pass
        elif saida.logica == "XOR" or saida.logica == "XNOR":
            relacao_acumulada = "com"
        else:
            print("ERRO RELACAO NAO ENCONTRADA PARA:", saida.nome, saida.logica)

        for entrada in saida.entradas:
            Relacionar(saida_global, entrada, nodos, entradas, relacao_acumulada)

# Funcao que define sinais para entradas nao relevantes ao sinal analisado
def Fixar(saida, entradas):
    # Escolhe as paridades das entradas fixas
    paridade = "a"
    if saida.sinal == 1:
        if saida.logica == "NAND" or saida.logica == "NOR" or saida.logica == "NOT":
            paridade = 0
        elif saida.logica == "AND" or saida.logica == "OR":
            paridade = 1  # Pra realmente fixar todas as entradas tem que ser 1
        elif saida.logica == "XOR" or saida.logica == "XNOR":
            paridade = "x"
        else:
            print("PORTA LOGICA " + saida.nome + "NAO REGISTRADA (FIX)")
    elif saida.sinal == 0:
        if saida.logica == "NAND" or saida.logica == "NOR" or saida.logica == "NOT":
            paridade = 1  # Pra realmente fixar todas as entradas tem que ser 1
            permissaoPraMudarX = True
        elif saida.logica == "AND" or saida.logica == "OR":
            paridade = 0
        elif saida.logica == "XOR" or saida.logica == "XNOR":
            paridade = "x"
        else:
            print("PORTA LOGICA " + saida.nome + " NAO REGISTRADA (FIX)")

    # Altera os valores das entradas quando possivel
    for entrada in saida.entradas:
        if saida.sinal == "nx":  # x determinado na neutralizacao
            entrada.sinal = "nx"
        elif saida.sinal == "x":
            if entrada.sinal == "t": entrada.sinal = "x"
        elif saida.sinal == "t":  # t significa tanto faz kkkkkk
            pass
        elif saida.sinal == 0 or saida.sinal == 1:
            if entrada.sinal == "t":
                entrada.sinal = paridade
            elif entrada.sinal == "x":
                pass
            elif entrada.sinal != paridade and (paridade == 0 or paridade == 1):
                print("PARIDADE DUPLA PARA: " + entrada.nome + " NX ATRIBUIDO (FIX)")
                entrada.sinal = "nx"  # ele tambem pode atribuir nx aqui kkk
        else:
            print("ERRO TIPO DE SINAL NAO REGISTRADO: " + str(saida.sinal))

        # Repete a funcao pra entradas nao elementares
        if not entrada in entradas:
            Fixar(entrada, entradas)

# Funcao que recursivamente corre do nodo pra saida neutralizando entradas paralelas
def Neutralizar(saida, alvo, nodos, saidas):
    alvo.sinal = "x"
    for i in range(len(nodos)):
        for entrada in nodos[i].entradas:
            if entrada.nome == alvo.nome:  # Achou uma porta que tem o alvo como entrada
                paridade = -1
                if nodos[i].logica == "NAND" or nodos[i].logica == "AND":
                    paridade = 1
                elif nodos[i].logica == "NOR" or nodos[i].logica == "OR":
                    paridade = 0
                elif nodos[i].logica == "NOT":
                    pass
                elif nodos[i].logica == "XNOR" or nodos[i].logica == "XOR":
                    paridade = "nx"  # X determinado na neutralizacao, que deve ser fixado
                else:
                    print("PORTA LOGICA " + nodos[i].logica + " NAO REGISTRADA (NEU)")

                for outra_entrada in nodos[i].entradas:
                    if outra_entrada.nome != alvo.nome:  # Achou uma outra entrada e atribuiu o sinal
                        if outra_entrada.sinal == "t":
                            outra_entrada.sinal = paridade
                        elif outra_entrada.sinal == "x":
                            pass
                        elif outra_entrada.sinal == paridade:
                            pass
                        else:
                            print("PARADIDADE DUPLA PARA: " + outra_entrada.nome + " NX ATRIBUIDO (NEU)")
                            outra_entrada.sinal = "nx"

                # Repete o processo se nao eh saida global
                if nodos[i].nome in saidas:
                    pass
                else:
                    Neutralizar(saida, nodos[i], nodos, saidas)

# Finaliza as entradas logicas para ter apenas uma variavel
def Finalizar(entradas):
    for i in range(len(entradas)):
        if entradas[i].sinal == "t":
            entradas[i].sinal = 0
        elif entradas[i].sinal == "nx":
            entradas[i].sinal = "x"

# Gera as validacoes logicas de uma entrada para uma saida
def Validar(alvo, entradas, nodos, saida, saidas):
    logica_entrada = []

    # Zera a validacao se nao ha relacao, o que impede que a validacao logica seja feita mais pra frente
    for relacao in alvo.relacoes:
        if relacao[0] == saida and relacao[1] == "nao":
            for i in range(len(entradas)):
                logica_entrada.append(0)

    # Reseta todos os sinais
    for i in range(len(entradas)):
        entradas[i].sinal = "t"
    for i in range(len(nodos)):
        nodos[i].sinal = "t"

    # Altera a saida de string para objeto
    for i in range(len(nodos)):
        if nodos[i].nome == saida:
            saida = nodos[i]

        # Realiza as validacoes logicas
    alvo.sinal = "x"
    if not len(logica_entrada):

        Fixar(alvo, entradas)  # Declara como X todas as entradas que tem influencia no nivel logico do nodo

        Neutralizar(saida, alvo, nodos, saidas)  # Limpa o caminho do nodo ate a saida

        Fixar(saida, entradas)  # Fixa entradas ainda nao determinadas que tem influencia na saida

        Finalizar(entradas)  # Coloca em 0 entradas sem influencia na saida analisada

        # Salva a validacao logica em um vetor
        logica_entrada = list()
        for i in range(len(entradas)):
            logica_entrada.append(entradas[i].sinal)

    alvo.validacao.append([saida.nome, logica_entrada])

# Funcao que recebe o arquivo e retorna os parametros
def Parametrar(circuito, entradas, saidas):
    # Instanciacao de todos os nodos que nao entradas

    nodos = instanciar_nodos(circuito,saidas)

    Agregar_Nodos(nodos, entradas) #Agrega nodos a nodos

    # Define o relacionamento de cada nodo com cada saida
    for saida in saidas:
        for nodo in nodos:
            if nodo.nome == saida:
                Relacionar(nodo, nodo, nodos, entradas, "dir")

    # Realiza a validacao logica de cada nodo para cada entrada
    for nodo in nodos:
        for saida in saidas:
            Validar(nodo, entradas, nodos, saida, saidas)
    return nodos