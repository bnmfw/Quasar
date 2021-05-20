import os
from arquivos import *

# Funcao que verifica se aquela analise de radiacao eh valida (ou seja, se tem o efeito desejado na saida)
def verificar_validacao(circuito, arqv_radiacao, nodo, direcao_pulso_nodo, saida, direcao_pulso_saida, vdd):
    ajustar_pulso(arqv_radiacao, nodo, 0.0, saida, direcao_pulso_nodo)
    os.system("hspice " + circuito + " | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensao_pico_saida = ler_pulso(direcao_pulso_saida, 0)
    tensao_pico_nodo = ler_pulso(direcao_pulso_nodo, 2)
    if analise_manual:
        print("Verificacao de Sinal: Vpico nodo: " + str(tensao_pico_nodo) + " Vpico saida: " + str(
            tensao_pico_saida) + "\n")

    # Leitura sem pulso
    if direcao_pulso_saida == "rise" and tensao_pico_saida > vdd * 0.51:
        return [False, 1]
    elif direcao_pulso_saida == "fall" and tensao_pico_saida < vdd * 0.1:
        return [False, 1]
    elif direcao_pulso_nodo == "rise" and tensao_pico_nodo > vdd * 0.51:
        return [False, 1]
    elif direcao_pulso_nodo == "fall" and tensao_pico_nodo < vdd * 0.1:
        return [False, 1]

    ajustar_pulso(arqv_radiacao, nodo, 499.0, saida, direcao_pulso_nodo)
    os.system("hspice " + circuito + " | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensao_pico_saida = ler_pulso(direcao_pulso_saida, 0)
    tensao_pico_nodo = ler_pulso(direcao_pulso_nodo, 2)
    if analise_manual:
        print("Verificacao de Pulso: Vpico nodo: " + str(tensao_pico_nodo) + " Vpico saida: " + str(
            tensao_pico_saida) + "\n")
    # Leitura com pulso
    if direcao_pulso_saida == "rise" and tensao_pico_saida < vdd * 0.50:
        return [False, 2]
    elif direcao_pulso_saida == "fall" and tensao_pico_saida > vdd * 0.50:
        return [False, 2]
    elif direcao_pulso_nodo == "rise" and tensao_pico_nodo < vdd * 0.50:
        return [False, 2]
    elif direcao_pulso_nodo == "fall" and tensao_pico_nodo > vdd * 0.50:
        return [False, 2]

    return [True, 2]


def largura_pulso(circuito, nodo, nodo_saida, vdd, atraso):  ##### REALIZA A MEDICAO DE LARGURA DE PULSO #####
    escrever_largura_pulso(nodo, nodo_saida, vdd)  # Determina os parametros no arquivo de leitura de largura de pulso
    os.system("hspice " + circuito + " | grep \"pulso\" > texto.txt")
    largura_de_pulso = ler_largura_pulso()
    if analise_manual:
        print("Atraso do circuito: " + str(atraso) + " Largura de pulso: " + str(largura_de_pulso))
    if atraso < largura_de_pulso:
        if analise_manual: print("Largura valida")
        return largura_de_pulso
    else:
        if analise_manual: print("Largura invalida")
        return 4444


def Corrente(circuito, vdd, entradas, direcao_pulso_nodo, direcao_pulso_saida, nodo, saida, validacao):
    radiacao = "SETs.txt"
    fontes = "fontes.txt"

    precisao = 0.05

    # Escreve a validacao no arquivo de fontes
    for i in range(len(entradas)):
        entradas[i].sinal = validacao[i]
    definir_fontes(fontes, vdd, entradas)
    # Verifica se as saidas estao na tensao correta pra analise de pulsos
    analise_valida, simulacoes_feitas = verificar_validacao(circuito, radiacao, nodo, direcao_pulso_nodo, saida,
                                                            direcao_pulso_saida, vdd)
    if not analise_valida:
        if simulacoes_feitas == 1: print("Analise invalida - Tensoes improprias\n")
	elif simulacoes_feitas == 2: print("Analise invalida - Pulso sem efeito\n")
	else: print("Analise invalida - WTF?\n")
        return [1111 * simulacoes_feitas, simulacoes_feitas]

    tensao_pico = 0

    # variaveis da busca binaria da corrente
    corrente_sup = 500
    corrente = 499
    corrente_inf = 0

    # Reseta os valores no arquivo de radiacao. (Se nao fizer isso o algoritmo vai achar a primeira coisa como certa)
    ajustar_pulso(radiacao, nodo, corrente, saida, direcao_pulso_nodo)

    while not ((1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2):

        # Roda o HSPICE e salva os valores no arquivo de texto
        os.system("hspice " + circuito + " | grep \"minout\|maxout\" > texto.txt")
        simulacoes_feitas += 1

        # Le a o pico de tensao na saida do circuito
        tensao_pico = ler_pulso(direcao_pulso_saida, 0)

        if analise_manual:
            print("Corrente testada: " + str(corrente) + " Resposta na saida: " + str(tensao_pico) + "\n")

        # Encerramento por excesso de simulacoes
        if simulacoes_feitas >= 25:
            if 1 < corrente < 499:
                print("Encerramento por estouro de ciclos maximos - Corrente encontrada\n")
                return[corrente, simulacoes_feitas]
            else:
                print("Encerramento por estouro de ciclos maximos - Corrente nao encontrada\n")
                return[3333, simulacoes_feitas]

        # Busca binaria
        elif direcao_pulso_saida == "fall":
            if tensao_pico <= (1 - precisao) * vdd / 2: corrente_sup = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2: corrente_inf = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente,simulacoes_feitas]
        elif direcao_pulso_saida == "rise":
            if tensao_pico <= (1 - precisao) * vdd / 2: corrente_inf = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2: corrente_sup = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoes_feitas]

        corrente = float((corrente_sup + corrente_inf) / 2)

        # Escreve os paramtros no arquivo dos SETs
        ajustar_pulso(radiacao, nodo, corrente, saida, direcao_pulso_nodo)
