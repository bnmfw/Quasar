from param import Entrada
analiseManual = False

#Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
def Ajustar_Valor(tensao):
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
                    combinacoes = [["rise", "fall"], ["fall", "rise"]]
                elif tipo == "dir":
                    combinacoes = [["rise", "rise"], ["fall", "fall"]]
                elif tipo == "com":
                    combinacoes = [["rise", "rise"], ["fall", "fall"], ["rise", "fall"], ["fall", "rise"]]
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
#Recebe vdd (float) e altera o vdd no arquivo e no clock
def Definir_Tensao(vdd):
    with open("vdd.txt", "w") as arquivoVdd:
        arquivoVdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
        arquivoVdd.write("Vvdd vdd gnd " + str(vdd) + "\n")
        arquivoVdd.write("Vclk clk gnd PULSE(0 " + str(vdd) + " 1n 0.01n 0.01n 1n 2n)")

#Descobre quais as entradas do circuto a partir do arquivo "fontes.txt" e retorna a lista com elas
def Instanciar_Entradas(fontes):
    entradas = list()
    with open(fontes, "r") as fonte:
        for linha in fonte:
            if "V" in linha:
                a, nome, b, c = linha.split()
                entrada = Entrada(nome, "t")
                entradas.append(entrada)
    return entradas

#Escreve os sinais no arquivo "fontes.txt"
def Definir_Fontes(fontes, vdd, entradas):
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
def Ler_Pulso(direcaoPulsoSaida, offset):
    linha_texto = list(range(4))
    texto = "texto.txt"
    tensao_pico = 3333
    with open(texto, "r") as text:
        if offset:
            linha_texto[0] = text.readline()
            linha_texto[1] = text.readline()

        linha_texto[0 + offset] = text.readline()
        linhaDeTensao = linha_texto[0 + offset].split()
        if len(linhaDeTensao[0]) != 7:
            min_tensao = linhaDeTensao[0][7:]
        else:
            min_tensao = linhaDeTensao[1]

        linha_texto[1 + offset] = text.readline()
        linhaDeTensao = linha_texto[1 + offset].split()
        if len(linhaDeTensao[0]) != 7:
            max_tensao = linhaDeTensao[0][7:]
        else:
            max_tensao = linhaDeTensao[1]

    # Converte as strings lidas em floats
    max_tensao = Ajustar_Valor(max_tensao)
    min_tensao = Ajustar_Valor(min_tensao)
    if analiseManual: print("Tensao max: " + str(max_tensao) + " Tensao min: " + str(min_tensao))

    # Identifica se o pico procurado e do tipo rise ou fall
    if direcaoPulsoSaida == "rise":
        tensao_pico = max_tensao
    elif direcaoPulsoSaida == "fall":
        tensao_pico = min_tensao
    else:
        print("ERRO: O TIPO DE PULSO NAO FOI IDENTIFICADO")

    # retorna a tensao de pico lida
    return tensao_pico

#Le o atraso do nodo a saida no arquivo "textp.txt"
def Ler_Atraso(vdd):
    texto = "texto.txt"
    linhasDeAtraso = list()
    linhasDeTensao = list()
    min_tensao = 0.0
    max_tensao = 0.0
    atrasos = list() #0 rr, 1 rf, 2 ff, 3 fr
    with open(texto,"r") as text:
        #Leitura das 4 linhas com atraso
        for i in range(4):
            linhasDeAtraso.append(text.readline().split())
            atrasos.append(linhasDeAtraso[i][1]) #salva os 4 atrasos
            if atrasos[i][0] == "(" or atrasos[i][0] == "f":
                atrasos[i] = "0.0p"
            atrasos[i] = Ajustar_Valor(atrasos[i])
        #Leitura das 2 linhas com tensao
        linhasDeTensao.append(text.readline().split())
        linhasDeTensao.append(text.readline().split())
        if len(linhasDeTensao[0][0]) != 7:
            min_tensao = linhasDeTensao[0][0][7:]
        else:
            min_tensao = linhasDeTensao[0][1]
        if len(linhasDeTensao[1][0]) != 7:
            max_tensao = linhasDeTensao[1][0][7:]
        else:
            max_tensao = linhasDeTensao[1][1]
	print(max_tensao,min_tensao)
        max_tensao = Ajustar_Valor(max_tensao)
        min_tensao = Ajustar_Valor(min_tensao)
        if abs(max_tensao-min_tensao) < vdd*0.2:
            for i in range(atrasos):
                atrasos[i]=0
    return atrasos

#Escreve informacoes no arquivo "SETs.txt"
def Ajustar_Pulso(arqvRadiacao, nodo, corrente, saida, direcaoPulsoNodo):
    with open(arqvRadiacao, "w") as sets:
        sets.write("*SETs para serem usados nos benchmarks\n")
        if direcaoPulsoNodo == "fall": sets.write("*")
        sets.write("Iseu gnd " + nodo + " EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //rise\n")
        if direcaoPulsoNodo == "rise": sets.write("*")
        sets.write("Iseu " + nodo + " gnd EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //fall\n")
        sets.write(".meas tran minout min V(" + saida + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxout max V(" + saida + ") from=1.0n to=4.0n\n")
        # Usado apenas na verificacao de validacao:
        sets.write(".meas tran minnod min V(" + nodo + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxnod max V(" + nodo + ") from=1.0n to=4.0n\n")

#Altera o arquivo "atraso.txt"
def Escrever_Atraso(entrada, saida, vdd):
    with open("atraso.txt","w") as atraso:
        atraso.write("*Arquivo com atraso a ser medido\n")
        tensao = str(vdd * 0.5)
        atraso.write(".measure tran atraso_rr TRIG v("+entrada.nome+") val='"+tensao+"' rise=1 TARG v("+saida+") val='"+tensao+"' rise=1\n")
        atraso.write(".measure tran atraso_rf TRIG v("+entrada.nome+") val='"+tensao+"' rise=1 TARG v("+saida+") val='"+tensao+"' fall=1\n")
        atraso.write(".measure tran atraso_ff TRIG v("+entrada.nome+") val='"+tensao+"' fall=1 TARG v("+saida+") val='"+tensao+"' fall=1\n")
        atraso.write(".measure tran atraso_fr TRIG v("+entrada.nome+") val='"+tensao+"' fall=1 TARG v("+saida+") val='"+tensao+"' rise=1\n")

