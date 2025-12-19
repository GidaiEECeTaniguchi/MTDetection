#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
対訳コーパス抽出スクリプト
UTF-8形式の日英対訳ファイルからTSV形式で対訳ペアを抽出
各入力ファイルを個別のTSVファイルとして出力
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
    
    # 装飾線（3文字以上の同じ記号の繰り返し）
    if re.match(r'^[-=_*]{3,}$', line):
        return True
    
    # URL行（<>で囲まれた場合も含む）
    if line.startswith('http://') or line.startswith('https://') or line.startswith('<http'):
        return True
    
    # 感嘆符や記号のみの行
    if re.match(r'^[!！]+$', line):
        return True
    
    # 訳注
    if line.startswith('（訳注：') or line.startswith('(訳注:') or line.startswith('訳注：'):
        return True
    
    # 脚注マーカー（注、注1、注A、数字のみなど）
    if re.match(r'^注[:：]?\s*$', line):  # 「注：」だけの行
        return True
    if re.match(r'^注\s*\d+[:：]', line):  # 「注 1：」形式
        return True
    if re.match(r'^注[A-Z][:：]', line):  # 「注A:」形式
        return True
    if re.match(r'^\d+\.?\s*$', line):  # 数字のみの行
        return True
    
    # Version情報やメタデータ
    if 'Version' in line and ('Page' in line or 'Progress' in line):
        return True
    
    # 短すぎる行（2文字以下）
    if len(line) <= 2:
        return True
    
    return False

def extract_pairs_from_block(lines):
    """1ブロックから対訳ペアを抽出"""
    # スキップすべき行を除外
    lines = [line for line in lines if not should_skip_line(line)]
    
    if not lines:
        return []
    
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
    
    # ペアを作成
    pairs = []
    
    # ケース1: 日英が同数 → 順番に対応
    if len(ja_lines) == len(en_lines):
        for ja, en in zip(ja_lines, en_lines):
            if len(ja) >= 3 and len(en) >= 3:
                pairs.append((ja, en))
    
    # ケース2: 英語が複数行に分割されている可能性
    # 日本語1行に対して英語が複数行（セミコロン区切りなど）
    elif len(ja_lines) == 1 and len(en_lines) > 1:
        ja = ja_lines[0]
        # 英語を結合
        en = ' '.join(en_lines)
        # セミコロンの後のスペース調整
        en = re.sub(r';\s*', '; ', en)
        if len(ja) >= 3 and len(en) >= 3:
            pairs.append((ja, en))
    
    # ケース3: 数が合わない場合は短い方に合わせる
    elif len(ja_lines) > 0 and len(en_lines) > 0:
        min_len = min(len(ja_lines), len(en_lines))
        for i in range(min_len):
            ja = ja_lines[i]
            en = en_lines[i]
            if len(ja) >= 3 and len(en) >= 3:
                pairs.append((ja, en))
    
    return pairs

def extract_pairs_from_file(filepath):
    """1ファイルから対訳ペアを抽出"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return []
    
    # 改行コードを統一
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 脚注セクションを削除（「注：」や空行+「注 数字」で始まる部分以降）
    # パターン1: 「注：」で始まる行以降を削除
    notes_pattern1 = r'\n\n注[:：]\s*\n.*'
    content = re.sub(notes_pattern1, '', content, flags=re.DOTALL)
    
    # パターン2: 「Notes:」で始まる行以降を削除
    notes_pattern2 = r'\n\nNotes?[:：]?\s*\n.*'
    content = re.sub(notes_pattern2, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # 空行で分割してブロックを作成
    blocks = re.split(r'\n\n+', content)
    
    pairs = []
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        block_pairs = extract_pairs_from_block(lines)
        pairs.extend(block_pairs)
    
    return pairs

def write_tsv(pairs, output_path):
    """対訳ペアをTSVファイルに書き込み"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for ja, en in pairs:
            # タブや改行が含まれている場合はスペースに置換
            ja = ja.replace('\t', ' ').replace('\n', ' ')
            en = en.replace('\t', ' ').replace('\n', ' ')
            f.write(f"{ja}\t{en}\n")

def process_directory(input_dir, output_dir):
    """ディレクトリ内の全ファイルを処理"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory {input_dir} does not exist", file=sys.stderr)
        return
    
    # 出力ディレクトリを作成
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_count = 0
    total_pairs = 0
    error_files = []
    
    # すべてのテキストファイルを処理
    for input_file in sorted(input_path.glob('*.alm')):
        print(f"Processing: {input_file.name}", file=sys.stderr)
        
        # 対訳ペアを抽出
        pairs = extract_pairs_from_file(input_file)
        
        if not pairs:
            print(f"  WARNING: No pairs extracted", file=sys.stderr)
            error_files.append(input_file.name)
        else:
            # 出力ファイル名（.txt → .tsv）
            output_file = output_path / input_file.with_suffix('.tsv').name
            
            # TSV出力
            write_tsv(pairs, output_file)
            
            print(f"  Extracted {len(pairs)} pairs → {output_file.name}", file=sys.stderr)
            total_pairs += len(pairs)
        
        file_count += 1
    
    # サマリー表示
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Total files processed: {file_count}", file=sys.stderr)
    print(f"Files with no pairs: {len(error_files)}", file=sys.stderr)
    if error_files:
        print(f"  Files: {', '.join(error_files[:5])}", file=sys.stderr)
        if len(error_files) > 5:
            print(f"  ... and {len(error_files) - 5} more", file=sys.stderr)
    print(f"Total pairs extracted: {total_pairs}", file=sys.stderr)
    print(f"Output directory: {output_dir}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_corpus.py <input_dir> <output_dir>")
        print("Example: python extract_corpus.py ./input ./output")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    process_directory(input_dir, output_dir)

if __name__ == '__main__':
    main()