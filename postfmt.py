"""Turns a plain post body (h2/h3/p/ol/ul, as written by the bot or by hand) into Clay UI blocks that use CSS classes
(so dark mode works). Reuses the parser from styler.py."""
import re, html
from styler import nodes, sanitize, plain, is_questions, is_answers, list_items, strip_b, _QP, faq_pairs

TYPES = {"faq": ("teal", "FAQ"), "answers": ("green", "Answer key"), "questions": ("blue", "Practice"),
         "mistakes": ("red", "Avoid this"), "plan": ("purple", "Study plan"), "tips": ("yellow", "Smart tips"),
         "practice": ("green", "Practice"), "key": ("blue", "Key points"), "resources": ("cyan", "Resources")}
CYCLE = ["blue", "cyan", "lime", "pink"]

def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60] or "section"

def classify(title, ns):
    tl = title.lower()
    if re.search(r"\bfaqs?\b|frequently asked", tl): return "faq"
    if is_questions(ns): return "questions"
    if is_answers(title, ns): return "answers"
    if re.search(r"mistake|avoid|pitfall|wrong", tl): return "mistakes"
    if re.search(r"plan|schedule|roadmap|strategy|step|day-wise|how to prepare|how to study", tl): return "plan"
    if re.search(r"tip|trick|shortcut|revis|health|motivat|stay |remember", tl): return "tips"
    if re.search(r"practice|paper|mock|test|quiz", tl): return "practice"
    if re.search(r"syllabus|pattern|overview|understand|basic|key|important|note|fact|summary|know the", tl): return "key"
    if re.search(r"resource|source|book|reference", tl): return "resources"
    return None

def raw(ns):
    return "".join(f"<{t}>{i}</{t}>" for t, i in ns)

def badge(text, cls="blk-badge"):
    return f'<span class="badge {cls}">{html.escape(text)}</span>'

def answer_box(a):
    a = re.sub(r"^\s*(?:<b>)?\s*Answer\s*:?\s*(?:</b>)?\s*:?\s*", "", a.strip(), flags=re.I)
    return f'<div class="qans"><b>Answer:</b> {strip_b(a)}</div>'

def qcard(num, q, opts=None, ans=None):
    o = "".join(f'<div class="qopt"><b>({chr(97 + k)})</b> {strip_b(li)}</div>' for k, li in enumerate(opts or []))
    return (f'<article class="qcard">{badge("Q" + str(num), "badge-primary")}'
            f'<p class="qtext">{strip_b(q)}</p>{o}{answer_box(ans) if ans else ""}</article>')

def render_questions(title, hid, ns):
    out, i = [f'<div class="qhead" id="{hid}">{badge("Practice", "badge-primary")}<h2>{html.escape(title)}</h2></div>'], 0
    while i < len(ns):
        t, inner = ns[i]; txt = plain(inner)
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
        if not (t == "h3" and re.match(r"question\s*\d+", txt, re.I)):
            out.append(f'<div class="qplain"><{t}>{inner}</{t}></div>')
        i += 1
    return "\n".join(out)

def render_answers(title, hid, ns):
    rows = ""
    for t, inner in ns:
        if t != "p": rows += f"<{t}>{inner}</{t}>"; continue
        m = _QP.match(inner)
        lab, rest = (f"Q{m.group(2)}", (m.group(1) or "") + inner[m.end():]) if m else ("", inner)
        rows += f'<div class="arow">{badge(lab, "arow-badge") if lab else ""}<p>{rest}</p></div>'
    return f'<section class="blk blk-green" id="{hid}">{badge("Answer key")}<h2>{html.escape(title)}</h2>{rows}</section>'

def render_faq(title, hid, ns):
    items = []
    for k, (q, a) in enumerate(faq_pairs(ns)):
        items.append(f'<details class="faq-item"{" open" if k == 0 else ""}><summary>{html.escape(q)}'
                     f'<span class="faq-chev"><svg aria-hidden="true" viewBox="0 0 24 24"><use href="#i-chev"/></svg></span></summary>'
                     f'<p>{html.escape(a)}</p></details>')
    return (f'<section class="postfaq" id="{hid}"><span class="sec-kicker">FAQ</span><h2>{html.escape(title)}</h2>'
            f'<div class="faq-list">{"".join(items)}</div></section>')

def quick_answer(first, rest_nodes):
    txt = re.sub(r"^\s*(?:<b>)?\s*quick\s*answer\s*:?\s*(?:</b>)?\s*:?\s*", "", first, flags=re.I).strip()
    sents = re.split(r"(?<=[.!?])\s+", txt); head, used = [], 0
    for s in sents:
        if head and used + len(s) > 300: break
        head.append(s); used += len(s) + 1
    tail = " ".join(sents[len(head):])
    more = (f'<p class="qa-more">{tail}</p>' if tail else "") + "".join(f'<div class="qa-more">{raw([n])}</div>' for n in rest_nodes)
    return (f'<div class="qa" id="quick-answer">{badge("Quick answer", "badge-qa")}'
            f'<p class="qa-text">{" ".join(head)}</p>{more}</div>')

def format_post(body):
    """-> dict(html, toc[(id,title)], faq[(q,a)], qa(text))"""
    ns = nodes(sanitize(body))
    first_h2 = next((k for k, (t, _) in enumerate(ns) if t == "h2"), len(ns))
    pre, rest = ns[:first_h2], ns[first_h2:]
    parts, toc, faq, qa_text = [], [], [], ""
    k = next((j for j, (t, _) in enumerate(pre) if t == "p"), None)
    if k is not None:
        parts.append(quick_answer(pre[k][1], pre[:k] + pre[k + 1:])); toc.append(("quick-answer", "Quick answer"))
        qa_text = plain(re.sub(r"^\s*(?:<b>)?\s*quick\s*answer\s*:?\s*(?:</b>)?", "", pre[k][1], flags=re.I))
    sections, cur = [], None
    for t, i in rest:
        if t == "h2": cur = [plain(i), []]; sections.append(cur)
        elif cur: cur[1].append((t, i))
    cyc, seen = 0, {"quick-answer"}
    for title, sn in sections:
        hid = slugify(title); base, n = hid, 2
        while hid in seen: hid = f"{base}-{n}"; n += 1
        seen.add(hid)
        kind = classify(title, sn); toc.append((hid, title))
        if kind == "faq": parts.append(render_faq(title, hid, sn)); faq = faq_pairs(sn)
        elif kind == "questions": parts.append(render_questions(title, hid, sn))
        elif kind == "answers": parts.append(render_answers(title, hid, sn))
        else:
            if kind is None: tint, label = CYCLE[cyc % 4], "Guide"; cyc += 1
            else: tint, label = TYPES[kind]
            parts.append(f'<section class="blk blk-{tint}" id="{hid}">{badge(label)}<h2>{html.escape(title)}</h2>{raw(sn)}</section>')
    return {"html": "\n".join(parts), "toc": toc, "faq": faq, "qa": qa_text}
