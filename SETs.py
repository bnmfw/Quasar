from circuito import *
from time import time

def main():
    tempo_inicial = time()

    circuito = Circuito()
    circuito.run()



    ##### RELATORIO DE TEMPO DE EXECUCAO #####
    tempo_final = time()
    tempo_total = int(tempo_final - tempo_inicial)
    dias_de_simulacao = int(tempo_total / 86400)
    horas_de_simulacao = int((tempo_total % 86400) / 3600)
    minutos_de_simulacao = int((tempo_total % 3600) / 60)
    if dias_de_simulacao:
        print(str(dias_de_simulacao) + " dias, ", end='')
    if horas_de_simulacao:
        print(str(horas_de_simulacao) + " horas, ", end='')
    print(str(minutos_de_simulacao) + " minutos e " + str(tempo_total % 60) + " segundos de execucao\n")

if __name__ == '__main__':
    main()


# EU USAVA ISSO O
# for sets in self.sets_validos: print(sets)
# print("\n")
# for sets in self.sets_invalidos: print(sets)
#
# print("\n1111-SET invalidado em analise de tensao")
# print("2222-SET invalidado em analise de pulso")
# print("3333-SET Passou validacoes anteriores mas foi mal concluido")
# print("4444-SET invalidado em validacao de largura de pulso")
# print("5555-SET Aproximou indeterminadamente de um limite")
#
# # Retorno do numero de simulacoes feitas e de tempo de execucao
# print("\n" + str(self.simulacoes_feitas) + " simulacoes feitas\n")