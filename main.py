
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
対訳コーパス抽出スクリプト
Shift-JIS形式の日英対訳ファイルからTSV形式で対訳ペアを抽出
"""

import re
import sys
from pathlib import Path

def is_japanese(text):
    """日本語を含むかどうかを判定"""
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))

def clean_text(text):
    """テキストのクリーニング"""
    # &#数字4桁を削除
    text = re.sub(r'&#\d{4}', '', text)
    # 前後の空白を削除
    text = text.strip()
    return text

def should_skip_line(line):
    """スキップすべき行かどうか判定"""
    line = line.strip()
    
    # 空行
    if not line:
        return True
    
    # 訳注
    if line.startswith('（訳注：') or line.startswith('(訳注:'):
        return True
    
    # 脚注マーカー（注A、注B、数字のみなど）
    if re.match(r'^注[A-Z][:：]', line):
        return True
    if re.match(r'^\d+$', line.strip()):
        return True
    
    # Version情報
    if 'Version' in line and ('Page' in line or 'Progress' in line):
        return True
    
    return False

def extract_pairs_from_file(filepath):
    """1ファイルから対訳ペアを抽出"""
    try:
        with open(filepath, 'r', encoding='shift-jis', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return []
    
    # 空行で分割してブロックを作成
    blocks = re.split(r'\r?\n\r?\n+', content)
    
    pairs = []
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        # スキップすべき行を除外
        lines = [line for line in lines if not should_skip_line(line)]
        
        if not lines:
            continue
        
        # 日本語行と英語行を分離
        ja_lines = []
        en_lines = []
        
        for line in lines:
            cleaned = clean_text(line)
            if not cleaned:
                continue
                
            if is_japanese(cleaned):
                ja_lines.append(cleaned)
            else:
                en_lines.append(cleaned)
        
        # 日英ペアを作成
        # 基本的に同じ数であることを期待するが、不一致の場合は短い方に合わせる
        min_len = min(len(ja_lines), len(en_lines))
        
        for i in range(min_len):
            ja = ja_lines[i]
            en = en_lines[i]
            
            # 極端に短いペアや明らかに対訳でないものをフィルタ
            if len(ja) < 3 or len(en) < 3:
                continue
            
            # セミコロンで終わる英語の断片は次の行と結合されるべきだが
            # ここでは単純に保持（必要に応じて後処理）
            
            pairs.append((ja, en))
    
    return pairs

def process_directory(input_dir, output_file):
    """ディレクトリ内の全ファイルを処理"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist", file=sys.stderr)
        return
    
    all_pairs = []
    file_count = 0
    
    # すべてのテキストファイルを処理
    for filepath in sorted(input_path.glob('*.alm')):
        print(f"Processing: {filepath.name}", file=sys.stderr)
        pairs = extract_pairs_from_file(filepath)
        all_pairs.extend(pairs)
        file_count += 1
        print(f"  Extracted {len(pairs)} pairs", file=sys.stderr)
    
    # TSV出力
    with open(output_file, 'w', encoding='utf-8') as f:
        for ja, en in all_pairs:
            f.write(f"{ja}\t{en}\n")
    
    print(f"\nTotal: {file_count} files, {len(all_pairs)} pairs", file=sys.stderr)
    print(f"Output: {output_file}", file=sys.stderr)

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_corpus.py <input_dir> <output_tsv>")
        print("Example: python extract_corpus.py ./texts corpus.tsv")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    process_directory(input_dir, output_file)

if __name__ == '__main__':
    main()
