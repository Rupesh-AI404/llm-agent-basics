import json

import requests


def call_llm_with_fallback(prompt: str):
    """LLMs fail constantly. Plan for it."""
    try:
        # This is what real agent code looks like
        response = mock_llm_call(prompt)  # Replace with real API
        return json.loads(response)  # LLMs return JSON strings

    except json.JSONDecodeError as e:
        print(f"LLM gave bad JSON: {e}")
        return {"error": "invalid_json", "raw_response": response}

    except ConnectionError as e:
        print(f"API down: {e}")
        return {"error": "api_unavailable"}

    except Exception as e:
        print(f"Unknown disaster: {e}")
        return {"error": "unknown", "details": str(e)}

    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return {"error": "connection_error", "details": str(e)}

    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
        return {"error": "timeout_error", "details": str(e)}\

    except requests.exceptions.TooManyRedirects as e:
        print(f"Too many redirects error: {e}")
        return {"error": "too_many_redirects", "details": str(e)}

    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return {"error": "request_exception", "details": str(e)}


def mock_llm_call(prompt):
    # Simulates LLM returning malformed JSON
    return "{'wrong_quotes': 'this uses single quotes'}"  # This will fail
