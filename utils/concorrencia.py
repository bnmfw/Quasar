import os
from collections.abc import Callable
import multiprocessing as mp
import signal
import sys
import json
from time import sleep, perf_counter

class ProcessFolder:
    def __init__(self, dir: str):
        self.pid = None
        self.dir = dir

    def __enter__(self):
        self.pid = os.getpid()
        os.mkdir(f"work/{self.pid}")
        os.system(f"cp -R {self.dir} work/{self.pid}/{self.dir}")
        os.chdir(f"work/{self.pid}")

    def __exit__(self, type, value, traceback):
        os.chdir(f"..")
        os.system(f"rm -r {self.pid}")
        os.chdir(f"..")

class ProcessWorker:
    def __init__(self, work_func: Callable, static_args: list, max_work: int):
        self.func = work_func
        self.args = static_args
        self.max_work = max_work

    # Quando o processo eh terminado extermente pelo metodo .terminate ele entra aqui
    def __termination_handler(self, signal, frame):
        sys.exit(0)
        pass
    
    def run(self, master: object):
        # Essa linha tem que de vir aqui pois eh quando o processo ja iniciou, nao coloque no construtor
        signal.signal(signal.SIGTERM, self.__termination_handler)

        # Cria os ambientes de processo na pasta work e move os processos para elas
        with ProcessFolder("circuitos"):
            
            # While True limitado pelo maximo de trabalhos possiveis
            for _ in range(self.max_work):

                # Recebe um trabalho a ser feito do mestre
                job = master.request_job()
                if job == -1:
                    break

                # Realiza o trabalho
                start_time = perf_counter()
                result = self.func(*job["job"], *self.args)
                end_time = perf_counter()

                total_time = end_time - start_time

                # Envia o resultado para o mestre
                master.post_result(result, job["id"], total_time)
        return

class ProcessMaster:
    def __init__(self, circuito, func: Callable, jobs, progress_report: Callable = None) -> None:
        self.func = func
        self.circuito = circuito
        self.done_copy = []
        self.progress_report = progress_report
        if jobs: self.total_jobs = len(jobs)

        # Sincronizacao
        self.lock_jobs = mp.Lock()
        self.lock_done = mp.Lock()
        self.lock_inpg = mp.Lock()

        # Queue dos trabalhos
        self.jobs = mp.Queue()
        self.done = mp.Queue()
        self.inpg = mp.Queue() #inpg = in progress

        # Queue para regular o tempo de sleep da rotina de descanso
        self.sleep_time = 10
        self.__starting_sleep_time = True
        self.job_time = mp.Queue()
        self.lock_time = mp.Lock()

        # Preenche a Queue dos trabalhos
        if not jobs is None:
            for i, job in enumerate(jobs):
                self.jobs.put({"id": i, "job": job})
    
    
    ##### MATA TODOS OS PROCESSOS TRABALHADORES #####
    def terminate_work(self, workers: list):
        for worker in workers:
            worker.terminate()
    
    ##### SLEEP SO QUE MELHOR #####
    def smart_sleep(self):
        sleep(self.sleep_time*0.8)
        # Manutencao do tempo de espera
        with self.lock_time:

            # Soma 10 segundos ao tempo de espera caso ele nao tenha sido alterado desde o inicio 
            if not self.job_time.empty():
                self.__starting_sleep_time = False
            if self.__starting_sleep_time:
                self.sleep_time += 20

            # Novo tempo de espera eh o maior tempo de execucao de um job
            times = [self.sleep_time]
            while not self.job_time.empty():
                times.append(self.job_time.get())
        self.sleep_time = max(times)

    ##### ROTINA DE BACKUP #####
    def backup_routine(self):
        while True:

            self.smart_sleep()

            with self.lock_done:

                # Atualiza o progresso (ISSO EH DO MAL KKKKKKKK)
                if not self.progress_report is None:
                    self.progress_report(self.done.qsize()/self.total_jobs)

                # Ainda ha trabalhos a serem feitos
                if self.done.qsize() != self.total_jobs:
                    continue

                # Nao ha trabalhos a serem feitos, esvazia a queue
                while not self.done.empty():
                    self.done_copy.append(self.done.get())
                
                return
    
    ##### REMOVE UM ITEM DE UMA QUEUE, DADO UM ID #####
    def __remove_from_queue(self, queue: mp.Queue, id: int):
        for _ in range(queue.qsize()):
            content = queue.get()
            if content["id"] == id:
                return
            queue.put(content)

    ##### RETORNA UM TRABALHO A SER FEITO #####
    def request_job(self):
        with self.lock_jobs:
            
            # Nao ha mais trabalhos retorna -1 para encerrar o processo
            if self.jobs.empty():
                job = -1
            
            # Adquire um job da queue e o coloca na queue dos jobs em progresso
            else:
                job = self.jobs.get()
                with self.lock_inpg:
                    self.inpg.put(job)
        return job
    
    ##### RECEBE UM TRABALHO PRONTO #####
    def post_result(self, resultado, id: int, total_time: float):
        # Coloca o job na queue de jobs prontos
        with self.lock_done:
            self.done.put(resultado)
            # print(f"Finished job: {id}/{self.total_jobs}")
        # Remove o job da queue de jobs em progresso
        with self.lock_inpg:
            self.__remove_from_queue(self.inpg, id)
        with self.lock_time:
            self.job_time.put(total_time)
    
    ##### RETORNA OS JOBS CONCLUIDOS #####
    def return_done(self):
        return self.done_copy

    # Cria os processos e roda eles
    def work(self, static_args: list, n_workers: int = mp.cpu_count()):
        
        # Cria todos os processos que realizam as simulacoes MC
        workers = [mp.Process(target=ProcessWorker(self.func, static_args, self.jobs.qsize()).run, args = (self,)) for _ in range(n_workers)]

        # Inicia os processos
        # print("Trabalho Concorrente Iniciado!")
        for worker in workers:
            worker.start()

        # Executa a rotina de backup do master
        self.backup_routine()

        # Espera os processos finalizarem
        if self.done.qsize(): print(f"Queue done finalizou com {self.done.qsize()} itens dentro")
        if self.jobs.qsize(): print(f"Queue jobs finalizou com {self.jobs.qsize()} itens dentro")
        if self.inpg.qsize(): print(f"Queue inpg finalizou com {self.inpg.qsize()} itens dentro")

        for worker in workers:
            worker.join()
            # print(f"joined: {worker.pid}")
        
        if len(os.listdir("work")):
            raise ChildProcessError("Master Process Joined Withouth Child Finishing")

class PersistentProcessMaster(ProcessMaster):
    def __init__(self, circuito, func: Callable, jobs, backup_prefix, progress_report: Callable = None) -> None:
        super().__init__(circuito, func, jobs, progress_report)

        self.prefix = backup_prefix
        
        # Copias dos conteudos das queues usados para dump e load
        self.jobs_copy = []
        self.done_copy = []
        self.inpg_copy = []   
    
    ##### CHECK IF BACKUP EXISTS #####
    def check_backup(self):
        return os.path.exists(f"circuitos/{self.circuito.nome}/{self.prefix}_jobs.json")
    
    ##### EMPTIES A QUEUE #####
    def empty_queue(self, queue: mp.Queue):
        while not queue.empty():
            queue.get()
    
    ##### DELETA OS ARQUIVOS DE CONTEXTO #####
    def delete_backup(self):
        os.remove(f"circuitos/{self.circuito.nome}/{self.prefix}_jobs.json")
        os.remove(f"circuitos/{self.circuito.nome}/{self.prefix}_done.json")

    ##### DESCARREGA O CONTEXTO DAS SIMULACOES DA ANALISE MC #####
    def dump_backup(self):
        json.dump(list(self.inpg_copy+self.jobs_copy), open(f"circuitos/{self.circuito.nome}/{self.prefix}_jobs.json", "w"))
        json.dump(list(self.done_copy), open(f"circuitos/{self.circuito.nome}/{self.prefix}_done.json", "w"))
    
    ##### CARREGA O CONTEXTO DAS SIMULACOES DA ANALISE MC #####
    def load_backup(self, circuito):
        self.jobs_copy = json.load(open(f"circuitos/{circuito.nome}/{self.prefix}_jobs.json", "r"))
        self.done_copy = json.load(open(f"circuitos/{circuito.nome}/{self.prefix}_done.json", "r"))
        self.total_jobs = len(self.jobs_copy) + len(self.done_copy)
        # Carregamento das Queues com os conteudos do arquivo
        for job in self.jobs_copy:
            self.jobs.put(job)
        for job in self.done_copy:
            self.done.put(job)

    ##### RECEBE JOBS E OS CARREGA NA QUEUE EFETIVAMENTE RESETA OS TRABALHOS ####
    def load_jobs(self, jobs):

        self.total_jobs = len(jobs)
        # Enumera os jobs com ids
        jobs = [{"id": id, "job": job} for id, job in enumerate(jobs)]

        # Preenche a Queue dos trabalhos
        for job_dict in jobs:
            self.jobs.put(job_dict)

        # Persistencia do trabalho feito
        self.jobs_copy = jobs
        self.done_copy = []
        self.inpg_copy = []
    
        self.dump_backup()

    ##### RETORNA OS CONTEUDOS DE UMA QUEUE #####
    def __read_queue(self, queue: mp.Queue):
        contents = []
        for _ in range(queue.qsize()):
            value = queue.get()
            contents.append(value)
            queue.put(value)
        return contents
    
    ##### ROTINA DE BACKUP #####
    def backup_routine(self):
        # Periodicamente salva o progresso
        while True:
            self.smart_sleep()

            with self.lock_jobs, self.lock_inpg, self.lock_done:
                # Le todas as queues
                self.jobs_copy = self.__read_queue(self.jobs)
                self.inpg_copy = self.__read_queue(self.inpg)
                self.done_copy = self.__read_queue(self.done)
                # Realiza o backup
                self.dump_backup()

                # Atualiza o progresso (ISSO EH DO MAL KKKKKKKK)
                if not self.progress_report is None:
                    self.progress_report(self.done.qsize()/self.total_jobs)

                # Se ainda ha trabalhos a serem feitos continua
                if len(self.done_copy) != self.total_jobs:
                    continue

                # Pela forma que Queues funcionam em python eh necessario limpalas antes de dar join
                self.empty_queue(self.done)
                break