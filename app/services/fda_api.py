import httpx
from app.config import settings

async def search_drugs(query: str):
    """Searches openFDA for drugs matching the query."""
    url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": f"(openfda.brand_name:{query} OR openfda.generic_name:{query})",
        "limit": 10
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get('results', []):
                openfda = item.get('openfda', {})
                results.append({
                    "brand_name": openfda.get('brand_name', ['Unknown'])[0],
                    "generic_name": openfda.get('generic_name', ['Unknown'])[0],
                    "manufacturer": openfda.get('manufacturer_name', ['Unknown'])[0],
                    "ndc": openfda.get('product_ndc', ['Unknown'])[0],
                    "purpose": item.get('purpose', [''])[0] if item.get('purpose') else "",
                    "warnings": item.get('warnings', [''])[0][:200] + "..." if item.get('warnings') else ""
                })
            return results
        except Exception as e:
            print(f"FDA API Error: {e}")
            return []
