"""
Prediction Unit.
Classes on this file are responsible for gathering and predicting data.
Each class is responsible for its own synchronization as
"""

import multiprocessing as mp
from time import sleep

class Predictor:
    """
    Abstract predictor
    """
    def __init__(self, file_dir: str, data_template: dict = None) -> None:
        self.data = data_template
        self.file_dir = file_dir

        # submit sync
        self.submit_lock = mp.Lock()
        self.submit_queue = mp.Queue()

        self.process = mp.Process(target=self.work, args = ())

        with open(f"{file_dir}/Raw_data.csv", "w"):
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
    
    def submit_data(self, data: dict) -> None:
        """
        Gets data

        Args:
            data (dict): data to be submitted
        """
        with self.submit_lock:
            self.submit_queue.put(data)
    
    def predict(self, input: dict) -> dict:
        return None
    
    def work(self):
        header: bool = False
        with open(f"{self.file_dir}/Raw_data.csv", "a") as file:
            while True:
                data: dict = self.submit_queue.get()
                if data == -1: return
                if not header:
                    file.write(",".join(data.keys())+"\n")
                    header = True
                file.write(",".join(map(lambda e: str(e), data.values()))+"\n")

    
    def __enter__(self):
        self.start()

    def __exit__(self, a, b, c):
        self.submit_data(-1)
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
        if test_file.readline() != "a,b,c\n": ok = False
        if test_file.readline() != "0,1,2\n": ok = False
        if test_file.readline() != "0,10,20\n": ok = False
        remove("Raw_data.csv")
        assert ok, "DATA GATTERING FAILED"
    
    print("Prediction Module OK.")
        