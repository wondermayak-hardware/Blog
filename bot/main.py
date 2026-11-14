"""Daily blog bot (same repo as the website).
  python bot/main.py generate   writes content/posts/<slug>.html for the next unused idea
  python bot/main.py notify     sends the Telegram message for the post that was just published
Progress is the posts themselves: every bot post has 'idea: N' in its front matter, so there is no separate state to lose.
"""
import os, re, json, sys, html, datetime, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "content" / "posts"
OUT = ROOT / "out"
IDEAS = json.loads((Path(__file__).parent / "ideas.json").read_text(encoding="utf-8"))

OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
SITE_URL = os.environ.get("SITE_URL", "https://blog.thunderstudy.info").rstrip("/")
LANGUAGE = os.environ.get("LANGUAGE", "simple English")
MODELS = [m.strip() for m in os.environ.get("MODELS", "").split(",") if m.strip()]   # optional override
DRY = os.environ.get("DRY_RUN") == "1"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

SYSTEM = ("You are an expert Indian exam-prep content writer for CUET students. You write accurate, student-friendly, "
          "original blog posts. Output ONLY an HTML fragment: no <html>, <head>, <body>, <title>, <h1>, markdown, or code fences. "
          "Use only <h2>, <h3>, <p>, <ul>, <ol>, <li>, <b>, <i>, <br>. Never add links. "
          "Only state facts you are sure are correct; avoid time-sensitive claims.")

def prompt_for(idea):
    t, topic, subj = idea["title"], idea["topic"], idea["subject"]
    if idea["type"] == "questions":
        return (f"Blog title: {t}\nSubject: {subj} / {topic}\nLanguage: {LANGUAGE}\n\nWrite the post with:\n"
                "1. First line: <p>Quick Answer: ...</p> (one direct 30-50 word answer to the title), then a 2-sentence intro using the main keyword once.\n"
                "2. A short <h2>How to Use This Set</h2> tip.\n"
                "3. <h2>Practice Questions</h2> with exactly 10 MCQs at CUET level (match the difficulty in the title). Format each as: "
                "<p><b>Q1.</b> question</p> then an <ol type=\"a\"> with 4 options. Vary the correct option.\n"
                "4. An <h2>Answer Key with Explanations</h2> section: for each Q, '<p><b>Q1. Answer: (b) text</b> - one-line explanation</p>'.\n"
                "5. <h2>Common Mistakes</h2> (3 bullets), <h2>Quick Tips</h2> (4 bullets) and <h2>FAQs</h2> with 3 Q&As (each question as <h3>, answer as <p>).\n"
                "Make every question different from common textbook examples.")
    return (f"Blog title: {t}\nSubject: {subj} / {topic}\nLanguage: {LANGUAGE}\n\n"
            "Write 900-1200 words. First line: <p>Quick Answer: ...</p> (one direct 30-50 word answer to the title), then a short intro (use the main keyword once), "
            "then 5-6 <h2> sections with practical, specific advice, a simple day-wise or step-wise plan where relevant, 3 example practice questions with answers, "
            "a <h2>Common Mistakes</h2> section, a <h2>Quick Tips</h2> section, and an <h2>FAQs</h2> section with 4 short Q&As (each question as <h3>, answer as <p>). "
            "Keep it motivating and honest; do not promise results.")

GOOD = ("nemotron", "llama", "qwen", "deepseek", "gemini", "gemma", "mistral", "gpt-oss", "glm", "kimi", "minimax", "laguna", "mimo")
BAD = ("embed", "rerank", "guard", "image", "audio", "vision", "-vl", "tts", "whisper", "moderation", "stealth")

def discover_free_models(limit=6):
    """Reads OpenRouter's public model list and returns currently free text models, best first."""
    try:
        data = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json().get("data", [])
    except Exception as e:
        print("model discovery failed:", e); return []
    found = []
    for m in data:
        mid = m.get("id", "").lower(); p = m.get("pricing") or {}
        try: free = float(p.get("prompt", 1)) == 0 and float(p.get("completion", 1)) == 0
        except (TypeError, ValueError): free = False
        text_out = "text" in ((m.get("architecture") or {}).get("output_modalities") or ["text"])
        ctx = m.get("context_length") or 0
        if not free or not text_out or any(b in mid for b in BAD) or mid.startswith("openrouter/") or ctx < 32000: continue
        found.append(((any(g in mid for g in GOOD), mid.endswith(":free"), min(ctx, 262144), m.get("created") or 0), m["id"]))
    found.sort(reverse=True)
    return [mid for _, mid in found[:limit]]

def model_chain():
    return (MODELS + [m for m in discover_free_models() if m not in MODELS] + ["openrouter/free"])[:8]

def clean(t):
    t = re.sub(r"^```(?:html)?\s*|\s*```$", "", t.strip())
    t = re.sub(r"(?is)<!doctype.*?>|</?(html|head|body)[^>]*>|<title>.*?</title>|<h1[^>]*>.*?</h1>", "", t)
    return t.strip()

def call_model(prompt):
    models, last, t0 = model_chain(), None, time.time()
    print("trying models:", models)
    for model in models:
        if time.time() - t0 > 540: break
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OR_KEY}", "HTTP-Referer": SITE_URL, "X-Title": "ThunderStudy Blog Bot"},
                json={"model": model, "temperature": 0.7, "max_tokens": 6000,
                      "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}, timeout=100)
            r.raise_for_status()
            text = clean(r.json()["choices"][0]["message"].get("content") or "")
            ok = len(text) > 1500 and "<h2" in text and ("Answer" not in prompt or "Answer" in text)
            if ok: return text, model
            last = f"{model}: output too short or incomplete"
        except Exception as e:
            last = f"{model}: {e}"
        print("skip", last)
    raise RuntimeError(last or "no models available")

def verify_answers(body):
    """Second AI pass: fact-check answers. Returns a short note for the Telegram message."""
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))
    if "Answer" not in text: return "No answer key in this post."
    prompt = ("You are a strict CUET exam fact-checker. Check every question's answer and every factual claim below. "
              'Reply ONLY with JSON: {"issues":[{"item":"Q3","problem":"...","correct":"..."}]}. '
              "List only real errors you are confident about; use an empty list if all is correct.\n\n" + text[:9000])
    for model in model_chain()[:3]:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OR_KEY}", "HTTP-Referer": SITE_URL, "X-Title": "ThunderStudy Blog Bot"},
                json={"model": model, "temperature": 0, "max_tokens": 1500, "messages": [{"role": "user", "content": prompt}]}, timeout=80)
            r.raise_for_status()
            data = json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"].get("content") or "", re.S).group())
            issues = data.get("issues", [])
            if not issues: return "AI answer check: no errors found (still skim it)."
            return "AI answer check, please verify these and edit the post file if needed:\n" + "\n".join(
                f"- {i.get('item','?')}: {i.get('problem','')} (suggested: {i.get('correct','')})" for i in issues[:8])
        except Exception:
            continue
    return "AI answer check unavailable today, please skim the answers."

def slugify(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def make_description(title, body):
    paras = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p))).strip() for p in re.findall(r"(?is)<p[^>]*>(.*?)</p>", body)]
    paras = [re.sub(r"(?i)^quick answer\s*:?\s*", "", p) for p in paras if p]
    text = " ".join(paras[:2]) if paras else ""
    if len(text) < 80: text = f"{title}. Free CUET practice, answers and study tips from ThunderStudy Blog."
    if len(text) > 155:
        cut = max(text.rfind(". ", 0, 155), text.rfind("? ", 0, 155), text.rfind("! ", 0, 155))
        text = text[:cut + 1] if cut >= 90 else text[:152].rsplit(" ", 1)[0].rstrip(",;:- ") + "..."
    return text

def scan_posts():
    used, titles = set(), set()
    for f in POSTS.glob("*.html"):
        head = f.read_text(encoding="utf-8")[:2000]
        m = re.search(r"^idea:\s*(\d+)", head, re.M); t = re.search(r"^title:\s*(.+)$", head, re.M)
        if m: used.add(int(m.group(1)))
        if t: titles.add(t.group(1).strip().lower())
    return used, titles

def pick_idea():
    forced = os.environ.get("IDEA_ID", "").strip()
    if forced.isdigit():
        return next((i for i in IDEAS if i["id"] == int(forced)), None)
    used, titles = scan_posts()
    return next((i for i in IDEAS if i["id"] not in used and i["title"].lower() not in titles), None)

def tg(method, data=None, files=None):
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/{method}", data=data, files=files, timeout=60)
    r.raise_for_status()

def generate():
    OUT.mkdir(exist_ok=True); POSTS.mkdir(parents=True, exist_ok=True)
    idea = pick_idea()
    if not idea:
        print("No unused ideas left.")
        if not DRY and TG_TOKEN: tg("sendMessage", {"chat_id": TG_CHAT, "text": "All blog ideas are used. Time to generate a new ideas list."})
        return
    try:
        body, model = ("<h2>Test</h2><p>" + "dry run " * 300 + "</p>", "dry-run") if DRY else call_model(prompt_for(idea))
    except Exception as e:
        print("FAILED:", e)
        if not DRY and TG_TOKEN: tg("sendMessage", {"chat_id": TG_CHAT, "text": f"Blog bot could not write idea #{idea['id']}: {str(e)[:300]}\nIt will retry tomorrow with the same idea."})
        sys.exit(1)
    check = "skipped (dry run)" if DRY else verify_answers(body)
    title = re.sub(r"\s+", " ", idea["title"]).strip()
    slug = slugify(title)[:70].strip("-")
    if (POSTS / f"{slug}.html").exists(): slug = f"{slug[:60].strip('-')}-{idea['id']}"
    labels = ["CUET 2027" if l == "CUET" else l for l in idea["labels"]]
    today = datetime.datetime.now(IST).date().isoformat()
    fm = (f"---\ntitle: {title}\ndescription: {make_description(title, body)}\ndate: {today}\n"
          f"category: {idea['subject']}\nlabels: {', '.join(labels)}\nidea: {idea['id']}\n---\n")
    target = (OUT / "dry" if DRY else POSTS); target.mkdir(parents=True, exist_ok=True)
    (target / f"{slug}.html").write_text(fm + body + "\n", encoding="utf-8")
    (OUT / "last.json").write_text(json.dumps({"id": idea["id"], "title": title, "slug": slug, "labels": labels, "check": check,
                                              "model": model, "url": f"{SITE_URL}/{slug}/", "file": str(target / f"{slug}.html")}), encoding="utf-8")
    print(f"wrote {target / (slug + '.html')} (idea #{idea['id']}, model {model})")

def notify():
    f = OUT / "last.json"
    if not f.exists(): print("nothing to notify"); return
    m = json.loads(f.read_text(encoding="utf-8"))
    text = (f"Blog #{m['id']} is published\n\n{m['title']}\n{m['url']}\n\nLabels: {', '.join(m['labels'])}\n"
            f"It goes live in about 1-2 minutes, after Cloudflare finishes deploying.\n\n{m['check']}")[:3900]
    if DRY: print(text); return
    tg("sendMessage", {"chat_id": TG_CHAT, "text": text})
    tg("sendDocument", {"chat_id": TG_CHAT, "caption": "Backup copy of the post file (edit it in content/posts if you want to change anything)"},
       {"document": (f"{m['slug']}.html", Path(m["file"]).read_bytes())})

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "generate"
    {"generate": generate, "notify": notify}[mode]()
