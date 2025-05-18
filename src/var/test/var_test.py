from ...utl.math import InDir, Time, compare_fault_config_lists
from ...cfg.simulationConfig import sim_config
from ...spi.spiceRunner import HSpiceRunner
from ...ckt.circuit import Circuito
from ..distribution import SpiceGaussianDist
from ..mcManager import MCManager
from os import path
import json


def run_test(
        circuit: str,
        vdd: float,
        pvar_model: str,
        pvar_var: str,
        pvar_sigmas: float,
        pvar_std: float,
        nvar_model: str,
        nvar_var: str,
        nvar_sigmas: float,
        nvar_std: float,
        mcManager_kwargs: dict = {},
        single_threaded: bool = False,
        var_points: int = 20,
        ans_file: str = None,
    ):
    sim_config.runner_type = HSpiceRunner
    if sim_config.runner.test_spice():
        exit(1)
    sim_config.vdd = vdd

    print("\tTesting MC simulation...")
    with InDir("debug"):
        sim_config.circuit = Circuito(circuit).from_json()
        pvar_mean = sim_config.model_manager[pvar_model][pvar_var]
        nvar_mean = sim_config.model_manager[nvar_model][nvar_var]
        pvar = SpiceGaussianDist(pvar_model, pvar_var, pvar_mean, pvar_sigmas, pvar_std)
        nvar = SpiceGaussianDist(nvar_model, nvar_var, nvar_mean, nvar_sigmas, nvar_std)
        mc = MCManager(**mcManager_kwargs)
        mc.full_mc_analysis(var_points, [pvar, nvar], single_threaded=single_threaded)
        with open(mc.results_file, "r") as file:
            results_data = file.read()
        if (results_data.count("\n") != var_points):
            print("MC SIMULATION FAILED")
            return False

    if ans_file:
        with open(ans_file, "r") as file:
            ans = json.load(file)
        with InDir("debug"):
            with open(path.join(sim_config.circuit.path_to_my_dir, "Raw_data.csv"), "r") as file:
                data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))

        for line in data:
            line[4] = int(float(line[4]))
        if compare_fault_config_lists(data, ans):
            print("Results OK")
            return True
        else:
            print("Test Failed: Simulation results are different than expected")
            return False
    else:
        print("ans_file was not provided")
        return None

if __name__ == "__main__":
    test_config = {
        "circuit": "nand_fin",
        "vdd": 0.7,
        "pvar_model": "pmos_rvt",
        "pvar_var": "phig",
        "pvar_sigmas": 3,
        "pvar_std": 0.05,
        "nvar_model": "nmos_rvt",
        "nvar_var": "phig",
        "nvar_sigmas": 3,
        "nvar_std": 0.05,
        "mcManager_kwargs": {},
        "single_threaded": True,
        "var_points": 20,
        "ans_file": path.join("src", "variability", "test", "data", "nand_fin_fault_config_list.json"),
    }
    print("Circuit: nand_fin")
    run_test(**test_config)
    print()


if __name__ == "__main__":
    test_config = {
        "circuit": "c17v3",
        "vdd": 0.7,
        "pvar_model": "pmos_rvt",
        "pvar_var": "phig",
        "pvar_sigmas": 3,
        "pvar_std": 0.05,
        "nvar_model": "nmos_rvt",
        "nvar_var": "phig",
        "nvar_sigmas": 3,
        "nvar_std": 0.05,
        "mcManager_kwargs": {},
        "single_threaded": True,
        "var_points": 20,
        "ans_file": "",
    }
    print("Circuit: c17v3")
    run_test(**test_config)
    print()

if __name__ == "__main__":
    test_config = {
        "circuit": "nand",
        "vdd": 0.9,
        "pvar_model": "pmos",
        "pvar_var": "vth0",
        "pvar_sigmas": 3,
        "pvar_std": 0.01,
        "nvar_model": "nmos",
        "nvar_var": "vth0",
        "nvar_sigmas": 3,
        "nvar_std": 0.01,
        "mcManager_kwargs": {},
        "single_threaded": True,
        "var_points": 20,
        "ans_file": path.join("src", "variability", "test", "data", "nand_fault_config_list.json"),
    }
    print("Circuit: nand")
    run_test(**test_config)
    print()

if __name__ == "__main__":
    test_config = {
        "circuit": "fadder",
        "vdd": 0.7,
        "pvar_model": "pmos_rvt",
        "pvar_var": "phig",
        "pvar_sigmas": 3,
        "pvar_std": 0.05,
        "nvar_model": "nmos_rvt",
        "nvar_var": "phig",
        "nvar_sigmas": 3,
        "nvar_std": 0.05,
        "mcManager_kwargs": {},
        "single_threaded": True,
        "var_points": 20,
        "ans_file": "",
    }
    print("Circuit: fadder")
    run_test(**test_config)
    print()
