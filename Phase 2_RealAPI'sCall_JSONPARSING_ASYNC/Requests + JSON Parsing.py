import requests
import json
from typing import Dict, Any


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Professional search tool that an agent can call."""
    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": query,
        "num": max_results
    })

    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()  # Raises error if status is not 200

        data = response.json()  # Convert response to Python dict

        # Clean and return only what agent needs
        results = []
        for item in data.get("organic", [])[:max_results]:
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })

        return {
            "success": True,
            "query": query,
            "results": results,
            "total_found": len(results)
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Search request timed out"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
