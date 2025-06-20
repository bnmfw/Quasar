"""
Concurrent Framework.
This is the only module in the project that knows cuncurrency exists, as it should be transparent to other modules.
The interface provided is of a function executed multiple times with a queue of its inputs.
"""

import os
from collections.abc import Callable
from traceback import format_exc
import multiprocessing as mp
import signal
import sys
import json
from time import sleep, perf_counter
from os import path, sep


class ProcessFolder:
    """
    Context manager that creates a directory for a process that is a copy of the circuits directory. These copys are created in the work directory.
    As the context manager is exited said folder is deleted.
    """

    def __init__(self, dir: str, circuit: str = None):
        self.pid = None
        self.dir = dir
        self.first_dir = self.dir.split(sep)[0]
        self.depth = self.dir.count(sep) + 1
        self.circuit_name = circuit

    def __enter__(self):
        self.pid = os.getpid()
        os.mkdir(path.join("work", str(self.pid)))
        os.mkdir(path.join("work", str(self.pid), self.first_dir))
        if self.circuit_name:
            for target in {"dis", "include.cir", "include", self.circuit_name}:
                os.system(
                    f"cp -R {path.join(self.first_dir,target)} {path.join('work',str(self.pid),self.first_dir,target)}"
                )
        else:
            os.system(
                f"cp -R {self.first_dir} {path.join('work',str(self.pid),self.first_dir)}"
            )
        os.chdir(path.join("work", str(self.pid), self.dir, ".."))

    def __exit__(self, type, value, traceback):
        for _ in range(self.depth):
            os.chdir(f"..")
        os.system(f"rm -r {self.pid}")
        os.chdir(f"..")


class ProcessWorker:
    """
    Executes some function multiple times with different inputs. The static_args+job define the inputs.
    """

    def __init__(
        self,
        work_func: Callable,
        static_args: list,
        max_work: int,
        work_dir: str = path.join("project", "circuits"),
        target_circuit: str = None,
    ) -> None:
        """
        Constructor.

        Args:
            work_func (Callable): Function to be executed multiple times.
            static_args (list): Arguments in function input that do not change over different jobs. Static args must be the last part of the input.
            max_work (int): Maximum number of functions a worker can run (used to not loop indefinatly in very edge cases).
            workdir (str, optional): Main circuits directory. Defaults to 'project/circuits'
            target_circuit (str, optional): Specific Circuit directory. Defaults to None
        """
        self.func = work_func
        self.args = static_args
        self.max_work = max_work
        self.work_dir = work_dir
        self.target_circuit = target_circuit

    def __termination_handler(self, signal, frame):
        """
        Handles the termination signal.
        """
        sys.exit(0)

    def run(self, master: object) -> None:
        """
        Executes multiple jobs and posts its results.

            master (ProcessMaster): Process Master.
        """
        # This line has to come here in run. Do not dare to put it in the constructor. Learn more about signals.
        signal.signal(signal.SIGTERM, self.__termination_handler)

        # Changes the worker execution to its own folder
        with ProcessFolder(self.work_dir, self.target_circuit):

            # While True limited by the max_work load
            for _ in range(self.max_work):

                # Gets a job from the master
                job = master.request_job()
                # Job bein -1 means there is no more jobs to be done
                if job == -1:
                    break

                # Does the job and times it as well
                start_time = perf_counter()
                try:
                    result = self.func(*job["job"], *self.args)
                except Exception as excp:
                    master.throw_exception([*job["job"]] + [*self.args], excp)
                    return
                end_time = perf_counter()

                # Posts a job to master
                master.post_result(result, job["id"], end_time - start_time)
        return


class ProcessMaster:
    """
    Handles the multiple workers, jobs and sync.
    """

    def __init__(
        self,
        func: Callable,
        jobs: list or None,
        work_dir: str = path.join("project", "circuits"),
        progress_report: Callable = None,
    ) -> None:
        """
        Constructor.

        Args:
            func (Callable): Function to be executed multiple times.
            jobs (list or None): List of jobs to be done.
            work_dir (str): Main circuits directory.
            progress_report (Callable): Function that the progress is to be reported to.
        """
        self.func = func  # Function to be executed
        self.work_dir = work_dir.split(sep)[0]
        self.target_circuit = (
            None if not work_dir.count(sep) else work_dir.split(sep)[1]
        )
        self.done_copy = []
        self.progress_report = (
            progress_report  # Function that Master should report its progress to
        )
        if jobs is not None:
            self.total_jobs = len(jobs)
        # else: print("HUH")

        # Sync
        self.lock_jobs = mp.Lock()
        self.lock_done = mp.Lock()
        self.lock_inpg = mp.Lock()  # inpg = in progress
        self.lock_excp = mp.Lock()

        self.jobs = mp.Queue()
        self.done = mp.Queue()
        self.inpg = mp.Queue()
        self.excp = mp.Queue()

        # Fills the job Queue
        if not jobs is None:
            for i, job in enumerate(jobs):
                self.jobs.put({"id": i, "job": job})

    def __terminate_work(self):
        """
        Terminated all the process
        """
        for worker in self.workers:
            worker.terminate()

    def master_routine(self):
        """
        Routine of Process Master, including sleeping, reporting progress and finishing parallel execution.

        Returns:
            None if no exceptions were raised, (problem job, exception) if exceptions were raised.
        """

        # Sets the response to being terminated
        signal.signal(signal.SIGTERM, self.__terminate_work)

        while True:

            # sleeps
            sleep(1)

            # Stops and throws any exceptions
            if self.excp.qsize():
                self.__terminate_work()
                return self.excp.get(True)

                raise type(exception)(f"{exception} (Job: {job})")

            # Report progress if there is something to report progress to
            if not self.progress_report is None:
                self.progress_report(self.done.qsize() / self.total_jobs)

            # Continues working if there still are jobs to be done
            if self.done.qsize() != self.total_jobs:
                continue

            # No job to be done, just gets all jobs in self.done_copy wich will be returned
            while not self.done.empty():
                self.done_copy.append(self.done.get())

            return

    def __remove_from_queue(self, queue: mp.Queue, id: int):
        """
        Recieves a Queue and an id and removes the item from the Queue (kinda evil).

        Args:
            :queue (mp.Queue): Queue to have the item removed from.
            :id (int): Id of the item to be removed.
        """
        for _ in range(queue.qsize()):
            content = queue.get()
            if content["id"] == id:
                return
            queue.put(content)

    def request_job(self) -> list or int:
        """
        Returns a single job to be executed. If there are no jobs left returns -1. Called by workers.

        Returns:
            list or -1: Returns a job to be done or -1 if there are none left
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

        Args:
            :output: Output of the function.
            :id (int): Id of the job completed.
            :total_time (float): Time taken to complete the job.
        """
        # Puts the done job in its queue
        with self.lock_done:
            self.done.put(output)
            # print(f"Finished job: {id}/{self.total_jobs}")
        # Removes job from in progress queue
        with self.lock_inpg:
            self.__remove_from_queue(self.inpg, id)

    def return_done(self):
        """
        Returns all completed jobs.

        Returns:
            lsit: Complete jobs.
        """
        return self.done_copy

    def throw_exception(self, problem_job: list, exception: Exception) -> None:
        """
        Sends the generated exception to the master process

        Args:
            problem_job (list): list of arguments that raised an exception
            exception (Exception): the exception
        """
        with self.lock_excp:
            self.excp.put((problem_job, exception))

    def work(self, static_args: list, n_workers: int = mp.cpu_count()):
        """
        Creates all workers and runs all workers.

        Args:
            :static_args (list): List containing the static arguments of the jobs, that dont change in between jobs.
            :n_workers (int): Number of workers to be created, will take the cpu count as standard.

        Returns:

        Returns:
            None if no exceptions were raised, (problem job, exception) if exceptions were raised.
        """
        # Initial progress report
        if not self.progress_report is None:
            self.progress_report(self.done.qsize() / self.total_jobs)

        # Creates all workers
        self.workers = [
            mp.Process(
                target=ProcessWorker(
                    self.func,
                    static_args,
                    self.jobs.qsize(),
                    work_dir=self.work_dir,
                    target_circuit=self.target_circuit,
                ).run,
                args=(self,),
            )
            for _ in range(n_workers)
        ]

        # Starts all workers
        for worker in self.workers:
            worker.start()

        # Master rountine executed
        job_excp = self.master_routine()

        # Returns a problem job exception pair if exceptions were raised
        if job_excp:
            return job_excp

        # This should never happen
        if self.done.qsize():
            print(f"ERROR: Queue done finished with {self.done.qsize()} items")
        if self.jobs.qsize():
            print(f"ERROR: Queue jobs finished with {self.jobs.qsize()} items")
        if self.inpg.qsize():
            print(f"ERROR: Queue inpg finished with {self.inpg.qsize()} items")

        # Joins all workers
        for worker in self.workers:
            worker.join()

        # Should never happen
        if len(os.listdir("work")):
            raise ChildProcessError("Master Process Joined Without Child Finishing")

        # Reports progress completion
        if not self.progress_report is None:
            self.progress_report(-1)


class PersistentProcessMaster(ProcessMaster):
    """
    Specialization of ProcessMaster that also backups jobs in its routine.
    """

    def __init__(
        self,
        func: Callable,
        jobs: list or None,
        backup_prefix: str,
        work_dir: str = path.join("project", "circuits"),
        progress_report: Callable = None,
    ) -> None:
        """
        Constructor.

        Args:
            func (Callable): Function to be executed.
            jobs (list or None): List of jobe to be run.
            work_dir (str): Main circuits directory.
            backup_prefix (str): Path and prefix from root to backup, in the format path/.../filename excluding extensions.
            progress_report (Callable): Function that the progress is to be reported to.
        """
        super().__init__(func, jobs, work_dir=work_dir, progress_report=progress_report)

        self.prefix = backup_prefix

        # Copias dos conteudos das queues usados para dump e load
        self.jobs_copy = []
        self.done_copy = []
        self.inpg_copy = []

    def check_backup(self) -> bool:
        """
        Checks whether of not a backup exists.

        Return:
            bool: A boolean informing whether or not said backup exists.
        """
        return os.path.exists(f"{self.prefix}_jobs.json")

    def empty_queue(self, queue: mp.Queue):
        """
        Emptys a queue.

        Args:

            queue (mp.Queue): Queue to be emptied.
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
        json.dump(
            list(self.inpg_copy + self.jobs_copy), open(f"{self.prefix}_jobs.json", "w")
        )
        json.dump(list(self.done_copy), open(f"{self.prefix}_done.json", "w"))

    def load_backup(self):
        """
        Loads jobs from backup.

        Return:
            bool: A boolean informing whether or not backups were read
        """
        if not self.check_backup():
            return False
        self.jobs_copy = json.load(open(f"{self.prefix}_jobs.json", "r"))
        self.done_copy = json.load(open(f"{self.prefix}_done.json", "r"))
        self.total_jobs = len(self.jobs_copy) + len(self.done_copy)
        # Carregamento das Queues com os conteudos do file
        for job in self.jobs_copy:
            self.jobs.put(job)
        for job in self.done_copy:
            self.done.put(job)
        return True

    def load_jobs(self, jobs: list):
        """
        Alternative for passing jobs in the construction of the object.

        Args:
            jobs (list): List containing jobs to be done.
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

        Args:
            queue (mp.Queue): Queue to be read.

        Returns:
            list: the contents of the queue.
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
        total_sleeps = 1
        max_sleeps = 300
        while True:
            sleep(1)
            total_sleeps += 1
            total_sleeps % max_sleeps

            # Updates progress through a callback
            if not self.progress_report is None:
                self.progress_report(self.done.qsize() / self.total_jobs)

            if not total_sleeps:
                with self.lock_jobs, self.lock_inpg, self.lock_done:
                    # Le todas as queues
                    self.jobs_copy = self.__read_queue(self.jobs)
                    self.inpg_copy = self.__read_queue(self.inpg)
                    self.done_copy = self.__read_queue(self.done)
                    # Realiza o backup
                    self.dump_backup()

            # Continues if there are still jobs to be done
            if self.done.qsize() != self.total_jobs:
                continue

            self.done_copy = []
            while not self.done.empty():
                self.done_copy.append(self.done.get())

            # Empties the queue in order to join (python quirk)
            self.empty_queue(self.done)

            break


if __name__ == "__main__":
    print("Testing Concurrent Module...")

    print("\tTesting Simple Parallel execution...")

    def function(a, x):
        return x * a

    test_jobs = [[i] for i in range(10)]

    manager = ProcessMaster(function, test_jobs)
    manager.work((10,))
    assert set(manager.return_done()) == {
        i * 10 for i in range(10)
    }, "SIMPLE PARALLEL MANAGER FAILED"

    print("\tTesting Backuping Parallel execution...")

    def sleeper(a, x):
        sleep(1)
        return x * a

    backuper = PersistentProcessMaster(
        sleeper, test_jobs, path.join("debug", "backup_test", "test")
    )
    backuper.work((10,))
    assert set(backuper.return_done()) == {
        i * 10 for i in range(10)
    }, "BACKUPING PARALLEL MANAGER FAILED"

    print("Concurrent Module OK.")
