"""Tiny CSS toolkit: parse, purge unused classes, drop unused keyframes, minify."""
import re

def parse(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i, n, items = 0, len(css), []
    while i < n:
        j = i
        while j < n and css[j] not in "{;":
            if css[j] in "\"'":
                j = css.index(css[j], j + 1)
            j += 1
        if j >= n: break
        head = css[i:j].strip()
        if css[j] == ";":
            if head: items.append((head, None))
            i = j + 1; continue
        depth, k = 1, j + 1
        while k < n and depth:
            c = css[k]
            if c in "\"'": k = css.index(c, k + 1)
            elif c == "{": depth += 1
            elif c == "}": depth -= 1
            k += 1
        items.append((head, css[j + 1:k - 1])); i = k
    return items

def split_sel(head):
    out, depth, cur = [], 0, ""
    for ch in head:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if ch == "," and depth == 0: out.append(cur.strip()); cur = ""
        else: cur += ch
    return out + [cur.strip()]

_CLS = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")
def keep_sel(sel, used):
    s = re.sub(r":(not|where)\([^)]*\)", "", sel)
    s = re.sub(r"\[[^\]]*\]", "", s)
    return all(c in used for c in _CLS.findall(s))

def purge(items, used):
    out = []
    for head, body in items:
        if body is None: out.append(head + ";"); continue
        h = head.lower()
        if h.startswith(("@media", "@supports", "@layer", "@container")):
            inner = purge(parse(body), used)
            if inner: out.append(head + "{" + inner + "}")
        elif h.startswith("@"):
            out.append(head + "{" + body + "}")
        else:
            keep = [s for s in split_sel(head) if keep_sel(s, used)]
            if keep: out.append(",".join(keep) + "{" + body + "}")
    return "".join(out)

def drop_unused_keyframes(css):
    names = re.findall(r"@(?:-webkit-)?keyframes\s+([\w-]+)", css)
    for nm in set(names):
        uses = len(re.findall(r"(?<![\w-])" + re.escape(nm) + r"(?![\w-])", css))
        defs = len(re.findall(r"@(?:-webkit-)?keyframes\s+" + re.escape(nm) + r"(?![\w-])", css))
        if uses <= defs:
            for it in parse(css):
                pass
            css = re.sub(r"@(?:-webkit-)?keyframes\s+" + re.escape(nm) + r"\s*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    return css

def minify(css):
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    return css.replace(";}", "}").strip()

def build(full_css, extra_css, used):
    css = purge(parse(full_css), used) + purge(parse(extra_css), used)
    return minify(drop_unused_keyframes(css))
