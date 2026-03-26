"""
Unit Tests for CV-LinkedIn Comparator
Tests parsing, comparison, and scoring functionality.
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

# Add backend directory to path so imports work when running from test/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from cv_parser import CVParser, parse_cv_from_bytes, parse_linkedin_from_bytes
from comparator import CVLinkedInComparator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes(text: str) -> bytes:
    """
    Create a minimal valid PDF in memory containing `text`.
    Used to test parse_*_from_bytes without real PDF files.
    Requires the `reportlab` package (optional dev dependency).
    Falls back to a pre-built minimal PDF stub if reportlab is unavailable.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        import io
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        y = 800
        for line in text.splitlines():
            c.drawString(40, y, line.strip())
            y -= 14
            if y < 40:
                c.showPage()
                y = 800
        c.save()
        return buf.getvalue()
    except ImportError:
        # Minimal valid single-page PDF stub (no real text layer, but parseable)
        return (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n"
            b"0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n"
        )


def _make_docx_bytes(text: str) -> bytes:
    """Create a minimal DOCX in memory containing `text`."""
    from docx import Document
    import io
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sample data shared across tests
# ---------------------------------------------------------------------------

SAMPLE_CV_TEXT = """
WORK EXPERIENCE
Senior Developer at Tech Corp (2020-2023)
Led team of 5 developers
Built scalable Python microservices

SKILLS
Python, JavaScript, React, AWS, Docker

EDUCATION
BS Computer Science, University XYZ (2016-2020)
"""

SAMPLE_LINKEDIN_TEXT = """
Experience
Senior Software Engineer at Tech Corp
Jan 2020 - Present
Led engineering team, built cloud-native applications with Python and FastAPI

Top Skills
Python, JavaScript, React, Docker, Kubernetes

Education
University XYZ
Bachelor of Science, Computer Science
2012 - 2016
"""


# ---------------------------------------------------------------------------
# TestCVParser
# ---------------------------------------------------------------------------

class TestCVParser(unittest.TestCase):
    """Test cases for CVParser."""

    def setUp(self):
        self.parser = CVParser()

    # --- _split_into_sections (CV mode) ---

    def test_split_into_sections_basic(self):
        sections = self.parser._split_into_sections(SAMPLE_CV_TEXT)

        self.assertIn('experience', sections)
        self.assertIn('skills', sections)
        self.assertIn('education', sections)
        self.assertIn('Senior Developer', sections['experience'])
        self.assertIn('Python', sections['skills'])
        self.assertIn('Computer Science', sections['education'])

    def test_experience_section_patterns(self):
        headers = [
            "WORK EXPERIENCE\nSenior Dev",
            "Professional Experience\nSenior Dev",
            "Employment History\nSenior Dev",
            "EXPERIENCIA LABORAL\nSenior Dev",
        ]
        for text in headers:
            sections = self.parser._split_into_sections(text)
            self.assertIn('Senior Dev', sections['experience'],
                          f"Experience header not recognised in: {text[:30]}")

    def test_skills_section_patterns(self):
        headers = [
            "SKILLS\nPython",
            "Technical Skills\nPython",
            "Competencies\nPython",
            "HABILIDADES\nPython",
        ]
        for text in headers:
            sections = self.parser._split_into_sections(text)
            self.assertIn('Python', sections['skills'],
                          f"Skills header not recognised in: {text[:30]}")

    def test_education_section_patterns(self):
        headers = [
            "EDUCATION\nBachelor",
            "Academic Background\nBachelor",
            "EDUCACIÓN\nBachelor",
        ]
        for text in headers:
            sections = self.parser._split_into_sections(text)
            self.assertIn('Bachelor', sections['education'],
                          f"Education header not recognised in: {text[:30]}")

    def test_unknown_content_goes_to_other(self):
        text = "Random intro line that has no section header"
        sections = self.parser._split_into_sections(text)
        self.assertIn('Random intro', sections['other'])

    # --- _split_into_sections (LinkedIn mode) ---

    def test_linkedin_mode_top_skills_header(self):
        """'Top Skills' must be recognised as a skills header in linkedin_mode."""
        text = "Top Skills\nPython\nDocker"
        sections = self.parser._split_into_sections(text, linkedin_mode=True)
        self.assertIn('Python', sections['skills'])

    def test_linkedin_mode_extra_headers_go_to_other(self):
        """LinkedIn-specific sections (Licenses, Volunteer…) must not bleed into main sections."""
        text = (
            "Experience\nSenior Dev at Corp\n"
            "Licenses & Certifications\nAWS Certified\n"
            "Education\nBS CS\n"
        )
        sections = self.parser._split_into_sections(text, linkedin_mode=True)
        self.assertNotIn('AWS Certified', sections['experience'])
        self.assertNotIn('AWS Certified', sections['skills'])
        self.assertNotIn('AWS Certified', sections['education'])

    # --- extract_skills ---

    def test_extract_skills_finds_known_keywords(self):
        text = "Experienced with Python, JavaScript, React, and AWS."
        skills = self.parser.extract_skills(text)
        self.assertIsInstance(skills, list)
        self.assertTrue(any('Python' in s for s in skills))
        self.assertTrue(any('Aws' in s or 'AWS' in s for s in skills))

    def test_extract_skills_empty_text(self):
        skills = self.parser.extract_skills("No technical content here at all.")
        self.assertIsInstance(skills, list)
        self.assertLessEqual(len(skills), 2)

    def test_extract_skills_no_duplicates(self):
        text = "Python Python Python"
        skills = self.parser.extract_skills(text)
        self.assertEqual(len(skills), len(set(skills)))

    # --- parse_cv_from_bytes ---

    def test_parse_cv_from_bytes_docx(self):
        docx_bytes = _make_docx_bytes(SAMPLE_CV_TEXT)
        result = parse_cv_from_bytes(docx_bytes, "cv.docx")

        self.assertIn('experience', result)
        self.assertIn('skills', result)
        self.assertIn('education', result)
        self.assertIn('extracted_skills', result)
        self.assertIsInstance(result['extracted_skills'], list)

    def test_parse_cv_from_bytes_unsupported_format(self):
        with self.assertRaises(Exception):
            parse_cv_from_bytes(b"dummy", "cv.txt")

    # --- parse_linkedin_from_bytes ---

    def test_parse_linkedin_from_bytes_docx(self):
        docx_bytes = _make_docx_bytes(SAMPLE_LINKEDIN_TEXT)
        result = parse_linkedin_from_bytes(docx_bytes, "linkedin.docx")

        self.assertIn('experience', result)
        self.assertIn('skills', result)
        self.assertIn('education', result)
        self.assertIn('extracted_skills', result)
        self.assertIsInstance(result['extracted_skills'], list)

    def test_parse_linkedin_from_bytes_unsupported_format(self):
        with self.assertRaises(Exception):
            parse_linkedin_from_bytes(b"dummy", "profile.csv")

    def test_parse_linkedin_result_has_same_keys_as_cv(self):
        """Both parsers must return dicts with identical top-level keys."""
        docx_cv = _make_docx_bytes(SAMPLE_CV_TEXT)
        docx_li = _make_docx_bytes(SAMPLE_LINKEDIN_TEXT)

        cv_result = parse_cv_from_bytes(docx_cv, "cv.docx")
        li_result = parse_linkedin_from_bytes(docx_li, "linkedin.docx")

        self.assertEqual(set(cv_result.keys()), set(li_result.keys()))


# ---------------------------------------------------------------------------
# TestComparator
# ---------------------------------------------------------------------------

class TestComparator(unittest.TestCase):
    """Test cases for CVLinkedInComparator."""

    def setUp(self):
        # Patch SentenceTransformer so the model is never actually loaded
        patcher = patch('comparator.SentenceTransformer')
        self.mock_st_cls = patcher.start()
        self.addCleanup(patcher.stop)

        mock_instance = MagicMock()
        mock_instance.encode.return_value = [[0.1] * 384, [0.1] * 384]
        self.mock_st_cls.return_value = mock_instance

        self.comparator = CVLinkedInComparator()

    # --- compute_similarity ---

    def test_compute_similarity_both_empty(self):
        self.assertEqual(self.comparator.compute_similarity("", ""), 0.0)

    def test_compute_similarity_one_empty(self):
        self.assertEqual(self.comparator.compute_similarity("", "text"), 0.0)
        self.assertEqual(self.comparator.compute_similarity("text", ""), 0.0)

    def test_compute_similarity_returns_float_in_range(self):
        self.comparator.model.encode.return_value = [
            [1.0] * 384,
            [0.9] * 384,
        ]
        score = self.comparator.compute_similarity("Python dev", "Senior Python engineer")
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    # --- calculate_score ---

    def test_calculate_score_returns_correct_structure(self):
        cv_data = {
            'experience': 'Senior Developer at Tech Corp',
            'skills': 'Python, JavaScript',
            'education': 'BS Computer Science',
            'extracted_skills': ['Python', 'JavaScript']
        }
        linkedin_data = {
            'experience': 'Senior Software Engineer at Tech Corp',
            'skills': 'Python, JavaScript, React',
            'education': 'Bachelor of Science in CS',
            'extracted_skills': ['Python', 'JavaScript', 'React']
        }

        result = self.comparator.calculate_score(cv_data, linkedin_data)

        for key in ('overall_score', 'section_scores', 'skills_comparison',
                    'discrepancies', 'weights'):
            self.assertIn(key, result)

        self.assertIsInstance(result['overall_score'], float)
        self.assertIsInstance(result['section_scores'], dict)
        self.assertIsInstance(result['skills_comparison'], dict)
        self.assertIsInstance(result['discrepancies'], list)

    def test_calculate_score_overall_in_range(self):
        data = {
            'experience': 'Dev',
            'skills': 'Python',
            'education': 'CS',
            'extracted_skills': ['Python']
        }
        result = self.comparator.calculate_score(data, data)
        self.assertGreaterEqual(result['overall_score'], 0.0)
        self.assertLessEqual(result['overall_score'], 100.0)

    def test_calculate_score_section_scores_present(self):
        data = {
            'experience': 'Dev', 'skills': 'Python',
            'education': 'CS', 'extracted_skills': []
        }
        result = self.comparator.calculate_score(data, data)
        for section in ('experience', 'skills', 'education'):
            self.assertIn(section, result['section_scores'])

    # --- skills comparison ---

    def test_skills_comparison_common_cv_only_linkedin_only(self):
        cv_data = {
            'experience': 'Dev', 'skills': 'S', 'education': 'E',
            'extracted_skills': ['Python', 'JavaScript', 'React']
        }
        linkedin_data = {
            'experience': 'Dev', 'skills': 'S', 'education': 'E',
            'extracted_skills': ['Python', 'JavaScript', 'Docker']
        }

        result = self.comparator.calculate_score(cv_data, linkedin_data)
        skills = result['skills_comparison']

        self.assertIn('Python', skills['common'])
        self.assertIn('JavaScript', skills['common'])
        self.assertIn('React', skills['cv_only'])
        self.assertIn('Docker', skills['linkedin_only'])

    def test_skills_match_rate_perfect(self):
        skills = ['Python', 'JavaScript']
        data = {
            'experience': '', 'skills': '', 'education': '',
            'extracted_skills': skills
        }
        result = self.comparator.calculate_score(data, data)
        self.assertEqual(result['skills_comparison']['match_rate'], 100.0)

    def test_skills_match_rate_no_overlap(self):
        cv_data = {
            'experience': '', 'skills': '', 'education': '',
            'extracted_skills': ['Python']
        }
        linkedin_data = {
            'experience': '', 'skills': '', 'education': '',
            'extracted_skills': ['Docker']
        }
        result = self.comparator.calculate_score(cv_data, linkedin_data)
        self.assertEqual(result['skills_comparison']['match_rate'], 0.0)

    # --- discrepancies ---

    def test_discrepancies_flagged_for_low_scores(self):
        """When model always returns 0 similarity, all sections should be flagged."""
        self.comparator.model.encode.return_value = [[0.0] * 384, [1.0] * 384]
        cv_data = {
            'experience': 'A', 'skills': 'B', 'education': 'C',
            'extracted_skills': []
        }
        linkedin_data = {
            'experience': 'X', 'skills': 'Y', 'education': 'Z',
            'extracted_skills': []
        }
        result = self.comparator.calculate_score(cv_data, linkedin_data)
        self.assertGreater(len(result['discrepancies']), 0)

    # --- get_recommendations ---

    def test_get_recommendations_returns_list(self):
        comparison_result = {
            'overall_score': 85.0,
            'section_scores': {'experience': 90.0, 'skills': 80.0, 'education': 85.0},
            'skills_comparison': {
                'common': ['Python'], 'cv_only': ['React'],
                'linkedin_only': ['Docker'], 'match_rate': 50.0
            }
        }
        recs = self.comparator.get_recommendations(comparison_result)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

    def test_get_recommendations_excellent_score(self):
        result = {
            'overall_score': 90.0,
            'section_scores': {'experience': 90.0, 'skills': 90.0, 'education': 90.0},
            'skills_comparison': {'common': ['Python'], 'cv_only': [], 'linkedin_only': [], 'match_rate': 100.0}
        }
        recs = self.comparator.get_recommendations(result)
        self.assertTrue(any('Excellent' in r or '✅' in r for r in recs))

    def test_get_recommendations_poor_score(self):
        result = {
            'overall_score': 30.0,
            'section_scores': {'experience': 20.0, 'skills': 30.0, 'education': 40.0},
            'skills_comparison': {'common': [], 'cv_only': ['Python'], 'linkedin_only': ['Docker'], 'match_rate': 0.0}
        }
        recs = self.comparator.get_recommendations(result)
        self.assertTrue(any('❌' in r or 'differences' in r for r in recs))

    def test_get_recommendations_cv_only_skills_mentioned(self):
        result = {
            'overall_score': 70.0,
            'section_scores': {'experience': 70.0, 'skills': 70.0, 'education': 70.0},
            'skills_comparison': {
                'common': [], 'cv_only': ['React', 'Django'],
                'linkedin_only': [], 'match_rate': 0.0
            }
        }
        recs = self.comparator.get_recommendations(result)
        self.assertTrue(any('LinkedIn' in r for r in recs))

    def test_get_recommendations_linkedin_only_skills_mentioned(self):
        result = {
            'overall_score': 70.0,
            'section_scores': {'experience': 70.0, 'skills': 70.0, 'education': 70.0},
            'skills_comparison': {
                'common': [], 'cv_only': [],
                'linkedin_only': ['Docker', 'Kubernetes'], 'match_rate': 0.0
            }
        }
        recs = self.comparator.get_recommendations(result)
        self.assertTrue(any('CV' in r for r in recs))


# ---------------------------------------------------------------------------
# TestLinkedInParser  (file-based, replacing the old text-based tests)
# ---------------------------------------------------------------------------

class TestLinkedInParser(unittest.TestCase):
    """Test cases for LinkedIn profile file parsing."""

    def test_parse_linkedin_from_bytes_docx_basic(self):
        """parse_linkedin_from_bytes on a DOCX returns the expected structure."""
        docx_bytes = _make_docx_bytes(SAMPLE_LINKEDIN_TEXT)
        result = parse_linkedin_from_bytes(docx_bytes, "linkedin_profile.docx")

        for key in ('full_text', 'experience', 'skills', 'education',
                    'other', 'extracted_skills'):
            self.assertIn(key, result)

        self.assertIsInstance(result['extracted_skills'], list)

    def test_parse_linkedin_experience_extracted(self):
        text = (
            "Experience\n"
            "Senior Engineer at Corp\n"
            "Led a team of developers\n"
            "Education\n"
            "BS CS\n"
        )
        docx_bytes = _make_docx_bytes(text)
        result = parse_linkedin_from_bytes(docx_bytes, "li.docx")
        self.assertIn('Senior Engineer', result['experience'])

    def test_parse_linkedin_skills_extracted(self):
        text = (
            "Top Skills\n"
            "Python\nDocker\nKubernetes\n"
            "Experience\n"
            "Engineer at Corp\n"
        )
        docx_bytes = _make_docx_bytes(text)
        result = parse_linkedin_from_bytes(docx_bytes, "li.docx")
        self.assertIn('Python', result['skills'])

    def test_parse_linkedin_certifications_not_in_main_sections(self):
        text = (
            "Experience\nSenior Dev\n"
            "Licenses & Certifications\nAWS Certified\n"
            "Education\nBS CS\n"
        )
        docx_bytes = _make_docx_bytes(text)
        result = parse_linkedin_from_bytes(docx_bytes, "li.docx")
        self.assertNotIn('AWS Certified', result['experience'])
        self.assertNotIn('AWS Certified', result['skills'])
        self.assertNotIn('AWS Certified', result['education'])


# ---------------------------------------------------------------------------
# TestIntegration
# ---------------------------------------------------------------------------

class TestIntegration(unittest.TestCase):
    """Integration tests — full pipeline without real model."""

    def test_full_pipeline_cv_and_linkedin_docx(self):
        """
        Parses both a CV and a LinkedIn DOCX, then runs calculate_score.
        The sentence-transformer model is mocked so no download is needed.
        """
        with patch('comparator.SentenceTransformer') as mock_cls:
            mock_inst = MagicMock()
            mock_inst.encode.return_value = [[0.8] * 384, [0.75] * 384]
            mock_cls.return_value = mock_inst
            comp = CVLinkedInComparator()

        cv_bytes = _make_docx_bytes(SAMPLE_CV_TEXT)
        li_bytes = _make_docx_bytes(SAMPLE_LINKEDIN_TEXT)

        cv_data = parse_cv_from_bytes(cv_bytes, "cv.docx")
        li_data = parse_linkedin_from_bytes(li_bytes, "linkedin.docx")

        result = comp.calculate_score(cv_data, li_data)

        self.assertIn('overall_score', result)
        self.assertGreaterEqual(result['overall_score'], 0.0)
        self.assertLessEqual(result['overall_score'], 100.0)

        recs = comp.get_recommendations(result)
        self.assertIsInstance(recs, list)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for cls in (TestCVParser, TestComparator, TestLinkedInParser, TestIntegration):
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
