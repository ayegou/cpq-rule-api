from fastapi import FastAPI
from pydantic import BaseModel
import re, requests, json

app = FastAPI()

class RuleRequest(BaseModel):
    rule: str
    values: dict

@app.post("/evaluate")
def evaluate_rule(req: RuleRequest):
    def convert_expr(expr):
        expr = re.sub(r'"([^"]*)"\|', r'"\1"', expr)
        expr = re.sub(r'\bNot\s*\(', 'not(', expr, flags=re.IGNORECASE)
        expr = expr.replace('-', '_')
        expr = expr.replace('<>', '!=')
        expr = re.sub(r'(?<![<>=!])=(?!=)', '==', expr)
        expr = re.sub(r'"(\d+(\.\d+)?)"', r'\1', expr)
        return expr

    assignments = []
    for k, v in req.values.items():
        safe_k = k.replace('-', '_')
        if str(v).isdigit():
            assignments.append(f'{safe_k} = {v}')
        else:
            assignments.append(f'{safe_k} = "{v}"')

    python_expr = convert_expr(req.rule)
    code = '\n'.join(assignments) + f'\nprint({python_expr})'

    piston_payload = {
        "language": "python3",
        "version": "3.10.0",
        "files": [{"name": "main.py", "content": code}]
    }

    r = requests.post("https://emkc.org/api/v2/piston/execute", json=piston_payload)
    resp = r.json()
    return {
    "code_sent": code,
    "original_rule_escaped": json.dumps(req.rule),
    "piston_raw": resp
    }
    

