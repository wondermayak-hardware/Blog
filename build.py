#!/usr/bin/env python3
"""ThunderStudy Blog static site generator -> _site/ (GitHub Pages). Usage: python build.py"""
import re, json, html, pathlib, datetime, shutil, hashlib, math
from xml.sax.saxutils import escape as xesc
from postfmt import format_post, slugify
import cssutil

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "_site"
D = ROOT / "design"
SITE = "https://blog.thunderstudy.info"
NAME = "ThunderStudy Blog"
MAIN, TEST, AI = "https://thunderstudy.indevs.in", "https://thundertest.indevs.in", "https://ai.thunderstudy.indevs.in"
TG, CONTACT = "https://t.me/thunderstudy", "https://wondermayank.in/contact"
OG = "/assets/og-default.jpg"
PER_PAGE = 12
CAT_DESC = {
    "English": "Free CUET English practice: vocabulary, grammar, reading comprehension, verbal ability and simple study plans.",
    "GK": "Free General Knowledge practice for CUET: static GK, science, history, polity, current affairs and study plans.",
    "General Test": "Free CUET General Test practice: quantitative reasoning, logical reasoning and mental ability.",
}
esc = lambda s: html.escape(str(s), quote=True)
read = lambda n: (D / n).read_text(encoding="utf-8").strip()

# ---------------------------------------------------------------- content
def parse_post(path):
    t = path.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---\s*\n(.*)", t, re.S)
    if not m: raise ValueError("missing front matter")
    fm = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)); body = m.group(2).strip()
    for k in ("title", "description", "date", "category"):
        if not fm.get(k): raise ValueError(f"front matter needs '{k}'")
    f = format_post(body)
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    d = datetime.date.fromisoformat(fm["date"])
    return {"slug": fm.get("slug") or path.stem, "title": fm["title"], "desc": fm["description"], "date": d,
            "updated": datetime.date.fromisoformat(fm["updated"]) if fm.get("updated") else d,
            "cat": fm["category"], "cslug": slugify(fm["category"]),
            "labels": [x.strip() for x in fm.get("labels", "").split(",") if x.strip()],
            "body": f["html"], "toc": f["toc"], "faq": f["faq"], "qa": f["qa"], "words": words,
            "mins": max(1, round(words / 200))}

def load_posts():
    out = []
    for p in sorted((ROOT / "content/posts").glob("*.html")):
        try: out.append(parse_post(p))
        except (SystemExit, ValueError, KeyError) as e:
            print(f"WARNING: skipped {p.name}: {e}")
    return out
posts = sorted(load_posts(), key=lambda p: (p["date"], p["slug"]), reverse=True)
slugs = [p["slug"] for p in posts]
assert len(slugs) == len(set(slugs)), "duplicate slugs"
cats = {}
for p in posts: cats.setdefault(p["cat"], []).append(p)
cat_list = sorted(cats, key=lambda c: (-len(cats[c]), c))
today = max([p["updated"] for p in posts] or [datetime.date.today()])

# ---------------------------------------------------------------- helpers
def fdate(d): return d.strftime("%d %b %Y").lstrip("0")
def url(path): return SITE + path
def ld(*objs): return "".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>" for o in objs)
ORG = {"@type": "Organization", "@id": SITE + "/#org", "name": "ThunderStudy", "url": MAIN, "logo": {"@type": "ImageObject", "url": SITE + "/favicon.svg"},
       "sameAs": [TG, "https://wondermayank.in"]}
def crumbs_ld(items): return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
    {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}
def crumbs_html(items):
    li = "".join(f'<li><a href="{esc(u)}">{esc(n)}</a></li>' for n, u in items[:-1]) + f'<li><span aria-current="page" title="{esc(items[-1][0])}">{esc(items[-1][0] if len(items[-1][0]) <= 42 else items[-1][0][:40].rstrip() + "…")}</span></li>'
    return f'<nav class="ds-crumbs" aria-label="Breadcrumb"><ol>{li}</ol></nav>'

ICO = {"home": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/>', "list": '<path d="M4 7h16M4 12h12M4 17h8"/>',
       "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
       "spark": '<path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>', "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7M12 17h.01"/>',
       "dot": '<circle cx="12" cy="12" r="3"/>', "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
       "test": '<rect x="5" y="3" width="14" height="18" rx="3"/><path d="m9 12 2 2 4-4"/>', "send": '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
       "tag": '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="8" cy="8" r="1.5"/>'}
def svg(k, cls=""): return f'<svg{f" class=\"{cls}\"" if cls else ""} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICO[k]}</svg>'

# ---------------------------------------------------------------- shared chrome
HEADER = (read("header.html").replace("ThunderStudy AI by Wondermayank", "ThunderStudy Blog by Wondermayank").replace("ThunderStudy AI logo", "ThunderStudy Blog logo")
          .replace("Study AI", "Study Blog").replace('href="/faq"', 'href="/faq/"').replace('href="/new"', 'href="/new/"').replace('href="/about"', 'href="/about/"'))
_sd = read("side.html"); _i = _sd.index('<nav class="side-scroll"'); _j = _sd.index("</nav>", _i) + 6
SIDE_PRE, SIDE_POST = _sd[:_i], _sd[_j:]

def side(groups, title="Sections"):
    g = "".join(f'<div class="side-group"><p class="side-label">{esc(l)}</p>' + "".join(
        f'<a class="side-link" href="#{i}"><span class="side-ico">{svg(ic)}</span><span class="side-text">{esc(t if len(t) < 30 else t[:28] + "…")}</span></a>' for i, t, ic in items) + "</div>" for l, items in groups)
    return SIDE_PRE.replace(">Sections<", f">{esc(title)}<", 1) + f'<nav class="side-scroll" aria-label="{esc(title)}">{g}</nav>' + SIDE_POST

def dock(active):
    items = [("home", "Home", "/"), ("grid", "Topics", "/topics/"), ("search", "Search", "/search/"), ("spark", "New", "/new/"), ("test", "Free Mock Test", TEST)]
    b = "".join(f'<a class="dock-btn" href="{u}" data-label="{l}" aria-label="{l}"{" aria-current=\"page\"" if l == active else ""}{" target=\"_blank\" rel=\"noopener\"" if u.startswith("http") else ""}>{svg(ic)}</a>' for ic, l, u in items)
    return f'<nav class="dock" aria-label="Blog navigation"><div class="dock-bar"><span class="dock-indicator" aria-hidden="true"></span>{b}</div></nav>'

def layout(*, title, desc, path, main, side_html, dock_active, jsonld="", og_type="website", robots="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
           extra_head="", img=OG, img_alt="ThunderStudy girl mascot studying outside school next to a board that says Dream Study Achieve"):
    canon = url(path); t = title if len(title) <= 62 else title[:59].rsplit(" ", 1)[0] + "…"
    return f"""<!DOCTYPE html>
<html lang="en-IN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{esc(t)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="{robots}">
<meta name="theme-color" id="metaTheme" content="#70A1FC">
<meta name="color-scheme" id="metaScheme" content="light">
<meta name="supported-color-schemes" content="light">
<meta name="darkreader-lock">
<meta name="author" content="ThunderStudy">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:locale" content="en_IN">
<meta property="og:image" content="{SITE}{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:alt" content="{esc(img_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}{img}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
{extra_head}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
{read("theme_init.html")}
<link rel="stylesheet" href="/assets/{{{{CSS}}}}">
{jsonld}
</head>
<body>
<a class="skip" href="#top">Skip to content</a>
{read("loader.html")}
{read("sprite.html")}
{HEADER}
{side_html}
<main id="top">
{main}
</main>
{read("footer.html")}
{dock(dock_active)}
{read("totop.html")}
<script src="/assets/{{{{JS}}}}" defer></script>
</body>
</html>
"""

# ---------------------------------------------------------------- components
def pcard(p, feat=False):
    return (f'<article class="card pcard{" pfeat" if feat else ""}"><a class="pcard-link" href="/{p["slug"]}/">'
            f'<div class="pcard-top"><span class="badge badge-primary">{esc(p["cat"])}</span><time datetime="{p["date"]}">{fdate(p["date"])}</time></div>'
            f'<h{2 if feat else 3} class="pcard-title">{esc(p["title"])}</h{2 if feat else 3}><p class="pcard-desc">{esc(p["desc"])}</p>'
            f'<div class="pcard-foot"><span>{p["mins"]} min read</span><span class="pcard-go">Read post <svg aria-hidden="true" viewBox="0 0 24 24"><use href="#i-arrow"/></svg></span></div></a></article>')

def sec_head(kicker, h2, sub=""):
    return f'<div class="sec-head"><span class="sec-kicker">{esc(kicker)}</span><h2>{h2}</h2>{f"<p>{sub}</p>" if sub else ""}</div>'

def pager(base, page, total):
    if total <= 1: return ""
    def href(n): return base if n == 1 else f"{base}{n}/"
    li = ""
    if page > 1: li += f'<li><a class="pg" rel="prev" href="{href(page - 1)}" aria-label="Previous page">Prev</a></li>'
    for n in range(1, total + 1):
        li += f'<li><a class="pg{" on" if n == page else ""}" href="{href(n)}"{" aria-current=\"page\"" if n == page else ""}>{n}</a></li>'
    if page < total: li += f'<li><a class="pg" rel="next" href="{href(page + 1)}" aria-label="Next page">Next</a></li>'
    return f'<nav aria-label="Pagination"><ul class="ds-pager pgr">{li}</ul></nav>'

def faq_list(pairs, open_first=True):
    return '<div class="faq-list">' + "".join(
        f'<details class="faq-item"{" open" if k == 0 and open_first else ""}><summary>{esc(q)}<span class="faq-chev"><svg aria-hidden="true" viewBox="0 0 24 24"><use href="#i-chev"/></svg></span></summary><p>{esc(a)}</p></details>'
        for k, (q, a) in enumerate(pairs)) + "</div>"

def faq_ld(pairs): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}

def cta_box():
    return (f'<aside class="cta-box" aria-label="Practice more"><span class="badge badge-qa">Free practice</span><h2>Practise more for free</h2>'
            f'<p>Take free CUET mock tests, build cheatsheets and flashcards with ThunderStudy AI, and join the Telegram community for daily updates.</p>'
            f'<div class="cta-btns"><a class="btn btn-primary" href="{TEST}">Free mock tests</a><a class="btn btn-secondary" href="{AI}">ThunderStudy AI</a>'
            f'<a class="btn btn-secondary" href="{TG}" rel="noopener">Join Telegram</a></div></aside>')

SIDE_HOME = [("Start", [("top", "Top", "home")]), ("Explore", [("latest", "Latest posts", "list"), ("topics", "Topics", "grid"), ("tools", "Free tools", "spark"), ("faq", "FAQ", "help")])]
SIDE_LIST = [("Start", [("top", "Top", "home"), ("posts", "Posts", "list")])]

pages = {}   # path -> html
def add(path, html_): pages[path] = html_

# ---------------------------------------------------------------- home
HOME_FAQ = [("Is ThunderStudy Blog free?", "Yes. Every post, practice set and guide on this blog is free to read, with no signup."),
            ("Which exams does this blog cover?", "The focus is CUET: English, General Knowledge and General Test practice, plus study plans. More subjects are added over time."),
            ("Are the practice answers checked?", "Practice posts are reviewed before publishing. If you find a mistake, message us through the contact page and we will fix it."),
            ("Where can I take full mock tests?", "Use ThunderTest for free timed mock tests, then come back here for topic practice and study plans.")]
def build_home():
    n_posts, n_cats = len(posts), len(cats)
    words = ["Free", "CUET", "practice,", "study", "guides", "and", "plans"]
    h1 = " ".join(f'<span class="hx-w{" hx-acc" if w == "CUET" else ""}" style="--i:{i}">{w}</span>' for i, w in enumerate(words))
    chips = "".join(f'<span class="hx-mc"><i></i>{esc(c)}</span>' for c in (cat_list + ["Study plans", "Mock tests", "Free practice"]) * 2)
    hero = f"""<section class="hero hx"><div class="hx-bg" aria-hidden="true"><i class="hx-orb o1"></i><i class="hx-orb o2"></i><i class="hx-orb o3"></i><span class="hx-dots-bg"></span></div>
<div class="wrap"><span class="hero-badge hx-badge"><span class="hx-ping"></span>New CUET practice and study plans</span>
<h1 class="hx-h1">{h1}</h1>
<p class="hero-sub hx-sub">ThunderStudy Blog publishes free CUET English, GK and General Test practice sets with answers, simple study plans and exam tips for Indian students.</p>
<form class="hero-search" role="search" action="/search/" method="get"><label class="sr" for="hq">Search posts</label><input id="hq" class="text-input" type="search" name="q" placeholder="Search synonyms, ISRO, study plan…" autocomplete="off"><button class="btn btn-primary" type="submit">Search</button></form>
<div class="hero-actions hx-actions"><a class="btn btn-primary btn-lg hx-shine" href="/new/"><svg aria-hidden="true"><use href="#i-spark"/></svg>Read latest posts</a><a class="btn btn-secondary btn-lg" href="/topics/">Browse topics</a></div>
<div class="hx-stats"><div class="hx-stat"><strong data-to="{n_posts}">{n_posts}</strong><small>free posts</small></div><div class="hx-stat"><strong data-to="{n_cats}">{n_cats}</strong><small>topics</small></div><div class="hx-stat"><strong>Free</strong><small>no signup</small></div><div class="hx-stat"><strong>Quick</strong><small>answer first</small></div></div>
<div class="hx-marq" aria-hidden="true"><div class="hx-track">{chips}</div></div></div></section>"""
    feat = pcard(posts[0], True) if posts else ""
    grid = "".join(pcard(p) for p in posts[1:9])
    latest = (f'<section class="sec" id="latest"><div class="wrap">{sec_head("Latest", "Fresh practice and <span class=\"accent\">study guides</span>", "New posts added regularly, each with a quick answer you can read in seconds.")}'
              f'{feat}<div class="pgrid">{grid}</div><p class="center"><a class="btn btn-secondary" href="/new/">See all posts</a></p></div></section>')
    tcards = "".join(f'<a class="card tcard" href="/category/{slugify(c)}/"><div class="card-ico">{svg("tag")}</div><h3>{esc(c)}</h3><p>{esc(CAT_DESC.get(c, f"Free CUET {c} practice questions and study guides."))}</p><span class="tcount">{len(cats[c])} post{"s" if len(cats[c]) != 1 else ""}</span></a>' for c in cat_list)
    topics = f'<section class="sec sec-alt" id="topics"><div class="wrap">{sec_head("Topics", "Pick a subject and <span class=\"accent\">start practising</span>")}<div class="tgrid">{tcards}</div></div></section>'
    tools = [("Free mock tests", "Timed CBT-style CUET mock tests on ThunderTest.", TEST, "test"), ("ThunderStudy AI", "Cheatsheets, flashcards and formula explainers from your chapters.", AI, "spark"),
             ("Study material", "Free notes, formula sheets and resources on ThunderStudy.", MAIN, "list"), ("Telegram community", "Daily updates and quizzes with other students.", TG, "send")]
    tl = "".join(f'<a class="card tcard" href="{u}"{" rel=\"noopener\"" if "t.me" in u else ""}><div class="card-ico">{svg(ic)}</div><h3>{esc(t)}</h3><p>{esc(d)}</p><span class="tcount">Open &rarr;</span></a>' for t, d, u, ic in tools)
    tools_s = f'<section class="sec" id="tools"><div class="wrap">{sec_head("Free tools", "More ways to <span class=\"accent\">prepare</span>", "Everything on ThunderStudy is free for students.")}<div class="tgrid">{tl}</div></div></section>'
    faq = f'<section class="sec sec-alt" id="faq"><div class="wrap">{sec_head("FAQ", "Questions, <span class=\"accent\">answered</span>")}<div class="narrow">{faq_list(HOME_FAQ)}</div></div></section>'
    desc = "Free CUET English, GK and General Test practice sets with answers, simple study plans and exam tips. Read the quick answer, practise, and take free mock tests."
    web = {"@context": "https://schema.org", "@graph": [ORG, {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": NAME, "description": desc, "inLanguage": "en-IN", "publisher": {"@id": SITE + "/#org"},
           "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": SITE + "/search/?q={search_term_string}"}, "query-input": "required name=search_term_string"}},
           {"@type": "Blog", "@id": SITE + "/#blog", "url": SITE + "/", "name": NAME, "publisher": {"@id": SITE + "/#org"}, "inLanguage": "en-IN"}]}
    add("/", layout(title="ThunderStudy Blog | Free CUET Practice and Study Guides", desc=desc, path="/", main=hero + latest + topics + tools_s + faq,
                    side_html=side(SIDE_HOME), dock_active="Home", jsonld=ld(web)))

# ---------------------------------------------------------------- listings
def listing(base, heading, kicker, sub, plist, dock_active, crumbs, desc, title, ldtype="CollectionPage"):
    total = max(1, math.ceil(len(plist) / PER_PAGE))
    for pg in range(1, total + 1):
        chunk = plist[(pg - 1) * PER_PAGE: pg * PER_PAGE]
        path = base if pg == 1 else f"{base}{pg}/"
        grid = "".join(pcard(p) for p in chunk) or '<p class="center">No posts yet. Check back soon.</p>'
        head = f'<span class="sr">Page {pg}</span>' if pg > 1 else ""
        main = (f'<section class="sec lsec"><div class="wrap">{crumbs_html(crumbs)}<div class="lhead"><span class="sec-kicker">{esc(kicker)}</span><h1>{heading}</h1><p>{esc(sub)}</p></div>'
                f'<div class="pgrid" id="posts">{grid}</div>{pager(base, pg, total)}</div></section>')
        extra = (f'<link rel="prev" href="{url(base if pg == 2 else base + str(pg - 1) + "/")}">' if pg > 1 else "") + (f'<link rel="next" href="{url(base + str(pg + 1) + "/")}">' if pg < total else "")
        coll = {"@context": "https://schema.org", "@type": ldtype, "name": title, "description": desc, "url": url(path), "inLanguage": "en-IN", "isPartOf": {"@id": SITE + "/#website"},
                "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": (pg - 1) * PER_PAGE + i + 1, "url": url(f"/{p['slug']}/"), "name": p["title"]} for i, p in enumerate(chunk)]}}
        add(path, layout(title=title + (f" (Page {pg})" if pg > 1 else ""), desc=desc, path=path, main=main, side_html=side(SIDE_LIST), dock_active=dock_active,
                         jsonld=ld(coll, crumbs_ld(crumbs)), extra_head=extra, robots="index,follow,max-image-preview:large" if pg == 1 else "noindex,follow"))

def build_listings():
    listing("/new/", "All <span class=\"accent\">posts</span>", "Latest", "Every free practice set and study guide, newest first.", posts, "New",
            [("Home", "/"), ("All posts", "/new/")], "All ThunderStudy Blog posts: free CUET practice sets, study plans and exam tips, newest first.", "All Posts | ThunderStudy Blog")
    for c in cat_list:
        cs = slugify(c); d = CAT_DESC.get(c, f"Free CUET {c} practice questions and study guides.")
        listing(f"/category/{cs}/", f"CUET <span class=\"accent\">{esc(c)}</span> posts", "Topic", d, cats[c], "Topics",
                [("Home", "/"), ("Topics", "/topics/"), (c, f"/category/{cs}/")], d, f"CUET {c} Practice and Study Guides | ThunderStudy Blog")
    tc = "".join(f'<a class="card tcard" href="/category/{slugify(c)}/"><div class="card-ico">{svg("tag")}</div><h2>{esc(c)}</h2><p>{esc(CAT_DESC.get(c, f"Free CUET {c} practice questions and study guides."))}</p><span class="tcount">{len(cats[c])} post{"s" if len(cats[c]) != 1 else ""}</span></a>' for c in cat_list)
    cr = [("Home", "/"), ("Topics", "/topics/")]
    main = (f'<section class="sec lsec"><div class="wrap">{crumbs_html(cr)}<div class="lhead"><span class="sec-kicker">Topics</span><h1>Browse <span class="accent">topics</span></h1><p>Pick a subject to see every free practice set and study guide for it.</p></div>'
            f'<div class="tgrid" id="posts">{tc}</div></div></section>')
    add("/topics/", layout(title="Topics | ThunderStudy Blog", desc="Browse ThunderStudy Blog topics: CUET English, GK and General Test practice sets and study guides.", path="/topics/", main=main,
                           side_html=side(SIDE_LIST), dock_active="Topics", jsonld=ld(crumbs_ld(cr))))

# ---------------------------------------------------------------- posts
def build_posts():
    for i, p in enumerate(posts):
        path = f"/{p['slug']}/"
        newer, older = (posts[i - 1] if i > 0 else None), (posts[i + 1] if i + 1 < len(posts) else None)
        rel = [q for q in posts if q is not p and q["cat"] == p["cat"]][:3]
        rel += [q for q in posts if q is not p and q not in rel][:3 - len(rel)]
        crumbs = [("Home", "/"), (p["cat"], f"/category/{p['cslug']}/"), (p["title"], path)]
        chips = f'<a class="chip active" href="/category/{p["cslug"]}/">{esc(p["cat"])}</a>' + "".join(f'<span class="chip">{esc(l)}</span>' for l in p["labels"] if l != p["cat"])
        upd = f' &middot; Updated <time datetime="{p["updated"]}">{fdate(p["updated"])}</time>' if p["updated"] != p["date"] else ""
        share_u = esc(url(path)); share_t = esc(p["title"])
        share = (f'<div class="share" aria-label="Share this post"><span>Share</span>'
                 f'<a class="chip" href="https://t.me/share/url?url={share_u}&amp;text={share_t}" rel="noopener" target="_blank">Telegram</a>'
                 f'<a class="chip" href="https://wa.me/?text={share_t}%20{share_u}" rel="noopener" target="_blank">WhatsApp</a>'
                 f'<button class="chip" type="button" data-copy="{share_u}">Copy link</button></div>')
        nav = ""
        if newer or older:
            nav = '<nav class="post-nav" aria-label="More posts">' + (f'<a class="card" href="/{older["slug"]}/"><small>Older</small><b>{esc(older["title"])}</b></a>' if older else "<span></span>") + \
                  (f'<a class="card" href="/{newer["slug"]}/"><small>Newer</small><b>{esc(newer["title"])}</b></a>' if newer else "<span></span>") + "</nav>"
        related = (f'<section class="related" aria-labelledby="rel-h"><h2 id="rel-h">Keep practising</h2><div class="pgrid">{"".join(pcard(q) for q in rel)}</div></section>' if rel else "")
        main = (f'<article class="wrap post" itemscope itemtype="https://schema.org/BlogPosting"><div class="post-wrap">{crumbs_html(crumbs)}'
                f'<header class="post-head"><div class="chip-row">{chips}</div><h1 itemprop="headline">{esc(p["title"])}</h1>'
                f'<p class="post-meta">By <a href="{MAIN}" rel="noopener">ThunderStudy</a> &middot; <time datetime="{p["date"]}" itemprop="datePublished">{fdate(p["date"])}</time>{upd} &middot; {p["mins"]} min read</p></header>'
                f'<div class="post-body" itemprop="articleBody">{p["body"]}</div>{share}{cta_box()}{nav}</div>{related}</article>')
        faq_obj = [faq_ld(p["faq"])] if p["faq"] else []
        post_ld = {"@context": "https://schema.org", "@type": "BlogPosting", "@id": url(path) + "#post", "headline": p["title"], "description": p["desc"], "inLanguage": "en-IN",
                   "datePublished": str(p["date"]), "dateModified": str(p["updated"]), "mainEntityOfPage": {"@type": "WebPage", "@id": url(path)}, "image": [SITE + OG],
                   "author": {"@type": "Organization", "name": "ThunderStudy", "url": MAIN}, "publisher": {"@id": SITE + "/#org"}, "articleSection": p["cat"],
                   "keywords": ", ".join(p["labels"]), "wordCount": p["words"], "timeRequired": f"PT{p['mins']}M", "isPartOf": {"@id": SITE + "/#blog"}}
        toc_groups = [("On this page", [("top", "Top", "home")] + [(i_, t, "dot") for i_, t in p["toc"]])]
        add(path, layout(title=p["title"] if len(p["title"]) > 48 else p["title"] + " | ThunderStudy Blog", desc=p["desc"], path=path, main=main,
                         side_html=side(toc_groups, "On this page"), dock_active="Topics", og_type="article",
                         jsonld=ld(ORG | {"@context": "https://schema.org"}, post_ld, crumbs_ld(crumbs), *faq_obj),
                         extra_head=f'<meta property="article:published_time" content="{p["date"]}">\n<meta property="article:modified_time" content="{p["updated"]}">\n<meta property="article:section" content="{esc(p["cat"])}">\n'))

# ---------------------------------------------------------------- static pages
SITE_FAQ = [("What is ThunderStudy Blog?", "ThunderStudy Blog is a free blog with CUET practice sets, answer keys, study plans and exam tips for Indian students, made by the ThunderStudy team."),
            ("Is everything on this blog free?", "Yes. All posts and practice sets are free to read and use, and no signup is needed."),
            ("Which exams are covered?", "The blog focuses on CUET: English, General Knowledge and General Test. More subjects and exams are added over time."),
            ("How often are new posts published?", "New practice sets and guides are added regularly. Follow the Telegram community or the RSS feed to see them first."),
            ("Are the answers in practice sets checked?", "Practice posts are reviewed before they are published. If you spot a mistake, tell us through the contact page and we will correct it."),
            ("Where can I take a full mock test?", "Use ThunderTest for free timed mock tests. This blog is best for topic-wise practice and study plans."),
            ("Can I share these posts with friends?", "Yes. Every post has share buttons for Telegram, WhatsApp and a copy-link button."),
            ("How do I report an error or request a topic?", "Use the contact page or message the Telegram community with the post link and what needs fixing.")]
def build_static():
    cr = [("Home", "/"), ("FAQ", "/faq/")]
    main = (f'<section class="sec lsec"><div class="wrap">{crumbs_html(cr)}<div class="lhead"><span class="sec-kicker">FAQ</span><h1>Frequently asked <span class="accent">questions</span></h1><p>Short, plain answers about ThunderStudy Blog.</p></div>'
            f'<div class="narrow" id="posts">{faq_list(SITE_FAQ)}</div></div></section>')
    add("/faq/", layout(title="FAQ | ThunderStudy Blog", desc="Answers about ThunderStudy Blog: what it covers, whether it is free, how answers are checked and how to report a mistake.", path="/faq/", main=main,
                        side_html=side(SIDE_LIST), dock_active="Home", jsonld=ld(faq_ld(SITE_FAQ), crumbs_ld(cr))))
    cr = [("Home", "/"), ("About", "/about/")]
    main = (f'<section class="sec lsec"><div class="wrap">{crumbs_html(cr)}<div class="lhead"><span class="sec-kicker">About</span><h1>About <span class="accent">ThunderStudy Blog</span></h1></div>'
            f'<div class="narrow prose" id="posts"><p>ThunderStudy Blog is the free writing arm of <a href="{MAIN}">ThunderStudy</a>, a set of free study tools for Indian competitive exam students. We publish CUET practice sets with answer keys, simple study plans and exam tips in plain language.</p>'
            f'<h2>What you will find here</h2><ul><li>Quick answers at the top of every post, so you can learn the key point in seconds.</li><li>Practice questions with answer keys and short explanations.</li><li>Day-by-day study plans you can follow alongside school or college.</li></ul>'
            f'<h2>Our promise</h2><p>Everything is free. We review practice posts before publishing and fix mistakes when students report them. We never promise results: consistent practice is what helps.</p>'
            f'<h2>Related tools</h2><p>Take timed mock tests on <a href="{TEST}">ThunderTest</a>, build cheatsheets and flashcards with <a href="{AI}">ThunderStudy AI</a>, or join the <a href="{TG}" rel="noopener">Telegram community</a>. To reach us, use the <a href="{CONTACT}" rel="noopener">contact page</a>.</p></div></div></section>')
    add("/about/", layout(title="About | ThunderStudy Blog", desc="About ThunderStudy Blog: free CUET practice sets, answer keys and study plans from the ThunderStudy team.", path="/about/", main=main,
                          side_html=side(SIDE_LIST), dock_active="Home", jsonld=ld({"@context": "https://schema.org", "@type": "AboutPage", "name": "About ThunderStudy Blog", "url": url("/about/"), "publisher": {"@id": SITE + "/#org"}}, crumbs_ld(cr), ORG | {"@context": "https://schema.org"})))
    main = (f'<section class="sec lsec"><div class="wrap"><div class="lhead"><span class="sec-kicker">Search</span><h1>Search <span class="accent">posts</span></h1><p id="sstat">Type a word to search all posts.</p></div>'
            f'<form class="hero-search wide" id="sq-form" role="search" onsubmit="return false"><label class="sr" for="sq">Search posts</label><input id="sq" class="text-input" type="search" placeholder="Search synonyms, ISRO, study plan…" autocomplete="off" autofocus></form>'
            f'<div class="sres" id="sres" aria-live="polite"></div></div></section>')
    add("/search/", layout(title="Search | ThunderStudy Blog", desc="Search ThunderStudy Blog for CUET practice sets and study guides.", path="/search/", main=main, side_html=side(SIDE_LIST), dock_active="Search", robots="noindex,follow"))
    main = (f'<section class="sec lsec"><div class="wrap center"><span class="sec-kicker">Error 404</span><h1>This page <span class="accent">is missing</span></h1><p class="lead">The link may be old or mistyped. Try search or go back to the latest posts.</p>'
            f'<div class="hero-actions"><a class="btn btn-primary btn-lg" href="/">Go home</a><a class="btn btn-secondary btn-lg" href="/search/">Search posts</a></div></div></section>')
    add("/404.html", layout(title="Page not found | ThunderStudy Blog", desc="This page could not be found on ThunderStudy Blog. Try search or go back to the latest free CUET practice posts.", path="/404.html", main=main, side_html=side(SIDE_LIST), dock_active="Home", robots="noindex,follow"))

# ---------------------------------------------------------------- feeds and files
def build_files(css_name, js_name):
    urls = [("/", today, "1.0"), ("/new/", today, "0.8"), ("/topics/", today, "0.7"), ("/faq/", today, "0.5"), ("/about/", today, "0.4")]
    urls += [(f"/category/{slugify(c)}/", max(p["updated"] for p in cats[c]), "0.7") for c in cat_list]
    urls += [(f"/{p['slug']}/", p["updated"], "0.9") for p in posts]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"<url><loc>{xesc(url(u))}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>\n" for u, d, pr in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    items = "".join(f"<item><title>{xesc(p['title'])}</title><link>{url('/' + p['slug'] + '/')}</link><guid isPermaLink=\"true\">{url('/' + p['slug'] + '/')}</guid>"
                    f"<pubDate>{datetime.datetime.combine(p['date'], datetime.time(6, 0)).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate><category>{xesc(p['cat'])}</category><description>{xesc(p['desc'])}</description></item>\n" for p in posts[:30])
    (OUT / "feed.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{NAME}</title><link>{SITE}/</link>'
                                  f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/><description>Free CUET practice sets, study plans and exam tips.</description><language>en-in</language>\n{items}</channel></rss>\n', encoding="utf-8")
    (OUT / "search.json").write_text(json.dumps([[p["title"], f"/{p['slug']}/", p["cat"], str(p["date"])] for p in posts], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "site.webmanifest").write_text(json.dumps({"name": NAME, "short_name": "TS Blog", "start_url": "/", "display": "standalone", "background_color": "#EEF3FF", "theme_color": "#70A1FC",
                                                      "icons": [{"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}, {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}]}), encoding="utf-8")
    (OUT / "_headers").write_text("/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n\n/favicon.svg\n  Cache-Control: public, max-age=86400\n\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  X-Frame-Options: SAMEORIGIN\n", encoding="utf-8")

# ---------------------------------------------------------------- assets
def build_js():
    s3 = read("script_3.js"); core = s3[: s3.index("/* ---------- TOAST")] + "\n})();"
    prog = "(function(){var sp=document.createElement('div');sp.className='sp';document.body.appendChild(sp);addEventListener('scroll',function(){var m=document.documentElement.scrollHeight-innerHeight;sp.style.transform='scaleX('+(m>0?scrollY/m:0)+')'},{passive:true});})();"
    return "\n".join([core, read("script_6.js"), read("script_7.js"), prog, (ROOT / "assets/blog.js").read_text(encoding="utf-8")])

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    build_home(); build_listings(); build_posts(); build_static()
    js = build_js()
    used = set()
    for h in pages.values():
        for m in re.findall(r'class="([^"]+)"', h): used.update(m.split())
    used.update(re.findall(r"['\"]([A-Za-z_-][\w-]*)['\"]", js)); used.update(["hide", "open", "up", "in", "show", "gone", "min", "rail", "no-anim", "theme-swap", "sp", "on", "active", "dock-ripple"])
    css = cssutil.build(read("design.css"), (ROOT / "assets/blog.css").read_text(encoding="utf-8"), used)
    ch, jh = hashlib.md5(css.encode()).hexdigest()[:8], hashlib.md5(js.encode()).hexdigest()[:8]
    css_name, js_name = f"style.{ch}.css", f"site.{jh}.js"
    (OUT / "assets" / css_name).write_text(css, encoding="utf-8"); (OUT / "assets" / js_name).write_text(js, encoding="utf-8")
    for path, h in pages.items():
        h = h.replace("{{CSS}}", css_name).replace("{{JS}}", js_name)
        f = OUT / path.lstrip("/") if path.endswith(".html") else OUT / path.lstrip("/") / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True); f.write_text(h, encoding="utf-8")
    for n in ("favicon.svg", "apple-touch-icon.png"): shutil.copy(ROOT / "assets" / n, OUT / n)
    shutil.copy(ROOT / "assets/og-default.jpg", OUT / "assets/og-default.jpg")
    build_files(css_name, js_name)
    print(f"built {len(pages)} pages, {len(posts)} posts | css {len(css)//1024} KB, js {len(js)//1024} KB -> {OUT}")

if __name__ == "__main__":
    main()
