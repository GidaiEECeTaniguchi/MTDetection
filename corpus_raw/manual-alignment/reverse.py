import os
import json

src_dir = "./outenjp"
dst_dir = "./outenjpjson"
os.makedirs(dst_dir, exist_ok=True)
for filename in os.listdir(src_dir):
    if not filename.endswith(".tsv"):
        continue
    src_path = os.path.join(src_dir, filename)
    dst_filename = filename.replace(".tsv", ".json")
    dst_path = os.path.join(dst_dir, dst_filename)
    with open(src_path, "r", encoding="utf-8") as fin, \
         open(dst_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.rstrip("\n")
            parts = line.split("\t", 2)
            if len(parts) >= 2:
                obj = {"en": parts[0], "ja": parts[1]}
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
