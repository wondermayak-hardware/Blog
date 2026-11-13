"""Builds ideas.json: 5000 unique blog ideas. Run once: python generate_ideas.py"""
import json, random

YEAR = 2027
random.seed(2026)

ENGLISH = ["Synonyms","Antonyms","One Word Substitution","Idioms and Phrases","Fill in the Blanks","Error Spotting",
"Reading Comprehension","Para Jumbles (Sentence Rearrangement)","Cloze Test","Active and Passive Voice","Direct and Indirect Speech",
"Tenses","Subject-Verb Agreement","Prepositions","Articles","Conjunctions","Phrasal Verbs","Spelling Correction","Vocabulary Building",
"Modal Verbs","Pronouns","Adjectives and Adverbs","Question Tags","Conditional Sentences","Gerunds and Participles","Determiners",
"Homophones and Homonyms","Sentence Improvement","Paragraph Completion","Narration Change","Literary Terms","Figures of Speech",
"Word Analogies","Foreign Words and Phrases","Punctuation","Transformation of Sentences","Unseen Passages","Verb Forms",
"Common Grammar Mistakes","Poetry Comprehension"]

GK = ["Indian History","Ancient India","Medieval India","Modern India","Freedom Movement","World History","Indian Geography",
"World Geography","Indian Rivers","Mountains and Plateaus of India","Indian Polity","Indian Constitution","Fundamental Rights and Duties",
"Parliament of India","President and Governor","Indian Judiciary","Indian Economy","Banking and Finance","Budget and Taxation",
"General Science","Physics Basics","Chemistry Basics","Biology Basics","Human Body","Space and ISRO","Environment and Ecology",
"National Parks and Wildlife","Awards and Honours","Books and Authors","Sports","Olympics and Asian Games","Important Days and Themes",
"Current Affairs","States and Capitals","Union Territories","National Symbols","Indian Art and Culture","Classical Dances",
"Folk Dances and Music","Festivals of India","Famous Personalities","Inventions and Discoveries","International Organizations",
"Currencies of the World","Countries and Capitals","Committees and Commissions","Wars and Treaties","UNESCO World Heritage Sites in India",
"Government Schemes","Computer and Technology Awareness","Static GK","Famous Places","Scientific Instruments",
"Abbreviations and Full Forms","Indian Railways and Transport","Agriculture in India","Ports and Industries","Indian Army and Defence",
"Famous Dams and Projects","Nobel Prize Winners"]

GENERAL = ["Quantitative Reasoning","Logical Reasoning","Number Series","Data Interpretation","Percentage Basics","Ratio and Proportion",
"Syllogism","Coding-Decoding","Blood Relations","Direction Sense"]

DOMAIN = ["Accountancy","Business Studies","Economics","Political Science","History","Geography","Psychology","Sociology","Physics",
"Chemistry","Mathematics","Biology","Computer Science","Home Science","Physical Education","Legal Studies","Entrepreneurship",
"Mass Media","Environmental Science","Hindi","Sanskrit","Fine Arts","Anthropology","Teaching Aptitude","Agriculture","Engineering Graphics"]

ideas = []
def add(title, typ, subject, topic, labels):
    ideas.append({"title": title, "type": typ, "subject": subject, "topic": topic, "labels": labels})

for subject, topics in (("English", ENGLISH), ("GK", GK), ("General Test", GENERAL)):
    base = ["CUET", subject, "Free Practice"]
    for t in topics:
        for k in range(1, 13):
            add(f"{t} Practice Set {k}: 10 Free MCQs with Answers for CUET {YEAR}", "questions", subject, t, base)
        for lvl in ("Easy", "Medium", "Hard"):
            for k in range(1, 7):
                add(f"{lvl} {t} Questions for CUET {YEAR} (Set {k}) with Answers", "questions", subject, t, base + [lvl])
        for d in (7, 15, 30):
            add(f"How to Prepare {t} for CUET {YEAR} in {d} Days", "guide", subject, t, ["CUET", subject, "Study Plan"])
        add(f"{t} Tricks and Shortcuts to Score Full Marks in CUET", "guide", subject, t, ["CUET", subject, "Tips"])
        add(f"Common Mistakes Students Make in {t} (and How to Fix Them)", "guide", subject, t, ["CUET", subject, "Tips"])
        add(f"Most Repeated {t} Questions in CUET: Free Practice", "questions", subject, t, base)
        add(f"{t} for CUET: Important Notes and Quick Revision Sheet", "guide", subject, t, ["CUET", subject, "Notes"])
        add(f"{t} Question Pattern in CUET: What to Expect", "guide", subject, t, ["CUET", subject, "Exam Pattern"])
        add(f"Free {t} Quiz for CUET: Test Yourself in 10 Minutes", "questions", subject, t, base)

for s in DOMAIN:
    lab = ["CUET", s]
    add(f"How to Study {s} for CUET {YEAR}: Complete Guide", "guide", s, s, lab + ["Study Plan"])
    add(f"{s} CUET Syllabus, Important Chapters and Weightage", "guide", s, s, lab + ["Syllabus"])
    add(f"{s} CUET 30-Day Preparation Plan", "guide", s, s, lab + ["Study Plan"])
    for k in range(1, 7):
        add(f"{s} CUET Practice Set {k}: Free MCQs with Answers", "questions", s, s, lab + ["Free Practice"])

for n in range(1, 251):
    add(f"CUET Daily GK Practice, Day {n}: 10 Questions with Answers", "questions", "GK", "Mixed GK", ["CUET", "GK", "Daily Practice"])
    add(f"CUET Daily English Practice, Day {n}: 10 Questions with Answers", "questions", "English", "Mixed English", ["CUET", "English", "Daily Practice"])
for n in range(1, 151):
    add(f"CUET General Test Daily Practice, Day {n}: 10 Questions with Answers", "questions", "General Test", "Mixed Reasoning", ["CUET", "General Test", "Daily Practice"])

seen, unique = set(), []
for i in ideas:
    k = i["title"].lower()
    if k not in seen:
        seen.add(k); unique.append(i)
random.shuffle(unique)
unique = unique[:5000]
assert len(unique) == 5000, f"only {len(unique)} ideas, add more topics"
for n, i in enumerate(unique):
    i["id"] = n + 1
json.dump(unique, open("ideas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ideas:", len(unique))
