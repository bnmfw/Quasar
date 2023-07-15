"""
Concurrent Framework.
This is the only module in the project that knows cuncurrency existis, as it should be transparent to other modules.
The interface provided is of a function executed multiple times with a queue of its inputs.
"""
import os
from collections.abc import Callable
import multiprocessing as mp
import signal
import sys
import json
from time import sleep, perf_counter

class ProcessFolder:
    """
    Context manager that creates a directory for a process that is a copy of the circuits directory. These copys are created in the work directory.
    As the context manager is exited said folder is deleted.
    """
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
    """
    Executes some function multiple times with different inputs. The static_args+job define the inputs.
    """
    def __init__(self, work_func: Callable, static_args: list, max_work: int) -> None:
        """
        Constructor.

            :param Callable work_func: Function to be executed multiple times.
            :param list static_args: Arguments in function input that do not change over different jobs. Static args must be the last part of the input.
            :param int max_work: Maximum number of functions a worker can run (used to not loop indefinatly in very edge cases).
        """
        self.func = work_func
        self.args = static_args
        self.max_work = max_work

    def __termination_handler(self, signal, frame):
        """
        Handles the termination signal.
        """
        sys.exit(0)
    
    def run(self, master: object) -> None:
        """
        Executes multiple jobs and posts its results.

            :param object master: Process Master.
        """
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

class ProcessMaster:
    """
    Handles the multiple workers, jobs and sync.
    """
    def __init__(self, func: Callable, jobs: list or None, progress_report: Callable = None) -> None:
        """
        Constructor.

            :param Callable func: Function to be executed multiple times.
            :param list or None jobs: List of jobs to be done.
            :param Callable progress_report: Function that the progress is to be reported to.
        """
        self.func = func # Function to be executed
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
       
    def terminate_work(self, workers: list):
        """
        Terminates all the Process Workers.
        """
        for worker in workers:
            worker.terminate()
    
    def smart_sleep(self):
        """
        Sleeps for a variable amount of time depending on the time workers post jobs.
        """

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

    def master_routine(self):
        """
        Routine of Process Master, including sleeping, reporting progress and finishing parallel execution.
        """
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
    
    def __remove_from_queue(self, queue: mp.Queue, id: int):
        """
        Recieves a Queue and an id and removes the item from the Queue (kinda evil).

            :param mp.Queue queue: Queue to have the item removed from.
            :param int id: Id of the item to be removed.
        """
        for _ in range(queue.qsize()):
            content = queue.get()
            if content["id"] == id:
                return
            queue.put(content)

    def request_job(self):
        """
        Returns a single job to be executed. If there are no jobs left returns -1. Called by workers.

            :returns: A job or -1
        """
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
    
    def post_result(self, output, id: int, total_time: float):
        """
        Posts the output of a function. Called by workers.

            :param output: Output of the function.
            :param int id: Id of the job completed.
            :param float total_time: Time taken to complete the job.
        """
        # Puts the done job in its queue
        with self.lock_done:
            self.done.put(output)
            # print(f"Finished job: {id}/{self.total_jobs}")
        # Removes job from in progress queue
        with self.lock_inpg:
            self.__remove_from_queue(self.inpg, id)
        # Puts time used to run job in its queue
        with self.lock_time:
            self.job_time.put(total_time)
    
    def return_done(self):
        """
        Returns all completed jobs.

            :returns: Complete jobs.
        """
        return self.done_copy

    def work(self, static_args: list, n_workers: int = mp.cpu_count()):
        """
        Creates all workers and runs all workers.

            :param list static_args: List containing the static arguments of the jobs, that dont change in between jobs.
            :param int n_workers: Number of workers to be created, will take the cpu count as standard. 
        """
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
    """
    Specialization of ProcessMaster that also backups jobs in its routine.
    """
    def __init__(self, func: Callable, jobs: list or None, backup_prefix: str, progress_report: Callable = None) -> None:
        """
        Constructor.

            :param Callable func: Function to be executed.
            :param list or None jobs: List of jobe to be run.
            :param str backup_prefix: Path and prefix from root to backup, in the format path/.../filename excluding extensions.
            :param Callable progress_report: Function that the progress is to be reported to. 
        """
        super().__init__(func, jobs, progress_report)

        self.prefix = backup_prefix
        
        # Copias dos conteudos das queues usados para dump e load
        self.jobs_copy = []
        self.done_copy = []
        self.inpg_copy = []   
    
    def check_backup(self) -> bool:
        """
        Checks whether of not a backup exists.

            :returns: A boolean informing whether or not said backup exists.
        """
        return os.path.exists(f"{self.prefix}_jobs.json")
    
    def empty_queue(self, queue: mp.Queue):
        """
        Emptys a queue.

            :param mp.Queue queue: Queue to be emptied.
        """
        while not queue.empty():
            queue.get()
    
    def delete_backup(self):
        """
        Deletes backups.
        """
        os.remove(f"{self.prefix}_jobs.json")
        os.remove(f"{self.prefix}_done.json")

    def dump_backup(self):
        """
        Dumps all jobs into backup files.
        """
        json.dump(list(self.inpg_copy+self.jobs_copy), open(f"{self.prefix}_jobs.json", "w"))
        json.dump(list(self.done_copy), open(f"{self.prefix}_done.json", "w"))
    
    def load_backup(self):
        """
        Loads jobs from backup.
        """
        self.jobs_copy = json.load(open(f"{self.prefix}_jobs.json", "r"))
        self.done_copy = json.load(open(f"{self.prefix}_done.json", "r"))
        self.total_jobs = len(self.jobs_copy) + len(self.done_copy)
        # Carregamento das Queues com os conteudos do arquivo
        for job in self.jobs_copy:
            self.jobs.put(job)
        for job in self.done_copy:
            self.done.put(job)

    def load_jobs(self, jobs: list):
        """
        Alternative for passing jobs in the construction of the object.

            :param list jobs: List containing jobs to be done.
        """

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

    def __read_queue(self, queue: mp.Queue) -> list:
        """
        Reads the contents of a queue.

            :param mp.Queue queue: Queue to be read.
            :returns: the contents of the queue.
        """
        contents = []
        for _ in range(queue.qsize()):
            value = queue.get()
            contents.append(value)
            queue.put(value)
        return contents
    
    def master_routine(self):
        """
        Routine of Process Master, including sleeping, reporting progress and backuping.
        """
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
    print("Testing Simple Parallel execution...")
    def function(a, x):
        return x * a

    test_jobs = [[i] for i in range(10)]

    manager = ProcessMaster(function, test_jobs)
    manager.work((10,))
    assert set(manager.return_done()) == {i*10 for i in range(10)}, "SIMPLE PARALLEL MANAGER FAILED"

    print("Testing Backuping Parallel execution...")
    def sleeper(a, x):
        sleep(10)
        return x * a
    
    backuper = PersistentProcessMaster(sleeper, test_jobs, "debug/backup_test/test")
    backuper.work((10,))
    assert set(backuper.return_done()) == {i*10  for i in range(10)}, "BACKUPING PARALLEL MANAGER FAILED"