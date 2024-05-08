"""
Graph Module. Used to model wich nodes of a circuit can propagate a fault to and logically simulate a circuit.
"""

from .matematica import all_vector_n_bits
from typing import Callable

class Graph:
    """
    Graph object.
    """
    def __init__(self, transistors: list, non_passing: list):
        """
        Creates a graph given a transistor list.

            :transistors (list[tuple[int or None, list[str]]]): List of transistors in the form: (if it was p type, nodes).
            :ignore (list[str]): List of nodes to be ignored in the moddeling.
            :non_passing (list[str]): List of nodes that should not be passed through a search (i.g. vdd or gnd)
        """
        self.vertices: dict = {}
        self.arcs: list = []
        self.non_passing: set = set(non_passing)

        # Creates all nodes
        for is_pmos, transistor in transistors:
            _, gate, _ = transistor
            for node in transistor:
                if not node in self.vertices.keys():
                    self.vertices[node] = {"name": node, "signal": None, "reaches": [], "fall_valid": False, "rise_valid": False}
                if node == gate: continue
                if is_pmos:
                    self.vertices[node]["rise_valid"] = True
                else: 
                    self.vertices[node]["fall_valid"] = True
        
        for name, vertice in self.vertices.items():
            if name in self.non_passing or {"a", "b", "cin"}: continue
            if not vertice["rise_valid"]: print(f"{name}: rise invalid")
            if not vertice["fall_valid"]: print(f"{name}: fall invalid")

        # Connects all existing arcs
        for invert, transistor in transistors:
            invert = invert == 1
            source, gate, drain = transistor
            # Creates the relationships
            self.arcs.append({"from": drain, "to": source, "invert": invert ,"control": gate, "conduct": True})
            self.arcs.append({"from": source, "to": drain, "invert": invert ,"control": gate, "conduct": True})
            self.arcs.append({"from": gate, "to": drain, "invert": False ,"control": None, "conduct": False})
            self.arcs.append({"from": gate, "to": source, "invert": False ,"control": None, "conduct": False})
    
        self.arcs = sorted(self.arcs, key = lambda e: e["from"])

        for name, v in self.vertices.items():
            v["from"] = list(filter(lambda e: e["from"] == name, self.arcs))
            v["to"] = list(filter(lambda e: e["to"] == name, self.arcs))
            v["control"] = list(filter(lambda e: e["control"] == name, self.arcs))
        
        # for v in self.vertices.values():
        #     print(v)
        # for vi in self.vertices.values():
        #     vi["reaches"] = self.my_reach(vi["name"])        
    
    def sees(self, source: str, target: str, already_seen: set = None) -> bool:
        """
        Returns whether or not source node sees the target. (DPS)

        Args:
            source (str): Source of search
            target (str): Target of searc
            already_seen (set, optional): A list of already seen vertices, used by recursive call. Defaults to None.

        Returns:
            bool: Whether or not source node sees the target
        """
        
        # If there already is a reaches list
        if self.vertices[source]["reaches"] != []:
            return target in self.vertices[source]["reaches"]

        # Creates the already seen set if necessary
        original = False
        if already_seen is None:
            original = True
            already_seen = set()

        # A search should never go through a non_passing node
        if not original and source in self.non_passing:
            return False
        
        # Found it
        if source == target:
            return True

        # Stops infinite search
        if source in already_seen:
            return False

        # Adds source to already seen node
        already_seen.add(source)

        # Passes the call to all children
        for arc in self.arcs:
            if arc["from"] != source: continue
            if self.sees(arc["to"], target, already_seen=already_seen):
                return True

        # If none of children sees it returns false
        return False

    def my_reach(self, source: str, already_seen: set = None) -> set:
        """
        Returns a set with the names of all vertices the source can see.

        Args:
            source (str): Node that will have its reach defined.
            already_seen (set, optional): A list of already seen vertices, used by recursive call. Defaults to None.

        Returns:
            set: Set with the names of all vertices the source can see.
        """
        # ""
        # Returns a set with the names of all vertices the source can see.

        #     :source (str): Node that will have its reach defined.
        # ""
        # Creates the already seen set if necessary
        original = False
        if already_seen is None:
            original = True
            already_seen = set()

        # A search should never go through a non_passing node
        if not original and source in self.non_passing:
            return

        # Stops infinite search
        if source in already_seen:
            return

        # Adds source to already seen node
        already_seen.add(source)

        # Passes the call to all children
        for arc in self.arcs:
            if arc["from"] != source: continue
            self.my_reach(arc["to"], already_seen=already_seen)

        # If none of children sees it returns false
        return already_seen

    def set_logic(self, input_list: list) -> None:
        """
        Given input values sets the logic value of all vertices. Must contain vdd, gnd and other tension sources

        Args:
            input_list (list): List of tuples on the format (vertice_name, 0 or 1). The list MUST contain vdd, gnd, etc... i.g. (vdd, 1), (gnd, 0).
        """
        # Resets all logic
        for v in self.vertices.values():
            v["signal"] = None
        
        # Sets the values of all inputs
        input_list = list(filter(lambda e: e[0] in self.vertices, input_list))
        for node, sig in input_list:
            self.vertices[node]["signal"] = sig
        
        # Recursivelly propagates logic
        def recursive_propagation(node: str):
            
            # Propagates signal to all nodes in region
            # Iterates over arcs starting from the node
            for arc in self.vertices[node]["from"]:
                # Arc doesnt conduct logic signal
                if not arc["conduct"]: continue
                # Destiny already has a logic value
                if not self.vertices[arc["to"]]["signal"] is None: 
                    # if self.vertices[arc["to"]]["signal"] != self.vertices[node]["signal"]:
                    #     raise RuntimeError("Tried to flip a bit during propagation")
                    continue
                # Arc's controller doesnt allow passing
                if arc["control"] and (self.vertices[arc["control"]]["signal"] is None or self.vertices[arc["control"]]["signal"]==arc["invert"]): continue
                # Sets the destiny value equal to its own and propagates from it
                self.vertices[arc["to"]]["signal"] = self.vertices[node]["signal"]
                recursive_propagation(arc["to"])
            
            # Propagates signal to controlled nodes
            for arc in self.vertices[node]["control"]:
                # I dont allow passing through this arc
                if arc["invert"] == self.vertices[node]["signal"]: continue
                # Remember that controlled arcs go both directions so the "to" is a "from" of other arc
                origin_sig, destiny_sig = self.vertices[arc["from"]]["signal"], self.vertices[arc["to"]]["signal"]
                # This arc cant propagate signal
                if origin_sig is None: continue
                # This arc conducting SHOULD not change anything
                if not origin_sig is None and not destiny_sig is None:
                    if origin_sig != destiny_sig:
                        raise RuntimeError("Origin and destiny signal are different and they connect")
                    continue
                recursive_propagation(arc["from"])
        
        # Propagates
        for node, _ in input_list:
            recursive_propagation(node)
        
    def is_affected_by(self, node: str, already_seen: set = None) -> set:
        """
        Considering a logical configurates searches the nodes that if changed might affect the node.

        Args:
            node (str): node that is to be affected.
            already_seen (set, optional): Recursive set, not to be inputed. Defaults to None.

        Returns:
            set: All the nodes that might affect the given node.
        """
        
        # Creates the propagated set
        if already_seen is None:
            already_seen = set()
        
        # Stops if job has already been done
        if node in set(map(lambda e: e[0], already_seen)):
            return
        
        # No propagation should be done through non_passing nodes
        if node in self.non_passing:
            return
        
        already_seen.add((node, self.vertices[node]["signal"]))

        # Iterates over arcs that go to node
        for arc in self.vertices[node]["to"]:
            # Arc's controller doesnt allow passing
            # TODO: Does a floating arc on pmos allow passing? Maybe.
            if arc["control"] and (self.vertices[arc["control"]]["signal"] is None or self.vertices[arc["control"]]["signal"]==arc["invert"]): continue
            # Propagates search
            self.is_affected_by(arc["from"], already_seen)

        return already_seen

    def valid_orientation(self, node: str, orientation: str) -> bool:
        """
        Given a node and a fault orientation returns wether or not said orientation is possible

        Args:
            node (str): node faulted
            orientation (str): orientation, either 'rise', 'fall',

        Returns:
            bool: if the orientation is valid
        """

        if orientation == "rise": return self.vertices[node]["rise_valid"]
        return self.vertices[node]["fall_valid"]
    
    def simulate_fault(self, faulted_node: str, output: str) -> bool:
        """
        Assumes the "set logic" method is already set. 
        Flips the faulted_node signal and returns if the output was fliped.

        Args:
            faulted_node (str): Faulted node.
            output (str): Output measured.

        Returns:
            bool: Wether or not flipping the node logical value flipped the outputs.
        """

        # Floating node will never affect an output
        # TODO: It actually can as it can switch a gate on or off
        if self.vertices[faulted_node]["signal"] is None: return False
        
        old_output = self.vertices[output]["signal"]
        
        # Determines nodes that can flip
        can_flip = {v: v not in self.non_passing for v in self.vertices}
        can_flip[faulted_node] = False

        # Flips the node
        self.vertices[faulted_node]["signal"] = not self.vertices[faulted_node]["signal"]

        # Recursivelly propagates logic
        def recursive_propagation(node: str) -> None:
            
            # Propagates signal to all nodes in region
            # Iterates over arcs starting from the node
            for arc in self.vertices[node]["from"]:
                # Arc doesnt conduct logic signal
                if not arc["conduct"]: continue
                # Arc's controller doesnt allow passing
                if arc["control"] and (self.vertices[arc["control"]]["signal"] is None or self.vertices[arc["control"]]["signal"]==arc["invert"]): continue
                # Node reached actually cant flip so nothing to update
                if not can_flip[arc["to"]]: continue
                # No fault actually propagated
                if self.vertices[arc["to"]]["signal"] == self.vertices[node]["signal"]: continue
                self.vertices[arc["to"]]["signal"] = self.vertices[node]["signal"]
                can_flip[arc["to"]] = False
                recursive_propagation(arc["to"])
            
            # Propagates signal to controlled nodes
            for arc in self.vertices[node]["control"]:
                # I dont allow passing through this arc
                if arc["invert"] == self.vertices[node]["signal"]: continue
                # This arc cant propagate signal
                if self.vertices[arc["from"]]["signal"] is None: continue
                recursive_propagation(arc["from"])

        # Propagates the fault from the faulted node
        recursive_propagation(faulted_node)

        return old_output != self.vertices[output]["signal"]
    
    def generate_valid_let_configs(self, nodes: list, outputs: list, inputs: list, get_node_callback: Callable) -> list:
        """
        Generates all valid let configs

        Args:
            nodes (list[str]): List of circuit node names
            outputs (list[str]): List of circuit output names
            inputs (list[str]): List of circuit input names
            get_node_callback (Callable): Callable function that returns

        Returns:
            list: all valid lets
        """
        lets_f1 = []
        # Iterates over all input combinations 
        for signals in all_vector_n_bits(len(inputs)):
            # Sets the inputs
            logic_signals = [(inp, sig==1) for inp, sig in zip(inputs, signals)] + [("vdd", True), ("vcc", True), ("gnd", False), ("vss", False)]
            self.set_logic(logic_signals)
            for output in outputs:
                # Gets the nodes that affect it. effect_group is a list of formar (node, signal)
                effect_group = list(filter(lambda e: e[0] in nodes, self.is_affected_by(output)))
                effect_group = list(filter(lambda e: e[0][0] not in {"f"}, effect_group))
                for nodo in effect_group:
                    if nodo[0] == output:
                        output_dir = "fall" if nodo[1] else "rise" if nodo[1] == 0 else None
                        break
                lets_f1 += [[get_node_callback(node[0]), get_node_callback(output), signals, "fall" if node[1] else "rise" if node[1] == 0 else None, output_dir] for node in effect_group]
            
        # Filters orientations that cannot happen due to no nmos or pmos contact
        lets_f2 = list(filter(lambda let: self.valid_orientation(let[0].name, let[3]), lets_f1))

        # Filter lets that only actually propagate a fault to output
        lets_f3 = []
        for let in lets_f2:
             # let[2] => signals
            logic_signals = [(inp, sig==1) for inp, sig in zip(inputs, let[2])] + [("vdd", True), ("vcc", True), ("gnd", False), ("vss", False)]
            self.set_logic(logic_signals)
            if self.simulate_fault(let[0].name, let[1].name):
                lets_f3 += [let]

        return lets_f3

    def __repr__(self) -> str:
        ret = "Nodes:\n"
        for v, vi in self.vertices.items():
            ret += f"\t{v}: {vi['signal']}\n"
        ret += "Arcs:\n"
        for arc in self.arcs:
            # if not arc["conduct"]: continue
            ret += f"\t{arc['from']} {arc['invert']} --{arc['control'] if arc['control'] else ''}--> {arc['to']}\n"
        return ret

if __name__ == "__main__":

    print("Testing Logic module...")

    fadder = [
        (1, "vdd ta p1_p2".split()),
        (1, "p1_p2 tb p2_n1".split()),

        (1, "vdd ta p3_p4".split()),
        (1,"vdd tb p3_p4".split()),
        (1,"p3_p4 tcin p2_n1".split()),

        (1,"vdd tcin p6_p9".split()),
        (1,"vdd ta p6_p9".split()),
        (1,"vdd tb p6_p9".split()),

        (1,"p6_p9 p2_n1 p9_n6".split()),

        (1,"vdd ta p10_p11".split()),
        (1,"p10_p11 tb p11_p12".split()),
        (1,"p11_p12 tcin p9_n6".split()),

        (0,"p2_n1 tb n1_n2".split()),
        (0,"n1_n2 ta gnd".split()),

        (0,"n4_n3 ta gnd".split()),
        (0,"p2_n1 tcin n4_n3".split()),
        (0,"n4_n3 tb gnd".split()),

        (0,"p9_n6 p2_n1 n6_n7".split()),

        (0,"n6_n7 tcin gnd".split()),
        (0,"n6_n7 ta gnd".split()),
        (0,"n6_n7 tb gnd".split()),

        (0,"p9_n6 tcin i10".split()),
        (0,"i10 tb i11".split()),
        (0,"i11 ta gnd".split()),
        
        (1,"vdd p9_n6 sum".split()),
        (0,"sum p9_n6 gnd".split()),
        
        (1,"vdd p2_n1 cout".split()),
        (0,"cout p2_n1 gnd".split()),

        (1,"vdd sum nsum".split()),
        (0,"nsum sum gnd".split()),
        
        (1,"vdd cout ncout".split()),
        (0,"ncout cout gnd".split())
    ]

    nor = [(1,"vdd a i".split()), (1,"i b s".split()), (0,"s a gnd".split()), (0,"s b gnd".split())]
    
    nots = [(1, "vdd a b".split()), (0, "b a gnd".split()),
            (1, "vdd b c".split()), (0, "c b gnd".split())]

    g = Graph(fadder, ["vdd", "gnd"])
    print("\tTesting sees method...")
    assert g.sees("p1_p2","cout"), "SEES FUNCTION FAILED"
    assert not g.sees("cout","p1_p2"), "SEES FUNCTION FAILED"

    print("\tTesting my_reach method...")
    assert g.my_reach("p1_p2") == {'p9_n6', 'p3_p4', 'i11', 'i10', 'n1_n2', 'p2_n1', 'p1_p2', 'n4_n3', 'p6_p9', 'p11_p12', 'n6_n7', 'sum', 'nsum', 'p10_p11', 'ncout', 'cout'}
    
    print("\tTesting set_logic method...")
    g.set_logic([("ta",1), ("tb",0), ("tcin",1),("vdd",1),("gnd",0)])
    assert list(map(lambda e: e["signal"], g.vertices.values())) == [1,1,0,0,0,1,1,1,1,None,None,0,0,0,0,1,0,0,1,1,0], "SET LOGIC FUNCTION FAILED"
    
    print("\tTesting is affected_by method...")
    assert set(map(lambda e: e[0], g.is_affected_by("sum"))) == {'i10', 'ta', 'tb', 'p2_n1', 'p6_p9', 'p9_n6', 'n4_n3', 'p1_p2', 'sum', 'tcin'}, "IS AFFECTED BY FUNCTION FAILED"
    g.set_logic([("ta",0), ("tb",0), ("tcin",0),("vdd",1),("gnd",0)])
    assert set(map(lambda e: e[0], g.is_affected_by("sum"))) == {'ta', 'tcin', 'p9_n6', 'tb', 'p3_p4', 'p1_p2', 'p11_p12', 'n6_n7', 'p10_p11', 'sum', 'p2_n1'}, "IS AFFECTED BY FUNCTION FAILED"
    
    print("\tTesting valid_orientation method...")
    assert not g.valid_orientation("p6_p9", "fall") and g.valid_orientation("sum", "rise"), "ORIENTATION VALIDATION FAILED"

    print("\tTesting simlate_fault method...")
    propag_test = Graph(nor, ["vdd", "gnd"])
    propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 1), ("b", 0)])
    assert propag_test.simulate_fault("i", "s"), "FAULT SIMULATION FAILED"
    propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 0), ("b", 1)])
    assert not propag_test.simulate_fault("i", "s"), "FAULT SIMULATION FAILED"
    propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 0), ("b", 0)])
    assert propag_test.simulate_fault("a", "s"), "FAULT SIMULATION FAILED"
    propag_test.set_logic([("vdd", 1), ("gnd", 0), ("a", 1), ("b", 1)])
    assert not propag_test.simulate_fault("a", "s"), "FAULT SIMULATION FAILED"

    print("Logic Module OK")