import asyncio
from backend.main import analyze, AnalyzeRequest

def main():
    req = AnalyzeRequest(user_id="test_user", text="The experiment results was very interesting.")
    res = analyze(req)
    print("FINAL TEXT:", res.corrected_text)
    print("DOMAIN:", res.domain)
    print("STYLE PROFILE:", res.style_profile)

if __name__ == "__main__":
    main()
