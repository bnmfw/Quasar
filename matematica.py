from math import sqrt
# Recebe um inteiro e retonra uma lista com seus digitos binarios
def bin2list(inteiro: int, tamanho:int) -> list:
    lista = []
    binario = bin(inteiro)[2:] #Transforma o inteiro no binario em texto
    for digito in range(tamanho-len(binario)):
        lista.append(0)
    for digito in binario:
        lista.append(int(digito))
    return lista

# Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
def ajustar(tensao: str) -> float:
    tensao = tensao.strip()
    grandeza = 0
    if tensao == "failed":
        return None
    if tensao[-1] in {"m", "M"}:
        grandeza = -3
    elif tensao[-1] in {"u", "U"}:
        grandeza = -6
    elif tensao[-1] in {"n", "N"}:
        grandeza = -9
    elif tensao[-1] in {"p", "P"}:
        grandeza = -12
    elif tensao[-1] in {"f", "F"}:
        grandeza = -15
    elif tensao[-1] in {"g", "G"}:
        grandeza = 9
    elif tensao[-1] in {"t", "T"}:
        grandeza = 12
    elif tensao[-1] not in ("0","1","2","3","4","5","6","7","8","9","."):
        raise ValueError(f"Recebi \"{tensao}\" como entrada de ajuste")
    else:
        return float(tensao)
    return float(tensao[:-1]) * 10 ** grandeza

# Converte uma corrente para LET
def corrente_para_let(corrente: float) -> float:
    return (corrente * 10 ** -6) * (0.000000000164 - (5 * 10 ** -11)) / ((1.08 * 10 ** -14) * 0.000000021)

# Retorna a media dos valores numa lista
def media(lista: list) -> float:
    acumulador: float = 0
    for num in lista:
        acumulador += num
    return acumulador/len(lista)

def desvio_padrao(lista: list, media: float) -> float:
    acumulador: float = 0
    for num in lista:
        acumulador += (media-num) ** 2
    acumulador = acumulador/(len(lista)-1)
    return sqrt(acumulador)


if __name__ == "__main__":
    assert ajustar("  24.56u ") == (24.56 * 10 ** -6), "ajuste_valor FALHOU"
    assert ajustar("2.349e-02") == 0.02349, "ajuste_valor FALHOU"
    assert bin2list(14, 4) == [1,1,1,0], "bin2list FALHOU"
    #assert converter_binario("0b10", ["x","x","x","x","x"], 5) == [0,0,0,1,0], "converter_binario FALHOU"
    assert corrente_para_let(100) == 50264550.26455026, "corrente_para_let FALHOU" # DEFINIDO PELA PROPRIA FUNCAO
    assert media([1.1, 2.8, 3.6, 4.1]) == 2.9, "media FALHOU"
    assert desvio_padrao([4, 9, 11, 12, 17, 5, 8, 12, 14], media([4, 9, 11, 12, 17, 5, 8, 12, 14])) == 4.176654695380556, "desvio_padrao FALHOU"