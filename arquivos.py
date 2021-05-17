class Entrada():
    def __init__(self, nome, sinal):
        self.nome = nome
        self.sinal = sinal
        self.atraso = [0,"saida.nome",["Vetor de validacao"]]

class Nodo():
    def __init__(self, nome, entradas = None, logica = None, relacoes = None, sinal = None, validacao = None):
        if validacao == None: validacao = []
        if relacoes == None: relacoes = []
        self.nome = nome
        self.entradas = entradas  # Lista de objetos
        self.logica = logica  # Logica da porta que o tem como saida
        self.relacoes = relacoes  # Tipo de relacao com cada saida: inv, dir, nao, com
        self.sinal = sinal  # Sinal logico (usado apenas na validacao)
        self.validacao = validacao  # Lista que contem 1 lista pra cara saida contendo: [nome da saida, validacao generica]
        self.LETth = {}

analise_manual = True

#Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
def ajustar_valor(tensao):
    grandeza = 0
    if tensao[-1] == "m":
        grandeza = -3
    elif tensao[-1] == "u":
        grandeza = -6
    elif tensao[-1] == "n":
        grandeza = -9
    elif tensao[-1] == "p":
        grandeza = -12
    elif tensao[-1] == "f":
        grandeza = -15
    tensao = tensao[:-1]
    tensao = float(tensao)
    tensao = tensao * 10 ** grandeza
    return tensao

#Recebe o nome de uma tabela e os nodos do circuito analisado, entao escreve nessa tabela os LETs de cada nodo alem de outras informacoes
def escrever_csv(tabela, nodos):
    linha = 2
    with open(tabela, "w") as sets:
        sets.write("nodo,saida,pulso,pulso,corrente,set,num val,validacoes->\n")
        for nodo in nodos:
            for relacao in nodo.relacoes:
                combinacoes = []
                offset = 0
                # identifica a relacao do nodo com a saida
                if relacao[5] < 1111 and relacao[1] < 1111:
                    combinacoes = [["rise", "rise"], ["fall", "fall"], ["rise", "fall"], ["fall", "rise"]]
                elif relacao[1] < 1111:
                    combinacoes = [["rise", "rise"], ["fall", "fall"]]
                elif relacao[5] < 1111:
                    combinacoes = [["rise", "fall"], ["fall", "rise"]]
                    offset = 4
                for i in range(len(combinacoes)):
                    sets.write(nodo.nome + "," + relacao[0] + "," + combinacoes[i][0] + "," + combinacoes[i][1] + ",")
                    sets.write(str(relacao[1 + offset + 2 * i]) + "E-6,=E" + str(linha))
                    sets.write("*(0.000000000164 - 5E-11)/(1.08E-14*0.000000021)")
                    sets.write(str(len(relacao[2 + offset + 2 * i]))) #Numero de validacoes
                    for validacao in relacao[2 + offset + 2 * i]:
                        sets.write(",'")
                        for num in validacao:
                            sets.write(str(num))
                    sets.write("\n")
                    linha += 1
    print("Tabela "+tabela+" gerada com sucesso\n")

#Escreve informacoes no arquivo "vdd.txt"
def definir_tensao(vdd):
    with open("vdd.txt", "w") as arquivo_vdd:
        arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
        arquivo_vdd.write("Vvdd vdd gnd " + str(vdd) + "\n")
        arquivo_vdd.write("Vvcc vcc gnd " + str(vdd) + "\n")
        arquivo_vdd.write("Vclk clk gnd PULSE(0 " + str(vdd) + " 1n 0.01n 0.01n 1n 2n)")

#Descobre quais as entradas do circuto a partir do arquivo "fontes.txt" e retorna a lista com elas
def instanciar_entradas(entradas):
    novas_entradas = list()
    for entrada in entradas:
        novas_entradas.append(Entrada(entrada,"t"))
    return novas_entradas

#Descobre quais os nodos nao do circuito a partir de um arquivo "circuito.txt"
def instanciar_nodos(circuito, saidas, entradas):
    nodos = list()
    nodos_nomes = list()
    inputs = list()
    for entrada in entradas:
        inputs.append(entrada)
        inputs.append("ta")
        inputs.append("tb")
        inputs.append("tc")
        inputs.append("td")
        inputs.append("te")
        inputs.append("fa")
        inputs.append("fb")
        inputs.append("fc")
        inputs.append("fd")
        inputs.append("fe")
    with open(circuito, "r") as circ:
        for linha in circ:
            if "M" in linha:
                transistor, coletor, base, emissor, bulk, modelo, nfin = linha.split()
                nodos_interessantes = [coletor, base, emissor]
                for nodo_interessante in nodos_interessantes:
                    if nodo_interessante not in nodos_nomes and nodo_interessante not in ["vdd","gnd"] and nodo_interessante not in inputs:
                        nodo = Nodo(nodo_interessante)
                        nodos_nomes.append(nodo_interessante)
                        for output in saidas:
                            nodo.relacoes.append([output])
                        nodos.append(nodo)
    return nodos

#Escreve os sinais no arquivo "fontes.txt"
def definir_fontes(fontes, vdd, entradas):
    with open(fontes, "w") as sinais:
        sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")
        for i in range(len(entradas)):
            sinais.write("V" + entradas[i].nome + " " + entradas[i].nome + " gnd ")
            if entradas[i].sinal == 1:
                sinais.write(str(vdd) + "\n")
            elif entradas[i].sinal == 0:
                sinais.write("0.0\n")
            elif entradas[i].sinal == "atraso":
                sinais.write("PWL(0n 0 1n 0 1.01n "+str(vdd)+" 3n "+str(vdd)+" 3.01n 0)\n")
            else:
                print("ERRO SINAL NAO IDENTIFICADO RECEBIDO: ", entradas[i].sinal)

#Le a resposta do pulso no arquivo "texto.txt"
def ler_pulso(direcao_pulso_saida, offset):
    linha_texto = list(range(4))
    texto = "texto.txt"
    tensao_pico = 3333
    with open(texto, "r") as text:
        if offset:
            linha_texto[0] = text.readline()
            linha_texto[1] = text.readline()

        linha_texto[0 + offset] = text.readline()
        linha_de_tensao = linha_texto[0 + offset].split()
        if len(linha_de_tensao[0]) != 7:
            min_tensao = linha_de_tensao[0][7:]
        else:
            min_tensao = linha_de_tensao[1]

        linha_texto[1 + offset] = text.readline()
        linha_de_tensao = linha_texto[1 + offset].split()
        if len(linha_de_tensao[0]) != 7:
            max_tensao = linha_de_tensao[0][7:]
        else:
            max_tensao = linha_de_tensao[1]

    # Converte as strings lidas em floats
    max_tensao = ajustar_valor(max_tensao)
    min_tensao = ajustar_valor(min_tensao)
    if analise_manual: print("Tensao max: " + str(max_tensao) + " Tensao min: " + str(min_tensao))

    # Identifica se o pico procurado e do tipo rise ou fall
    if direcao_pulso_saida == "rise":
        tensao_pico = max_tensao
    elif direcao_pulso_saida == "fall":
        tensao_pico = min_tensao
    else:
        print("ERRO: O TIPO DE PULSO NAO FOI IDENTIFICADO")

    # retorna a tensao de pico lida
    return tensao_pico

#Le o atraso do nodo a saida no arquivo "texto.txt"
def ler_atraso(vdd):
    texto = "texto.txt"
    linhas_de_atraso = list()
    atrasos = list() #0 rr, 1 rf, 2 ff, 3 fr
    with open(texto,"r") as text:
        #Leitura das 4 linhas com atraso
        for i in range(4):
            linhas_de_atraso.append(text.readline().split())
            if linhas_de_atraso[i][0][0] == "*":
                #print(linhas_de_atraso[i][0])
                return [0,0,0,0]

            atrasos.append(linhas_de_atraso[i][1]) #salva os 4 atrasos
            atrasos[i] = ajustar_valor(atrasos[i])
        linhas_de_atraso.append(text.readline().split())
        largura_pulso_saida = linhas_de_atraso[4][1]
        largura_pulso_saida = abs(ajustar_valor(largura_pulso_saida))
        if largura_pulso_saida < 1 * 10**-9: #Largura de pulso menor que 1 nanosegundo
            #print("Pulso menor que 1 nano",largura_pulso_saida)
            return [0,0,0,0]
    return atrasos

#Le a validacao predeterminada em um arquivo "valcircuito.txt"
def ler_validacao(circuito, nodos, saidas):
    arq_validacao = "val" + circuito
    linhas = list()
    #Leitura das linhas
    with open(arq_validacao, "r") as arquivo:
        for linha in arquivo:
            linhas.append(linha)
    atraso = float(linhas[0].split()[1]) * 10 ** -12
    for nodo in nodos:
        validacao = list()
        for linha in linhas:
            nome,resto = linha.split(" ",1)
            if nome == nodo.nome:
                sinais_de_entrada = resto.split()
                for saida in saidas:
                    sinais_de_entrada.remove(saida)
                sinais_de_entrada_1 = sinais_de_entrada[:5]
                for i in range(len(sinais_de_entrada_1)):
                    try: sinais_de_entrada_1[i] = int(sinais_de_entrada_1[i])
                    except: pass
                validacao.append([saidas[0], sinais_de_entrada_1])
                sinais_de_entrada_2 = sinais_de_entrada[-5:]
                #Conversao de string pra inteiro
                for i in range(len(sinais_de_entrada_2)):
                    try: sinais_de_entrada_2[i] = int(sinais_de_entrada_2[i])
                    except: pass
                validacao.append([saidas[1], sinais_de_entrada_2])
                break
        if not len(validacao):
            for saida in saidas:
                validacao.append([saida,["x","x","x","x","x"]])
        nodo.validacao = validacao
    return atraso

#Escreve informacoes no arquivo "SETs.txt"
def ajustar_pulso(arqv_radiacao, nodo, corrente, saida, direcao_pulso_nodo):
    #saida = saida.nome
    nodo = nodo.nome
    with open(arqv_radiacao, "w") as sets:
        sets.write("*SETs para serem usados nos benchmarks\n")
        if direcao_pulso_nodo == "fall": sets.write("*")
        sets.write("Iseu gnd " + nodo + " EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //rise\n")
        if direcao_pulso_nodo == "rise": sets.write("*")
        sets.write("Iseu " + nodo + " gnd EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //fall\n")
        sets.write(".meas tran minout min V(" + saida + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxout max V(" + saida + ") from=1.0n to=4.0n\n")
        # Usado apenas na verificacao de validacao:
        sets.write(".meas tran minnod min V(" + nodo + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxnod max V(" + nodo + ") from=1.0n to=4.0n\n")

#Altera o arquivo "atraso.txt"
def escrever_atraso(entrada, saida, vdd):
    with open("atraso.txt","w") as atraso:
        atraso.write("*Arquivo com atraso a ser medido\n")
        tensao = str(vdd * 0.5)
        atraso.write(".meas tran atraso_rr TRIG v("+entrada.nome+") val='"+tensao+"' rise=1 TARG v("+saida+") val='"+tensao+"' rise=1\n")
        atraso.write(".meas tran atraso_rf TRIG v("+entrada.nome+") val='"+tensao+"' rise=1 TARG v("+saida+") val='"+tensao+"' fall=1\n")
        atraso.write(".meas tran atraso_ff TRIG v("+entrada.nome+") val='"+tensao+"' fall=1 TARG v("+saida+") val='"+tensao+"' fall=1\n")
        atraso.write(".meas tran atraso_fr TRIG v("+entrada.nome+") val='"+tensao+"' fall=1 TARG v("+saida+") val='"+tensao+"' rise=1\n")
        atraso.write(".meas tran largura TRIG v("+saida+") val='"+tensao+"' fall=1 TARG v("+saida+") val='"+tensao+"' rise=1\n")

#Altera o arquivo "largura_pulso.txt"
def escrever_largura_pulso(nodo,saida,vdd):
    with open ("largura_pulso.txt","w") as larg:
        larg.write("*Arquivo com a leitura da lergura dos pulsos\n")
        tensao = str(vdd*0.5)
        larg.write(".meas tran pulso TRIG v("+saida+") val='"+tensao+"' rise=1 TARG v("+saida+") val='"+tensao+"' fall=1\n")

#Leitura do arquivo "leitura_pulso.txt"
def ler_largura_pulso():
    with open("texto.txt","r") as larg:
        pulso = larg.readline().split()
    if analise_manual: print(pulso)
    if pulso[0][0] == "*":
            return 0
    if "-" in pulso[0]:
        pulso = pulso[0].split("-")
        pulso = ajustar_valor(pulso[1])
        return pulso
