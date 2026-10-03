# English Squad Placement Test

Streamlit app: adaptive grammar / vocabulary / reading placement (A1.1 to C2.3). No paid APIs.

| File | Purpose |
|---|---|
| `app.py` | Student test + teacher area |
| `scoring.py` | **All adaptive and placement rules (edit constants here)** |
| `storage.py` | Google Sheets storage, with local fallback in `data/` |
| `questions.json` | Sample bank (36 questions). `make_bank.py` regenerates it |

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
Students: the main URL. Teachers: add `?page=teacher` to the URL. With no secrets set, results and edited questions are saved in `data/` and the temporary teacher password is `teacher123`.

## How it works
- Starts at A1.1. Asks blocks of 3 questions per sublevel; 2 of 3 correct moves up. A failed block repeats once, then the test ends.
- 4 wrong answers in a row ends the test. Also ends at 60 minutes, 72 questions, or after C2.3.
- Placement = the **highest sublevel** where accuracy at that sublevel is at least 60% (min. 2 answers) and accuracy over that sublevel and the two below is also at least 60%. Skill levels use the same rule per skill (50%, min. 1 answer), kept within 2 sublevels of overall.
- Questions are random, balanced across skills, and avoid anything the same WhatsApp number has seen, when enough alternatives exist. If a sublevel runs out, the nearest sublevel is used.

## Question bank format
JSON: list of `{id, skill, level, question, options[4], answer, explanation, passage}`. CSV columns: `id,skill,level,question,option_a,option_b,option_c,option_d,answer,explanation,passage`.
`answer` must exactly equal one option. `skill` is Grammar, Vocabulary or Reading; `passage` is optional (Reading). **Aim for at least 4 questions per skill per sublevel** (the sample has about 2 per sublevel) so adaptivity and retakes work well.

## Google Sheets (free persistent storage)
1. Go to console.cloud.google.com, create a project, enable **Google Sheets API** and **Google Drive API**.
2. IAM & Admin → Service Accounts → create one → Keys → Add key → JSON. Download it.
3. Create a Google Sheet. Click Share and give the service account's `client_email` **Editor** access.
4. Copy the Sheet ID from its URL (`docs.google.com/spreadsheets/d/<SHEET_ID>/edit`).
5. Add secrets (locally in `.streamlit/secrets.toml`, never commit; on Streamlit Cloud under App → Settings → Secrets):
```toml
TEACHER_PASSWORD = "choose-a-strong-password"
SHEET_ID = "your-sheet-id"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```
Tabs `results` and `questions` are created automatically. The Teacher area shows which storage is active. Once the `questions` tab has rows, it is the source of truth for the bank.

## Free public deployment (Streamlit Community Cloud)
1. Push this folder to a GitHub repo (`data/` and secrets are git-ignored).
2. Go to share.streamlit.io → New app → pick the repo, branch, main file `app.py`.
3. Advanced settings → Secrets → paste the TOML above. Deploy.
4. Share `https://<your-app>.streamlit.app` on WhatsApp. Teacher area: `https://<your-app>.streamlit.app/?page=teacher`.

Without Google Sheets, Streamlit Cloud wipes local files on restart, so configure Sheets before real use.
