import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # First, register a new session to test
        resp = await client.post("http://localhost:8000/api/simulations", json={
            "player_name": "Test Player",
            "facilitator_name": "Test Facilitator",
            "industry": "Consumer Goods"
        })
        if resp.status_code != 200:
            print("Failed to start session:", resp.text)
            return
            
        session_id = resp.json()["session_id"]
        print(f"Started session {session_id}")
        
        # Advance through 10 rounds to make interview available
        for i in range(10):
            r = await client.post(f"http://localhost:8000/api/simulations/{session_id}/decision", json={
                "choice": "option_a"
            })
            if r.status_code != 200:
                print(f"Failed to advance round {i+1}:", r.text)
                return
        print("Advanced to end of game.")
        
        # Try assessing
        responses = [
            "We prioritized short-term profits but eventually realized the importance of sustainability and invested heavily in it.",
            "We balanced stakeholder needs by communicating openly and offering compromises where possible.",
            "I learned that decisions compound over time, so early investments in ESG had massive payoffs later.",
            "I would have invested earlier in the community fund to prevent the activist intervention.",
            "I'd diversify our supply chain and improve ESG transparency to defend against activist claims."
        ]
        
        print("Submitting interview responses...")
        resp = await client.post(f"http://localhost:8000/api/simulations/{session_id}/ceo-interview/assess", json={
            "responses": responses
        }, timeout=30.0)
        
        if resp.status_code == 200:
            data = resp.json()
            print("Success!")
            print("LLM Used:", data.get("llm_used"))
            print("Final Scores:", data.get("final_scores"))
            print("Response Scores:", data.get("response_scores"))
            print("Data Scores:", data.get("raw_data_scores"))
        else:
            print("Failed assessment:", resp.status_code, resp.text)

if __name__ == "__main__":
    asyncio.run(test())
