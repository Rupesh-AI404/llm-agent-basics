import requests
import json
import os
from dotenv import load_dotenv

# Load your API key from .env file (Example 2.1)
load_dotenv()


def call_openai(prompt: str) -> str:
    """
    Send a prompt to OpenAI and get the response.
    This is the foundation of every AI agent you'll build.
    """

    # The URL where OpenAI lives (always this)
    url = "https://api.openai.com/v1/chat/completions"

    # Your ID badge to prove you're allowed in
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
        "User-Agent": "My-Agent/1.0.0"
    }

    # The actual message you're sending
    payload = {
        "model": "gpt-3.5-turbo",  # Which OpenAI brain to use
        "messages": [
            {"role": "user", "content": prompt}  # What you want to say
        ],
        "temperature": 0.7,  # How creative to be (0=robot, 1=wild)
        "max_tokens": 150  # How long the response can be
    }

    try:
        # Send the request and wait for response
        response = requests.post(url, headers=headers, json=payload)

        # If status code is not 200, raise an exception
        response.raise_for_status()

        # Convert JSON string to Python dictionary
        result = response.json()
        response.close()

        # Navigate through the nested response to get the text
        # OpenAI returns: result["choices"][0]["message"]["content"]
        reply = result["choices"][0]["message"]["content"]

        return reply

    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        return None

    finally:
        print("API call completed.")
        return None


# Use it
user_question = "What is the capital of Japan?"
answer = call_openai(user_question)
print(f"User: {user_question}")
print(f"AI: {answer}")

