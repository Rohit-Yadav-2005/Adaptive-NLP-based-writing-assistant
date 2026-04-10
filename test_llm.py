import sys
sys.path.append('.')
from backend.style import extract_features
from backend.llm_engine import analyze_and_improve_with_llm
from dotenv import load_dotenv
load_dotenv()

try:
    print('Extracting features...')
    features = extract_features('This is a test.')
    print('Sending to LLM...')
    res = analyze_and_improve_with_llm('This is a test.', features)
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
