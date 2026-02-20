Hardware Diagnostic Dashboard

Time As Record Closure (TRC) - Redundancy Witness for Quantum Hardware

This repository contains the operational Python/Qiskit implementation of the Two-Engine TRC Framework, a thermodynamic diagnostic tool for mapping crosstalk and decoherence in NISQ-era quantum processors.

The Theory: Time As Record Closure

In the TRC framework, macroscopic decoherence (and the thermodynamic "Arrow of Time") is not a continuous background clock. It only ticks forward when the environment successfully copies and proliferates a stable record of a quantum system's pointer state (Quantum Darwinism).

This dashboard operationalizes that theory into a practical, two-engine hardware diagnostic tool using Classical Mutual Information.

The Two-Engine Approach

Engine 1: Global Redundancy (The Thermodynamic Clock)

Measures the Average Mutual Information across the spectator bath.

Purpose: Detects true, irreversible macroscopic record closure. If the average crosses the threshold, the leak is global, and the system has decohered.

Engine 2: Spatial Leakage Witness (The Hardware Forensics)

Measures the Maximum Mutual Information of specific fragment qubits and applies a time-stability filter ($\tau_{\text{min}}$).

Purpose: Maps specific hardware leaks. It classifies the leakage topology into:

PLUME: Contiguous, local hardware crosstalk (e.g., bad microwave shielding).

GHOST: Disconnected, parasitic leakage (e.g., missing Hamiltonian edges).

FLOOD: Global, common-mode noise.

Getting Started

You can run this diagnostic suite locally or in a cloud environment like Google Colab.

Prerequisites

pip install qiskit qiskit-aer numpy networkx

Running the Simulation

The trc_dashboard_v2.py script includes a built-in 21-qubit hardware simulation. By default, it runs a "Flood Test", injecting coherent crosstalk from a system qubit to 20 spectator qubits to demonstrate how Engine 1 triggers a systemic alert when redundancy saturates the bath.

python trc_dashboard_v2.py

License

This project is licensed under the MIT License. You are free to use this diagnostic framework in both academic research and commercial quantum calibration software, provided proper attribution is given.
