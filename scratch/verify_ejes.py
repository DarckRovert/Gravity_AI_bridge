import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'f:/Gravity_AI_bridge')

errors = []

# EJE 5: gravity_brain cache
from core.gravity_brain import _CONTEXT_TTL
assert _CONTEXT_TTL == 15.0, f'FAIL TTL: {_CONTEXT_TTL}'
print(f'EJE 5 - GravityBrain TTL: {_CONTEXT_TTL}s OK')

# EJE 6: image_router
from core.image_router import generate
import inspect
sig = inspect.signature(generate)
params = list(sig.parameters.keys())
assert 'prompt' in params and 'output_path' in params and 'title' in params
print(f'EJE 6 - ImageRouter params: {params} OK')

# EJE 2: web_search
from tools.web_search import MAX_RES, fetch_page_text
assert MAX_RES == 10, f'FAIL MAX_RES={MAX_RES}'
assert callable(fetch_page_text)
print(f'EJE 2 - MAX_RES={MAX_RES}, fetch_page_text callable: OK')

# EJE 1: research_writer source checks
with open('f:/Gravity_AI_bridge/tools/research_writer.py', 'r', encoding='utf-8') as f:
    src = f.read()

checks_eje1 = {
    "tables extension": "tables",
    "latex_cleaner.full_clean": "latex_cleaner.full_clean",
    "max_free_chapters": "max_free_chapters",
    "image_router.generate": "image_router.generate",
    "_post_process_markdown usa latex_cleaner": "latex_cleaner.full_clean(md_content)",
    "3 queries OSINT": "queries = [q.strip",
}
for check, pattern in checks_eje1.items():
    if pattern in src:
        print(f'EJE 1 - {check}: OK')
    else:
        print(f'EJE 1 - {check}: FAIL (pattern not found: {pattern})')
        errors.append(check)

# EJE 4: multi_agent
with open('f:/Gravity_AI_bridge/core/multi_agent.py', 'r', encoding='utf-8') as f:
    ma_src = f.read()
for check, pattern in [("TF-IDF", "_tfidf_vector"), ("synthesize mode", "synthesize"), ("cosine", "_cosine"), ("method key", '"method"')]:
    if pattern in ma_src:
        print(f'EJE 4 - {check}: OK')
    else:
        print(f'EJE 4 - {check}: FAIL')
        errors.append(f'EJE4 {check}')

# EJE 3: model_selector
from core.model_selector import TASK_PROFILES, _rank_model
assert 'creative' in TASK_PROFILES, 'FAIL: creative not in TASK_PROFILES'
# rank model debe funcionar para creative
r_llama = _rank_model('llama-3.1-8b', 'creative')
r_coder = _rank_model('qwen2.5-coder-14b', 'creative')
assert r_llama > r_coder, f'FAIL: llama {r_llama} no supera coder {r_coder}'
print(f'EJE 3 - creative profile: OK (llama={r_llama}, coder={r_coder})')

# EJE 7: latex_cleaner full test
from tools.latex_cleaner import clean
t = r'\Sigma T_{\text{max}} = \frac{1}{T} y T \to 0'
r = clean(t)
assert 'Σ' in r, f'FAIL Sigma: {r}'
assert '→' in r, f'FAIL to: {r}'
assert '1/T' in r, f'FAIL frac: {r}'
assert r'\frac' not in r, f'FAIL frac raw: {r}'
print(f'EJE 7 - latex_cleaner output: {r!r} OK')

print()
if errors:
    print(f'FAILURES: {errors}')
else:
    print('=== ALL 7 EJES VERIFIED CLEAN ===')
