"""
Prediction Unit.
Classes on this file are responsible for gathering and predicting data.
Each class is responsible for its own synchronization as
"""

import multiprocessing as mp
from multiprocessing import Manager

manager = Manager()
response_q = manager.Queue()

import queue
from os import path


class PredictionServer:
    """
    Abstract predictor
    """

    def __init__(self, file_dir: str) -> None:
        self.file_dir = file_dir
        self.let_map = {}

        # submit sync
        self.submit_queue = mp.Queue()
        self.request_queue = mp.Queue()
        self.client_queue: mp.Queue = None  # Janky

        self.process = mp.Process(target=self.work, args=())

        with open(path.join(file_dir, "Raw_data.csv"), "w"):
            pass

    def start(self) -> None:
        """
        Starts the predictor process
        """
        self.process.start()

    def join(self) -> None:
        """
        Joins the predictor process
        """
        self.process.join()

    def submit_data(self, let_identity: tuple, var: tuple, current: float) -> None:
        """
        Submits the result of a LET job

        Args:
            let_identity (tuple): the property let.identity of a let
            var (tuple[float]): a tuple of type (var_1_value, var_2_value, .. var_n_value)
            current (float): the current value
        """
        self.submit_queue.put((let_identity, var, current))

    def request_prediction(self, let_identity: tuple, var: tuple) -> float:
        """
        Args:
            let_identity (tuple): the property let.identity of a let
            var (tuple): a tuple of type (var_1_value, var_2_value, .. var_n_value)

        Returns:
            dict: the predicted current
        """
        # This function will be called by another process, each process has their own queue stored on self.client_queue
        if self.client_queue is None:
            self.client_queue = Manager().Queue()

        self.request_queue.put((self.client_queue, let_identity, var))

        return self.client_queue.get()

    def __process_submission(self) -> bool:
        """
        Process the submissions

        Returns:
            bool: True if the submission is done signal has been sent
        """
        try:
            let_identity, var, current = self.submit_queue.get(block=False)
        except queue.Empty:
            return False
        if let_identity == -1:
            for key, value in self.let_map.items():
                print(key)
                for v in value:
                    print(v)
            return True
        if let_identity not in self.let_map.keys():
            self.let_map[let_identity] = set()
        self.let_map[let_identity].add((var, current))
        return False

    def __process_request(self) -> None:
        """
        Process the requests for predictions
        """
        try:
            response_queue, let_identity, var = self.request_queue.get(block=False)
        except queue.Empty:
            return
        prediction: float = self.__predict(let_identity, var)
        print(f"{let_identity} {var} = {prediction}")
        response_queue.put(prediction)

    def __predict(self, let_identity, var) -> float:
        if let_identity not in self.let_map.keys():
            self.let_map[let_identity] = set()
            return None
        print(self.let_map[let_identity])
        points: set = self.let_map[let_identity]
        if not len(points):
            return None
        return sum(map(lambda point: point[1], points)) / len(points)

    def work(self):
        while True:
            if self.__process_submission():
                return
            self.__process_request()

    def __enter__(self):
        self.start()

    def __exit__(self, a, b, c):
        self.submit_data(-1, -1, -1)
        self.join()


if __name__ == "__main__":
    from os import remove

    print("Testing Prediction Module...")

    print("\tTesting Data Gattering...")
    pred = PredictionServer(".")
    with pred:
        pred.submit_data({"a": 0, "b": 1, "c": 2})
        pred.submit_data({"a": 00, "b": 10, "c": 20})
    with open("Raw_data.csv") as test_file:
        ok = True
        if test_file.readline() != "a,b,c\n":
            ok = False
        if test_file.readline() != "0,1,2\n":
            ok = False
        if test_file.readline() != "0,10,20\n":
            ok = False
        remove("Raw_data.csv")
        assert ok, "DATA GATTERING FAILED"

    print("Prediction Module OK.")
