# ⚡ ResumeAI Parser — Hackathon Project

A powerful, zero-API-key resume parser built in pure Python with a sleek dark-mode web UI. Extracts structured data from PDF, DOCX, and TXT resumes using regex + NLP heuristics, and optionally enhances with spaCy.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional but recommended
```

### 2. Run the web app
```bash
python app.py
```
Then open **http://localhost:5000** in your browser.

### 3. CLI usage
```bash
# Parse a single file
python cli_parser.py sample_resume.txt

# Parse all resumes in a folder
python cli_parser.py resumes/ --out results/

# Output raw JSON
python cli_parser.py resume.pdf --format json
```

---

## 🧠 What It Extracts

| Field | Details |
|-------|---------|
| **Contact** | Name, Email, Phone, LinkedIn, GitHub |
| **Skills** | 100+ skills across 6 categories (Programming, Web, Data, ML/AI, Cloud, Soft) |
| **Experience** | Job titles, companies, dates, descriptions |
| **Education** | Degrees, institutions, years |
| **Projects** | Names, descriptions, tech stack |
| **Certifications** | Text extraction |
| **Summary** | Professional objective/summary |
| **Score** | 0–100 resume quality score |

---

## 📁 Project Structure

```
resume_parser/
├── app.py              # Flask web server
├── parser_engine.py    # Core parsing logic (regex + NLP)
├── cli_parser.py       # Command-line interface
├── requirements.txt    # Python dependencies
├── sample_resume.txt   # Test resume
├── templates/
│   └── index.html      # Web UI (single file, dark mode)
├── uploads/            # Temp upload dir (auto-cleaned)
└── parsed_results/     # Saved JSON outputs
```

---

## 🛠 Tech Stack

- **Backend**: Python, Flask
- **Parsing**: Regex, spaCy (NLP), pdfplumber, python-docx
- **Frontend**: Vanilla HTML/CSS/JS (zero dependencies, dark-mode)
- **CLI**: argparse + rich

---

## 📊 Scoring System

Resumes are scored 0–100 based on:
- Contact completeness (20 pts)
- Summary presence (10 pts)
- Skills breadth (25 pts)
- Experience entries (25 pts)
- Education (15 pts)
- Projects (5 pts)

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| POST | `/parse` | Upload file (multipart/form-data) |
| POST | `/parse_text` | Parse raw text (JSON body: `{text: "..."}`) |

### Example API call:
```bash
curl -X POST http://localhost:5000/parse_text \
  -H "Content-Type: application/json" \
  -d '{"text": "John Doe\njohn@email.com\n..."}'
```

---

## 🏆 Hackathon Extensions (Ideas)

- [ ] Job-Resume matching score using sentence-transformers
- [ ] Bulk CSV export of parsed fields
- [ ] Resume improvement suggestions
- [ ] ATS keyword checker
- [ ] Integration with LinkedIn/Indeed APIs

---

Built with ❤️ for hackathons. No API keys needed. Works offline.
