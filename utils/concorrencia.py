import os
from collections.abc import Callable
import multiprocessing as mp
import signal
import sys
import json
from time import sleep, perf_counter

# This file is responsible for the concurrent execution of Quasar and is the only part of the project that
# should know how to handle any concurrent work, form the perspective of all other files the project is serialized
# This file itself does not know what types of jobs its paralalizing, it should be generic

# This is a context manager that creates a folder for a process that is a copy of its inteded workspace
# As the context manager is exited said folder is deletes
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

# This class is responsible for executing some function multiple times with different inputs.
# The static_args+job define the inputs and are gotten from a Queue with request_job
# When done the output is posted in a Queue with post_results
class ProcessWorker:
    def __init__(self, work_func: Callable, static_args: list, max_work: int):
        self.func = work_func
        self.args = static_args
        self.max_work = max_work

    # Handler of the termination signal
    def __termination_handler(self, signal, frame):
        sys.exit(0)
    
    # Usual execution of jobs
    def run(self, master: object):
        # This line has to come here in run. Do not dare to put it in the constructor. Learn more about signals.
        signal.signal(signal.SIGTERM, self.__termination_handler)

        # Changes the worker execution to its own folder
        with ProcessFolder("circuitos"):
            
            # While True limited by the max_work load
            for _ in range(self.max_work):

                # Gets a job from the master
                job = master.request_job()
                # Job bein -1 means there is no more jobs to be done
                if job == -1:
                    break

                # Does the job and times it as well
                start_time = perf_counter()
                result = self.func(*job["job"], *self.args)
                end_time = perf_counter()

                # Posts a job to master
                master.post_result(result, job["id"], end_time - start_time)
        return

# This class handles the execution of workers, it is responsible for synchronization and job formatting
class ProcessMaster:
    def __init__(self, circuito, func: Callable, jobs, progress_report: Callable = None) -> None:
        self.func = func # Function to be executed
        self.circuito = circuito # Used for Persisten Child for backup
        self.done_copy = []
        self.progress_report = progress_report # Function that Master should report its progress to
        if jobs: self.total_jobs = len(jobs)

        # Sync
        self.lock_jobs = mp.Lock()
        self.lock_done = mp.Lock()
        self.lock_inpg = mp.Lock() #inpg = in progress

        self.jobs = mp.Queue()
        self.done = mp.Queue()
        self.inpg = mp.Queue()

        # Queue for smart sleep
        self.sleep_time = 10
        self.__starting_sleep_time = True
        self.job_time = mp.Queue()
        self.lock_time = mp.Lock()

        # Fills the job Queue
        if not jobs is None:
            for i, job in enumerate(jobs):
                self.jobs.put({"id": i, "job": job})
    
    
    # Terminate all workers
    def terminate_work(self, workers: list):
        for worker in workers:
            worker.terminate()
    
    # sleeps that varies in time depending on execution
    def smart_sleep(self):

        # Actually sleeps zzzzz
        sleep(self.sleep_time*0.8)

        # Maintanance of sleep_time
        with self.lock_time:

            # If no job_time was reported no job has ended yet, so we just add 20 seconds because
            if not self.job_time.empty():
                self.__starting_sleep_time = False
            if self.__starting_sleep_time:
                self.sleep_time += 20

            # New sleep_time is the longest job time yet
            times = [self.sleep_time]
            while not self.job_time.empty():
                times.append(self.job_time.get())
        self.sleep_time = max(times)

    # Routine of master process
    def master_routine(self):
        while True:

            # Like sleep, but better
            self.smart_sleep()

            with self.lock_done:

                # Report progress if there is something to report progress to
                if not self.progress_report is None:
                    self.progress_report(self.done.qsize()/self.total_jobs)

                # Continues working if there still are jobs to be done
                if self.done.qsize() != self.total_jobs:
                    continue

                # No dobje to be done, just gets all jobs (dont remembre why I do this)
                while not self.done.empty():
                    self.done_copy.append(self.done.get())
                
                return
    
    # Given an id and a queue, said content with that id is removed. This is kinda evil
    def __remove_from_queue(self, queue: mp.Queue, id: int):
        for _ in range(queue.qsize()):
            content = queue.get()
            if content["id"] == id:
                return
            queue.put(content)

    # Returns a job to be done, called by workers
    def request_job(self):
        with self.lock_jobs:
            
            # If there are no jobs left returns -1
            if self.jobs.empty():
                job = -1
            
            # Gets a job and puts it in progress
            else:
                job = self.jobs.get()
                with self.lock_inpg:
                    self.inpg.put(job)
        return job
    
    # Posts a job done
    def post_result(self, resultado, id: int, total_time: float):
        # Puts the done job in its queue
        with self.lock_done:
            self.done.put(resultado)
            # print(f"Finished job: {id}/{self.total_jobs}")
        # Removes job from in progress queue
        with self.lock_inpg:
            self.__remove_from_queue(self.inpg, id)
        # Puts time used to run job in its queue
        with self.lock_time:
            self.job_time.put(total_time)
    
    # Returns all done jobs, a list of all outputs not in order
    def return_done(self):
        return self.done_copy

    # Creates all workers, waits for them to finish and returns
    def work(self, static_args: list, n_workers: int = mp.cpu_count()):
        
        # Creates all workers
        workers = [mp.Process(target=ProcessWorker(self.func, static_args, self.jobs.qsize()).run, args = (self,)) for _ in range(n_workers)]

        # Starts all workers
        for worker in workers:
            worker.start()

        # Master rountine executed
        self.master_routine()

        # This should never happen
        if self.done.qsize(): print(f"ERROR: Queue done finished with {self.done.qsize()} items")
        if self.jobs.qsize(): print(f"ERROR: Queue jobs finished with {self.jobs.qsize()} items")
        if self.inpg.qsize(): print(f"ERROR: Queue inpg finished with {self.inpg.qsize()} items")

        # Joins all workers
        for worker in workers:
            worker.join()
        
        # Should never happen
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
    def master_routine(self):
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

if __name__ == "__main__":
    print("Testing Parallel execution...")
    def function(a, x): return x*a

    manager = ProcessMaster(None, function, [[1],[2],[3],[4],[5]], None)
    manager.work((10,))
    print(manager.return_done())