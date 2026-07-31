import time
import requests
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("dataeng")

class UniProtFetcher:
    BASE_URL = "https://rest.uniprot.org/uniprotkb/search"

    def __init__(self, retries: int = 3, backoff_factor: float = 1.0, timeout: int = 10):
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    def fetch(self, query: str, size: int = 25) -> Dict[str, Any]:
        """按关键词或 ID 抓取数据，带退避重试"""
        params = {
            "query": query,
            "size": size,
            "format": "json"
        }
        
        for attempt in range(1, self.retries + 1):
            try:
                logger.info(f"正在请求 UniProt API (尝试 {attempt}/{self.retries}): query={query}")
                resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                if not data.get("results"):
                    logger.warning(f"查询无结果: query='{query}'")
                return data
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.error(f"请求失败 (尝试 {attempt}/{self.retries}): {e}")
                if attempt == self.retries:
                    raise RuntimeError(f"数据源不可达或响应异常: {e}")
                time.sleep(self.backoff_factor * (2 ** (attempt - 1)))
        return {}

    def save_raw(self, data: Dict[str, Any], output_dir: Path, filename: str) -> Path:
        """原始响应落盘（保留可追溯性）"""
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{filename}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"原始响应已落盘: {file_path}")
        return file_path
