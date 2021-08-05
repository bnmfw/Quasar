from arquivos import *
from components import LET
from codificador import alternar_combinacao
import os

SR = SpiceManager()

# Funcao que verifica se aquela analise de radiacao eh valida (ou seja, se tem o efeito desejado na saida)
def verificar_validacao(circuito, nodo, direcao_pulso_nodo, saida, direcao_pulso_saida, vdd):
    SR.set_pulse(nodo, 0.0, saida, direcao_pulso_nodo)
    os.system(f"hspice {circuito} | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    print("Verificacao 1")
    with open("texto.txt", "r") as arq:
        print(arq.readline())
    tensao_pico_saida = SR.get_peak_tension(direcao_pulso_saida, 0)
    tensao_pico_nodo = SR.get_peak_tension(direcao_pulso_nodo, 2)

    if analise_manual:
        print(f"Verificacao de Sinal: Vpico nodo: {tensao_pico_nodo} Vpico saida: {tensao_pico_saida}\n")

    # Leitura sem pulso
    if direcao_pulso_saida == "rise" and tensao_pico_saida > vdd * 0.51: return [False, 1]
    elif direcao_pulso_saida == "fall" and tensao_pico_saida < vdd * 0.1: return [False, 1]
    elif direcao_pulso_nodo == "rise" and tensao_pico_nodo > vdd * 0.51: return [False, 1]
    elif direcao_pulso_nodo == "fall" and tensao_pico_nodo < vdd * 0.1: return [False, 1]

    SR.set_pulse(nodo, 499.0, saida, direcao_pulso_nodo)
    os.system(f"hspice {circuito} | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")

    tensao_pico_saida = SR.get_peak_tension(direcao_pulso_saida, 0)
    tensao_pico_nodo = SR.get_peak_tension(direcao_pulso_nodo, 2)

    if analise_manual:
        print(f"Verificacao de Pulso: Vpico nodo: {tensao_pico_nodo} Vpico saida: {tensao_pico_saida}\n")
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

def largura_pulso(circuito, nodo, nodo_saida, vdd, corrente, direcao_pulso_nodo, direcao_pulso_saida):  ##### REALIZA A MEDICAO DE LARGURA DE PULSO #####
    SR.set_pulse_width_param(nodo.nome, nodo_saida.nome, vdd, direcao_pulso_nodo, direcao_pulso_saida)  # Determina os parametros no arquivo de leitura de largura de pulso
    SR.set_pulse(nodo, corrente, nodo_saida, direcao_pulso_nodo)
    os.system(f"hspice {circuito} | grep \"atraso\|larg\" > texto.txt")
    return SR.get_pulse_delay_validation()

def encontrar_corrente_minima(circuito, vdd, nodo, saida, direcao_pulso_nodo, direcao_pulso_saida):
    # variaveis da busca binaria da corrente
    corrente_sup = 500
    corrente = 499
    corrente_inf = 0

    # Reseta os valores no arquivo de radiacao. (Se nao fizer isso o algoritmo vai achar a primeira coisa como certa)
    SR.set_pulse(nodo, corrente, saida, direcao_pulso_nodo)

    # Busca binaria para largura de pulso
    diferenca_largura = 100
    precisao_largura = 0.05
    precisao_largura = precisao_largura * 10 ** -9

    # Busca binaria para corrente minima
    while (diferenca_largura == "pulso_muito_pequeno") or not (-precisao_largura < diferenca_largura < precisao_largura):
        #
        diferenca_largura = largura_pulso(circuito, nodo, saida, vdd, corrente, direcao_pulso_nodo, direcao_pulso_saida)
        if abs(corrente_sup - corrente_inf) < 3:
            print("PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA")
            return corrente
        elif diferenca_largura == "pulso_muito_pequeno":  # Caso que o pulso foi tao pequeno que o atraso sequer foi medido
            corrente_inf = corrente
        elif diferenca_largura > precisao_largura:
            corrente_sup = corrente
        elif diferenca_largura < -precisao_largura:
            corrente_inf = corrente
        corrente = float((corrente_sup + corrente_inf) / 2)

    print("PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA")
    return corrente

def definir_corrente(circuito, let:LET, validacao:list) -> list:
    direcao_pulso_nodo = alternar_combinacao(let.orientacao)[0]
    direcao_pulso_saida = alternar_combinacao(let.orientacao)[1]
    nodo = circuito.encontrar_nodo(let.nodo_nome)
    saida = circuito.encontrar_nodo(let.saida_nome)
    precisao = 0.05

    # Renomeamento de variaveis
    vdd = circuito.vdd
    entradas = circuito.entradas
    circuito = circuito.arquivo

    # Escreve a validacao no arquivo de fontes
    for i in range(len(entradas)):
        entradas[i].sinal = validacao[i]
    SR.set_signals(vdd, entradas)

    # Verifica se as saidas estao na tensao correta pra analise de pulsos
    analise_valida, simulacoes_feitas = verificar_validacao(circuito, nodo, direcao_pulso_nodo, saida,
                                                            direcao_pulso_saida, vdd)
    if not analise_valida:
        if simulacoes_feitas == 1:
            print("Analise invalida - Tensoes improprias\n")
        elif simulacoes_feitas == 2:
            print("Analise invalida - Pulso sem efeito\n")
        else:
            print("Analise invalida - WTF?\n")
        let.corrente = 1111*simulacoes_feitas
        return simulacoes_feitas

    tensao_pico = 0

    # variaveis da busca binaria da corrente
    corrente_sup = 500
    corrente_inf = encontrar_corrente_minima(circuito, vdd, nodo, saida, direcao_pulso_nodo, direcao_pulso_saida)
    corrente = corrente_inf

    # Busca binaria para dar bit flip
    while not ((1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2):

        # Roda o HSPICE e salva os valores no arquivo de texto
        os.system(f"hspice {circuito} | grep \"minout\|maxout\" > texto.txt")
        simulacoes_feitas += 1

        # Le a o pico de tensao na saida do arquivo
        tensao_pico = SR.get_peak_tension(direcao_pulso_saida, 0)

        if analise_manual:
            print(f"Corrente testada: {corrente} Resposta na saida: {tensao_pico}\n")

        # Encerramento por excesso de simulacoes
        if simulacoes_feitas >= 25:
            if 1 < corrente < 499:
                print("Encerramento por estouro de ciclos maximos - Corrente encontrada\n")
                let.corrente = corrente
            else:
                print("Encerramento por estouro de ciclos maximos - Corrente nao encontrada\n")
                let.corrente = 3333
            return simulacoes_feitas

        # Encerramento por precisao satisfatoria
        elif corrente_sup-corrente_inf < 1:
            if 1 < corrente < 499:
                print("Corrente encontrada - Aproximacao nao convencional\n")
                let.corrente = corrente
            else:
                print("Corrente nao encontrada - Aproximacao extrema\n")
                let.corrente = 5555
            return simulacoes_feitas

        # Busca binaria
        elif direcao_pulso_saida == "fall":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_sup = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_inf = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                let.corrente = corrente
                return simulacoes_feitas
        elif direcao_pulso_saida == "rise":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_inf = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_sup = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                let.corrente = corrente
                return simulacoes_feitas

        corrente = float((corrente_sup + corrente_inf) / 2)

        # Escreve os parametros no arquivo dos SETs
        SR.set_pulse(nodo, corrente, saida, direcao_pulso_nodo)