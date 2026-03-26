"""
Comparator Module
Compares CV data with LinkedIn profile using local sentence transformers.
Computes similarity scores and identifies discrepancies.
"""

import numpy as np
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class CVLinkedInComparator:
    """Compares CV and LinkedIn profile data."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the comparator with a sentence transformer model.

        Args:
            model_name: Name of the sentence-transformers model to use locally
        """
        print(f"Loading model '{model_name}' locally...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded successfully!")
        
        self.section_weights = {
            'experience': 0.4,
            'skills': 0.35,
            'education': 0.25
        }
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts using embeddings.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        if not text1.strip() or not text2.strip():
            return 0.0
        
        embeddings = self.model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def compute_section_similarities(
        self,
        cv_data: Dict,
        linkedin_data: Dict
    ) -> Dict[str, float]:
        """
        Compute similarity for each section.

        Args:
            cv_data: Parsed CV data
            linkedin_data: Parsed LinkedIn data

        Returns:
            Dictionary with similarity scores for each section
        """
        similarities = {}
        
        for section in ['experience', 'skills', 'education']:
            cv_text = cv_data.get(section, '')
            linkedin_text = linkedin_data.get(section, '')
            
            if cv_text or linkedin_text:
                similarities[section] = self.compute_similarity(cv_text, linkedin_text)
            else:
                similarities[section] = 0.0
        
        return similarities
    
    def calculate_score(self, cv_data: Dict, linkedin_data: Dict) -> Dict:
        """
        Calculate overall match score between CV and LinkedIn profile.

        Args:
            cv_data: Parsed CV data with sections
            linkedin_data: Parsed LinkedIn data with sections

        Returns:
            Dictionary with scores and details
        """
        section_scores = self.compute_section_similarities(cv_data, linkedin_data)
        
        overall_score = 0.0
        for section, weight in self.section_weights.items():
            overall_score += section_scores.get(section, 0.0) * weight
        
        discrepancies = []
        for section, score in section_scores.items():
            if score < 0.6:
                discrepancies.append({
                    'section': section,
                    'score': score,
                    'severity': 'high' if score < 0.4 else 'medium'
                })
        
        cv_skills = set(cv_data.get('extracted_skills', []))
        linkedin_skills = set(linkedin_data.get('extracted_skills', []))
        
        common_skills = cv_skills & linkedin_skills
        cv_only_skills = cv_skills - linkedin_skills
        linkedin_only_skills = linkedin_skills - cv_skills
        
        return {
            'overall_score': round(overall_score * 100, 2),
            'section_scores': {
                section: round(score * 100, 2)
                for section, score in section_scores.items()
            },
            'discrepancies': discrepancies,
            'skills_comparison': {
                'common': list(common_skills),
                'cv_only': list(cv_only_skills),
                'linkedin_only': list(linkedin_only_skills),
                'match_rate': round(
                    len(common_skills) / max(len(cv_skills | linkedin_skills), 1) * 100,
                    2
                )
            },
            'weights': self.section_weights
        }
    
    def get_recommendations(self, comparison_result: Dict) -> List[str]:
        """
        Generate recommendations based on comparison results.

        Args:
            comparison_result: Result from calculate_score

        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        overall = comparison_result['overall_score']
        section_scores = comparison_result['section_scores']
        skills = comparison_result['skills_comparison']
        
        if overall >= 80:
            recommendations.append("✅ Excellent match! Your CV and LinkedIn profile are well aligned.")
        elif overall >= 60:
            recommendations.append("⚠️ Good match, but some improvements can be made.")
        else:
            recommendations.append("❌ Significant differences detected. Consider updating your profiles.")
        
        for section, score in section_scores.items():
            if score < 60:
                recommendations.append(
                    f"🔍 Update your {section.title()} section - "
                    f"it shows only {score}% match between CV and LinkedIn."
                )
        
        if skills['cv_only']:
            recommendations.append(
                f"📝 Add these skills to LinkedIn: {', '.join(skills['cv_only'][:5])}"
            )
        
        if skills['linkedin_only']:
            recommendations.append(
                f"📄 Add these skills to your CV: {', '.join(skills['linkedin_only'][:5])}"
            )
        
        if skills['match_rate'] < 50:
            recommendations.append(
                "⚡ Your skills sections differ significantly. "
                "Ensure consistency across platforms."
            )
        
        return recommendations


# Example usage
if __name__ == "__main__":
    comparator = CVLinkedInComparator()
    
    cv_data = {
        'experience': 'Senior Developer at Tech Corp. Led team of 5 developers. Built Python applications.',
        'skills': 'Python, JavaScript, React, AWS',
        'education': 'BS Computer Science from University XYZ',
        'extracted_skills': ['Python', 'JavaScript', 'React', 'Aws']
    }
    
    linkedin_data = {
        'experience': 'Senior Software Engineer at Tech Corp. Team lead managing 5 engineers. Developed scalable applications.',
        'skills': 'Python, JavaScript, React, Docker',
        'education': 'Bachelor of Science in Computer Science, University XYZ',
        'extracted_skills': ['Python', 'JavaScript', 'React', 'Docker']
    }
    
    result = comparator.calculate_score(cv_data, linkedin_data)
    recommendations = comparator.get_recommendations(result)
    
    print("Comparison Result:")
    print(f"Overall Score: {result['overall_score']}%")
    print(f"\nSection Scores:")
    for section, score in result['section_scores'].items():
        print(f"  {section.title()}: {score}%")
    print(f"\nSkills Comparison:")
    print(f"  Common: {result['skills_comparison']['common']}")
    print(f"  CV Only: {result['skills_comparison']['cv_only']}")
    print(f"  LinkedIn Only: {result['skills_comparison']['linkedin_only']}")
    print(f"\nRecommendations:")
    for rec in recommendations:
        print(f"  {rec}")
