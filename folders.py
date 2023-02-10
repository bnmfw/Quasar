import os
import multiprocessing as mp
import time

class AmbienteProcesso:
    def __init__(self):
        self.jobs = mp.Queue()
        self.done = mp.Queue()

        self.lock = mp.Lock()
        
        for elemento in list(range(100)):
            self.jobs.put(elemento)

    def request_job(self):
        self.lock.acquire()
        if self.jobs.empty():
            ret = -1
        else:
            ret = self.jobs.get()
        self.lock.release()
        return ret
    
    def post_result(self, resultado):
        self.done.put(resultado)
    
ambienteProcesso = AmbienteProcesso()

class ProcessFolder:
    def __init__(self, dir_name: str):
        self.dir = dir_name

    def __enter__(self):
        self.pid = os.getpid()
        os.system(f"cp -R {self.dir} {self.dir}_{self.pid}")

    def __exit__(self, type, value, traceback):
        os.system(f"rm -r {self.dir}_{self.pid}")

class Simulador:
    def __init__(self):
        self.pid = None

    def run(self):
        self.pid = os.getpid()
        for _ in range(10000):

            job = ambienteProcesso.request_job()
            
            # Nao ha mais trabalhos portanto pode-se matar o processo
            if job == -1:
                self.pid = None
                return
            
            print(self.pid, job)
            time.sleep(2)
            ambienteProcesso.post_result(job)

        self.pid = None


if __name__ == "__main__":
    workers = [mp.Process(target = Simulador().run, args=()) for _ in range(10)]
    print (workers)
    print("iniciando a simulacao")
    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
    
    print("trabalho finalizado com sucesso")