#!/usr/bin/env python3
"""批量在含 CDN 图片的 .mdx 文件中注入 <LazyImages />。

用法：
    python tools/ci/inject_lazy_images.py            # 干跑（dry-run）
    python tools/ci/inject_lazy_images.py --write    # 实际写入

幂等：已有 LazyImages import 或挂载的文件会被跳过。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

IMPORT_LINE = 'import { LazyImages } from "/snippets/lazy-images.jsx";'
MOUNT_LINE = "<LazyImages />"

# 匹配 frontmatter（--- 起 --- 止）
FRONTMATTER_RE = re.compile(r"^(---\n[\s\S]*?\n---\n)", re.MULTILINE)
# 匹配已有的 import 行
IMPORT_RE = re.compile(r"^import\s+.*from\s+[\"']/snippets/", re.MULTILINE)


def find_target_files() -> list[Path]:
    """找出所有引用了 CDN 图片的 mdx。"""
    targets = []
    for path in ROOT.rglob("*.mdx"):
        if "node_modules" in path.parts or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "cdn.newenergycoder.club" in text:
            targets.append(path)
    return targets


def inject(path: Path) -> tuple[bool, str]:
    """注入 import 与挂载点。返回 (是否修改, 原因)。"""
    text = path.read_text(encoding="utf-8")
    if IMPORT_LINE in text and MOUNT_LINE in text:
        return False, "already injected"

    # 拆分 frontmatter 与正文
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return False, "no frontmatter"
    fm = fm_match.group(1)
    body = text[len(fm):].lstrip("\n")

    # 在 body 中找到现有 import 块（若存在），把新 import 追加到其后；
    # 否则把 import 放最前面。
    lines = body.splitlines(keepends=True)
    new_lines: list[str] = []
    import_inserted = IMPORT_LINE in text
    mount_inserted = MOUNT_LINE in text
    inserted_import_pos = False

    for line in lines:
        new_lines.append(line)
        if not import_inserted and not inserted_import_pos and IMPORT_RE.match(line):
            # 在已有 snippet import 行后面追加
            new_lines.append(IMPORT_LINE + "\n")
            inserted_import_pos = True
            import_inserted = True

    if not import_inserted:
        # 没有任何已有 snippet import，直接放在最前
        new_lines.insert(0, IMPORT_LINE + "\n\n")

    # 在 import 块之后插入挂载
    if not mount_inserted:
        # 找到第一行非空、非 import 的行，在它之前插入
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("import "):
                continue
            # 在第一个非 import 内容之前插入
            new_lines.insert(i, MOUNT_LINE + "\n\n")
            mount_inserted = True
            break

    new_text = fm + "".join(new_lines)
    if new_text == text:
        return False, "no change"
    path.write_text(new_text, encoding="utf-8")
    return True, "injected"


def main() -> int:
    write = "--write" in sys.argv
    targets = find_target_files()
    print(f"目标文件数: {len(targets)}")
    changed = 0
    skipped = 0
    for path in sorted(targets):
        rel = path.relative_to(ROOT).as_posix()
        if write:
            ok, reason = inject(path)
        else:
            # dry-run：只检查是否会修改
            text = path.read_text(encoding="utf-8")
            ok = not (IMPORT_LINE in text and MOUNT_LINE in text)
            reason = "would inject" if ok else "already injected"
        status = "✏️ " if ok else "⏭️ "
        print(f"  {status} {rel} — {reason}")
        if ok:
            changed += 1
        else:
            skipped += 1
    print(f"\n将修改: {changed}  已注入跳过: {skipped}")
    if not write:
        print("（dry-run；加 --write 实际写入）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
