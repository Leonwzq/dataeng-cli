import random
from datetime import datetime, timedelta

def generate_mock_uniprot_data(query: str, size: int = 5):
    """在无网/目标 API 不可用时，模拟生成符合规范的 UniProt REST 响应"""
    results = []
    base_id = 100000
    for i in range(size):
        acc = f"P{base_id + i}"
        dt = (datetime.now() - timedelta(days=random.randint(0, 10))).strftime("%Y-%m-%d")
        results.append({
            "primaryAccession": acc,
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": f"Mock Protein {query.capitalize()} {i+1}"}}
            },
            "organism": {"scientificName": "Homo sapiens"},
            "entryAudit": {"lastAnnotationUpdateDate": dt},
            "sequence": {"length": random.randint(100, 1000)}
        })
    return {"results": results}
