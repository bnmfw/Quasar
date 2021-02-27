import os

analiseManual = False

# Converte os valores em inteiros ajustando as casas decimais
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


def Ler_pulso(direcaoPulsoSaida, offset):
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


def Ajustar_pulso(arqvRadiacao, nodo, corrente, saida, direcaoPulsoNodo):
    with open(arqvRadiacao, "w") as sets:
        sets.write("*SETs para serem usados nos benchmarks\n")
        if direcaoPulsoNodo == "down": sets.write("*")
        sets.write("Iseu gnd " + nodo + " EXP(0 " + str(corrente) + "u 2n 10p 10p 200p) //up\n")
        if direcaoPulsoNodo == "up": sets.write("*")
        sets.write("Iseu " + nodo + " gnd EXP(0 " + str(corrente) + "u 2n 10p 10p 200p) //down\n")
        sets.write(".meas tran minout min V(" + saida + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxout max V(" + saida + ") from=1.0n to=4.0n\n")
        # Usado apenas na verificacao de validacao:
        sets.write(".meas tran minnod min V(" + nodo + ") from=1.0n to=4.0n\n")
        sets.write(".meas tran maxnod max V(" + nodo + ") from=1.0n to=4.0n\n")


def Definir_fontes(fontes, validacao, vdd, entradas):
    with open(fontes, "w") as sinais:
        sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")
        for i in range(len(validacao)):
            sinais.write("V" + entradas[i].nome + " " + entradas[i].nome + " gnd ")
            if validacao[i] == 1:
                sinais.write(str(vdd) + "\n")
            elif validacao[i] == 0:
                sinais.write("0.0\n")
            else:
                print("ERRO SINAL NAO BINARIO RECEBIDO: ", validacao[i])


def Verificar_validacao(circuito, arqvRadiacao, nodo, direcaoPulsoNodo, saida, direcaoPulsoSaida, vdd):
    corrente = 0
    Ajustar_pulso(arqvRadiacao, nodo, 0.0, saida, direcaoPulsoNodo)
    os.system("hspice " + circuito + " | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensaoPicoSaida = Ler_pulso(direcaoPulsoSaida, 0)
    tensaoPicoNodo = Ler_pulso(direcaoPulsoNodo, 2)
    if analiseManual:
        print("Verificacao Vpico nodo: " + str(tensaoPicoNodo) + " Vpico saida: " + str(tensaoPicoSaida) + "\n")

    if direcaoPulsoSaida == "up" and tensaoPicoSaida > vdd * 0.51:
        return False
    elif direcaoPulsoSaida == "down" and tensaoPicoSaida < vdd * 0.1:
        return False
    elif direcaoPulsoNodo == "up" and tensaoPicoNodo > vdd * 0.51:
        return False
    elif direcaoPulsoNodo == "down" and tensaoPicoNodo < vdd * 0.1:
        return False
    else:
        return True


def Corrente(circuito, vdd, entradas, direcaoPulsoNodo, direcaoPulsoSaida, nodo, saida, validacao):
    radiacao = "SETs.txt"
    fontes = "fontes.txt"

    precisao = 0.1

    simulacoesFeitas = 1

    # Escreve a validacao no arquivo de fontes
    Definir_fontes(fontes, validacao, vdd, entradas)

    # Verifica se as saidas estao na tensao correta pra analise de pulsos
    analiseValida = Verificar_validacao(circuito, radiacao, nodo, direcaoPulsoNodo, saida, direcaoPulsoSaida, vdd)

    if not analiseValida:
        print("Analise invalida\n")
        return [1111, simulacoesFeitas]

    tensao_pico = 0
    # max_tensao = 0
    # min_tensao = 0

    # variaveis da busca binaria da corrente
    corrente_sup = 500
    corrente = 499
    corrente_inf = 0

    # Reseta os valores no arquivo de radiacao. (Se nao fizer isso o algoritmo vai achar a primeira coisa como certa)
    Ajustar_pulso(radiacao, nodo, corrente, saida, direcaoPulsoNodo)

    while not ((1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2):

        # Roda o HSPICE e salva os valores no arquivo de texto
        os.system("hspice " + circuito + " | grep \"minout\|maxout\" > texto.txt")
        simulacoesFeitas += 1

        # Le a o pico de tensao na saida do circuito
        tensao_pico = Ler_pulso(direcaoPulsoSaida, 0)

        if analiseManual: print("Corrente testada: " + str(corrente) + " Resposta na saida: " + str(tensao_pico) + "\n")

        # Encerramento por excesso de simulacoes
        if simulacoesFeitas >= 20:
            print("Encerramento por estouro de ciclos maximos\n")
            return [2222, simulacoesFeitas]
        # Busca binaria
        elif direcaoPulsoSaida == "down":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_sup = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_inf = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoesFeitas]
        elif direcaoPulsoSaida == "up":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_inf = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_sup = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoesFeitas]

        corrente = float((corrente_sup + corrente_inf) / 2)

        # Escreve os paramtros no arquivo dos SETs
        Ajustar_pulso(radiacao, nodo, corrente, saida, direcaoPulsoNodo)
