import asyncio
import aiohttp  # pip install aiohttp (async version of requests)
import json
import os
from dotenv import load_dotenv

load_dotenv()


async def call_llm_async(
        session: aiohttp.ClientSession,
        prompt: str,
        user_id: str
) -> dict:
    """
    Async version of LLM call.
    Does NOT block other requests while waiting.
    """
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
        "data-encoding": "utf-8",
        "Accept": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    try:
        # async with = automatically closes connection when done
        # await = wait for this, but let other tasks run while waiting
        async with session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            reply = result["choices"][0]["message"]["content"]

            print(f"✅ User {user_id} completed: {reply[:50]}...")
            return {"user_id": user_id, "response": reply, "success": True}

    except Exception as e:
        print(f"❌ User {user_id} failed: {e}")
        return {"user_id": user_id, "response": None, "success": False, "error": str(e)}


async def handle_multiple_users():
    """
    Handle 3 users simultaneously.
    """
    # Create a single session (reused across all requests)
    async with aiohttp.ClientSession() as session:
        # Create 3 tasks - these will run CONCURRENTLY
        tasks = [
            call_llm_async(session, "What is machine learning? Explain briefly.", "user_1"),
            call_llm_async(session, "Tell me a short joke about programming.", "user_2"),
            call_llm_async(session, "What's the capital of France?", "user_3"),
            call_llm_async(session, "What's the meaning of life?", "user_4"),
            call_llm_async(session, "What's the weather in Paris?", "user_5"),
            call_llm_async(session, "what's the weather today?", "user_6"),
            call_llm_async(session, "What's the weather yesterday?", "user_7"),
            call_llm_async(session, "What's the weather today?", "user_8"),
        ]

        # Run all tasks at the same time and wait for ALL to complete
        results = await asyncio.gather(*tasks)

        return results


# ============= RUN IT =============
if __name__ == "__main__":
    print("Starting 3 simultaneous requests...")


    # asyncio.run() starts the async event loop
    all_responses = asyncio.run(handle_multiple_users())

    print("-" * 50)
    print("\nSUMMARY:")
    for result in all_responses:
        if result["success"]:
            print(f"  {result['user_id']}: {result['response'][:60]}...")
        else:
            print(f"  {result['user_id']}: FAILED - {result.get('error')}")
            print(f"    {result['response']}")
            print("-" * 50)

        results = asyncio.run(handle_multiple_users())
        print(results)

