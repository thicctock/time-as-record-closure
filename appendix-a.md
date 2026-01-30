# Appendix A: Toy models and a diagram

---

## A0. Core definitions: Γ(R) and record order

Let **Ω** be a microstate space and let **ρ** map microstates ω to a macroscopic record state **R** (a coarse-graining).
Define:

- **Γ(R) = { ω : ρ(ω) = R }**

The closure order is:

- **R′ ≽ R  ⇔  Γ(R′) ⊆ Γ(R)**  
  (later records exclude more alternative microhistories)

---

## A1. Classical toy model (redundant copying into environment bits)

Consider a classical bit **S ∈ {0,1}** interacting sequentially with fresh environment bits **E₁, E₂, …** initially set to 0.

At step k, a local interaction in **P** writes a copy of S into Eₖ (idealized):

- **Eₖ ← S**

The record state after n steps is:

- **Rₙ := (E₁,…,Eₙ)**

and the record map ρ returns this record vector.

### Closure as shrinking compatible-sets

- **Γ(Rₙ)** is the set of all microstates (S, E₁,…,Eₙ, …) consistent with the observed record vector (E₁,…,Eₙ).
- Appending one more stable record bit yields **Rₙ₊₁ := (E₁,…,Eₙ, Eₙ₊₁)** and therefore **Γ(Rₙ₊₁) ⊆ Γ(Rₙ)** (more constraints).
- If copying is noisy (flip probability ε), closure is softer but still monotone once R includes redundancy statistics (e.g., counts of 0/1 over many Eᵢ) and stability is required over time τ ≥ τmin.

### Operational record criterion (classical)

Call a record **stable** if it survives bounded local perturbations and persists for τ ≥ τmin, and **redundant** if it is encoded in many independent degrees of freedom.
In this toy model, redundancy is simply the number of independent copies of S distributed across the Eᵢ.

**Takeaway:** the arrow is not a new law here; it is the structural fact that durable records accumulate and thereby rule out alternatives.

---

## A2. Quantum toy model (CPTP dephasing + redundancy growth)

Let **S** be a qubit with pointer basis {|0⟩,|1⟩}.
Let each environment qubit **Eₖ** start in |0⟩ and interact via a CNOT (S controls Eₖ):

- **Uₖ = CNOT(S → Eₖ)**
 We use CNOT as a standard toy interaction that imprints the system’s pointer-basis value into an environment qubit, i.e., a minimal ‘record-writing’ mechanism.

For an initial |ψ⟩ = a|0⟩ + b|1⟩, after n interactions:

- **|Ψₙ⟩ = a |0⟩ |0…0⟩  +  b |1⟩ |1…1⟩**  (GHZ-like record state)

### CPTP view (reduced dynamics on S)

Tracing out the environment yields a dephasing channel on S.
Off-diagonal coherence in the pointer basis is suppressed. With imperfect interactions (or environmental noise), one commonly gets:

- **ρ₀₁ → γⁿ ρ₀₁** for some |γ| < 1,

while populations stay fixed.

### Redundancy (Darwinism-style, informal)

- Pick the recorded classical variable **X** = pointer outcome in {|0⟩,|1⟩}.
- Each disjoint fragment **F** carries accessible information about X.
- When many disjoint fragments each carry ≳(1−δ) of the information about X, the record is redundant; denote the redundancy by **rδ**.

In this toy model, once environment fragments separate, recohering the branches requires collecting and reversing *all* fragments (a global Loschmidt echo). Before redundancy spreads, recoherence (quantum eraser) is possible; after redundancy spreads, stability makes the record effectively classical. This is the intended boundary between reversible correlations and record-generating novelty **N\***.

---

## A3. Diagram: Record chain and Γ(R) nesting

Below is a simple **chain** example (a special case of a general poset).  
As stable records accumulate, the set of compatible microstates **shrinks**.

```text
Record chain (example):

+----+     +----+     +----+     +----+
| R0 | --> | R1 | --> | R2 | --> | R3 |
+----+     +----+     +----+     +----+
          (R_{k+1} ≽ R_k)

Compatible microstate sets (semantic anchor):

+--------------------------------------+
|               Γ(R0)                  |
|   +------------------------------+   |
|   |           Γ(R1)              |   |
|   |    +---------------------+   |   |
|   |    |        Γ(R2)         |   |   |
|   |    |   +-------------+    |   |   |
|   |    |   |   Γ(R3)     |    |   |   |
|   |    |   +-------------+    |   |   |
|   |    +---------------------+   |   |
|   +------------------------------+   |
+--------------------------------------+

Nesting:  Γ(R3) ⊆ Γ(R2) ⊆ Γ(R1) ⊆ Γ(R0)
Meaning: later records rule out more alternative microhistories.
