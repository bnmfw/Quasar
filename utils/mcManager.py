from .spiceInterface import HSRunner
from .components import *
from .concorrencia import PersistentProcessMaster
from .arquivos import CManager
from .circuitManager import CircuitManager

barra_comprida = "---------------------------"

class MCManager:
    def __init__(self, circuito, delay: bool = False):
        self.circuito = circuito
        self.circ_man = CircuitManager(circuito)
        self.delay = delay

        # Estado de simulacoes MC
        self.em_analise: bool = False
        self.total_jobs: int = None
        self.done_jobs: int = 0   

    ##### GERA OS PONTOS DE VARIABILIDADE E OS SALVA EM self.__var ####
    def __determinar_variabilidade(self, num_analises: int):
        # num_analises = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        print("Gerando pontos MC")
        var: dict = HSRunner.run_MC_var(self.circuito.path, self.circuito.arquivo, self.circuito.nome, num_analises)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        # Estado do manejador
        items = list(var.items())
        return items

    ##### RODA UMA INSTANCIA DA ANALISE MONTE CARLO ##### 
    def run_mc_iteration(self, index: int, point: list, delay: bool = False):
        pmos, nmos = point
         ### Guarda que com ctz tem como melhorar
        with HSRunner.MC_Instance(pmos, nmos):
            if delay: self.circ_man.get_atrasoCC()
            self.circ_man.atualizar_LETths(pmos, nmos, delay=delay)
            result = (round(pmos,4), round(nmos,4), self.circuito.LETth.nodo_nome, self.circuito.LETth.saida_nome, self.circuito.LETth.corrente, self.circuito.LETth.valor)
        return result
    
    ##### REALIZA A ANALISE MONTE CARLO TOTAL #####
    def analise_monte_carlo_total(self, n_analises: int, continuar:bool = False, delay:bool = False, progress_report = None):

        manager = PersistentProcessMaster(self.circuito, self.run_mc_iteration, None, f"circuitos/{self.circuito.nome}/MC", progress_report=progress_report)        

        ## Gera o arquivo caso nao exista ##
        if continuar and manager.check_backup():
            # print("\nSimulacao em andamento encontrada! continuando de onde parou...\n")
            manager.load_backup()
        else:
            jobs = self.__determinar_variabilidade(n_analises)
            manager.load_jobs(jobs)

        # A MAGIA ACONTECE AQUI
        manager.work((delay,))

        # Retorna os valores num csv
        saida = manager.return_done()
        CManager.tup_to_csv(f"{self.circuito.path}",f"{self.circuito.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

        # Destroi os arquivos de persistencia
        manager.delete_backup()
