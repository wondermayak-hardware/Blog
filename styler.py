"""styler.py: turns a plain post body (h2/h3/p/ol/ul) into ThunderStudy Clay UI blocks for Blogger.
Output is a body-only fragment: NO <html>, <head>, <body>, <title> or <h1> (Blogger already has them)."""
import re, html, json

# ---- ThunderStudy Clay UI tokens (light/blue theme, from design.html) ----
INK, BODY, SURFACE, CANVAS = "#26324A", "#4F5D75", "#F8FAFF", "#EEF3FF"
PRIMARY, PRIMARY_ACTIVE = "#70A1FC", "#5D79B3"
TINT = {  # (soft fill, deep ink)
    "purple": ("#D9CCFF", "#3E2A9E"), "blue": ("#C7DDFF", "#1F4FA3"), "green": ("#C6F0D3", "#1B6B3A"),
    "red": ("#FFCFCF", "#A12626"), "yellow": ("#FFF0A8", "#7A5C00"), "pink": ("#FFCFE6", "#9E2A68"),
    "teal": ("#BDF0EA", "#0F6A63"), "lime": ("#E0F5A8", "#4D6B0A"), "cyan": ("#BDEBFF", "#0B6180"),
}
SH_SM = "4px 4px 10px rgba(110,140,200,.45),-4px -4px 10px rgba(255,255,255,.9)"
SH_MD = "6px 6px 14px rgba(110,140,200,.45),-6px -6px 14px rgba(255,255,255,.9)"
SH_LG = "8px 8px 20px rgba(110,140,200,.45),-8px -8px 20px rgba(255,255,255,.9)"
RESET = "font-family:inherit;letter-spacing:0;text-transform:none;text-shadow:none;"

# section type -> (tint, pill label)
TYPES = {
    "faq": ("teal", "FAQ"), "answers": ("green", "Answer key"), "questions": ("blue", "Practice"),
    "mistakes": ("red", "Avoid this"), "plan": ("purple", "Study plan"), "tips": ("yellow", "Smart tips"),
    "practice": ("green", "Practice"), "key": ("blue", "Key points"), "resources": ("cyan", "Resources"),
}
CYCLE = ["blue", "cyan", "lime", "pink"]

def plain(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()

def sanitize(t):
    t = t.strip()
    t = re.sub(r"^```(?:html)?\s*|\s*```$", "", t)
    t = re.sub(r"(?is)<h1[^>]*>.*?</h1>", "", t)
    t = re.sub(r"(?is)<!doctype.*?>|<(script|style|iframe|object|embed|head|title|noscript)\b.*?</\1>", "", t)
    t = re.sub(r"(?is)</?(html|body|meta|link)\b[^>]*>", "", t)
    t = re.sub(r"""(?is)\s(?:on\w+|style|class|id)\s*=\s*("[^"]*"|'[^']*')""", "", t)
    return t.strip()

_OPEN = re.compile(r"<(h2|h3|h4|p|ol|ul|table|blockquote|div)\b[^>]*>", re.I)

def nodes(t):
    """Top-level (tag, inner_html) nodes; stray text becomes a <p>."""
    out, i = [], 0
    while True:
        m = _OPEN.search(t, i)
        stray = t[i:m.start() if m else len(t)]
        if plain(stray):
            out.append(("p", stray.strip()))
        if not m:
            break
        tag, depth, end = m.group(1).lower(), 1, None
        for mm in re.finditer(rf"<(/?){tag}\b[^>]*>", t[m.end():], re.I):
            depth += -1 if mm.group(1) else 1
            if depth == 0:
                end = mm; break
        if end is None:
            out.append((tag, t[m.end():].strip())); break
        out.append((tag, t[m.end():m.end() + end.start()].strip()))
        i = m.end() + end.end()
    return [("h3" if a == "h4" else a, b) for a, b in out]

def pill(text, tint="blue", solid=False, on_white=False):
    if solid: bg, fg = PRIMARY_ACTIVE, "#ffffff"
    elif on_white: bg, fg = "rgba(255,255,255,.75)", TINT[tint][1]
    else: bg, fg = TINT[tint]
    return (f'<span style="{RESET}display:inline-block;background:{bg};color:{fg};padding:6px 14px;border-radius:999px;'
            f'font-size:12px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;line-height:1.4;margin:0 8px 8px 0;">'
            f'{html.escape(text)}</span>')

def inline(t, ink=INK, mb=12):
    """Give every p/h3/ul/ol/li an inline style (Blogger themes override plain tags)."""
    S = {
        "p": f"{RESET}margin:0 0 {mb}px;color:{ink};font-size:16px;line-height:1.75;",
        "h3": f"{RESET}margin:16px 0 6px;color:{ink};font-size:17px;line-height:1.4;font-weight:700;",
        "ul": f"{RESET}margin:0 0 {mb}px;padding-left:22px;color:{ink};font-size:16px;line-height:1.75;",
        "ol": f"{RESET}margin:0 0 {mb}px;padding-left:22px;color:{ink};font-size:16px;line-height:1.75;",
        "li": f"{RESET}margin:0 0 8px;color:{ink};",
    }
    def rep(m):
        tag, attrs = m.group(1).lower(), m.group(2)
        tm = re.search(r'\btype\s*=\s*"([^"]*)"', attrs)
        keep = f' type="{tm.group(1)}"' if tag == "ol" and tm else ""
        return f'<{tag}{keep} style="{S["h3" if tag == "h4" else tag]}">'
    t = re.sub(r"<(p|h3|h4|ul|ol|li)\b([^>]*)>", rep, t, flags=re.I)
    t = re.sub(r"</h4>", "</h3>", t, flags=re.I)
    t = re.sub(r"<table\b[^>]*>", '<div style="overflow-x:auto;margin:0 0 12px;"><table style="width:100%;border-collapse:collapse;">', t, flags=re.I)
    t = re.sub(r"</table>", "</table></div>", t, flags=re.I)
    t = re.sub(r"<th\b[^>]*>", f'<th style="padding:10px;text-align:left;background:rgba(255,255,255,.6);color:{ink};">', t, flags=re.I)
    t = re.sub(r"<td\b[^>]*>", f'<td style="padding:10px;border-top:1px solid rgba(38,50,74,.12);color:{ink};">', t, flags=re.I)
    return t

def h2(text, ink=INK):
    return f'<h2 style="{RESET}margin:0 0 12px;font-size:22px;line-height:1.3;font-weight:700;color:{ink};">{text}</h2>'

def head_card(label, tint, title):
    return (f'<div style="background:{SURFACE};color:{INK};border-radius:24px;padding:16px 20px 8px;margin:30px 0 14px;box-shadow:{SH_SM};">'
            f'{pill(label, tint)}{h2(title)}</div>')

def tint_block(label, tint, title, inner_html):
    bg, fg = TINT[tint]
    return (f'<div style="background:{bg};color:{fg};border-radius:24px;padding:22px 20px 12px;margin:26px 0;">'
            f'{pill(label, tint, on_white=True)}{h2(title, fg)}{inline(inner_html, fg)}</div>')

def strip_b(s):
    return re.sub(r"</?(b|strong)\b[^>]*>", "", s, flags=re.I).strip()

def answer_box(ans_html):
    ans = re.sub(r"^\s*(?:<b>)?\s*Answer\s*:?\s*(?:</b>)?\s*:?\s*", "", ans_html.strip(), flags=re.I)
    ans = strip_b(ans)
    bg, fg = TINT["green"]
    return (f'<div style="{RESET}background:{bg};color:{fg};border-radius:16px;padding:12px 16px;margin-top:12px;font-size:15px;line-height:1.6;">'
            f'<b>Answer:</b> {ans}</div>')

def qcard(num, q_html, options=None, ans_html=None):
    opts = ""
    for k, li in enumerate(options or []):
        opts += (f'<div style="{RESET}background:{CANVAS};color:{INK};border-radius:16px;padding:10px 14px;margin-top:8px;font-size:15px;line-height:1.5;">'
                 f'<b>({chr(97 + k)})</b> {strip_b(li)}</div>')
    return (f'<div style="background:{SURFACE};color:{INK};border-radius:24px;padding:20px 20px 18px;margin:16px 0;box-shadow:{SH_MD};">'
            f'{pill("Q" + str(num), "blue")}'
            f'<p style="{RESET}margin:4px 0 4px;font-size:17px;font-weight:700;color:{INK};line-height:1.55;">{strip_b(q_html)}</p>'
            f'{opts}{answer_box(ans_html) if ans_html else ""}</div>')

def list_items(inner):
    return re.findall(r"(?is)<li\b[^>]*>(.*?)</li>", inner)

_QP = re.compile(r"^\s*(<b>|<strong>)?\s*Q\s*(\d+)\s*[.):]\s*", re.I)

def is_questions(ns):
    for k, (t, i) in enumerate(ns):
        if t == "h3" and re.match(r"question\s*\d+", plain(i), re.I): return True
        if t == "p" and _QP.match(i) and k + 1 < len(ns) and ns[k + 1][0] in ("ol", "ul"): return True
    return False

def is_answers(title, ns):
    if re.search(r"answer|solution|explanation", title, re.I): return True
    ps = [i for t, i in ns if t == "p"]
    return bool(ps) and sum(1 for p in ps if _QP.match(p) and "answer" in p.lower()) >= max(2, len(ps) // 2)

def classify(title, ns):
    tl = title.lower()
    if re.search(r"\bfaqs?\b|frequently asked", tl): return "faq"
    if is_questions(ns): return "questions"
    if is_answers(title, ns): return "answers"
    if re.search(r"mistake|avoid|pitfall|wrong", tl): return "mistakes"
    if re.search(r"plan|schedule|roadmap|strategy|step|day|how to", tl): return "plan"
    if re.search(r"tip|trick|shortcut|revis|health|motivat|stay |remember", tl): return "tips"
    if re.search(r"practice|paper|mock|test|quiz", tl): return "practice"
    if re.search(r"syllabus|pattern|overview|understand|basic|key|important|note|fact|summary", tl): return "key"
    if re.search(r"resource|source|book|reference", tl): return "resources"
    return None

def render_questions(title, ns):
    out, i, n = [head_card("Practice", "blue", title)], 0, 0
    while i < len(ns):
        t, inner = ns[i]
        txt = plain(inner)
        if t == "h3" and re.match(r"question\s*\d+", txt, re.I) and i + 1 < len(ns) and ns[i + 1][0] == "p":
            n = int(re.search(r"\d+", txt).group()); body = ns[i + 1][1]
            parts = re.split(r"(?i)<br\s*/?>", body, maxsplit=1)
            if len(parts) == 2: q, a = parts
            else:
                m = re.split(r"(?i)\banswer\s*:", body, maxsplit=1); q, a = (m[0], m[1]) if len(m) == 2 else (body, None)
            out.append(qcard(n, q, None, a)); i += 2; continue
        m = _QP.match(inner) if t == "p" else None
        if m:
            n = int(m.group(2)); q = inner[m.end():]
            if m.group(1) and "</b>" in q.lower(): q = re.sub(r"(?i)</b>|</strong>", "", q, count=1)
            opts, ans, i = None, None, i + 1
            if i < len(ns) and ns[i][0] in ("ol", "ul"): opts = list_items(ns[i][1]); i += 1
            if i < len(ns) and ns[i][0] == "p" and re.match(r"\s*(<b>)?\s*answer", ns[i][1], re.I): ans = ns[i][1]; i += 1
            out.append(qcard(n, q, opts, ans)); continue
        if t != "h3" or not re.match(r"question\s*\d+", txt, re.I):
            out.append(f'<div style="background:{SURFACE};border-radius:20px;padding:14px 18px;margin:12px 0;box-shadow:{SH_SM};">{inline(f"<{t}>{inner}</{t}>")}</div>')
        i += 1
    return "\n".join(out)

def render_answers(title, ns):
    bg, fg = TINT["green"]; rows = ""
    for t, inner in ns:
        if t != "p": rows += inline(f"<{t}>{inner}</{t}>", fg); continue
        m = _QP.match(inner)
        label, rest = (f"Q{m.group(2)}", (m.group(1) or "") + inner[m.end():]) if m else ("", inner)
        rows += (f'<div style="{RESET}background:rgba(255,255,255,.72);color:{fg};border-radius:16px;padding:12px 16px;margin:0 0 10px;font-size:15px;line-height:1.65;">'
                 f'{pill(label, "green", on_white=False) if label else ""}<br>{rest}</div>')
    return (f'<div style="background:{bg};color:{fg};border-radius:24px;padding:22px 20px 12px;margin:26px 0;">'
            f'{pill("Answer key", "green", on_white=True)}{h2(title, fg)}{rows}</div>')

def faq_pairs(ns):
    pairs, q, a = [], None, []
    for t, i in ns:
        if t == "h3":
            if q and a: pairs.append((q, " ".join(a)))
            q, a = plain(i), []
        elif q and t in ("p", "ul", "ol"): a.append(plain(i))
    if q and a: pairs.append((q, " ".join(a)))
    return pairs

def render_faq(title, ns):
    out = [head_card("FAQ", "teal", title)]
    for q, a in faq_pairs(ns):
        out.append(f'<div style="background:{SURFACE};color:{INK};border-radius:20px;padding:16px 18px 6px;margin:12px 0;box-shadow:{SH_MD};">'
                   f'{pill("Question", "teal")}<p style="{RESET}margin:2px 0 0;font-size:16px;font-weight:700;color:{INK};line-height:1.55;">{html.escape(q)}</p>'
                   f'<p style="{RESET}margin:8px 0 10px;color:{BODY};font-size:16px;line-height:1.7;">{html.escape(a)}</p></div>')
    return "\n".join(out)

def quick_answer(first, rest_nodes):
    txt = re.sub(r"^\s*(?:<b>)?\s*quick\s*answer\s*:?\s*(?:</b>)?\s*:?\s*", "", first, flags=re.I).strip()
    sents = re.split(r"(?<=[.!?])\s+", txt)
    head, used = [], 0
    for s in sents:
        if head and used + len(s) > 300: break
        head.append(s); used += len(s) + 1
    qa, tail = " ".join(head), " ".join(sents[len(head):])
    extra = (f'<p style="{RESET}margin:12px 0 0;color:{BODY};font-size:16px;line-height:1.75;">{tail}</p>' if tail else "")
    extra += inline("".join(f"<{t}>{i}</{t}>" for t, i in rest_nodes), BODY, 10) if rest_nodes else ""
    return (f'<div style="background:{SURFACE};color:{INK};border-radius:28px;padding:22px 22px 18px;margin:0 0 8px;box-shadow:{SH_LG};">'
            f'{pill("Quick answer", solid=True)}'
            f'<p style="{RESET}margin:2px 0 0;font-size:18px;font-weight:600;line-height:1.65;color:{INK};">{qa}</p>{extra}</div>')

def btn(label, url, kind):
    if kind == "primary": st = f"background:{PRIMARY};color:#ffffff;box-shadow:{SH_SM};"
    elif kind == "surface": st = f"background:{SURFACE};color:{INK};box-shadow:{SH_SM};"
    else: st = f"background:{TINT['blue'][0]};color:{TINT['blue'][1]};"
    return (f'<a href="{url}" target="_blank" rel="noopener" style="{RESET}display:inline-block;{st}padding:13px 22px;border-radius:999px;'
            f'font-size:15px;font-weight:700;text-decoration:none;margin:8px 10px 0 0;line-height:1.2;">{html.escape(label)}</a>')

def cta(test_url, study_url, blog_url):
    short = lambda u: re.sub(r"^https?://", "", u).rstrip("/")
    return (f'<div style="background:{SURFACE};color:{INK};border-radius:28px;padding:24px 22px 20px;margin:32px 0 8px;box-shadow:{SH_LG};">'
            f'{pill("Free practice", solid=True)}'
            f'<p style="{RESET}margin:2px 0 6px;font-size:20px;font-weight:700;color:{INK};line-height:1.4;">Practice more for free on ThunderStudy</p>'
            f'<p style="{RESET}margin:0 0 6px;font-size:16px;color:{BODY};line-height:1.7;">Take free CUET mock tests and previous year question practice. No signup needed.</p>'
            f'{btn("Free Mock Tests", test_url, "primary")}{btn("ThunderStudy", study_url, "surface")}{btn("More free posts", blog_url, "soft")}'
            f'<p style="{RESET}margin:16px 0 0;font-size:13px;color:{BODY};line-height:1.6;">{short(test_url)} &middot; {short(study_url)} &middot; {short(blog_url)}</p></div>')

def self_check(out):
    bad = re.search(r"(?i)<!doctype|<html|<head|<body|<title|<h1|<meta|<link", out)
    if bad: raise ValueError(f"fragment must not contain {bad.group()}")

def style_post(body, labels=(), test_url="https://thundertest.indevs.in", study_url="https://thunderstudy.indevs.in",
               blog_url="https://blog.thunderstudy.indevs.in", schema=True):
    ns = nodes(sanitize(body))
    first_h2 = next((k for k, (t, _) in enumerate(ns) if t == "h2"), len(ns))
    pre, rest = ns[:first_h2], ns[first_h2:]
    parts = []
    if labels:
        tints = ["blue", "green", "purple", "yellow", "pink", "cyan"]
        parts.append(f'<div style="margin:0 0 14px;">{"".join(pill(l, tints[k % 6]) for k, l in enumerate(labels))}</div>')
    if pre:
        k = next((j for j, (t, _) in enumerate(pre) if t == "p"), None)
        if k is not None:
            parts.append(quick_answer(pre[k][1], pre[:k] + pre[k + 1:]))
        else:
            parts.append(f'<div style="background:{SURFACE};border-radius:24px;padding:18px 20px 8px;box-shadow:{SH_MD};">{inline("".join(f"<{t}>{i}</{t}>" for t, i in pre))}</div>')
    sections, cur = [], None
    for t, i in rest:
        if t == "h2": cur = [plain(i), []]; sections.append(cur)
        elif cur: cur[1].append((t, i))
    cyc, faq = 0, []
    for title, sn in sections:
        kind = classify(title, sn)
        if kind == "faq": parts.append(render_faq(title, sn)); faq = faq_pairs(sn)
        elif kind == "questions": parts.append(render_questions(title, sn))
        elif kind == "answers": parts.append(render_answers(title, sn))
        else:
            if kind is None: tint, label = CYCLE[cyc % 4], "Guide"; cyc += 1
            else: tint, label = TYPES[kind]
            parts.append(tint_block(label, tint, html.escape(title), "".join(f"<{t}>{i}</{t}>" for t, i in sn)))
    parts.append(cta(test_url, study_url, blog_url))
    if schema and faq:
        data = {"@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
        parts.append('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    out = f'<div style="{RESET}max-width:100%;overflow-wrap:break-word;">\n' + "\n".join(parts) + "\n</div>"
    self_check(out)
    return out
