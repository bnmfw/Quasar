from .matematica import combinacoes_possiveis
from .spiceInterface import HSRunner
from .components import *
from .letFinder import LetFinder
from .concorrencia import ProcessMaster

barra_comprida = "---------------------------"
relatorio = False

class CircuitManager:
    def __init__(self, circuito):
        self.circuito = circuito
        self.let_manager = LetFinder(circuito)
        self.__limite_sup: float = 400
        self.__limite_sim: int = 25
    
    ##### DETERMINA TODAS AS COMBINACOES POSSIVEIS DE LETS #####
    def __possible_LETs(self, nodos: list, saidas: list, n_entradas: int):
        jobs = [[nodo, saida, inc1, inc2, validacao]\
                for nodo in nodos\
                for saida in saidas\
                for inc1 in ["rise", "fall"]\
                for inc2 in ["rise", "fall"]\
                for validacao in combinacoes_possiveis(n_entradas)]
        for i, job in enumerate(jobs):
            job.insert(0, i)
        return jobs
    
    ##### ENCONTRA O ATRASO DE CAMINHO CRITICO PARA UM CIRCUITO #####
    def get_atrasoCC(self):
        entrada_critica = None
        saida_critica = None
        self.circuito.atrasoCC = 0
        simulacoes: int = 0

        # Todas as entradas em todas as saidas com todas as combinacoes
        for entrada_analisada in self.circuito.entradas:
            for saida in self.circuito.saidas:
                for validacao in combinacoes_possiveis(len(self.circuito.entradas)):

                    index = 0
                    for entrada in self.circuito.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = validacao[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # Etapa de medicao de atraso
                    atraso: float = HSRunner.run_delay(self.circuito.path, self.circuito.arquivo, entrada_analisada.nome, saida.nome, self.circuito.vdd, self.circuito.entradas)

                    simulacoes += 1

                    if atraso > self.circuito.atrasoCC:
                        self.circuito.atrasoCC = atraso
                        saida_critica = saida.nome
                        entrada_critica = entrada.nome
        # with open("atrasoCC.txt", "a") as arq:
        #     arq.write(f"entada: {entrada_critica}\t saida: {saida_critica}\n")
        print(f"Atraso CC do arquivo: {self.circuito.atrasoCC} simulacoes: {simulacoes}")

    ##### ATUALIZA OS LETs DE UM CIRCUITO #####
    def atualizar_LETths(self, pmos=None, nmos=None, delay: bool = False):
        with HSRunner.Vdd(self.circuito.vdd):
            simulacoes: int = 0
            self.circuito.LETth = None
            ##### BUSCA DO LETs DO CIRCUITO #####
            for nodo in self.circuito.nodos:
                for let in nodo.LETs:
                    # try: 
                    ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                    if relatorio: print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                    simulacoes += self.let_manager.definir_corrente(let, let.validacoes[0], safe=True, delay=delay)
                    if relatorio: print(f"corrente: {let.corrente}\n")
                    if not self.circuito.LETth:
                        self.circuito.LETth = let
                    elif let < self.circuito.LETth: 
                        self.circuito.LETth = let
                    # except KeyboardInterrupt:
                    #     exit() 
                    # except (ValueError, KeyError):
                    #     with open("erros.txt", "a") as erro:
                    #         erro.write(f"pmos {pmos} nmos {nmos} {let.nodo_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
            # print(f"{simulacoes} simulacoes feitas na atualizacao")

    ##### RODA UM UNICO LET NAO TIRE O "_"#####
    def run_let_job(self, _, nodo, saida, inc1, inc2, validacao, delay):
        let_analisado = LET(None, self.circuito.vdd, nodo.nome, saida.nome, [inc1, inc2])
        self.let_manager.definir_corrente(let_analisado, validacao, delay = delay)
        return (let_analisado, validacao)
    
    ##### ENCONTRA OS LETS DO CIRCUITO #####
    def determinar_LETths(self, delay: bool = False):
        print("determinando lets")
        for nodo in self.circuito.nodos:
            nodo.LETs = []
    
        jobs = self.__possible_LETs(self.circuito.nodos, self.circuito.saidas, len(self.circuito.entradas))

        manager = ProcessMaster(self.circuito, self.run_let_job, jobs)
        manager.work((delay,),1)

        lets = manager.return_done()

        print("LETs calculados com sucesso")

        for (let, validacao) in lets:
            # Ignora correntes invalidas
            if let.corrente is None or let.corrente > 10000: continue

            for nodo_ in self.circuito.nodos:
                if nodo_.nome == let.nodo_nome:
                    nodo = nodo_

            # Atualizacao do LETth do circuito
            if self.circuito.LETth is None or let < self.circuito.LETth:
                self.circuito.LETth = let
            
            for let_possivel in nodo.LETs:
                if let_possivel == let:
                    if let < let_possivel:
                        nodo.LETs.remove(let_possivel)
                        nodo.LETs.append(let)
                    elif let.corrente == let_possivel.corrente:
                        let_possivel.append(validacao)
                    break
            else:
                nodo.LETs.append(let)

        print("fim da determinacao")