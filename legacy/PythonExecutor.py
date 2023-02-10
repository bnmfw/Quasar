from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed

class Executor:
    __args = {}
    def __init__(self, max_workers: int = None):
        """
        Inicializa o executor

        Parameters
        ----------
        max_workers : int, optional
            Quantidade máxima de processos em paralelo. The default is None.
            Quando None, é utilizada a quantidade de núcleos da máquina.
        """
        self.__executor = ProcessPoolExecutor(max_workers=max_workers)

    def submit(self, func: Callable, args: dict, callback: Callable = None):
        """
        Começa um novo processo

        Parameters
        ----------
        func : Callable
            Função a ser executada.
        args : dict
            Argumentos a serem passados para a função e para o callback.
        callback : Callable, optional
            Função que é executada após o processo terminar. The default is None.
        """
        fut = self.__executor.submit(func, **args)
        if callback:
            self.__args[fut] = args
            fut.add_done_callback(lambda f, cb=callback: self.__callback_wrapper(f, cb))

    def __callback_wrapper(self, future, callback):
        """
        Wrapper para callbacks.
        Chama o callback com os mesmos argumentos chamados na criação do processo.
        """
        callback(future, **self.__args.pop(future))

    def __del__(self):
        self.__executor.shutdown()

if __name__ == '__main__':
    def task(path, nome, time):
        print("%i começando" %(a))
        time.sleep(time)

    # esta função será chamada após cada processo terminar de executar
    def callbackExemplo(future, nome: str, time: float, **args):
        print("%s acabou de executar %.1f segundos" %(nome, time))
    
    ex = Executor()
    for i in range(20):
        ex.submit(task, {"nome": "task %i" %(i), "time": 2+i/2}, callbackExemplo)