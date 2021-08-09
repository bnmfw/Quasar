from arquivos import SpiceManager, analise_manual
from codificador import alternar_combinacao
from components import Entrada, Nodo, LET
import os

SR = SpiceManager()


# Funcao que verifica se aquela analise de radiacao eh valida (ou seja, se tem o efeito desejado na saida)
def verificar_validacao(circuito, vdd: float, let: LET) -> list:
    direcao_pulso_nodo = alternar_combinacao(let.orientacao)[0]
    direcao_pulso_saida = alternar_combinacao(let.orientacao)[1]
    nodo_nome = let.nodo_nome
    saida_nome = let.saida_nome
    SR.set_pulse(nodo_nome, 0.0, saida_nome, direcao_pulso_nodo)
    os.system(f"hspice {circuito.arquivo} | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensao_pico_saida = SR.get_peak_tension(direcao_pulso_saida, 0)
    tensao_pico_nodo = SR.get_peak_tension(direcao_pulso_nodo, 2)

    if analise_manual:
        print(f"Verificacao de Sinal: Vpico nodo: {tensao_pico_nodo} Vpico saida: {tensao_pico_saida}\n")

    # Leitura sem pulso
    if direcao_pulso_saida == "rise" and tensao_pico_saida > vdd * 0.51:
        return [False, 1]
    elif direcao_pulso_saida == "fall" and tensao_pico_saida < vdd * 0.1:
        return [False, 1]
    elif direcao_pulso_nodo == "rise" and tensao_pico_nodo > vdd * 0.51:
        return [False, 1]
    elif direcao_pulso_nodo == "fall" and tensao_pico_nodo < vdd * 0.1:
        return [False, 1]

    SR.set_pulse(nodo_nome, 499.0, saida_nome, direcao_pulso_nodo)
    os.system(f"hspice {circuito.arquivo} | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")

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


##### REALIZA A MEDICAO DE LARGURA DE PULSO #####
def largura_pulso(circuito, corrente: float, let: LET):
    direcao_pulso_nodo: str = alternar_combinacao(let.orientacao)[0]
    direcao_pulso_saida: str = alternar_combinacao(let.orientacao)[1]
    nodo: Nodo = circuito.encontrar_nodo(let.nodo_nome)
    saida: Nodo = circuito.encontrar_nodo(let.saida_nome)
    vdd: float = circuito.vdd
    # Determina os parametros no arquivo de leitura de largura de pulso
    SR.set_pulse_width_param(nodo.nome, saida.nome, vdd, direcao_pulso_nodo, direcao_pulso_saida)
    SR.set_pulse(nodo.nome, corrente, saida.nome, direcao_pulso_nodo)
    os.system(f"hspice {circuito.arquivo} | grep \"atraso\|larg\" > texto.txt")
    return SR.get_pulse_delay_validation()


def encontrar_corrente_minima(circuito, let: LET) -> float:
    direcao_pulso_nodo: str = alternar_combinacao(let.orientacao)[0]

    # variaveis da busca binaria da corrente
    corrente_sup: float = 500
    corrente: float = 499
    corrente_inf: float = 0

    # Reseta os valores no arquivo de radiacao. (Se nao fizer isso o algoritmo vai achar a primeira coisa como certa)
    SR.set_pulse(let.nodo_nome, corrente, let.saida_nome, direcao_pulso_nodo)

    # Busca binaria para largura de pulso
    diferenca_largura: float = 100
    precisao_largura: float = 0.05 * 10 ** -9

    # Busca binaria para corrente minima
    while not (-precisao_largura < diferenca_largura < precisao_largura):
        #
        diferenca_largura: float = largura_pulso(circuito, corrente, let)

        if abs(corrente_sup - corrente_inf) < 3:
            print("PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA")
            return corrente
        elif diferenca_largura > precisao_largura: corrente_sup = corrente
        elif diferenca_largura < -precisao_largura: corrente_inf = corrente
        corrente = float((corrente_sup + corrente_inf) / 2)

    print("PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA")
    return corrente


def definir_corrente(circuito, let: LET, validacao: list) -> int:
    direcao_pulso_nodo: str = alternar_combinacao(let.orientacao)[0]
    direcao_pulso_saida: str = alternar_combinacao(let.orientacao)[1]
    precisao: float = 0.05

    # Renomeamento de variaveis
    vdd: float = circuito.vdd
    entradas: list = circuito.entradas

    # Escreve a validacao no arquivo de fontes
    for i in range(len(entradas)):
        entradas[i].sinal = validacao[i]
    SR.set_signals(vdd, entradas)

    # Verifica se as saidas estao na tensao correta pra analise de pulsos
    simulacoes_feitas: int = 0
    analise_valida, simulacoes_feitas = verificar_validacao(circuito, vdd, let)
    if not analise_valida:
        if simulacoes_feitas == 1:
            print("Analise invalida - Tensoes improprias\n")
        elif simulacoes_feitas == 2:
            print("Analise invalida - Pulso sem efeito\n")
        else:
            print("Analise invalida - WTF?\n")
        let.corrente = 1111 * simulacoes_feitas
        return simulacoes_feitas

    tensao_pico: float = 0

    # variaveis da busca binaria da corrente
    corrente_sup: float = 500
    corrente_inf: float = encontrar_corrente_minima(circuito, let)
    corrente: float = corrente_inf

    # Busca binaria para dar bit flip
    while not ((1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2):

        # Roda o HSPICE e salva os valores no arquivo de texto
        os.system(f"hspice {circuito.arquivo} | grep \"minout\|maxout\" > texto.txt")
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
        elif corrente_sup - corrente_inf < 1:
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

        corrente: float = float((corrente_sup + corrente_inf) / 2)
        print(corrente)

        # Escreve os parametros no arquivo dos SETs
        SR.set_pulse(let.nodo_nome, corrente, let.saida_nome, direcao_pulso_nodo)

if __name__ == "__main__":

    # Criacao de um circuito falso
    let1 = LET(154.3, 0.7, "nodo1", "saida1", "fr")
    let2 = LET(300, 0.7, "nodo1", "saida1", "rf")
    let3 = LET(190.8, 0.7, "nodo2", "saida1", "fr")
    let4 = LET(156.9, 0.7, "nodo2", "saida1", "ff")
    let5 = LET(7.4, 0.7, "saida", "saida1", "rr")
    let6 = LET(288.1, 0.7, "saida", "saida1", "rf")

    nodo1 = Nodo("nodo1")
    nodo1.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo1.LETs = [let1, let2]
    nodo1.LETth = 154.3

    nodo2 = Nodo("nodo2")
    nodo2.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo2.LETs = [let2, let3]
    nodo2.LETth = 156.9

    nodo3 = Nodo("saida1")
    nodo3.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo3.LETs = [let4, let5]
    nodo3.LETth = 7.4


    class FakeCircuit:
        def __init__(self):
            self.nome = "Teste"
            self.arquivo = "Teste.txt"
            self.entradas = [Entrada("a", "t"), Entrada("b", "t")]
            self.saidas = [nodo3]
            self.nodos = [nodo1, nodo2, nodo3]
            self.vdd = 0.7
            self.atrasoCC = 9999.0