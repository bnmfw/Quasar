# Nao tenho certeza
def converter_binario(binario, validacao, variaveis):  # Converte o binario esquisito numa lista
    final = list(validacao)
    flag = 0
    binary = list()
    # Transforma binario em uma lista de verdade e ajusta a validacao
    for i in range(variaveis - (len(binario) - 2)): binary.append(0)
    for i in range(len(binario) - 2): binary.append(int(binario[i + 2]))
    for i in range(len(final)):
        if final[i] == "x":
            final[i] = binary[flag]
            flag += 1
    return final

# Recebe um inteiro e retonra uma lista com seus digitos binarios
def converter_binario_lista(inteiro, tamanho):
    lista = []
    binario = bin(inteiro)[2:] #Transforma o inteiro no binario em texto
    for digito in range(tamanho-len(binario)):
        lista.append(0)
    for digito in binario:
        lista.append(int(digito))
    return lista

# Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
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
