# diag_genai.py
from dotenv import load_dotenv
load_dotenv()

import os, sys

print("=== Gemini diagnostic ===")
print("CWD:", os.getcwd())
print("GEMINI_API_KEY in env:", bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")))
print("PYTHON:", sys.version)

try:
    import google.generativeai as genai
    print("Imported google.generativeai OK")
    # show relevant members
    interesting = [n for n in dir(genai) if any(k in n.lower() for k in ('generate','image','images','chat','client','configure','api'))]
    print("\nInteresting members (filtered):", interesting)
    print("\ndir(genai) sample (first 120 chars):", str(dir(genai))[:120])
    # Try to print callable signatures or repr for a few likely candidates
    candidates = ['generate_text','generate_image','generate','images','chat','Client','configure','configure_api','configure_client','text','responses']
    for name in candidates:
        if hasattr(genai, name):
            attr = getattr(genai, name)
            try:
                print(f"\nFOUND: genai.{name} -> {repr(attr)[:300]}")
            except Exception:
                print(f"\nFOUND: genai.{name} -> (repr failed)")
except Exception as e:
    print("\nImport / inspection failed:", e)
    import traceback
    traceback.print_exc()

print("\n=== end diagnostic ===")
