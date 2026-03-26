"""
CV Parser Module
Extracts and normalizes text from PDF and DOCX files.
Uses heuristics to identify sections: experience, skills, education.
"""

import re
from typing import Dict, List, Optional
import pdfplumber
from docx import Document


class CVParser:
    """Parser for extracting structured data from CV files."""
    
    # Section headers patterns (case-insensitive)
    EXPERIENCE_PATTERNS = [
        r'work\s+experience',
        r'professional\s+experience',
        r'employment\s+history',
        r'work\s+history',
        r'experience',
        r'experiencia\s+laboral',
        r'experiencia\s+profesional',
    ]
    
    SKILLS_PATTERNS = [
        r'skills',
        r'technical\s+skills',
        r'competencies',
        r'technologies',
        r'habilidades',
        r'competencias',
        r'top\s+skills',          # LinkedIn PDF header
    ]
    
    EDUCATION_PATTERNS = [
        r'education',
        r'academic\s+background',
        r'qualifications',
        r'formación',
        r'educación',
    ]

    # LinkedIn-specific section headers to help the parser
    LINKEDIN_SECTION_PATTERNS = [
        r'licenses\s*&?\s*certifications?',
        r'volunteer\s+experience',
        r'publications?',
        r'honors?\s*&?\s*awards?',
        r'languages?',
        r'recommendations?',
        r'accomplishments?',
        r'interests?',
        r'following',
        r'groups?',
    ]
    
    def __init__(self):
        """Initialize the CV Parser."""
        self.experience_regex = self._compile_patterns(self.EXPERIENCE_PATTERNS)
        self.skills_regex = self._compile_patterns(self.SKILLS_PATTERNS)
        self.education_regex = self._compile_patterns(self.EDUCATION_PATTERNS)
        self.linkedin_other_regex = self._compile_patterns(self.LINKEDIN_SECTION_PATTERNS)
    
    @staticmethod
    def _compile_patterns(patterns: List[str]) -> re.Pattern:
        """Compile multiple patterns into a single regex."""
        combined = '|'.join(f'({pattern})' for pattern in patterns)
        return re.compile(combined, re.IGNORECASE)
    
    def read_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text as string
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
        
        return text.strip()
    
    def read_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extracted text as string
        """
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")
        
        return text.strip()
    
    def read_file(self, file_path: str) -> str:
        """
        Read file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text
        """
        if file_path.lower().endswith('.pdf'):
            return self.read_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return self.read_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Use PDF or DOCX.")
    
    def _split_into_sections(self, text: str, linkedin_mode: bool = False) -> Dict[str, str]:
        """
        Split CV/LinkedIn text into sections based on headers.

        Args:
            text: Full text
            linkedin_mode: If True, also catches LinkedIn-specific section headers
                           and routes them to 'other' to avoid polluting main sections.

        Returns:
            Dictionary with sections
        """
        sections = {
            'experience': '',
            'skills': '',
            'education': '',
            'other': ''
        }
        
        lines = text.split('\n')
        current_section = 'other'
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Skip empty lines (but preserve section separation)
            if not line_stripped:
                if current_section in sections:
                    sections[current_section] += '\n'
                continue

            # In LinkedIn mode, catch LinkedIn-specific section headers first
            # and redirect them to 'other' so they don't bleed into main sections.
            if linkedin_mode and self.linkedin_other_regex.search(line_lower):
                current_section = 'other'
                continue

            # Check which section this line belongs to
            if self.experience_regex.search(line_lower):
                current_section = 'experience'
                continue
            elif self.skills_regex.search(line_lower):
                current_section = 'skills'
                continue
            elif self.education_regex.search(line_lower):
                current_section = 'education'
                continue
            
            # Add line to current section
            sections[current_section] += line + '\n'
        
        # Clean sections
        for key in sections:
            sections[key] = sections[key].strip()
        
        return sections
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract potential skills from text using heuristics.

        Args:
            text: Text to extract skills from

        Returns:
            List of identified skills
        """
        skill_keywords = [
            'python', 'java', 'javascript', 'c\\+\\+', 'sql', 'html', 'css',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'fastapi',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
            'machine learning', 'deep learning', 'ai', 'data science',
            'agile', 'scrum', 'devops', 'ci/cd',
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if re.search(r'\b' + skill + r'\b', text_lower):
                found_skills.append(skill.replace('\\+\\+', '++').title())
        
        return list(set(found_skills))
    
    def parse(self, file_path: str) -> Dict:
        """
        Parse CV file and extract structured data.

        Args:
            file_path: Path to CV file

        Returns:
            Dictionary with parsed CV data
        """
        full_text = self.read_file(file_path)
        sections = self._split_into_sections(full_text)
        
        skills = self.extract_skills(sections['skills'])
        if not skills:
            skills = self.extract_skills(sections['experience'])
        
        return {
            'full_text': full_text,
            'experience': sections['experience'],
            'skills': sections['skills'],
            'education': sections['education'],
            'other': sections['other'],
            'extracted_skills': skills
        }

    def parse_linkedin(self, file_path: str) -> Dict:
        """
        Parse a LinkedIn-exported PDF/DOCX and extract structured data.
        Uses linkedin_mode in _split_into_sections to handle LinkedIn-specific headers.

        Args:
            file_path: Path to the LinkedIn profile file

        Returns:
            Dictionary with parsed LinkedIn data
        """
        full_text = self.read_file(file_path)
        sections = self._split_into_sections(full_text, linkedin_mode=True)

        # For LinkedIn, prefer the dedicated skills section; fall back to experience
        skills = self.extract_skills(sections['skills'])
        if not skills:
            skills = self.extract_skills(sections['experience'])

        return {
            'full_text': full_text,
            'experience': sections['experience'],
            'skills': sections['skills'],
            'education': sections['education'],
            'other': sections['other'],
            'extracted_skills': skills
        }


def parse_cv_from_bytes(file_bytes: bytes, filename: str) -> Dict:
    """
    Parse CV from bytes (for API uploads).

    Args:
        file_bytes: File content as bytes
        filename: Original filename

    Returns:
        Parsed CV data
    """
    import tempfile
    import os
    
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name
    
    try:
        parser = CVParser()
        return parser.parse(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def parse_linkedin_from_bytes(file_bytes: bytes, filename: str) -> Dict:
    """
    Parse a LinkedIn-exported PDF/DOCX from bytes (for API uploads).

    Args:
        file_bytes: File content as bytes
        filename: Original filename (used to determine extension)

    Returns:
        Parsed LinkedIn data with the same structure as parse_cv_from_bytes:
        {full_text, experience, skills, education, other, extracted_skills}
    """
    import tempfile
    import os

    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    try:
        parser = CVParser()
        return parser.parse_linkedin(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# Example usage
if __name__ == "__main__":
    parser = CVParser()
    
    sample_text = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    Senior Developer at Tech Corp (2020-2023)
    - Developed Python applications
    - Led team of 5 developers
    
    SKILLS
    Python, JavaScript, React, AWS, Docker
    
    EDUCATION
    BS Computer Science, University XYZ (2016-2020)
    """
    
    sections = parser._split_into_sections(sample_text)
    skills = parser.extract_skills(sample_text)
    
    print("Sections:", sections)
    print("\nExtracted Skills:", skills)
