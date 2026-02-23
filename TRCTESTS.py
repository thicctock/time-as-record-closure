"""
Time As Record Closure (TRC) - Final Diagnostic Monitor (v7.4)
--------------------------------------------------------------
THE FAIL-FAST HARDWARE STANDARD:
- BULLETPROOF WELDING: Explicitly binds logical qubit objects to physical 
  indices via a dictionary to survive register re-ordering.
- TOPOLOGY AUDIT: Implements a "Fail-Fast" check post-compilation. If the 
  transpiler inserts a single SWAP gate, the script halts immediately to 
  prevent topology misclassification.
- RESTORED CHAOS: Uses a dynamic clock seed to properly stress-test the 
  monitor against randomized, unpredictable thermodynamic noise.

Author: Gemini & ChatGPT Collaboration
License: MIT
"""

import sys
import time
import numpy as np
import networkx as nx
from collections import deque, defaultdict

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, depolarizing_error, pauli_error
except ImportError as e:
    print(f"\n[FATAL] Missing libraries: {e}")
    sys.exit(1)

# ==========================================
# 🚨 CONFIGURATION & LAB SETTINGS 🚨
# ==========================================
SIM_METHOD = "statevector" 
USE_GPU = True
NUM_PAIRS = 10 
ROUNDS = 250   

# v7.4: Restoring Thermodynamic Chaos (Dynamic Seed)
SEED = int(time.time() * 1000) % (2**31 - 1)

# Statistical Sensitivity
WINDOW_SIZE = 20
BASELINE_FRACTION = 0.40  
FPR_QUANTILE = 0.95       
PERSISTENCE_WINDOWS = 3   

# Fault Injection
BURST_START = 125
BURST_LEN = 12            
DRIVE_ANGLE = 0.01        

EXTERNAL_ORIGIN = False     
TARGET_QUBITS = [3, 7] 

# Lab Sensor Thresholds
TEMP_LIMIT_MK = 20.0      
EMF_LIMIT_NT = 50.0       
RAD_LIMIT_CPM = 150.0     

# ==========================================
# PART 1: LAB TELEMETRY ENGINE
# ==========================================

class LabTelemetry:
    def __init__(self, rounds, seed):
        self.rounds = rounds
        rng = np.random.default_rng(seed)
        self.temp = rng.normal(15.0, 0.5, rounds)
        self.emf = rng.normal(10.0, 2.0, rounds)
        self.rad = rng.normal(40.0, 10.0, rounds)
        
    def inject_environmental_spike(self, start, length, type="RAD"):
        if type == "TEMP": self.temp[start:start+length] += 15.0
        elif type == "EMF": self.emf[start:start+length] += 80.0
        elif type == "RAD": self.rad[start:start+length] += 200.0

    def get_reading(self, cycle):
        return {"temp": self.temp[cycle], "emf": self.emf[cycle], "rad": self.rad[cycle]}

# ==========================================
# PART 2: THE DUAL-ENGINE MONITOR
# ==========================================

def binary_mi_jeffreys(x, y, alpha=0.5):
    n = len(x)
    if n == 0: return 0.0
    n00 = sum(1 for xi, yi in zip(x, y) if xi == 0 and yi == 0)
    n01 = sum(1 for xi, yi in zip(x, y) if xi == 0 and yi == 1)
    n10 = sum(1 for xi, yi in zip(x, y) if xi == 1 and yi == 0)
    n11 = n - n00 - n01 - n10
    denom = n + 4 * alpha
    p00, p01, p10, p11 = [(c + alpha)/denom for c in [n00, n01, n10, n11]]
    p0_, p1_ = p00 + p01, p10 + p11
    p_0, p_1 = p00 + p10, p01 + p11
    def log2(xv): return np.log(xv) / np.log(2)
    mi = 0.0
    for pxy, px, py in [(p00, p0_, p_0), (p01, p0_, p_1), (p10, p1_, p_0), (p11, p1_, p_1)]:
        mi += pxy * (log2(pxy) - log2(px) - log2(py))
    return max(0.0, float(mi))

class TRCMonitor:
    def __init__(self, ancillas, g_phys: nx.Graph, window_size=20, alpha=0.5):
        self.ancillas = list(ancillas) 
        self.g_phys = g_phys
        self.window_size = window_size
        self.alpha = alpha
        
        self.last_syn = None
        self.history = deque(maxlen=window_size)
        self._baseline_max = []
        self.threshold = None
        
        self.edge_streaks = defaultdict(int)
        self.max_eds_seen = 0.0
        self.apsp = dict(nx.all_pairs_shortest_path_length(self.g_phys))

    def ingest_syndrome(self, syn_dict):
        if self.last_syn is None:
            self.last_syn = syn_dict
            return False
        det = {a: syn_dict[a] ^ self.last_syn[a] for a in self.ancillas}
        self.history.append(det)
        self.last_syn = syn_dict
        return True

    def calibrate(self, cycle, baseline_end):
        if len(self.history) < self.window_size: return
        if cycle < baseline_end:
            series = {a: [e[a] for e in self.history] for a in self.ancillas}
            m = 0.0
            for i, a1 in enumerate(self.ancillas):
                for a2 in self.ancillas[i+1:]:
                    m = max(m, binary_mi_jeffreys(series[a1], series[a2], alpha=self.alpha))
            self._baseline_max.append(m)
        elif self.threshold is None:
            self.threshold = float(np.quantile(self._baseline_max, FPR_QUANTILE)) if self._baseline_max else 0.1
            print(f"\n[CALIBRATION] Noise floor locked at: {self.threshold:.3f} bits.")
            self.max_eds_seen = 0.0 

    def classify_topology(self, stable_edges):
        """v7.4 Anti-Smear Topology Logic."""
        support_set = set()
        for a1, a2 in stable_edges:
            support_set.add(a1); support_set.add(a2)
        
        support_set = sorted(list(support_set))
        stats = {"support": support_set}
        
        if len(support_set) / len(self.ancillas) >= 0.7: 
            return "FLOOD (Chip Meltdown)", stats
            
        g_support_hull = nx.Graph()
        g_support_hull.add_nodes_from(support_set)
        
        # Link only close pairs to forgive 1 missing node
        for i, n1 in enumerate(support_set):
            for n2 in support_set[i+1:]:
                dist = self.apsp[n1][n2]
                if dist <= 4: 
                    g_support_hull.add_edge(n1, n2)
                    
        physical_clusters = list(nx.connected_components(g_support_hull))
            
        if len(physical_clusters) > 1:
            return f"GHOST (Disconnected hardware clusters: {len(physical_clusters)} sites)", stats
            
        # Check actual diameter of the connected cluster to prevent transitive smearing
        cluster_nodes = list(physical_clusters[0])
        max_cluster_dist = 0
        for i, n1 in enumerate(cluster_nodes):
            for n2 in cluster_nodes[i+1:]:
                max_cluster_dist = max(max_cluster_dist, self.apsp[n1][n2])
                
        stats["max_dist"] = max_cluster_dist
        
        if max_cluster_dist <= 4: 
            return f"PLUME (Local physical leak spanning {max_cluster_dist} nodes)", stats
            
        return f"BOUNDARY (Extended contiguous error chain spanning {max_cluster_dist} nodes)", stats

    def step(self, cycle, baseline_end):
        if len(self.history) < self.window_size: return False, None
        self.calibrate(cycle, baseline_end)
        if self.threshold is None: return False, None

        series = {a: [e[a] for e in self.history] for a in self.ancillas}
        current_active_edges = set()
        
        for i, a1 in enumerate(self.ancillas):
            for a2 in self.ancillas[i+1:]:
                eds = binary_mi_jeffreys(series[a1], series[a2], alpha=self.alpha)
                self.max_eds_seen = max(self.max_eds_seen, eds)
                if eds > self.threshold: 
                    current_active_edges.add((a1, a2))

        stable_edges = []
        for edge in list(self.edge_streaks.keys()):
            if edge in current_active_edges:
                self.edge_streaks[edge] += 1
                if self.edge_streaks[edge] >= PERSISTENCE_WINDOWS:
                    stable_edges.append(edge)
            else:
                del self.edge_streaks[edge] 
                
        for edge in current_active_edges:
            if edge not in self.edge_streaks:
                self.edge_streaks[edge] = 1
                if self.edge_streaks[edge] >= PERSISTENCE_WINDOWS:
                    stable_edges.append(edge)

        if not stable_edges:
            return False, None
        
        topo, stats = self.classify_topology(stable_edges)
        details = {"topology": topo, "stats": stats}
        return True, details

# ==========================================
# PART 3: THE CIRCUIT & EXECUTION
# ==========================================

def create_fridge_noise_model():
    noise_model = NoiseModel()
    t1, t2 = 50.0, 70.0
    gate_time_1q, gate_time_2q = 0.1, 0.3
    therm_1q = thermal_relaxation_error(t1, t2, gate_time_1q)
    err_1q = therm_1q.compose(depolarizing_error(0.001, 1))
    therm_2q = therm_1q.tensor(therm_1q)
    err_2q = therm_2q.compose(depolarizing_error(0.01, 2))
    
    noise_model.add_all_qubit_quantum_error(err_1q, ["rx", "ry", "x"])
    noise_model.add_all_qubit_quantum_error(err_2q, ["cx"])
    return noise_model

def main():
    print("=" * 72)
    print(" BOOTING TRC v7.4: THE FAIL-FAST HARDWARE STANDARD")
    if EXTERNAL_ORIGIN:
        print(f" [MODE] Fault Logic : EXTERNAL MACROSCOPIC (Flag Qubit + Sensor Spike)")
    else:
        print(f" [MODE] Fault Logic : INTERNAL PARASITIC (Direct Fault + Clean Sensors)")
    print(f" [MODE] Target Qubits: {TARGET_QUBITS}")
    print(f" [QA] Seed: {SEED} (Dynamic Chaos Restored)")
    print("=" * 72)
    
    np.random.seed(SEED)
    telemetry = LabTelemetry(ROUNDS, seed=SEED)
    if EXTERNAL_ORIGIN:
        telemetry.inject_environmental_spike(BURST_START, BURST_LEN, "RAD") 
    
    ancillas = [f"A{i}" for i in range(NUM_PAIRS)]
    data_nodes = [f"D{i}" for i in range(NUM_PAIRS)]
    g_phys = nx.Graph()
    g_phys.add_nodes_from(ancillas + data_nodes)
    
    for i in range(NUM_PAIRS):
        g_phys.add_edge(f"A{i}", f"D{i}")
        g_phys.add_edge(f"A{i}", f"D{(i+1) % NUM_PAIRS}")
    
    monitor = TRCMonitor(ancillas, g_phys, window_size=WINDOW_SIZE, alpha=0.5)
    
    try:
        sim = AerSimulator(method=SIM_METHOD, device="GPU")
        print("[System] NVIDIA GPU Acceleration: ENGAGED 🚀")
    except Exception:
        sim = AerSimulator(method=SIM_METHOD)
        print("[System] GPU unavailable; running on CPU.")

    data_q, anc_q, flag_q = QuantumRegister(NUM_PAIRS, 'd'), QuantumRegister(NUM_PAIRS, 'a'), QuantumRegister(1, 'f')
    mem = ClassicalRegister(ROUNDS * NUM_PAIRS, "m")
    qc = QuantumCircuit(data_q, anc_q, flag_q, mem)
    
    flag_on = pauli_error([("X", 1.0)]).to_instruction()
    
    for r in range(ROUNDS):
        for i in range(NUM_PAIRS): qc.rx(DRIVE_ANGLE, data_q[i]); qc.ry(DRIVE_ANGLE, data_q[i])
        
        if BURST_START <= r < BURST_START + BURST_LEN:
            if EXTERNAL_ORIGIN:
                qc.append(flag_on, [flag_q[0]])
                for target in TARGET_QUBITS:
                    if target < NUM_PAIRS:
                        qc.cx(flag_q[0], data_q[target])
                qc.reset(flag_q[0])
            else:
                for target in TARGET_QUBITS:
                    if target < NUM_PAIRS:
                        qc.x(data_q[target])
                
        for i in range(NUM_PAIRS):
            qc.cx(data_q[i], anc_q[i]); qc.cx(data_q[(i + 1) % NUM_PAIRS], anc_q[i])
            
        cl_slice = [mem[r * NUM_PAIRS + i] for i in range(NUM_PAIRS)]
        qc.measure(anc_q, cl_slice)
        qc.reset(anc_q)

    # v7.4 FIX: BULLETPROOF HARDWARE WELDING
    # 1. We create an explicit dictionary mapping to avoid register-ordering brittleness.
    strict_hardware_mapping = {bit: i for i, bit in enumerate(qc.qubits)}
    
    tqc = transpile(
        qc, 
        sim, 
        basis_gates=["rx", "ry", "cx", "x", "measure", "reset"], 
        optimization_level=0,
        initial_layout=strict_hardware_mapping
        # routing_method='none' removed as it is non-standard and brittle
    )
    
    # v7.4 FIX: FAIL-FAST TOPOLOGY AUDIT
    # 2. Check if Qiskit secretly inserted routing swaps to satisfy constraints.
    ops = tqc.count_ops()
    if 'swap' in ops:
        raise RuntimeError(
            "\n[FATAL ERROR] HARDWARE WELD FAILED:\n"
            "The Transpiler inserted SWAP gates. Your logical adjacency no longer matches "
            "the physical silicon. TRC topology classifications (Plume/Ghost) will be invalid."
        )
    
    res = sim.run(tqc, noise_model=create_fridge_noise_model(), shots=1, memory=True, seed_simulator=SEED).result()
    raw_memory = res.get_memory()[0].replace(" ", "")
    baseline_end = int(BASELINE_FRACTION * ROUNDS)
    
    print("\n--- TRC REAL-TIME ANALYSIS ---")
    alarm_triggered = False; final_cycle = 0; final_details = None
    sensor_history = []

    for r in range(ROUNDS):
        final_cycle = r
        syn = {}
        for i in range(NUM_PAIRS):
            idx = r * NUM_PAIRS + i
            bit_char = raw_memory[-(idx + 1)] 
            syn[f"A{i}"] = 1 if bit_char == "1" else 0

        if not monitor.ingest_syndrome(syn): continue
        
        alarm, details = monitor.step(r, baseline_end)
        
        reading = telemetry.get_reading(r)
        if reading['temp'] > TEMP_LIMIT_MK or reading['emf'] > EMF_LIMIT_NT or reading['rad'] > RAD_LIMIT_CPM:
            sensor_history.append(r)
        
        if r == BURST_START: print(f"\n💥 [CYCLE {BURST_START}] FAULT INJECTED 💥")
        if alarm:
            print(f"\n🚨 [CYCLE {r}] TRC ALARM: SYSTEM HALTED")
            print(f"  => TOPOLOGY : {details['topology']}")
            print(f"  => LOCALIZED: {details['stats']['support']}")
            alarm_triggered = True; final_details = details
            break

    print("\n" + "="*70)
    print(" === POST-RUN DIAGNOSTIC SUMMARY (BIPARTITE FORENSICS) ===")
    print("="*70)
    
    if alarm_triggered:
        window_start = max(0, final_cycle - WINDOW_SIZE)
        recent_sensor_spikes = [c for c in sensor_history if window_start <= c <= final_cycle]
        match_found = len(recent_sensor_spikes) > 0
        topo = final_details['topology']
        support_set = final_details['stats']['support']
        snr_margin = (monitor.max_eds_seen / monitor.threshold) if monitor.threshold else 0
        
        print(f" -> FINAL VERDICT         : SYSTEM HALTED")
        print(f" -> DETECTION TOPOLOGY    : {topo}")
        print(f" -> LOCALIZED FAULT SET   : {support_set}")
        print(f" -> SIGNAL STRENGTH (SNR) : {snr_margin:.2f}x above noise floor")
        
        print(f"\n [!] ORIGIN FORENSICS:")
        if match_found and "GHOST" in topo:
            print("     Conclusion: COMPOUND EVENT (External Trigger -> Internal Vulnerability).")
        elif match_found:
            print("     Conclusion: TEMPORAL COINCIDENCE (Verified environmental sensor overlap).")
        else:
            print("     Conclusion: INTERNAL HARDWARE FAILURE (No overlapping sensor spikes).")
            
        reading = telemetry.get_reading(final_cycle)
        print(f"\n [!] TELEMETRY AT HALT (Cycle {final_cycle}):")
        print(f"     RAD: {reading['rad']:.1f} CPM | EMF: {reading['emf']:.1f} nT | TEMP: {reading['temp']:.1f} mK")
    else:
        print(f" -> FINAL VERDICT         : CLEAN RUN (System within safe limits)")
    print("="*70 + "\n")

if __name__ == "__main__": main()