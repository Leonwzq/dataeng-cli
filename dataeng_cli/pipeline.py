import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("dataeng")

class SyncPipeline:
    def __init__(self, db_path: str = "./data/state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化 Watermark 与去重索引库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watermarks (
                    source TEXT PRIMARY KEY,
                    last_updated TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_records (
                    primary_accession TEXT PRIMARY KEY,
                    updated_at TEXT,
                    source TEXT
                )
            """)

    def get_watermark(self, source: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_updated FROM watermarks WHERE source = ?", (source,))
            row = cursor.fetchone()
            return row[0] if row else "1970-01-01"

    def set_watermark(self, source: str, watermark: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO watermarks (source, last_updated) VALUES (?, ?) ON CONFLICT(source) DO UPDATE SET last_updated=excluded.last_updated",
                (source, watermark)
            )

    @staticmethod
    def normalize_date(date_str: str) -> str:
        """自动修复：日期格式归一化转换至 YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(date_str.split("T")[0], fmt.split("T")[0]).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str

    def process_and_deduplicate(self, records: List[Dict[str, Any]], source: str, out_dir: Path) -> Tuple[int, int, int]:
        """数据增量判定、去重落盘"""
        out_dir.mkdir(parents=True, exist_ok=True)
        added, updated, skipped = 0, 0, 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for rec in records:
                accession = rec.get("primaryAccession")
                # 自动修复日期规范
                mod_date = self.normalize_date(rec.get("entryAudit", {}).get("lastAnnotationUpdateDate", ""))
                
                cursor.execute("SELECT updated_at FROM processed_records WHERE primary_accession = ?", (accession,))
                row = cursor.fetchone()

                if row is None:
                    # 新增
                    cursor.execute("INSERT INTO processed_records VALUES (?, ?, ?)", (accession, mod_date, source))
                    added += 1
                elif row[0] < mod_date:
                    # 更新
                    cursor.execute("UPDATE processed_records SET updated_at = ? WHERE primary_accession = ?", (mod_date, accession))
                    updated += 1
                else:
                    # 重复/未变更
                    skipped += 1
                    continue

                # 提取标准规范化文档并落盘
                clean_rec = {
                    "id": accession,
                    "protein_name": rec.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "Unknown"),
                    "organism": rec.get("organism", {}).get("scientificName", "Unknown"),
                    "updated_at": mod_date,
                    "sequence_length": rec.get("sequence", {}).get("length", 0)
                }
                with open(out_dir / f"{accession}.json", "w", encoding="utf-8") as f:
                    json.dump(clean_rec, f, ensure_ascii=False, indent=2)

        return added, updated, skipped
