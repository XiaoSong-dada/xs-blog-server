from pathlib import Path
from typing import Dict, List
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse
from pathlib import PurePosixPath
from typing import Optional
import zipfile


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


def _to_filename(url: str) -> str | None:
    """
    把一个图片 url/路径变成文件名：
    - http(s)://.../a.png -> a.png
    - /static/xx/a.png -> a.png
    - 2026/02/07/a.png -> a.png
    - data:... -> None（不处理）
    """
    s = url.strip()
    if not s:
        return None
    if s.startswith("data:"):
        return None

    p = urlparse(s)
    if p.scheme in ("http", "https"):
        path = p.path  # 只拿 path，忽略 query
    else:
        # 相对路径 / 绝对路径 / static 路径都走这里
        path = s

    name = PurePosixPath(path).name
    return name or None


def replace_md_img_urls_to_filenames(content: str) -> str:
    """把 content 中图片链接替换成仅文件名（保留原 Markdown/HTML 结构）。"""
    if not content:
        return content

    # 1) Markdown 图片替换
    def md_replacer(m: re.Match) -> str:
        raw_url = m.group("url").strip()
        wrapped = raw_url.startswith("<") and raw_url.endswith(">")
        url = raw_url[1:-1].strip() if wrapped else raw_url

        new_name = _to_filename(url)
        if not new_name:
            return m.group(0)

        replaced = f"<{new_name}>" if wrapped else new_name
        return m.group(0).replace(raw_url, replaced)

    content = _MD_IMAGE_RE.sub(md_replacer, content)

    # 2) HTML img 替换
    def html_replacer(m: re.Match) -> str:
        url = m.group("url")
        new_name = _to_filename(url)
        if not new_name:
            return m.group(0)
        return f"{m.group(1)}{m.group(2)}{new_name}{m.group(4)}"

    content = _HTML_IMG_RE.sub(html_replacer, content)

    return content


def extract_img_urls_from_md(content_md: str) -> List[str]:
    """
    从 Markdown 内容中提取图片链接（Markdown + HTML img）。
    返回：按出现顺序去重后的 url 列表。
    """
    if not content_md:
        return []

    urls: List[str] = []

    # 1) Markdown 图片
    for m in _MD_IMAGE_RE.finditer(content_md):
        raw_url = m.group("url").strip()
        # 支持 ![](<path with spaces>)
        if raw_url.startswith("<") and raw_url.endswith(">"):
            raw_url = raw_url[1:-1].strip()
        if raw_url:
            urls.append(raw_url)

    # 2) HTML img
    for m in _HTML_IMG_RE.finditer(content_md):
        url = m.group("url").strip()
        if url:
            urls.append(url)

    # 去重（保序）
    seen = set()
    uniq: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)

    return uniq


def _filename_from_url(url: str) -> str:
    p = urlparse(url)
    path = p.path if p.scheme else url
    return PurePosixPath(path).name


def _static_relpath_from_url(
    url: str, static_prefix: str = "/static/"
) -> Optional[str]:
    """
    把 /static/2026/02/a.png 或 http://host/static/2026/02/a.png
    转换成相对路径 2026/02/a.png
    """
    p = urlparse(url)
    path = p.path if p.scheme else url
    if not path.startswith(static_prefix):
        return None
    return path[len(static_prefix) :].lstrip("/")


async def fetch_or_copy_image_to_dir(
    img_url: str,
    export_dir: Path,
    file_storage_path: str,
    static_prefix: str = "/static/",
    allow_remote_download: bool = False,
) -> Optional[Path]:
    """
    将 img_url 对应的图片保存到 export_dir 下（文件名用 url 的 basename）。
    - 如果是本地 static url：从磁盘复制
    - 如果是远程 url：可选下载（allow_remote_download=True）

    返回保存后的图片路径（export_dir/filename），失败返回 None
    """
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = _filename_from_url(img_url)
    if not filename:
        return None

    dst = export_dir / filename

    # 1) 本地 static：copy
    rel = _static_relpath_from_url(img_url, static_prefix=static_prefix)
    if rel:
        src = Path(file_storage_path) / rel
        if src.exists() and src.is_file():
            shutil.copy2(src, dst)
            return dst
        return None

    # 2) 远程：下载（可选）
    p = urlparse(img_url)
    if p.scheme in ("http", "https") and allow_remote_download:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(img_url)
                r.raise_for_status()
                dst.write_bytes(r.content)
            return dst
        except Exception:
            return None

    return None


_WINDOWS_ILLEGAL = r'<>:"/\|?*'
_ILLEGAL_RE = re.compile(f"[{re.escape(_WINDOWS_ILLEGAL)}]")


def sanitize_filename(name: str, max_len: int = 80) -> str:
    name = name.strip().replace("\n", " ")
    name = _ILLEGAL_RE.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if len(name) > max_len:
        name = name[:max_len].rstrip(" .")
    return name or "untitled"


def unique_name(base: str, used: set[str], suffix: str) -> str:
    """
    base 不含后缀，suffix 含点（.md）
    """
    name = f"{base}{suffix}"
    if name not in used:
        used.add(name)
        return name
    i = 1
    while True:
        name = f"{base}_{i}{suffix}"
        if name not in used:
            used.add(name)
            return name
        i += 1


def write_articles_to_dir(articles: list, export_dir: Path) -> None:
    used = set()
    for a in articles:
        title = sanitize_filename(a.title)
        md_name = unique_name(title, used, ".md")
        (export_dir / md_name).write_text(a.content_md or "", encoding="utf-8")


def make_zip_from_dir(export_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in export_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p.relative_to(export_dir)))
