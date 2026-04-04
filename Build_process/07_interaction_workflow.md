# Agent-Environment Interaction Workflow

This document explains how an AI agent (LLM-based) interacts with the **OsWorld-OpenEnv** system. The environment follows a standard Reinforcement Learning (RL) loop, optimized for "Look-Before-You-Leap" diagnostic reasoning.

## 1. System Architecture

The system operates as a **Client-Server** model:
- **Server (OsWorld-OpenEnv)**: A FastAPI-based environment that maintains the state of the data files, executes Python code in a controlled way, and calculates rewards/grades.
- **Client (Agent)**: An LLM-powered agent that receives observations and sends actions.

## 2. The Interaction Loop

### Phase A: Reset & Diagnosis (Step 0)
When the environment resets, it generates a unique dataset based on a seed.
1.  **Agent Action**: `reset()`
2.  **Env Response**: Provides the `task_description` (e.g., "Fix duplicates and rename columns") and the initial `files` (dirty CSVs).
3.  **Agent Strategy**: Instead of writing code immediately, the agent should call `inspect_schema` or `view_head` to understand the *actual* corruption (e.g., "Are the columns capitalized? Are there NaN values?").

### Phase B: Action & Observation
The agent chooses one of the following actions:
- **Diagnostic Actions** (`inspect_schema`, `view_head`, `read_file`): These return data to the agent's "screen" without changing the files. These cost a tiny penalty but trigger the **Inspect-First Bonus**.
- **Transformation Actions** (`execute_python`): The agent sends a block of Pandas code. The environment runs this code against the `files` dictionary.
- **Safety Actions** (`preview_changes`): The agent runs code to see the output, but the environment automatically rolls back any file changes.

### Phase C: Grading & Reward
After every state-changing action:
1.  The `SemanticGrader` compares the current `files` against the `expected_df`.
2.  It calculates the **Phi (Φ) score** (0.0 to 1.0) based on content, schema, and constraints.
3.  The `RewardCalculator` generates a signal:
    - **Positive**: If Φ increases.
    - **Negative**: If a step is taken (Step Penalty) or an error occurs.
    - **Terminal**: A large bonus once Φ = 1.0, scaled by how many steps were taken (Efficiency Scaling).

## 3. How the AI "Sees" the World

The agent receives a JSON-like `Observation` object:

```json
{
  "screen_text": "Schema for data.csv:\nid     int64\nname   object",
  "files": {
    "data.csv": "id,name\n1,alice\n2,bob..."
  },
  "current_task": "Standardize names to lowercase...",
  "reward": 0.47,
  "score": 0.6,
  "done": false
}
```

## 4. Key Logic for Developers

- **Who does it call?** The environment calls `exec()` internally for Python actions, but wraps it in a snapshot/rollback mechanism for safety and `preview_changes`.
- **How does it know it's done?** The environment sets `done=True` when the score hits 1.0 (success) or `step_count` hits `max_steps` (timeout).
- **Efficiency**: An agent that solves a task in 2 steps gets a significantly higher reward than one that takes 8 steps, thanks to the `optimal_steps` scaling in `rewards.py`.
