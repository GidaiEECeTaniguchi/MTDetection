import json
from pathlib import Path

# ===== 設定 =====
INPUT_DIR = Path("./outenjpjson")       # 作品ごとの jsonl が入っているフォルダ
OUTPUT_FILE = Path("./sepalated_dataset.jsonl")

SEP_EN = "%%%%%%%%THISWORKENDSHERE%%%%%%%%"
SEP_JA = "%%%%%%%%この作品ここまで%%%%%%%%"

# ===== 実装 =====
with OUTPUT_FILE.open("w", encoding="utf-8") as out_f:
    for jsonl_file in sorted(INPUT_DIR.glob("*.json")):
        print(f"processing: {jsonl_file.name}")

        # 作品の中身を書き出す
        with jsonl_file.open("r", encoding="utf-8") as in_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                out_f.write(line + "\n")

        # この作品の終端に区切りを挿入
        sep_obj = {"en": SEP_EN, "ja": SEP_JA}
        out_f.write(json.dumps(sep_obj, ensure_ascii=False) + "\n")

print(f"\nmerged -> {OUTPUT_FILE}")
