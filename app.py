import hmac, html, random, time
from datetime import datetime
import pandas as pd
import streamlit as st
import scoring as sc
import storage as store

st.set_page_config(page_title="English Squad Placement Test", page_icon="📘", layout="centered")
st.markdown("""
<style>
.block-container{max-width:720px;padding-top:1.2rem}
.timer{font-weight:700;font-size:1.1rem;text-align:right}
.lvl{border-radius:16px;padding:1.4rem;text-align:center;margin:1rem 0;border:1px solid #d5dee6}
.lvl b{font-size:2.7rem;display:block}
.passage{border-left:4px solid #1B4965;padding:.9rem 1rem;border-radius:6px;margin-bottom:.9rem}
footer,#MainMenu{visibility:hidden}
</style>
""", unsafe_allow_html=True)
S=st.session_state


def start():
    st.title("English Squad Placement Test")
    st.write("Grammar, vocabulary and reading. Up to 60 minutes. Every answer is final.")
    with st.form("start"):
        name=st.text_input("Full name")
        phone=st.text_input("WhatsApp number",placeholder="+20 100 000 0000")
        go=st.form_submit_button("Start the test",type="primary",use_container_width=True)
    if not go:return
    digits="".join(c for c in phone if c.isdigit())
    if len(name.strip())<3 or len(digits)<8:
        st.error("Enter your full name and a valid WhatsApp number.");return
    bank=store.load_bank().to_dict("records")
    errs=store.validate(store.normalize(bank))
    if errs:
        st.error("Question bank needs attention before this test can start.")
        st.code("\n".join(errs[:10]));return
    S.update(stage="test",name=name.strip(),phone="+"+digits,digits=digits,started=time.time(),history=[],cur=None,bank=bank,prior=store.used_ids(digits),save_error=None,current_level=0)
    st.rerun()


def pick_level(level):
    used={h["id"] for h in S.history}
    prior=S.prior
    candidates=[q for q in S.bank if q["level"]==sc.LEVELS[level] and q["id"] not in used]
    if not candidates:return None
    # Prefer a balanced 2-per-skill block; within that, prefer questions never seen on this WhatsApp number.
    selected=[]
    for skill in sc.SKILLS:
        pool=[q for q in candidates if q["skill"]==skill and q["id"] not in prior]
        if len(pool)<2: pool=[q for q in candidates if q["skill"]==skill]
        if pool: selected.extend(random.sample(pool,min(2,len(pool))))
    random.shuffle(selected)
    return selected[:sc.QUESTIONS_PER_LEVEL]


@st.fragment(run_every=1)
def timer():
    left=int(S.started+sc.MAX_MINUTES*60-time.time())
    st.markdown(f"<div class='timer'>⏱ {max(0,left)//60:02d}:{max(0,left)%60:02d}</div>",unsafe_allow_html=True)
    if left<=0: st.rerun()


def finish():
    dur=int(min(time.time()-S.started,sc.MAX_MINUTES*60)); S.res=sc.summarize(S.history)
    try:
        store.save_result(dict(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),name=S.name,whatsapp=S.phone,
            overall=S.res["overall"],grammar=S.res["Grammar"],vocabulary=S.res["Vocabulary"],reading=S.res["Reading"],
            answered=len(S.history),duration_sec=dur,question_ids=",".join(h["id"] for h in S.history)))
    except Exception as e:S.save_error=str(e)
    S.stage="done"; st.rerun()


def test():
    if time.time()-S.started>=sc.MAX_MINUTES*60:return finish()
    level=S.current_level
    if S.cur is None:
        step=sc.next_step(S.history)
        if step[0]=="stop":return finish()
        level=step[1];S.current_level=level
        S.cur=pick_level(level)
        if not S.cur:return finish()
    q=S.cur[0]
    timer()
    st.caption(f"Question {len(S.history)+1} of up to {sc.MAX_QUESTIONS} · {q['skill']}")
    if q["passage"]:st.markdown(f"<div class='passage'>{html.escape(q['passage'])}</div>",unsafe_allow_html=True)
    st.subheader(q["question"])
    opts=[q.get(f"option_{c}", "") for c in "abcd"]
    choice=st.radio("Answer",random.sample(opts,4),index=None,key=f"q{len(S.history)}",label_visibility="collapsed")
    if st.button("Confirm answer",type="primary",disabled=choice is None,use_container_width=True):
        S.history.append(dict(id=q["id"],skill=q["skill"],level=q["level"],correct=choice==q["answer"]))
        S.cur.pop(0)
        if not S.cur:S.cur=None
        st.rerun()
    st.caption("Your answer is final. You cannot go back.")


def done():
    r=S.res; st.title("Test complete")
    st.markdown(f"<div class='lvl'>Your English level<b>{r['overall']}</b></div>",unsafe_allow_html=True)
    cols=st.columns(3)
    for c,s in zip(cols,sc.SKILLS): c.metric(s,r[s])
    st.write("Your teacher will contact you on WhatsApp.")
    if S.save_error:st.warning("The result was not saved. Please send your teacher a screenshot.")
    if st.button("Take the test again",use_container_width=True):S.clear();st.rerun()


def results_tab():
    df=store.load_results()
    if df.empty:st.info("No results yet.");return
    df=df.sort_values("timestamp").reset_index(drop=True); df["attempt"]=df.groupby("whatsapp").cumcount()+1
    hist=df.groupby("whatsapp")["overall"].apply(lambda s:" → ".join(s));df["retake_history"]=df["whatsapp"].map(hist)
    df["duration"]=pd.to_numeric(df["duration_sec"],errors="coerce").fillna(0).astype(int).map(lambda s:f"{s//60}m {s%60:02d}s")
    show=df.drop(columns=["question_ids","duration_sec"]).iloc[::-1]
    term=st.text_input("Search name or number")
    if term:show=show[show["name"].str.contains(term,case=False,na=False)|show["whatsapp"].str.contains(term,na=False)]
    st.dataframe(show,use_container_width=True,hide_index=True)
    st.download_button("Download results CSV",show.to_csv(index=False),"results.csv","text/csv",use_container_width=True)


def bank_tab():
    bank=store.load_bank()
    st.caption(f"Current bank: {len(bank)} questions · Target: 12 questions per sublevel (4 per skill).")
    up=st.file_uploader("Upload JSON/CSV",type=["json","csv"])
    mode=st.radio("Import",["Add","Replace"],horizontal=True)
    if up and st.button("Import question bank",type="primary"):
        try:
            import json
            new=store.normalize(json.load(up) if up.name.endswith("json") else pd.read_csv(up,dtype=str).fillna(""))
            merged=new if mode=="Replace" else pd.concat([bank,new]).drop_duplicates("id",keep="last")
            errs=store.validate(merged)
            if errs:st.error("\n\n".join(errs[:10]))
            else:store.save_bank(merged);st.success(f"Saved {len(merged)} questions.");st.rerun()
        except Exception as e:st.error(f"Could not import: {e}")
    sk=st.multiselect("Skill",sc.SKILLS);lv=st.multiselect("Sublevel",sc.LEVELS)
    sub=bank[(bank["skill"].isin(sk) if sk else True)&(bank["level"].isin(lv) if lv else True)]
    ed=st.data_editor(sub,num_rows="dynamic",use_container_width=True,hide_index=True)
    if st.button("Save edited bank"):
        new=pd.concat([bank[~bank["id"].isin(sub["id"])],store.normalize(ed)])
        errs=store.validate(new)
        if errs:st.error("\n\n".join(errs[:10]))
        else:store.save_bank(new);st.success("Saved.");st.rerun()


def teacher():
    st.title("Teacher area")
    pw=store.secret("TEACHER_PASSWORD")
    if not S.get("auth"):
        entered=st.text_input("Password",type="password")
        if st.button("Sign in",type="primary"):
            if hmac.compare_digest(entered,pw or "teacher123"):S.auth=True;st.rerun()
            st.error("Wrong password.")
        return
    st.caption("Storage: "+store.backend_name())
    a,b=st.tabs(["Results","Question bank"])
    with a:results_tab()
    with b:bank_tab()

if st.query_params.get("page")=="teacher":teacher()
else:
    S.setdefault("stage","start")
    {"start":start,"test":test,"done":done}[S.stage]()
