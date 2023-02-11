import os
from collections.abc import Callable
import multiprocessing as mp

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
    
    def run(self, master: object):

        # Cria os ambientes de processo na pasta work e move os processos para elas
        with ProcessFolder("circuitos"):
            # While True limitado pelo maximo de trabalhos possiveis
            for _ in range(self.max_work):

                # Recebe um trabalho a ser feito do mestre
                job = master.request_job()
                if job == -1:
                    break

                # Realiza o trabalho
                index, _ = job
                result = self.func(*job, *self.args)

                # Envia o resultado para o mestre
                master.post_result((index, result), job)

# class ProcessMaster:
#     def __init__(self, func: Callable, jobs) -> None:
#         self.func = func
#         self.jobs = jobs

#         # Sincronizacao
#         self.lock_jobs = mp.Lock()
#         self.lock_done = mp.Lock()
#         self.lock_inpg = mp.Lock()

#         # Queue dos trabalhos
#         self.jobs = mp.Queue()
#         self.done = mp.Queue()
#         self.inpg = mp.Queue() #inpg = in progress
    
#     ##### RETORNA OS CONTEUDOS DE UMA QUEUE #####
#     def __read_queue(self, queue: mp.Queue):
#         contents = []
#         for _ in range(queue.qsize()):
#             value = queue.get()
#             contents.append(value)
#             queue.put(value)
#         return contents
    
#     ##### REMOVE UM ITEM DE UMA QUEUE, POR FAVOR NAO USE COM QUEUES LONGAS #####
#     def __remove_from_queue(self, queue: mp.Queue, item):
#         for _ in range(queue.qsize()):
#             value = queue.get()
#             if value == item: return
#             queue.put(value)

#     # Retorna um ponto MC a ser calculado
#     def request_job(self):
#         with self.lock_jobs:
#             # Nao ha mais trabalhos
#             if self.jobs.empty():
#                 job = -1
#             else:
#                 job = self.jobs.get()
#                 print(f"Started job: {job}")
#                 with self.lock_inpg:
#                     self.inpg.put(job)
#         return job
    
#     # Recebe um ponto MC calculado
#     def post_result(self, resultado, job):
#         with self.lock_done:
#             self.done.put(resultado)
#             print(f"Finished job: {resultado}")
#         with self.lock_inpg:
#             self.__remove_from_queue(self.inpg, job)

#     def work(self, static_args: list, n_workers: int = mp.cpu_count()):
        
#         # Cria todos os processos que realizam as simulacoes MC
#         workers = [mp.Process(target=ProcessWorker(self.func, static_args, self.jobs).run, args = (self,)) for _ in range(n_workers)]

#         # Inicia os processos
#         for worker in workers:
#             worker.start()

#         # Espera os processos finalizarem
#         for worker in workers:
#             worker.join()