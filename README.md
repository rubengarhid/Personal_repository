# CV vs LinkedIn Comparator

🎯 **Goal**: Compare CVs (PDF/DOCX) with exported LinkedIn profiles (PDF/DOCX) using free, locally-run AI tools and provide visual match scores.

## 🌟 Features

- ✅ **Dual File Upload**: Upload your CV and your LinkedIn profile export — no copy-pasting needed
- ✅ **CV Parsing**: Extract and structure text from PDF and DOCX files
- ✅ **LinkedIn PDF Parsing**: Dedicated parser that handles LinkedIn's exported PDF format and section headers
- ✅ **Semantic Comparison**: Local sentence transformers — no data leaves your machine
- ✅ **Section Analysis**: Compare Experience, Skills, and Education separately
- ✅ **Skills Detection**: Automatically identify and compare technical skills
- ✅ **Visual Results**: Interactive Streamlit interface with progress bars
- ✅ **Recommendations**: Actionable suggestions to improve consistency

## 🏗️ Architecture

```
CV_LINKEDIN_COMPARATOR/
├── backend/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── cv_parser.py          # PDF/DOCX extraction for CV and LinkedIn
│   ├── comparator.py         # Semantic similarity computation
│   └── main.py               # FastAPI REST API
├── frontend/
│   └── app.py                # Streamlit UI
├── test/
│   └── test_comparator.py    # Unit tests
├── start.bat                 # Windows startup script
├── start.sh                  # Linux/Mac startup script
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- 4 GB+ RAM (for the local sentence-transformer model)

### Installation

1. **Clone or download the project**

2. **Install backend dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

### Running the Application

#### Option 1: Using startup scripts

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

#### Option 2: Manual startup

**Terminal 1 — Backend:**
```bash
cd backend
python -m uvicorn main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`

### Running Tests

```bash
cd test
python test_comparator.py
```

## 📖 How to Use

1. **Start the application** (backend + frontend)
2. **Upload your CV** — PDF or DOCX format
3. **Export your LinkedIn profile**:
   - Go to your LinkedIn profile
   - Click **More** → **Save to PDF**
   - Upload the downloaded PDF in the second file uploader
4. **Click "🔍 Compare CV and LinkedIn"**
5. **Review results**:
   - Overall match score
   - Section-by-section breakdown
   - Skills comparison
   - Recommendations

## 🔍 API Endpoints

### `POST /compare`
Compare a CV with a LinkedIn profile export. Both inputs are uploaded files.

**Request (multipart/form-data):**
- `cv_file` — CV file (PDF or DOCX)
- `linkedin_file` — LinkedIn profile export (PDF or DOCX)

**Response:**
```json
{
  "success": true,
  "overall_score": 85.5,
  "section_scores": {
    "experience": 88.2,
    "skills": 82.5,
    "education": 86.0
  },
  "skills_comparison": {
    "common": ["Python", "JavaScript"],
    "cv_only": ["React"],
    "linkedin_only": ["Docker"],
    "match_rate": 66.7
  },
  "recommendations": [
    "✅ Excellent match! Your CV and LinkedIn profile are well aligned."
  ]
}
```

### `POST /parse-cv`
Parse a CV file only (testing/debugging endpoint).

**Request:** `cv_file` — CV file (PDF or DOCX)

### `POST /parse-linkedin`
Parse a LinkedIn profile export only (testing/debugging endpoint).

**Request:** `linkedin_file` — LinkedIn export (PDF or DOCX)

### `GET /health`
Health check — confirms the API and model are running.

## 🧠 Technology Stack

### Backend
- **FastAPI** — REST API framework
- **sentence-transformers** — local semantic similarity (`all-MiniLM-L6-v2`)
- **pdfplumber** — PDF text extraction
- **python-docx** — DOCX text extraction
- **scikit-learn** — cosine similarity computation

### Frontend
- **Streamlit** — interactive web UI
- **requests** — HTTP client for API calls

### Privacy
- ✅ **100% Local Processing** — all AI models run on your machine
- ✅ **No External API Calls** — no data sent to third parties
- ✅ **No Rate Limits** — process unlimited comparisons

## 📊 Score Interpretation

| Score | Meaning | Icon |
|-------|---------|------|
| 80–100% | Excellent match — profiles are well aligned | ✅ |
| 60–79%  | Good match — minor improvements suggested | ⚠️ |
| 0–59%   | Needs improvement — significant differences | ❌ |

## 🎯 Section Weights

The overall score is a weighted average of section scores:

| Section    | Weight |
|------------|--------|
| Experience | 40%    |
| Skills     | 35%    |
| Education  | 25%    |

## 🔧 Configuration

### Model Selection
Edit `backend/comparator.py` to use a different sentence-transformer model:
```python
comparator = CVLinkedInComparator(model_name='paraphrase-MiniLM-L6-v2')
```

Available models: [Sentence Transformers Hub](https://www.sbert.net/docs/pretrained_models.html)

### Section Weights
Edit weights in `backend/comparator.py`:
```python
self.section_weights = {
    'experience': 0.4,
    'skills': 0.35,
    'education': 0.25
}
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000   # Windows
lsof -i :8000                  # Linux/Mac
```

### Model download issues
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### PDF parsing errors
- Ensure the PDF is not password-protected
- Try converting to DOCX first
- Verify the PDF has selectable text (not a scanned image)

### LinkedIn PDF sections appear empty
- Export the **complete** profile PDF from LinkedIn (`More → Save to PDF`)
- Confirm the PDF contains selectable text by opening it and trying to highlight text manually

## 📝 Limitations

- **Parsing accuracy**: Works best with well-formatted documents that use clear section headers
- **Skills detection**: Based on a predefined keyword list (expandable in `cv_parser.py`)
- **Language**: Optimised for English; partial Spanish support included
- **File size**: Files over 10 MB may take longer to process
- **LinkedIn PDF format**: Results depend on the structure of the exported PDF; layout changes by LinkedIn may affect section detection

## 🚀 Future Enhancements

- [ ] Multi-language support
- [ ] Custom skill dictionaries
- [ ] Export comparison reports as PDF
- [ ] Batch processing
- [ ] Historical comparison tracking
- [ ] Integration with LinkedIn API
- [ ] Advanced NLP for better section detection

## 📄 License

MIT License — feel free to use and modify.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) — semantic similarity
- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [Streamlit](https://streamlit.io/) — UI framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF parsing

---

**Built with ❤️ for job seekers and professionals maintaining a consistent online presence**
