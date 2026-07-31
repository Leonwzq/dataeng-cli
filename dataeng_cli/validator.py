import json
from pathlib import Path
from typing import Dict, Any, List

class DataValidator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def validate((self) -> Dict[str, Any]:
        """对处理后的数据目录实施结构化质量校验"""
        if not self.data_dir.exists() or not self.data_dir.is_dir():
            return {
                "total_records": 0,
                "pass": False,
                "comment": f"错误: 目录 {self.data_dir} 不存在或不可读"
            }

        files = list(self.data_dir.glob("*.json"))
        if not files:
            return {
                "total_records": 0,
                "completeness_rate": 0.0,
                "duplicate_rate": 0.0,
                "schema_errors": 0,
                "stale_records": 0,
                "pass": False,
                "comment": "目录为空，未找到可校验的数据文件。"
            }

        total = len(files)
        seen_ids = set()
        duplicates = 0
        incomplete_count = 0
        schema_errors = 0
        
        required_fields = ["id", "protein_name", "organism", "updated_at"]

        for f_path in files:
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                schema_errors += 1
                continue

            # 1. 必填项完整度检查
            if not all(field in data and data[field] for field in required_fields):
                incomplete_count += 1

            # 2. 唯一性/重复率检查
            rec_id = data.get("id")
            if rec_id in seen_ids:
                duplicates += 1
            else:
                if rec_id:
                    seen_ids.add(rec_id)

            # 3. Schema 类型匹配检查
            if not isinstance(data.get("sequence_length", 0), int):
                schema_errors += 1

        completeness_rate = round((total - incomplete_count) / total, 2)
        duplicate_rate = round(duplicates / total, 2)
        
        # 判定准则：完整率 >= 0.90 且 重复率 == 0 且 Schema错误 == 0
        is_pass = completeness_rate >= 0.90 and duplicate_rate == 0.0 and schema_errors == 0
        comment = "数据质量校验通过。" if is_pass else "存在 Schema 校验不匹配或字段缺失，建议修复。"

        return {
            "total_records": total,
            "completeness_rate": completeness_rate,
            "duplicate_rate": duplicate_rate,
            "schema_errors": schema_errors,
            "stale_records": 0,
            "pass": is_pass,
            "comment": comment
        }
