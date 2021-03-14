from param import Entrada
analiseManual = False

#Ajusta as casas decimais a partir da notacao cientifica
def Ajustar_valor(tensao):
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

#Funcao que escreve as informacoes dos SETs em tabelas CSV
def Escrever_CSV(tabela, nodos):
    linha = 2
    with open(tabela, "w") as sets:
        sets.write("nodo,saida,pulso,pulso,corrente,set,validacoes->\n")
        for nodo in nodos:
            for relacao in nodo.relacoes:
                tipo = relacao[1]
                combinacoes = []
                # identifica a relacao do nodo com a saida
                if tipo == "inv":
                    combinacoes = [["up", "down"], ["down", "up"]]
                elif tipo == "dir":
                    combinacoes = [["up", "up"], ["down", "down"]]
                elif tipo == "com":
                    combinacoes = [["up", "up"], ["down", "down"], ["up", "down"], ["down", "up"]]
                for i in range(len(combinacoes)):
                    sets.write(nodo.nome + "," + relacao[0] + "," + combinacoes[i][0] + "," + combinacoes[i][1] + ",")
                    sets.write(
                        str(relacao[2 + 2 * i]) + "E-6,=E" + str(linha) + "*(0.000000000164 - 5E-11)/(1.08E-14*0.000000021)")
                    for validacao in relacao[3 + 2 * i]:
                        sets.write(",'")
                        for num in validacao:
                            sets.write(str(num))
                    sets.write("\n")
                    linha += 1
    print("Tabela "+tabela+" gerada com sucesso\n")

#Escreve informacoes no arquivo "vdd.txt"
def Definir_Tensao(vdd):
    with open("vdd.txt", "w") as arquivoVdd:
        arquivoVdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
        arquivoVdd.write("Vvdd vdd gnd " + str(vdd) + "\n")
        arquivoVdd.write("Vclk clk gnd PULSE(0 " + str(vdd) + " 1n 0.01n 0.01n 1n 2n)")

#Descobre quais as entradas do circuto a partir do arquivo "fontes.txt"
def Instanciar_Entradas(fontes):
    entradas = list()
    with open(fontes, "r") as fonte:
        for linha in fonte:
            if "V" in linha:
                a, nome, b, c = linha.split()
                entrada = Entrada(nome, "t")
                entradas.append(entrada)
    return entradas

#Escreve a tensao no arquivo "fontes.txt"
def Definir_Fontes(fontes, vdd, entradas):
    with open(fontes, "w") as sinais:
        sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")
        for i in range(len(entradas)):
            sinais.write("V" + entradas[i].nome + " " + entradas[i].nome + " gnd ")
            if entradas[i].sinal == 1:
                sinais.write(str(vdd) + "\n")
            elif entradas[i].sinal == 0:
                sinais.write("0.0\n")
            elif entradas[i].sinal == "rise":
                sinais.write("PWL(0n 0 1n "+str(vdd)+")\n")
            elif entradas[i].sinal == "fall":
                sinais.write("PWL(0n "+str(vdd)+" 1n 0)\n")
            else:
                print("ERRO SINAL NAO IDENTIFICADO RECEBIDO: ", entradas[i].sinal)

#Le a resposta do pulso no arquivo "texto.txt"
def Ler_Pulso(direcaoPulsoSaida, offset):
    linha_texto = list(range(4))
    texto = "texto.txt"
    tensao_pico = 3333
    with open(texto, "r") as text:
        if offset:
            linha_texto[0] = text.readline()
            linha_texto[1] = text.readline()

        linha_texto[0 + offset] = text.readline()
        tensao, tempo1 = linha_texto[0 + offset].split('    ')
        if tensao[7] == "=":
            a, min_tensao = tensao.split('=')
        else:
            a, min_tensao = tensao.split()

        linha_texto[1 + offset] = text.readline()
        tensao, tempo1 = linha_texto[1 + offset].split('    ')
        if tensao[7] == "=":
            a, max_tensao = tensao.split('=')
        else:
            a, max_tensao = tensao.split()

    # Converte as strings lidas em floats
    max_tensao = Ajustar_valor(max_tensao)
    min_tensao = Ajustar_valor(min_tensao)
    if analiseManual: print("Tensao max: " + str(max_tensao) + " Tensao min: " + str(min_tensao))

    # Identifica se o pico procurado e do tipo up ou down
    if direcaoPulsoSaida == "up":
        tensao_pico = max_tensao
    elif direcaoPulsoSaida == "down":
        tensao_pico = min_tensao
    else:
        print("ERRO: O TIPO DE PULSO NAO FOI IDENTIFICADO")

    # retorna a tensao de pico lida
    return tensao_pico

#Escreve informacoes no arquivo "SETs.txt"
def Ajustar_Pulso(arqvRadiacao, nodo, corrente, saida, direcaoPulsoNodo):
    with open(arqvRadiacao, "w") as sets:
        sets.write("*SETs para serem usados nos benchmarks\n")
        if direcaoPulsoNodo == "down": sets.write("*")
        sets.write("Iseu gnd " + nodo + " EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //up\n")
        if direcaoPulsoNodo == "up": sets.write("*")
        sets.write("Iseu " + nodo + " gnd EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //down\n")
        sets.write(".meas tran minout min V(" + saida + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxout max V(" + saida + ") from=1.0n to=4.0n\n")
        # Usado apenas na verificacao de validacao:
        sets.write(".meas tran minnod min V(" + nodo + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxnod max V(" + nodo + ") from=1.0n to=4.0n\n")

#Altera o arquivo "atraso.txt"
def Escrever_Atraso(entrada, saida, vdd, direcaoNodo, direcaoSaida):
    with open("atraso.txt","w") as atraso:
        atraso.write("*Arquivo com atraso a ser medido\n")
        tensao = vdd * 0.5
        atraso.write(".measure tran atraso TRIG v("+entrada.nome+") val='"+str(tensao)+"' "+direcaoNodo+"=1 TARG v("+saida+") val='"+str(tensao)+"' "+direcaoSaida+"=1")
