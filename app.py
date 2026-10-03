import base64
import html
import hmac
import os
import random
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import scoring as sc
import storage as store

st.set_page_config(page_title="English Squad Placement Test", page_icon="📘", layout="centered")
st.set_option("client.toolbarMode", "viewer")

ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
S = st.session_state

st.markdown(
    """
<style>
:root{
  --es-purple:#7A32C9;
  --es-violet:#A04CFF;
  --es-magenta:#C8327A;
  --es-bg:#0E0A14;
  --es-panel:#15101C;
  --es-panel-2:#1B1424;
  --es-text:#FAF7FF;
  --es-muted:#C9C0D2;
}
html,body,[data-testid=stAppViewContainer],[data-testid=stHeader]{background:var(--es-bg)!important;color:var(--es-text)!important}
[data-testid=stSidebar]{background:var(--es-panel)!important}
[data-testid=stMarkdownContainer], [data-testid=stText], p, label, .stCaption, .stTextInput label, .stRadio label{color:var(--es-text)!important}
.block-container{max-width:760px;padding-top:3.6rem;padding-bottom:3rem}
.brand-line{height:4px;border-radius:999px;background:linear-gradient(90deg,var(--es-purple),var(--es-magenta));margin:0 0 1.1rem}
.timer-card{
  width:88%;max-width:640px;box-sizing:border-box;text-align:center;font-weight:900;padding:1rem .8rem;margin:0 auto 1.5rem;
  background:linear-gradient(180deg,#100B16,#171020)!important;color:var(--es-text)!important;
  border:2px solid var(--es-purple)!important;border-top-color:var(--es-violet)!important;border-radius:16px;
  box-shadow:0 10px 30px rgba(0,0,0,.34),0 0 24px rgba(122,50,201,.12);
}
.timer-card span{display:block;font-size:.76rem;letter-spacing:.23em;margin-bottom:.28rem;color:#E4D8EE!important}
.timer-card strong{display:block;font-size:2.5rem;line-height:1.02;letter-spacing:.08em;color:#fff!important}
.timer-card{position:relative;z-index:1}
.timer-card.warn{border-color:var(--es-magenta)!important}
.stForm, [data-testid=stForm]{background:var(--es-panel)!important;border:1px solid #35233F!important;border-radius:16px!important;padding:1rem!important}
[data-baseweb=base-input], [data-baseweb=select], textarea{background:#100B15!important;color:#fff!important;border-color:#4A3158!important}
[data-baseweb=base-input] input{color:#fff!important}
button[kind=primary]{background:linear-gradient(90deg,var(--es-purple),var(--es-magenta))!important;border:0!important;color:#fff!important}
button[kind=primary]:disabled{opacity:.26!important;cursor:not-allowed!important;box-shadow:none!important;filter:saturate(.7)!important}
button[kind=primary]:not(:disabled){position:relative;isolation:isolate;box-shadow:0 8px 24px rgba(122,50,201,.20)!important}
@keyframes esBorderTravel{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes esGlowPulse{0%,100%{opacity:.72}50%{opacity:1}}
button{border-color:#4A3158!important;color:#fff!important;background:#17111D!important}
.stRadio>div{gap:.55rem}
.stRadio div[role=radiogroup]>label{background:#17111D!important;border:1px solid #34233F!important;border-radius:10px!important;padding:.42rem .55rem!important;margin-bottom:.22rem!important}
.passage{background:#120D17!important;border-left:4px solid var(--es-purple)!important;padding:1rem 1.05rem;border-radius:9px;margin-bottom:.95rem;line-height:1.7;color:#fff!important;border-top:1px solid #281B31}
.lvl{border-radius:16px;padding:1.4rem;text-align:center;margin:1rem 0;border:1px solid var(--es-purple);background:linear-gradient(180deg,#17101F,#100C15)!important;color:#fff!important;box-shadow:0 12px 26px rgba(0,0,0,.25)}
.lvl b{font-size:2.8rem;display:block;margin-top:.2rem;color:#fff!important}
.feedback{border:1px solid #3B2846;border-radius:14px;padding:1rem;margin-top:.8rem;background:var(--es-panel)!important;color:#fff!important}
[data-testid=stMetricValue], [data-testid=stMetricLabel]{color:#fff!important}
.stAlert{background:#19121F!important;color:#fff!important}
.small-note{font-size:.9rem;color:var(--es-muted)!important}
footer,#MainMenu{visibility:hidden}
@media(max-width:640px){
  .block-container{padding-left:.7rem;padding-right:.7rem;padding-top:2.2rem}
  .timer-card{padding:.85rem .65rem;margin:.85rem auto 1.25rem}
  .timer-card span{font-size:.7rem}
  .timer-card strong{font-size:2.05rem}
  .brand-line{margin-bottom:.85rem}
}
</style>
""",
    unsafe_allow_html=True,
)


@st.fragment(run_every=1)
def show_timer():
    if "started" not in S:
        return
    remaining = max(0, int(S.started + sc.MAX_MINUTES * 60 - time.time()))
    mins, secs = divmod(remaining, 60)
    timer_cls = "timer-card warn" if remaining <= 5 * 60 else "timer-card"
    st.markdown(
        f"<div class='{timer_cls}'>⏱ <span>TIME REMAINING</span><strong>{mins:02d}:{secs:02d}</strong></div>",
        unsafe_allow_html=True,
    )
    if remaining <= 0:
        S.stage = "done"
        st.rerun()


def start():
    st.markdown("<div class='brand-line'></div>", unsafe_allow_html=True)
    st.title("English Squad Placement Test")
    st.write("Grammar, vocabulary and reading. Up to 30 minutes. Every answer is final.")
    with st.form("start"):
        name = st.text_input("Full name")
        phone = st.text_input("WhatsApp number", placeholder="+20 100 000 0000")
        go = st.form_submit_button("Start the test", type="primary", use_container_width=True)
    if not go:
        return
    digits = "".join(c for c in phone if c.isdigit())
    if len(name.strip()) < 3 or len(digits) < 8:
        st.error("Enter your full name and a valid WhatsApp number.")
        return

    bank = store.load_bank().to_dict("records")
    errs = store.validate(store.normalize(bank))
    if errs:
        st.error("Question bank needs attention before this test can start.")
        st.code("\n".join(errs[:10]))
        return

    S.update(
        stage="test",
        name=name.strip(),
        phone="+" + digits,
        digits=digits,
        started=time.time(),
        history=[],
        cur=None,
        bank=bank,
        prior=store.used_ids(digits),
        save_error=None,
        finish_reason="completed",
        current_level=0,
        res=None,
    )
    st.rerun()


def pick_level(level):
    """Select 2 questions per skill, preferably with different question types; freeze option order."""
    used = {h["id"] for h in S.history}
    prior = S.prior
    candidates = [q for q in S.bank if q["level"] == sc.LEVELS[level] and q["id"] not in used]
    selected = []

    for skill in sc.SKILLS:
        pool = [q for q in candidates if q["skill"] == skill and q["id"] not in prior]
        if len(pool) < 2:
            pool = [q for q in candidates if q["skill"] == skill]
        if not pool:
            continue

        by_type = {}
        for q in pool:
            by_type.setdefault(q.get("type", "mcq"), []).append(q)
        types = list(by_type)
        random.shuffle(types)
        chosen = []
        for typ in types:
            if len(chosen) >= 2:
                break
            chosen.append(random.choice(by_type[typ]))
        remaining = [q for q in pool if q["id"] not in {x["id"] for x in chosen}]
        while len(chosen) < 2 and remaining:
            q = random.choice(remaining)
            chosen.append(q)
            remaining = [x for x in remaining if x["id"] != q["id"]]
        selected.extend(chosen[:2])

    for q in selected:
        opts = [q.get(f"option_{c}", "") for c in "abcd"]
        q["display_options"] = random.sample(opts, len(opts))
    random.shuffle(selected)
    return selected[:sc.QUESTIONS_PER_LEVEL]


def finish(reason=None):
    S.finish_reason = reason or S.get("finish_reason", "completed")
    dur = int(min(time.time() - S.started, sc.MAX_MINUTES * 60))
    S.res = sc.summarize(S.history)
    try:
        store.save_result(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": S.name,
                "whatsapp": S.phone,
                "overall": S.res["overall"],
                "grammar": S.res["Grammar"],
                "vocabulary": S.res["Vocabulary"],
                "reading": S.res["Reading"],
                "answered": len(S.history),
                "duration_sec": dur,
                "question_ids": ",".join(h["id"] for h in S.history),
            }
        )
    except Exception as e:
        S.save_error = str(e)
    S.stage = "done"
    st.rerun()


def test_page():
    if time.time() - S.started >= sc.MAX_MINUTES * 60:
        return finish("time_limit")

    level = S.current_level
    if S.cur is None:
        step = sc.next_step(S.history)
        if step[0] == "stop":
            return finish(step[1])
        level = step[1]
        S.current_level = level
        S.cur = pick_level(level)
        if not S.cur:
            return finish("no_questions")

    q = S.cur[0]
    show_timer()
    st.caption(f"Question {len(S.history)+1} of up to {sc.MAX_QUESTIONS} · {q['skill']}")

    if q.get("image_data"):
        raw = q["image_data"]
        if "," in raw:
            st.image(base64.b64decode(raw.split(",",1)[1]), width=360)
    if q.get("passage"):
        st.markdown(f"<div class='passage'>{html.escape(q['passage'])}</div>", unsafe_allow_html=True)

    st.subheader(q["question"])
    opts = q["display_options"]
    choice = st.radio("Answer", opts, index=None, key=f"q_{len(S.history)}", label_visibility="collapsed")

    if choice is not None:
        st.markdown(
            """
            <style>
            /* Traveling border light inspired by the supplied CapCut reference.
               Only appears after the student selects an answer. */
            div.stButton > button[kind="primary"]:not(:disabled){
                box-shadow:0 0 0 1px rgba(160,76,255,.25),0 8px 24px rgba(122,50,201,.22)!important;
                animation:esGlowPulse 1.65s ease-in-out infinite;
            }
            div.stButton > button[kind="primary"]:not(:disabled)::before{
                content:"";position:absolute;inset:-3px;border-radius:inherit;padding:2px;
                background:conic-gradient(
                    from 0deg,
                    transparent 0deg,transparent 300deg,
                    rgba(160,76,255,.10) 320deg,
                    rgba(255,255,255,.98) 334deg,
                    rgba(200,50,122,.95) 344deg,
                    rgba(160,76,255,.45) 352deg,
                    transparent 360deg
                );
                -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);
                -webkit-mask-composite:xor;mask-composite:exclude;
                animation:esBorderTravel 1.2s linear infinite;
                pointer-events:none;z-index:-1;
                filter:drop-shadow(0 0 5px rgba(160,76,255,.95)) drop-shadow(0 0 10px rgba(200,50,122,.65));
            }
            div.stButton > button[kind="primary"]:not(:disabled)::after{
                content:"";position:absolute;inset:-6px;border-radius:inherit;
                background:conic-gradient(from 0deg,transparent 0deg 325deg,rgba(160,76,255,.34) 339deg,rgba(255,255,255,.55) 347deg,transparent 356deg 360deg);
                animation:esBorderTravel 1.2s linear infinite;
                filter:blur(6px);opacity:.45;z-index:-2;pointer-events:none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Confirm answer", type="primary", disabled=choice is None, use_container_width=True):
        S.history.append(
            {
                "id": q["id"],
                "skill": q["skill"],
                "level": q["level"],
                "correct": choice == q["answer"],
            }
        )
        S.cur.pop(0)
        if not S.cur:
            S.cur = None
        st.rerun()

    st.caption("Your answer is final. You cannot go back.")
    st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
    if st.button("This is too hard — I give up", use_container_width=True):
        finish("gave_up")


LEVEL_FEEDBACK = {
    "A1": {
        "title": "You’re building a strong foundation! 😊",
        "grammar": "You can use very basic sentence patterns. Improve next by practising am/is/are, present simple, basic word order, pronouns and articles.",
        "vocabulary": "You can handle familiar everyday words. Improve next by expanding core vocabulary for people, home, food, places and daily routines, and learning words in context.",
        "reading": "You can understand very short, simple texts and familiar information. Improve next by reading short messages, notices, descriptions and simple stories.",
    },
    "A2": {
        "title": "Well done! You can handle familiar English. 😊",
        "grammar": "You can use common grammar for everyday situations. Improve next by strengthening past forms, present perfect, comparatives, quantifiers and basic modals.",
        "vocabulary": "You have useful everyday vocabulary. Improve next by learning more collocations, common word families and words in short contexts instead of isolated definitions.",
        "reading": "You can understand straightforward texts about familiar topics. Improve next by reading longer everyday texts and checking meaning from the whole text, not single words.",
    },
    "B1": {
        "title": "Great job! You’re working with independent English. 😊",
        "grammar": "You can handle a useful range of grammar. Improve next by working on perfect forms, conditionals, reported speech, linking ideas and accuracy in longer sentences.",
        "vocabulary": "You can discuss familiar topics with a useful range of words. Improve next by building collocations, phrasal verbs, word families and more precise alternatives.",
        "reading": "You can understand the main ideas and important details in straightforward texts. Improve next by reading longer articles and answering inference questions from the whole text.",
    },
    "B2": {
        "title": "Excellent! You’re handling a wide range of English. 😊",
        "grammar": "You have good control of complex grammar. Improve next by refining tense contrasts, passives, relative clauses, gerunds/infinitives, modals and sentence-level accuracy.",
        "vocabulary": "You have a wide working vocabulary. Improve next by focusing on precision, collocation, register, word choice and subtle differences between near-synonyms.",
        "reading": "You can understand longer texts and some abstract ideas. Improve next by reading demanding articles, identifying implied meaning and following arguments across paragraphs.",
    },
    "C1": {
        "title": "Fantastic! You’re operating at an advanced level. 😊",
        "grammar": "You show strong grammatical control. Improve next by refining complex structures, inversion, emphasis, clause relationships, prepositions and fine distinctions in meaning.",
        "vocabulary": "You have a broad vocabulary. Improve next by developing precision, collocation, register, idiomaticity and nuanced choices between similar words.",
        "reading": "You can understand complex social, academic and professional texts, including implied meaning. Improve next by reading dense texts and tracking stance, nuance and argument structure.",
    },
    "C2": {
        "title": "Outstanding! You’re working with highly advanced English. 🌟",
        "grammar": "You show very strong control of complex language. Improve next by refining nuance, emphasis, register and the smallest differences between possible structures.",
        "vocabulary": "You can work with a very broad vocabulary. Improve next by refining nuance, idiomaticity, collocation and highly precise word choice.",
        "reading": "You can understand very demanding texts and subtle ideas. Improve next by reading widely across academic, professional and literary material and analysing tone and implication.",
    },
}


def done():
    st.markdown("<div class='brand-line'></div>", unsafe_allow_html=True)
    r = S.res
    band = r["overall"].split(".")[0]
    fb = LEVEL_FEEDBACK[band]
    st.title("Test complete")
    st.markdown(
        f"<div class='lvl'>Your English level<b>{html.escape(r['overall'])}</b></div>",
        unsafe_allow_html=True,
    )
    st.success(fb["title"])

    cols = st.columns(3)
    for c, skill in zip(cols, sc.SKILLS):
        c.metric(skill, r[skill])

    st.markdown("### What you need to focus on next")
    for skill in sc.SKILLS:
        below = sc.level_index(r[skill]) < sc.level_index(r["overall"])
        if below:
            lead = "This is currently below your overall placement. "
        else:
            lead = "To move to a higher level, "
        key = skill.lower()
        st.markdown(
            f"<div class='feedback'><strong>{skill}</strong><br>{lead}{html.escape(fb[key])}</div>",
            unsafe_allow_html=True,
        )

    st.write("😊 Well done! Your teacher will contact you on WhatsApp.")
    if S.save_error:
        st.warning("Your result could not be saved. Please send your teacher a screenshot of this page.")
    if st.button("Take the test again", use_container_width=True):
        S.clear()
        st.rerun()


def results_tab():
    df = store.load_results()
    if df.empty:
        st.info("No results have been saved yet.")
        return
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["attempt"] = df.groupby("whatsapp").cumcount() + 1
    hist = df.groupby("whatsapp")["overall"].apply(lambda s: " → ".join(s))
    df["retake_history"] = df["whatsapp"].map(hist)
    df["duration"] = pd.to_numeric(df["duration_sec"], errors="coerce").fillna(0).astype(int).map(lambda s: f"{s//60}m {s%60:02d}s")
    show = df.drop(columns=["question_ids", "duration_sec"]).iloc[::-1]
    term = st.text_input("Search name or number")
    if term:
        show = show[show["name"].str.contains(term, case=False, na=False) | show["whatsapp"].str.contains(term, na=False)]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.download_button("Download results CSV", show.to_csv(index=False), "results.csv", "text/csv", use_container_width=True)


def bank_tab():
    bank = store.load_bank()
    st.caption(f"Current bank: {len(bank)} questions · target: 12 per sublevel")
    up = st.file_uploader("Upload JSON/CSV", type=["json", "csv"])
    mode = st.radio("Import mode", ["Add", "Replace"], horizontal=True)
    if up and st.button("Import question bank", type="primary"):
        try:
            import json
            new = store.normalize(json.load(up) if up.name.endswith("json") else pd.read_csv(up, dtype=str).fillna(""))
            merged = new if mode == "Replace" else pd.concat([bank, new]).drop_duplicates("id", keep="last")
            errs = store.validate(merged)
            if errs:
                st.error("\n\n".join(errs[:10]))
            else:
                store.save_bank(merged)
                st.success(f"Saved {len(merged)} questions.")
                st.rerun()
        except Exception as e:
            st.error(f"Could not import: {e}")
    sk = st.multiselect("Skill", sc.SKILLS)
    lv = st.multiselect("Sublevel", sc.LEVELS)
    sub = bank[(bank["skill"].isin(sk) if sk else True) & (bank["level"].isin(lv) if lv else True)]
    ed = st.data_editor(sub, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("Save edited bank"):
        new = pd.concat([bank[~bank["id"].isin(sub["id"])], store.normalize(ed)])
        errs = store.validate(new)
        if errs:
            st.error("\n\n".join(errs[:10]))
        else:
            store.save_bank(new)
            st.success("Saved.")
            st.rerun()


def teacher():
    st.markdown("<div class='brand-line'></div>", unsafe_allow_html=True)
    st.title("Teacher area")
    pw = store.secret("TEACHER_PASSWORD")
    if not pw:
        st.error("Teacher access is not configured yet.")
        st.write("Set TEACHER_PASSWORD in Streamlit Secrets, then reopen this page.")
        return
    if not S.get("auth"):
        entered = st.text_input("Teacher password", type="password")
        if st.button("Sign in", type="primary"):
            if hmac.compare_digest(entered, pw):
                S.auth = True
                st.rerun()
            st.error("Wrong password.")
        return
    st.caption("Storage: " + store.backend_name())
    a,b = st.tabs(["Results", "Question bank"])
    with a: results_tab()
    with b: bank_tab()


if st.query_params.get("page") == "teacher":
    teacher()
else:
    S.setdefault("stage", "start")
    {"start": start, "test": test_page, "done": done}[S.stage]()
