# SPICESurfing

An multi-agent system for automatically generating and validating analog circuits using PySpice. Three LLM agents collaborate cyclically: a code generator, an optimizer/validator, and a knowledge curator (wise one) that updates and maintains a Self-Evolving Memory (SEM) that contains both general and task-specific information.

## Framework

- **Code Generator** — produces a PySpice script for a given circuit task, informed by the SEM and the previous iteration's script and associated repair plan
- **Optimizer** — runs a 5-stage check suite (requirement, op_point, dc_sweep, function, waveform), diagnosing and recording failures
- **Wise One** — curates generalizable lessons/heuristics from each iteration into the SEM for future runs

All three agents are currently configured to run on a local installation of qwen3.5:9b via the ollama api

## Setup

create new conda environment

```
conda create -n SPICE python=3.11
conda activate SPICE
pip install -r requirements.txt
```

PySpice also requires a local ngspice installation:

```
pyspice-post-installation --install-ngspice-dll
```

## Usage

Tasks are stored as json files in tasks\ and are provided as arguments like so:

```
python main.py --task tasks/your_task.json --max_attempts 10
```
