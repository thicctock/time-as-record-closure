import sys
!{sys.executable} -m pip install qiskit qiskit-aer numpy networkx

"""
Time As Record Closure (TRC) - Hardware Redundancy Witness (v2)
---------------------------------------------------------------
Implements the "Two-Engine" Approach:
1. Global Redundancy (Thermodynamic Clock) via Average MI.
2. Spatial Leakage Witness (Hardware Forensics) via Max/Support Set.

Dependencies:
    pip install qiskit qiskit-aer numpy networkx
"""

import numpy as np
import networkx as nx
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from collections import defaultdict

# ==========================================
# PART 1: THE TRC DIAGNOSTIC ENGINE
# ==========================================

class TRCDashboard:
    def __init__(self, system_qubit, fragment_qubits, coupling_edges):
        self.system = system_qubit
        self.fragments = fragment_qubits

        # Build the physical Coupling Graph (G)
        self.graph = nx.Graph()
        self.graph.add_nodes_from([self.system] + self.fragments)
        self.graph.add_edges_from(coupling_edges)

    def _entropy(self, probabilities):
        """Calculates Shannon Entropy in bits."""
        return -sum(p * np.log2(p) for p in probabilities if p > 0)

    def calculate_mutual_information(self, counts, total_shots):
        """Calculates I(S : F_i) for all fragments based on classical bitstrings."""
        mi_results = {}
        for f in self.fragments:
            joint_probs = {0: {0: 0.0, 1: 0.0}, 1: {0: 0.0, 1: 0.0}}
            for bitstring, count in counts.items():
                # Qiskit bitstrings are ordered from Q0 to Qn-1, so Qn-1 is bitstring[0]
                # We need to access from the end to match qubit index
                s_val = int(bitstring[-(self.system + 1)])
                f_val = int(bitstring[-(f + 1)])
                joint_probs[s_val][f_val] += count / total_shots

            p_s = [joint_probs[0][0] + joint_probs[0][1], joint_probs[1][0] + joint_probs[1][1]]
            p_f = [joint_probs[0][0] + joint_probs[1][0], joint_probs[0][1] + joint_probs[1][1]]

            h_s = self._entropy(p_s)
            h_f = self._entropy(p_f)
            # Flatten the joint probability dictionary values for entropy calculation
            h_sf = self._entropy([joint_probs[s_key][f_key] for s_key in [0,1] for f_key in [0,1]])

            mi = h_s + h_f - h_sf
            mi_results[f] = max(0.0, mi) # Floor to 0 to prevent negative due to floating point inaccuracies

        return mi_results

    def classify_topology(self, support_set):
        """Classifies the spatial nature of the leak using the Coupling Graph (G)."""
        if len(support_set) == 0: return "CLEAN (No stable records closed locally)"
        if len(support_set) == 1: return "SINGULAR (Isolated local leakage)"
        if len(support_set) > len(self.fragments) * 0.7: return "FLOOD (Global common-mode noise)"

        subgraph = self.graph.subgraph(support_set)
        components = list(nx.connected_components(subgraph))
        if len(components) == 1: return "PLUME (Contiguous leakage. Check local shielding)"
        else: return "GHOST (Disconnected leakage. Missing Hamiltonian edge)"

    def run_diagnostics(self, time_series_counts, total_shots, threshold_delta, tau_min):
        print("" + "="*65)

        print("     TRC DASHBOARD: THE TWO-ENGINE REDUNDANCY WITNESS")
        print("="*65)

        time_steps = len(time_series_counts)
        mi_over_time = []

        # 1. Calculate MI for all time steps
        for t in range(time_steps):
            mi_over_time.append(self.calculate_mutual_information(time_series_counts[t], total_shots))

        print(f"Parameters: Threshold = {threshold_delta} bits | Stability = {tau_min} steps")


        for t in range(time_steps - tau_min + 1):
            print(f"--- TIME STEP {t} ANALYSIS ---")

            # ---------------------------------------------------------
            # ENGINE 1: GLOBAL REDUNDANCY (The Thermodynamic Clock)
            # Uses the Average (Expectation) to check if the record has proliferated
            # ---------------------------------------------------------
            avg_mi = sum(mi_over_time[t].values()) / len(self.fragments)
            print(f" [Engine 1] Global Redundancy Proxy (Avg MI): {avg_mi:.4f} bits")
            if avg_mi >= threshold_delta:
                print("    -> SYSTEMIC ALERT: Macroscopic record closure detected. Time is ticking.")
            else:
                print("    -> Systemic Status: Superposition globally maintained.")

            # ---------------------------------------------------------
            # ENGINE 2: SPATIAL LEAKAGE WITNESS (The Hardware Forensics)
            # Uses the Maximum/Individual threshold to map specific hardware leaks
            # ---------------------------------------------------------
            support_set = []
            for f in self.fragments:
                # Check stability filter
                is_stable = all(mi_over_time[t + tau][f] >= threshold_delta for tau in range(tau_min))
                if is_stable:
                    support_set.append(f)

            print(f" [Engine 2] Spatial Support Set: Qubits {support_set}")
            topology = self.classify_topology(support_set)
            print(f"    -> TOPOLOGY MAP: {topology}")



# ==========================================
# PART 2: THE HARDWARE SIMULATION
# ==========================================

def simulate_hardware_crosstalk():
    """Simulates a 6-qubit linear hardware layout: Q0-Q1-Q2-Q3-Q4-Q5."""
    num_total_qubits = 21 # 1 system qubit + 20 fragment qubits
    sys_q = 10 # System qubit (e.g., the middle one)
    frag_qs = [q for q in range(num_total_qubits) if q != sys_q] # All other qubits as fragments
    edges = [(i, i + 1) for i in range(num_total_qubits - 1)] # Linear chain coupling

    dashboard = TRCDashboard(sys_q, frag_qs, edges)
    simulator = AerSimulator()
    time_series_data = []
    shots_per_state = 5000
    num_time_steps = 5

    print(f"Simulating Quantum Hardware with {num_total_qubits} qubits (Injecting 'Flood' crosstalk)...")
    print("WARNING: This simulation will be significantly slower due to the increased number of qubits and global interactions.")

    for t in range(num_time_steps):
        combined_counts = defaultdict(int)

        for prep_state in [0, 1]:
            qc = QuantumCircuit(num_total_qubits, num_total_qubits)
            if prep_state == 1: qc.x(sys_q)

            # INJECTING GLOBAL LEAKAGE (FLOOD) OVER TIME
            leakage_strength = 0.4 * t
            if t > 0:
                for f_q in frag_qs:
                    qc.crx(leakage_strength, sys_q, f_q)

            qc.measure(range(num_total_qubits), range(num_total_qubits))
            compiled_circuit = transpile(qc, simulator)
            result = simulator.run(compiled_circuit, shots=shots_per_state).result()
            counts = result.get_counts()

            for bitstring, count in counts.items():
                combined_counts[bitstring] += count

        time_series_data.append(combined_counts)

    dashboard.run_diagnostics(time_series_data, shots_per_state * 2, 0.05, 2)

if __name__ == "__main__":
    simulate_hardware_crosstalk()
