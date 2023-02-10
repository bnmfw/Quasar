from matematica import combinacoes_possiveis
from runner import HSRunner
from components import *
from arquivos import CManager
from circuitManager import CircMan
from folders import ProcessFolder
import multiprocessing as mp
import json
import os
import time

barra_comprida = "---------------------------"

class MCManager:
    def __init__(self, circuito, delay: bool = False):
        self.circuito = circuito
        self.delay = delay

        # Estado de simulacoes MC
        self.em_analise: bool = False
        self.total_jobs: int = None
        self.done_jobs: int = 0

        # Sincronizacao
        self.lock_jobs = mp.Lock()
        self.lock_done = mp.Lock()
        self.lock_inpg = mp.Lock()

        # Queue dos trabalhos
        self.jobs = mp.Queue()
        self.done = mp.Queue()
        self.inpg = mp.Queue() #inpg = in progress

        # Copias dos conteudos das queues usados para dump e load
        self.jobs_copy = []
        self.done_copy = []
        self.inpg_copy = []    

    ##### RETORNA OS CONTEUDOS DE UMA QUEUE #####
    def __read_queue(self, queue: mp.Queue):
        contents = []
        for _ in range(queue.qsize()):
            value = queue.get()
            contents.append(value)
            queue.put(value)
        return contents
    
    ##### REMOVE UM ITEM DE UMA QUEUE, POR FAVOR NAO USE COM QUEUES LONGAS #####
    def __remove_from_queue(self, queue: mp.Queue, item):
        for _ in range(queue.qsize()):
            value = queue.get()
            if value == item: return
            queue.put(value)

    ##### DELETA OS ARQUIVOS DE CONTEXTO #####
    def __delete_MC(self):
        os.remove(f"circuitos/{self.circuito.nome}/MC_jobs.json")
        os.remove(f"circuitos/{self.circuito.nome}/MC_done.json")

    ##### DESCARREGA O CONTEXTO DAS SIMULACOES DA ANALISE MC #####
    def __dump_MC(self):
        json.dump(list(self.inpg_copy+self.jobs_copy), open(f"circuitos/{self.circuito.nome}/MC_jobs.json", "w"))
        json.dump(list(self.done_copy), open(f"circuitos/{self.circuito.nome}/MC_done.json", "w"))

    ##### CARREGA O CONTEXTO DAS SIMULACOES DA ANALISE MC #####
    def __load_MC(self, circuito):
        self.jobs_copy = json.load(open(f"circuitos/{circuito.nome}/MC_jobs.json", "r"))
        self.done_copy = json.load(open(f"circuitos/{circuito.nome}/MC_done.json", "r"))
        self.total_jobs = len(self.jobs_copy) + len(self.done_copy)
        # Carregamento das Queues
        for job in self.jobs_copy:
            self.jobs.put(job)
        for job in self.done_copy:
            self.done.put(job)

    ##### GERA OS PONTOS DE VARIABILIDADE E OS SALVA EM self.__var ####
    def __determinar_variabilidade(self, circuito):
        num_analises = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        print("Gerando instancias MC")
        var: dict = HSRunner.run_MC_var(circuito.path, circuito.arquivo, circuito.nome, num_analises)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        # Estado do manejador
        items = list(var.items())
        self.total_jobs = len(items)
        
        # Preenche a Queue dos trabalhos
        for item in items:
            self.jobs.put(item)

        # Persistencia do trabalho feito
        self.jobs_copy = items
        self.done_copy = []
        self.inpg_copy = []
        self.__dump_MC()

    # Retorna um ponto MC a ser calculado
    def request_job(self):
        with self.lock_jobs:
            # Nao ha mais trabalhos
            if self.jobs.empty():
                job = -1
            else:
                job = self.jobs.get()
                print(f"Started job: {job}")
                with self.lock_inpg:
                    self.inpg.put(job)
        return job
    
    # Recebe um ponto MC calculado
    def post_result(self, resultado, job):
        with self.lock_done:
            self.done.put(resultado)
            print(f"Finished job: {resultado}")
        with self.lock_inpg:
            self.__remove_from_queue(self.inpg, job)

    # Retorna um dicionario com os resultados da analise MC
    def return_done(self):
        ret = {}
        while not self.done.empty():
            key, value = self.done.get()
            ret[key] = value
        return ret

    ##### GERA OS PROCESSOS TRABALHADORES ##### 
    def work(self, n_workers: int = mp.cpu_count()):
        # Cria todos os processos que realizam as simulacoes MC
        workers = [mp.Process(target=MCSlave(self.circuito, len(self.jobs_copy), self.delay).run, args = (self,)) for _ in range(n_workers)]
        
        # Inicia os processos
        for worker in workers:
            worker.start()

        # Periodicamente salva o progresso a cada 10 minutos
        while True:
            time.sleep(420)
            print("Backuping jobs")
            with self.lock_jobs, self.lock_inpg, self.lock_done:
                self.jobs_copy = self.__read_queue(self.jobs)
                self.inpg_copy = self.__read_queue(self.inpg)
                self.done_copy = self.__read_queue(self.done)
                self.__dump_MC()
                if len(self.done_copy) == self.total_jobs: break
            print("Backup done")

        # Espera os processos finalizarem
        for worker in workers:
            worker.join()
    
    ##### REALIZA A ANALISE MONTE CARLO TOTAL #####
    def analise_monte_carlo_total(self, circuito, delay:bool = False):
        
        ## Gera o arquivo caso nao exista ##
        if os.path.exists(f"circuitos{circuito.path}MC_jobs.json"):
            print("\nSimulacao em andamento encontrada! continuando de onde parou...\n")
            self.__load_MC(circuito)
        else:
            print("Encontrando LETth para cada instancia")
            self.__determinar_variabilidade(circuito)

        # A MAGIA ACONTECE AQUI
        self.work()

        # Retorna os valores num csv
        saida = self.return_done()
        CManager.tup_dict_to_csv(f"{circuito.path}",f"{circuito.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

        # Destroi os arquivos de persistencia
        self.__delete_MC()

class MCSlave:
    def __init__(self, circuito, max_jobs: int = 1000, delay: bool = False):
        self.circuito = circuito
        self.max_jobs = max_jobs
        self.delay = delay

    def run(self, mc: MCManager):
        with ProcessFolder("circuitos"):
            for _ in range(self.max_jobs):
                job = mc.request_job()
                if job == -1:
                    break
                index, (pmos, nmos) = job
                result = self.run_mc_iteration(self.circuito, index, pmos, nmos, delay=self.delay)
                mc.post_result((index, result), job)

    ##### RODA UMA INSTANCIA DA ANALISE MONTE CARLO ##### 
    def run_mc_iteration(self, circuito, index: int, pmos: float, nmos: float, delay: bool = False):
         ### Guarda que com ctz tem como melhorar
        with HSRunner.MC_Instance(pmos, nmos):
            if delay: CircMan.get_atrasoCC(circuito)
            CircMan.atualizar_LETths(circuito, pmos, nmos, delay=delay)
            result = (round(pmos,4), round(nmos,4), circuito.LETth.nodo_nome, circuito.LETth.saida_nome, circuito.LETth.corrente, circuito.LETth.valor)
        return result