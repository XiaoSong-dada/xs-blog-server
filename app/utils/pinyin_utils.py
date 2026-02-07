import re
from pypinyin import lazy_pinyin, Style


def filename_to_slug(stem: str, split_english_letters: bool = False) -> str:
    """
    把文件名（无后缀）转换为 slug：
    - 中文 -> 拼音
    - 其他符号作为分隔
    - 结果用 '-' 连接
    - 可选：是否把英文单词拆成字母（list -> l-i-s-t）
    """
    stem = stem.strip()

    # 先把常见分隔符统一成空格，方便分词
    # 允许中文、字母、数字，其余都当分隔符
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", " ", stem).strip()
    if not normalized:
        return "untitled"

    parts: list[str] = []
    for token in normalized.split():
        # token 里有中文：转拼音
        if re.search(r"[\u4e00-\u9fff]", token):
            parts.extend(lazy_pinyin(token, style=Style.NORMAL))
        else:
            # 纯英文/数字：保留
            if split_english_letters and token.isalpha():
                parts.extend(list(token.lower()))
            else:
                parts.append(token.lower())

    # 清理多余 '-'，保证 slug 干净
    slug = "-".join(p for p in parts if p)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "untitled"
