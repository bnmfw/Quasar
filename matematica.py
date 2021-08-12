from math import sqrt
from statistics import stdev
# Recebe um inteiro e retonra uma lista com seus digitos binarios
def converter_binario_lista(inteiro: int, tamanho:int) -> list:
    lista = []
    binario = bin(inteiro)[2:] #Transforma o inteiro no binario em texto
    for digito in range(tamanho-len(binario)):
        lista.append(0)
    for digito in binario:
        lista.append(int(digito))
    return lista

# Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
def ajustar_valor(tensao: str) -> float:
    tensao = tensao.strip()
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
    else:
        return float(tensao)
    return float(tensao[:-1]) * 10 ** grandeza

# Converte uma corrente para LET
def corrente_para_let(corrente: float) -> float:
    return (corrente * 10 ** -6) * (0.000000000164 - (5 * 10 ** -11)) / ((1.08 * 10 ** -14) * 0.000000021)

if __name__ == "__main__":
    assert ajustar_valor("  24.56u ") == (24.56 * 10 ** -6), "ajuste_valor FALHOU"
    assert ajustar_valor("2.349e-02") == 0.02349, "ajuste_valor FALHOU"
    assert converter_binario_lista(14, 4) == [1,1,1,0], "converter_binario_lista FALHOU"
    #assert converter_binario("0b10", ["x","x","x","x","x"], 5) == [0,0,0,1,0], "converter_binario FALHOU"
    assert corrente_para_let(100) == 50264550.26455026, "corrente_para_let FALHOU" # DEFINIDO PELA PROPRIA FUNCAO