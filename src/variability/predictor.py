"""
Prediction Unit.
Classes on this file are responsible for gathering and predicting data.
Each class is responsible for its own synchronization as
"""

import multiprocessing as mp
from os import path


class Predictor:
    """
    Abstract predictor
    """

    def __init__(self, file_dir: str) -> None:
        self.file_dir = file_dir
        self.let_map = {}

        # submit sync
        self.submit_lock = mp.Lock()
        self.submit_queue = mp.Queue()

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
            let_identity (tuple): te property let.identity of a let
            var (tuple[float]): a tuple of type (var_1_value, var_2_value, .. var_n_value)
            current (float): the current value
        """
        with self.submit_lock:
            self.submit_queue.put((let_identity, var, current))

    def predict(self, input: dict) -> dict:
        return None

    def work(self):
        with open(path.join(self.file_dir, "Raw_data.csv"), "a") as file:
            while True:
                let_identity, var, current = self.submit_queue.get()
                if let_identity == -1:
                    for let_id, pts in self.let_map.items():
                        print(f"{let_id}:")
                        for pt in pts:
                            print(pt)
                    return
                if let_identity not in self.let_map.keys():
                    self.let_map[let_identity] = set()
                self.let_map[let_identity].add((var, current))

    def __enter__(self):
        self.start()

    def __exit__(self, a, b, c):
        self.submit_data(-1, -1, -1)
        self.join()


if __name__ == "__main__":
    from os import remove

    print("Testing Prediction Module...")

    print("\tTesting Data Gattering...")
    pred = Predictor(".")
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
