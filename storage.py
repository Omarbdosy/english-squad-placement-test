import json, os, uuid
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
DATA = HERE / "data"
DATA.mkdir(exist_ok=True)
BANK_COLS = ["id","skill","level","type","question","option_a","option_b","option_c","option_d","answer","explanation","passage","source","image_data"]
RESULT_COLS = ["timestamp","name","whatsapp","overall","grammar","vocabulary","reading","answered","duration_sec","question_ids"]


def secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


@st.cache_resource
def _book():
    try:
        import gspread
        sa, sid = secret("gcp_service_account"), secret("SHEET_ID")
        if not sa or not sid:
            return None
        return gspread.service_account_from_dict(dict(sa)).open_by_key(sid)
    except Exception:
        return None


def backend_name():
    return "Google Sheets" if _book() else "Local files (temporary on Streamlit Cloud)"


def _ws(name, cols):
    b = _book()
    if not b:
        return None
    try:
        ws = b.worksheet(name)
    except Exception:
        ws = b.add_worksheet(name, rows=2000, cols=len(cols))
        ws.append_row(cols)
    return ws


def normalize(rows):
    recs = rows.to_dict("records") if isinstance(rows, pd.DataFrame) else rows
    out = []
    for r0 in recs:
        r = dict(r0)
        opts = r.pop("options", None) or []
        for i, o in enumerate(opts[:4]):
            r[f"option_{'abcd'[i]}"] = o
        out.append({c: ("" if r.get(c) is None else str(r.get(c)).strip()) for c in BANK_COLS})
    df = pd.DataFrame(out, columns=BANK_COLS)
    if not df.empty:
        blank = df["id"] == ""
        if blank.any():
            df.loc[blank, "id"] = ["Q" + uuid.uuid4().hex[:8] for _ in range(int(blank.sum()))]
    return df


def validate(df):
    import scoring as sc
    errs = []
    if df.empty:
        return ["Question bank is empty."]
    if df["id"].duplicated().any():
        errs.append("Duplicate question IDs.")
    allowed_types = {
        "Grammar": {"grammar_mcq"},
        "Vocabulary": {"vocab_context","vocab_definition","vocab_synonym","vocab_odd_one_out","vocab_picture","vocab_mcq"},
        "Reading": {"reading_main_idea","reading_detail","reading_inference","reading_mcq"},
    }
    for _, r in df.iterrows():
        opts = [r[f"option_{c}"] for c in "abcd"]
        p = f"Question {r['id']}: "
        if not r["question"]: errs.append(p + "empty question.")
        if r["skill"] not in sc.SKILLS: errs.append(p + f"invalid skill: {r['skill']}.")
        if r["level"] not in sc.LEVELS: errs.append(p + f"invalid sublevel: {r['level']}.")
        if r["skill"] in allowed_types and r["type"] not in allowed_types[r["skill"]]: errs.append(p + f"invalid type {r['type']} for {r['skill']}.")
        if "" in opts or len(set(opts)) < 4: errs.append(p + "needs 4 different non-empty options.")
        if r["answer"] not in opts: errs.append(p + "answer must exactly match an option.")
        if r["skill"] == "Reading" and not r["passage"]: errs.append(p + "reading question needs a passage.")
        if r["type"] == "vocab_picture" and not r["image_data"]: errs.append(p + "picture question needs image data.")
    return errs


def to_records(df):
    out = []
    for r in df.to_dict("records"):
        x = dict(r)
        x["options"] = [x.pop(f"option_{c}") for c in "abcd"]
        out.append(x)
    return out


def load_bank():
    if _book():
        recs = _ws("questions", BANK_COLS).get_all_records(numericise_ignore=["all"])
        if recs:
            return normalize(recs)
    local = DATA / "questions_local.json"
    path = local if local.exists() else HERE / "questions.json"
    return normalize(json.loads(path.read_text(encoding="utf-8")))


def save_bank(df):
    (DATA / "questions_local.json").write_text(json.dumps(to_records(df), ensure_ascii=False, indent=2), encoding="utf-8")
    if _book():
        ws = _ws("questions", BANK_COLS)
        ws.clear(); ws.update([BANK_COLS] + df[BANK_COLS].values.tolist(), value_input_option="RAW")


def save_result(row):
    vals = [row[c] for c in RESULT_COLS]
    if _book():
        _ws("results", RESULT_COLS).append_row(vals, value_input_option="RAW")
    else:
        p = DATA / "results.csv"
        pd.DataFrame([vals], columns=RESULT_COLS).to_csv(p, mode="a", header=not p.exists(), index=False)


def load_results():
    if _book():
        recs = _ws("results", RESULT_COLS).get_all_records(numericise_ignore=["all"])
        return pd.DataFrame(recs, columns=RESULT_COLS)
    p = DATA / "results.csv"
    return pd.read_csv(p, dtype=str).fillna("") if p.exists() else pd.DataFrame(columns=RESULT_COLS)


def has_completed_test(digits):
    """Return True when this normalized phone number already has a saved result."""
    df = load_results()
    if df.empty or "whatsapp" not in df.columns:
        return False
    cleaned = df["whatsapp"].astype(str).str.replace(r"\D", "", regex=True)
    return bool((cleaned == str(digits)).any())


def used_ids(digits):
    df = load_results(); ids=set()
    if df.empty: return ids
    for _, r in df[df["whatsapp"].str.replace(r"\D", "", regex=True) == digits].iterrows():
        ids |= {x for x in str(r["question_ids"]).split(",") if x}
    return ids
