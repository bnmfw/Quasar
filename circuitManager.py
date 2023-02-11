from matematica import combinacoes_possiveis
from runner import HSRunner
from components import *
from letFinder import LetManager

barra_comprida = "---------------------------"
relatorio = False

class CircuitManager:
    def __init__(self):
        self.circuito = None
        self.__limite_sup: float = 400
        self.__limite_sim: int = 25
    
    ##### DETERMINA TODAS AS COMBINACOES POSSIVEIS DE LETS #####
    def __possible_LETs(self, nodos: list, saidas: list, n_entradas: int):
        jobs = [{"nodo": nodo, "saida": saida, "incl1": inc1, "incl2": inc2, "val": validacao}\
                for nodo in nodos\
                for saida in saidas\
                for inc1 in ["rise", "fall"]\
                for inc2 in ["rise", "fall"]\
                for validacao in combinacoes_possiveis(n_entradas)]
        return jobs
    
    ##### ENCONTRA O ATRASO DE CAMINHO CRITICO PARA UM CIRCUITO #####
    def get_atrasoCC(self, circuito):
        entrada_critica = None
        saida_critica = None
        circuito.atrasoCC = 0
        simulacoes: int = 0

        # Todas as entradas em todas as saidas com todas as combinacoes
        for entrada_analisada in circuito.entradas:
            for saida in circuito.saidas:
                for validacao in combinacoes_possiveis(len(circuito.entradas)):

                    index = 0
                    for entrada in circuito.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = validacao[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # Etapa de medicao de atraso
                    atraso: float = HSRunner.run_delay(circuito.path, circuito.arquivo, entrada_analisada.nome, saida.nome, circuito.vdd, circuito.entradas)

                    simulacoes += 1

                    if atraso > circuito.atrasoCC:
                        circuito.atrasoCC = atraso
                        saida_critica = saida.nome
                        entrada_critica = entrada.nome
        # with open("atrasoCC.txt", "a") as arq:
        #     arq.write(f"entada: {entrada_critica}\t saida: {saida_critica}\n")
        print(f"Atraso CC do arquivo: {circuito.atrasoCC} simulacoes: {simulacoes}")

    ##### ATUALIZA OS LETs DE UM CIRCUITO #####
    def atualizar_LETths(self, circuito, pmos=None, nmos=None, delay: bool = False):
        with HSRunner.Vdd(circuito.vdd):
            simulacoes: int = 0
            circuito.LETth = None
            ##### BUSCA DO LETs DO CIRCUITO #####
            for nodo in circuito.nodos:
                for let in nodo.LETs:
                    # try: 
                    ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                    if relatorio: print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                    simulacoes += LetManager.definir_corrente(circuito, let, let.validacoes[0], safe=True, delay=delay)
                    if relatorio: print(f"corrente: {let.corrente}\n")
                    if not circuito.LETth:
                        circuito.LETth = let
                    elif let < circuito.LETth: 
                        circuito.LETth = let
                    # except KeyboardInterrupt:
                    #     exit() 
                    # except (ValueError, KeyError):
                    #     with open("erros.txt", "a") as erro:
                    #         erro.write(f"pmos {pmos} nmos {nmos} {let.nodo_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
            print(f"{simulacoes} simulacoes feitas na atualizacao")

    ##### DETERMINA OS LETs DE UM CIRCUITO #####
    def determinar_LETths(self, circuito, delay: bool = False):
        for nodo in circuito.nodos:
            nodo.LETs = []
        simulacoes: int = 0
        
        ##### ITERA SOBRE TODAS AS COMBINACOES POSSIVEIS DE NODO, SAIDA, VALIDACAO E INCLINACOES #####
        for job in self.__possible_LETs(circuito.nodos, circuito.saidas, len(circuito.entradas)):

            ##### ENCONTRA O LETth PARA AQUELA COMBINACAO #####
            let_analisado = LET(None, circuito.vdd, job["nodo"].nome, job["saida"].nome, [job["incl1"], job["incl2"]])

            print(job["nodo"].nome, job["saida"].nome, job["incl1"], job["incl2"], job["val"])
            
            simulacoes += LetManager.definir_corrente(circuito, let_analisado, job["val"], delay = delay)

            # Nenhum Let encontrado
            if let_analisado.corrente == None:
                continue

            # Atualizacao do LETth do circuito
            if circuito.LETth is None or let_analisado < circuito.LETth:
                circuito.LETth = let_analisado

            for let in nodo.LETs:
                if let == let_analisado:
                    if let_analisado < let:
                        nodo.LETs.remove(let)
                        nodo.LETs.append(let_analisado)
                    elif let_analisado.corrente == let.corrente:
                        let.append(job["val"])
                    break
            else:
                if let_analisado.corrente < 10000:
                    nodo.LETs.append(let_analisado)

CircMan = CircuitManager()