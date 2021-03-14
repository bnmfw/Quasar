import os
from arquivos import Ler_Pulso, Ajustar_Pulso, Definir_Fontes, analiseManual

#Funcao que verifica se aquela analise de radiacao eh valida (ou seja, se tem o efeito desejado na saida)
def Verificar_Validacao(circuito, arqvRadiacao, nodo, direcaoPulsoNodo, saida, direcaoPulsoSaida, vdd):
    Ajustar_Pulso(arqvRadiacao, nodo, 0.0, saida, direcaoPulsoNodo)
    os.system("hspice " + circuito + " | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensaoPicoSaida = Ler_Pulso(direcaoPulsoSaida, 0)
    tensaoPicoNodo = Ler_Pulso(direcaoPulsoNodo, 2)
    if analiseManual:
        print("Verificacao Vpico nodo: " + str(tensaoPicoNodo) + " Vpico saida: " + str(tensaoPicoSaida) + "\n")

    if direcaoPulsoSaida == "rise" and tensaoPicoSaida > vdd * 0.51:
        return False
    elif direcaoPulsoSaida == "fall" and tensaoPicoSaida < vdd * 0.1:
        return False
    elif direcaoPulsoNodo == "rise" and tensaoPicoNodo > vdd * 0.51:
        return False
    elif direcaoPulsoNodo == "fall" and tensaoPicoNodo < vdd * 0.1:
        return False
    else:
        return True

def Corrente(circuito, vdd, entradas, direcaoPulsoNodo, direcaoPulsoSaida, nodo, saida, validacao):
    radiacao = "SETs.txt"
    fontes = "fontes.txt"

    precisao = 0.1

    simulacoesFeitas = 1

    # Escreve a validacao no arquivo de fontes
    for i in range(len(entradas)):
        entradas[i].sinal = validacao[i]
    Definir_Fontes(fontes, vdd, entradas)

    # Verifica se as saidas estao na tensao correta pra analise de pulsos
    analiseValida = Verificar_Validacao(circuito, radiacao, nodo, direcaoPulsoNodo, saida, direcaoPulsoSaida, vdd)

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
    Ajustar_Pulso(radiacao, nodo, corrente, saida, direcaoPulsoNodo)

    while not ((1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2):

        # Roda o HSPICE e salva os valores no arquivo de texto
        os.system("hspice " + circuito + " | grep \"minout\|maxout\" > texto.txt")
        simulacoesFeitas += 1

        # Le a o pico de tensao na saida do circuito
        tensao_pico = Ler_Pulso(direcaoPulsoSaida, 0)

        if analiseManual: print("Corrente testada: " + str(corrente) + " Resposta na saida: " + str(tensao_pico) + "\n")

        # Encerramento por excesso de simulacoes
        if simulacoesFeitas >= 20:
            print("Encerramento por estouro de ciclos maximos\n")
            return [2222, simulacoesFeitas]
        # Busca binaria
        elif direcaoPulsoSaida == "fall":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_sup = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_inf = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoesFeitas]
        elif direcaoPulsoSaida == "rise":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_inf = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_sup = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoesFeitas]

        corrente = float((corrente_sup + corrente_inf) / 2)

        # Escreve os paramtros no arquivo dos SETs
        Ajustar_Pulso(radiacao, nodo, corrente, saida, direcaoPulsoNodo)