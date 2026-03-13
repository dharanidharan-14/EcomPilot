
import requests
import time
import sys

API_BASE = "http://127.0.0.1:8002/api"
TEST_URL = "https://www.amazon.in/dp/B0CXMC2H2R"

def test_consistency(n=3):
    scores = []
    for i in range(n):
        print(f"Run {i+1}...")
        try:
            res = requests.post(f"{API_BASE}/analyze", json={"url": TEST_URL})
            job_id = res.json()["job_id"]
            
            while True:
                status_res = requests.get(f"{API_BASE}/status/{job_id}")
                data = status_res.json()
                if data["status"] == "completed":
                    score = data["result"]["return_risk_score"]
                    scores.append(score)
                    print(f"  Score: {score}")
                    break
                elif data["status"] == "failed":
                    print(f"  Failed: {data['message']}")
                    break
                time.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")
    
    if len(scores) > 1:
        if all(s == scores[0] for s in scores):
            print("\nSUCCESS: Scores are consistent!")
        else:
            print(f"\nFAILURE: Scores varied: {scores}")
    else:
        print("\nCould not collect enough scores for consistency check.")

if __name__ == "__main__":
    test_consistency()
