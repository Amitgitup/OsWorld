import sys
import os
import pandas as pd
import io

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "server"))

from server.OsWorld_environment import OsworldEnvironment
from models import OsworldAction

def test_task(env_level, reset_count, seed, solver_code):
    env = OsworldEnvironment()
    # Force the level by manipulating the reset count inside get_next_level?
    # No, we can just call reset with difficulty option and then the internal state might cycle.
    # Actually, OsworldEnvironment.reset(options={"difficulty": env_level, "seed": seed})
    # Wait, the environment loops through variants using `self._reset_count`.
    # Let's override `self._reset_count` directly if we want a specific variant.
    
    # We will instantiate a new env, set its reset_count, and then reset it.
    env = OsworldEnvironment()
    env._reset_count = reset_count
    
    obs = env.reset(options={"difficulty": env_level, "seed": seed})
    initial_score = obs.score
    
    # Action 1: Inspect schema (to get the first_inspect bonus)
    action_1 = OsworldAction(action_type="inspect_schema", payload={"filename": "data.csv"})
    obs = env.step(action_1)
    inspect_reward = obs.reward
    
    # Action 2: Solver payload
    action_2 = OsworldAction(action_type="execute_python", payload={"code": solver_code})
    obs = env.step(action_2)
    
    final_score = obs.score
    final_reward = obs.reward
    is_done = obs.done
    
    return {
        "task_desc": obs.current_task[:50] + "...",
        "initial_score": initial_score,
        "final_score": final_score,
        "final_reward": final_reward,
        "done": is_done,
        "screen_text": obs.screen_text
    }

solvers = {
    "easy_0": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df.columns = ['id', 'name']; df = df.drop_duplicates(); files['data.csv'] = df.to_csv(index=False)",
    "easy_1": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df.columns = ['id', 'name']; df['name'] = df['name'].str.strip().str.lower(); files['data.csv'] = df.to_csv(index=False)",
    "easy_2": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df.columns = ['id', 'name', 'age', 'is_active']; df['age'] = df['age'].astype(str).str.replace(' yrs', '').astype(int); df['is_active'] = df['is_active'] == 'Yes'; files['data.csv'] = df.to_csv(index=False)",
    "easy_3": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df.columns = ['id', 'name', 'score']; files['data.csv'] = df.to_csv(index=False)",
    
    "medium_0": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df = df.drop(columns=['extra']); df.columns = ['id', 'val']; df['val'] = df['val'].fillna(0); files['data.csv'] = df.to_csv(index=False)",
    "medium_1": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df = df[['IDENTIFIER', 'VALUE']]; df.columns = ['id', 'val']; files['data.csv'] = df.to_csv(index=False)",
    "medium_2": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df.columns=['id','val','extra']; df=df.drop(columns=['extra']); df=df.drop_duplicates(subset=['id'], keep='first'); df['val']=df['val'].clip(0, 100); files['data.csv']=df.to_csv(index=False)",
    "medium_3": "import pandas as pd; import io; users = pd.read_csv(io.StringIO(files['users.csv'])); orders = pd.read_csv(io.StringIO(files['orders.csv'])); orders = orders[['UID', 'order_value']].rename(columns={'UID': 'user_id'}); df = pd.merge(users, orders, on='user_id', how='inner'); files['merged.csv'] = df.to_csv(index=False)",
    "medium_4": "import pandas as pd; import json; data = json.loads(files['data.json']); rows = [{'id': d['identifier'], 'name': d['person']['name'], 'city': d['person']['location']['city'], 'val': d['metric']} for d in data]; df = pd.DataFrame(rows); files['data.csv'] = df.to_csv(index=False)",
    
    "hard_0": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df.columns=['id','name','val','e']; df=df.drop(columns=['e']); df['name']=df['name'].str.strip().str.lower(); df=df.drop_duplicates(subset=['id'], keep='first'); df['val']=df['val'].fillna(0).clip(0,100); files['data.csv']=df.to_csv(index=False)",
    "hard_1": "import pandas as pd; import io; df = pd.read_csv(io.StringIO(files['data.csv'])); df['age']=df['age'].clip(0,100); df['score']=df['score'].clip(0,100); files['data.csv']=df.to_csv(index=False)",
    "hard_2": "import pandas as pd; import io; inv = pd.read_csv(io.StringIO(files['inventory.csv'])); rates = pd.read_csv(io.StringIO(files['rates.csv'])); inv['item_name'] = inv['item_name'].str.strip().str.lower(); inv['price_gbp'] = inv['price_gbp'].fillna(0); rate = rates[rates['currency']=='USD']['rate'].iloc[0]; inv['price_usd'] = inv['price_gbp'] * rate; files['final.csv']=inv.to_csv(index=False)"
}

tests = [
    ("easy", 0, "easy_0"),
    ("easy", 3, "easy_1"),
    ("easy", 6, "easy_2"),
    ("easy", 9, "easy_3"),
    ("medium", 0, "medium_0"),
    ("medium", 3, "medium_1"),
    ("medium", 6, "medium_2"),
    ("medium", 9, "medium_3"),
    ("medium", 12, "medium_4"),
    ("hard", 0, "hard_0"),
    ("hard", 3, "hard_1"),
    ("hard", 6, "hard_2")
]

results = []
for level, reset_count, solver_key in tests:
    print(f"Testing {solver_key}...")
    try:
        res = test_task(level, reset_count, 42, solvers[solver_key])
        res["key"] = solver_key
        results.append(res)
        print(f"Result for {solver_key}: {res['final_score']}")
    except Exception as e:
        print(f"Error on {solver_key}: {e}")

print("--- SUMMARY ---")
for r in results:
    status = "PASS" if r['final_score'] == 1.0 else f"FAIL (Score: {r['final_score']})"
    print(f"[{r['key']}] {status} - Reward: {r['final_reward']:.2f} | Init Score: {r['initial_score']:.2f}")

