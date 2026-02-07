from pathlib import Path
from typing import Dict, List
import re


def scan_temp_all_files(temp_dir: str) -> list[Path]:
    base = Path(temp_dir)
    return [p for p in base.rglob("*") if p.is_file()]


def scan_md_files(temp_dir: str) -> list[Path]:
    base = Path(temp_dir)
    return [p for p in base.rglob("*.md") if p.is_file()]


IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def scan_md_and_images(temp_dir: str):
    base = Path(temp_dir)

    md_files: list[Path] = []
    images: dict[str, Path] = {}  # key 用相对路径字符串，方便后续按 md 引用查找

    for p in base.rglob("*"):
        if not p.is_file():
            continue

        rel = p.relative_to(base).as_posix()  # 例如: c语言/数组.md
        suffix = p.suffix.lower()

        if suffix == ".md":
            md_files.append(p)
        elif suffix in IMG_EXTS:
            images[rel] = p

    return md_files, images


def scan_images(temp_dir: str):
    base = Path(temp_dir)

    images: dict[str, Path] = {}  # key 用相对路径字符串，方便后续按 md 引用查找
    for p in base.rglob("*"):
        if not p.is_file():
            continue

        rel = p.relative_to(base).as_posix()  # 例如: c语言/数组.md
        suffix = p.suffix.lower()

        if suffix in IMG_EXTS:
            images[rel] = p

    return images


_MD_IMAGE_RE = re.compile(
    r'!\[[^\]]*?\]\(\s*(?P<url><[^>]+>|[^)\s]+)(?:\s+["\'][^"\']*["\'])?\s*\)',
    flags=re.IGNORECASE,
)
_HTML_IMG_RE = re.compile(
    r'<img\b[^>]*\bsrc\s*=\s*(?P<q>["\'])(?P<url>.*?)(?P=q)[^>]*>',
    flags=re.IGNORECASE | re.DOTALL,
)


def read_md_images_map(
    root_dir: str | Path, encoding: str = "utf-8"
) -> Dict[str, List[str]]:
    """
    递归读取 root_dir 下所有 .md 文件，提取图片链接。
    仅返回“内容中包含图片”的 md 文件：{ md_path: [img_url, ...] }

    - 支持 Markdown 图片语法：![alt](url "title")
    - 支持 HTML 图片语法：<img src="...">

    参数：
      root_dir: 要扫描的目录
      encoding: 读取文件的编码，默认 utf-8

    返回：
      dict[str, list[str]]
    """
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    result: Dict[str, List[str]] = {}

    for md_path in root.rglob("*.md"):
        try:
            text = md_path.read_text(encoding=encoding, errors="replace")
        except OSError:
            # 读不了就跳过（你也可以改成 raise）
            continue

        urls: List[str] = []

        # 1) Markdown 图片
        for m in _MD_IMAGE_RE.finditer(text):
            url = m.group("url").strip()
            # 处理 Markdown 的 <...> 包裹形式：![](<path with spaces>)
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1].strip()
            if url:
                urls.append(url)

        # 2) HTML 图片
        for m in _HTML_IMG_RE.finditer(text):
            url = m.group("url").strip()
            if url:
                urls.append(url)

        # 去重（保序）
        if urls:
            seen = set()
            uniq = []
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    uniq.append(u)
            result[str(md_path)] = uniq

    return result


def replace_img_url(
    file: Path, url_mapping: Dict[str, str], encoding: str = "utf-8"
) -> bool:
    """
    将 md 文件中出现的旧图片 url 替换为新 url

    参数：
        file: Path 对象（md 文件）
        url_mapping: {old_url: new_url}
        encoding: 文件编码

    返回：
        bool: 是否发生了替换
    """
    if not file.exists() or not file.is_file():
        raise FileNotFoundError(f"File not found: {file}")

    text = file.read_text(encoding=encoding, errors="replace")
    original = text
    changed = False

    # -------- 1. Markdown 图片替换 --------
    def md_replacer(match: re.Match) -> str:
        nonlocal changed

        raw_url = match.group("url").strip()
        wrapped = raw_url.startswith("<") and raw_url.endswith(">")

        url = raw_url[1:-1].strip() if wrapped else raw_url

        if url in url_mapping:
            new_url = url_mapping[url]
            changed = True
            replaced = f"<{new_url}>" if wrapped else new_url
            return match.group(0).replace(raw_url, replaced)

        return match.group(0)

    text = _MD_IMAGE_RE.sub(md_replacer, text)

    # -------- 2. HTML 图片替换 --------
    def html_replacer(match: re.Match) -> str:
        nonlocal changed

        url = match.group("url")
        if url in url_mapping:
            changed = True
            return f"{match.group(1)}{match.group(2)}{url_mapping[url]}{match.group(4)}"

        return match.group(0)

    text = _HTML_IMG_RE.sub(html_replacer, text)

    # -------- 3. 写回文件 --------
    if changed and text != original:
        file.write_text(text, encoding=encoding)

    return changed
