"""
Intelligent Scoring Algorithm
==============================
Context-aware scoring that adjusts based on document type and intent.
Provides fair evaluation for all document categories.

World-class implementation with machine learning readiness.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class DocumentCategory(Enum):
    """Document categories with specific scoring needs"""
    FULL_DOCUMENT = "full_document"
    CONTENT_BLOCK = "content_block"
    TEMPLATE = "template"
    LEGAL = "legal"
    FINANCIAL = "financial"
    CORRESPONDENCE = "correspondence"
    FORM = "form"
    REPORT = "report"
    MINIMAL = "minimal"  # For blank/footer-only documents
    UNKNOWN = "unknown"


@dataclass
class ScoringProfile:
    """Scoring profile for a document category"""
    category: DocumentCategory
    content_weight: float
    structure_weight: float
    sharedo_weight: float
    formatting_weight: float
    technical_weight: float
    minimum_content_threshold: int  # Minimum characters for content scoring
    requires_sharedo: bool  # Whether Sharedo elements are expected


class IntelligentScorer:
    """
    Intelligent scoring system that adapts to document type and intent.
    Achieves fair and accurate scoring across all document categories.
    """
    
    # Scoring profiles for different document types
    SCORING_PROFILES = {
        DocumentCategory.FULL_DOCUMENT: ScoringProfile(
            category=DocumentCategory.FULL_DOCUMENT,
            content_weight=0.25,
            structure_weight=0.20,
            sharedo_weight=0.25,
            formatting_weight=0.15,
            technical_weight=0.15,
            minimum_content_threshold=100,
            requires_sharedo=False
        ),
        DocumentCategory.CONTENT_BLOCK: ScoringProfile(
            category=DocumentCategory.CONTENT_BLOCK,
            content_weight=0.35,
            structure_weight=0.25,
            sharedo_weight=0.10,  # Less emphasis on Sharedo for blocks
            formatting_weight=0.20,
            technical_weight=0.10,
            minimum_content_threshold=20,
            requires_sharedo=False
        ),
        DocumentCategory.TEMPLATE: ScoringProfile(
            category=DocumentCategory.TEMPLATE,
            content_weight=0.15,
            structure_weight=0.20,
            sharedo_weight=0.40,  # High emphasis on Sharedo for templates
            formatting_weight=0.15,
            technical_weight=0.10,
            minimum_content_threshold=50,
            requires_sharedo=True
        ),
        DocumentCategory.LEGAL: ScoringProfile(
            category=DocumentCategory.LEGAL,
            content_weight=0.30,
            structure_weight=0.25,
            sharedo_weight=0.20,
            formatting_weight=0.15,
            technical_weight=0.10,
            minimum_content_threshold=200,
            requires_sharedo=False
        ),
        DocumentCategory.MINIMAL: ScoringProfile(
            category=DocumentCategory.MINIMAL,
            content_weight=0.20,  # Less emphasis on content
            structure_weight=0.30,  # More emphasis on structure
            sharedo_weight=0.10,  # Minimal Sharedo expected
            formatting_weight=0.25,
            technical_weight=0.15,
            minimum_content_threshold=10,
            requires_sharedo=False
        ),
        DocumentCategory.CORRESPONDENCE: ScoringProfile(
            category=DocumentCategory.CORRESPONDENCE,
            content_weight=0.25,
            structure_weight=0.20,
            sharedo_weight=0.30,  # Letters often have tags
            formatting_weight=0.15,
            technical_weight=0.10,
            minimum_content_threshold=100,
            requires_sharedo=True
        ),
        DocumentCategory.UNKNOWN: ScoringProfile(
            category=DocumentCategory.UNKNOWN,
            content_weight=0.20,
            structure_weight=0.20,
            sharedo_weight=0.20,
            formatting_weight=0.20,
            technical_weight=0.20,
            minimum_content_threshold=0,
            requires_sharedo=False
        )
    }
    
    # Keywords for document categorization
    CATEGORY_KEYWORDS = {
        DocumentCategory.LEGAL: [
            'agreement', 'contract', 'legal', 'clause', 'terms', 'conditions',
            'liability', 'indemnity', 'jurisdiction', 'dispute', 'defendant',
            'claimant', 'witness', 'court', 'proceeding'
        ],
        DocumentCategory.FINANCIAL: [
            'invoice', 'payment', 'cost', 'fee', 'expense', 'budget',
            'financial', 'accounting', 'tax', 'revenue', 'profit'
        ],
        DocumentCategory.CORRESPONDENCE: [
            'letter', 'dear', 'sincerely', 'regards', 'yours', 'response',
            'inquiry', 'request', 'acknowledge', 'confirm'
        ],
        DocumentCategory.FORM: [
            'form', 'questionnaire', 'application', 'registration',
            'checkbox', 'field', 'fill', 'complete', 'submit'
        ],
        DocumentCategory.REPORT: [
            'report', 'analysis', 'summary', 'findings', 'conclusion',
            'recommendation', 'executive summary', 'results'
        ]
    }
    
    def __init__(self):
        """Initialize the intelligent scorer"""
        self.statistics = {
            'documents_scored': 0,
            'category_distribution': Counter(),
            'average_scores': {},
            'profile_adjustments': 0
        }
        
    def score_conversion(self, 
                        original_path: str,
                        original_content: str,
                        converted_html: str,
                        conversion_metadata: Dict,
                        structure_analysis: Optional[Dict] = None) -> Dict:
        """
        Score a document conversion with intelligent adaptation.
        
        Args:
            original_path: Path to original document
            original_content: Original document text
            converted_html: Converted HTML content
            conversion_metadata: Metadata from conversion process
            structure_analysis: Optional structure analysis results
            
        Returns:
            Comprehensive scoring results
        """
        # Detect document category
        category = self._detect_category(original_path, original_content, converted_html)
        
        # Get appropriate scoring profile (default to FULL_DOCUMENT if unknown)
        profile = self.SCORING_PROFILES.get(
            category, 
            self.SCORING_PROFILES[DocumentCategory.FULL_DOCUMENT]
        )
        
        # Perform category-specific scoring
        scores = {
            'content': self._score_content(
                original_content, converted_html, profile
            ),
            'structure': self._score_structure(
                converted_html, structure_analysis, profile
            ),
            'sharedo': self._score_sharedo(
                converted_html, conversion_metadata, profile
            ),
            'formatting': self._score_formatting(
                converted_html, profile
            ),
            'technical': self._score_technical(
                conversion_metadata, profile
            )
        }
        
        # Calculate weighted total
        weighted_total = sum(
            scores[aspect] * getattr(profile, f"{aspect}_weight")
            for aspect in scores
        )
        
        # Apply adjustments
        adjusted_score = self._apply_adjustments(
            weighted_total, category, original_content, scores
        )
        
        # Update statistics
        self.statistics['documents_scored'] += 1
        self.statistics['category_distribution'][category] += 1
        
        # Determine grade
        grade = self._calculate_grade(adjusted_score)
        
        return {
            'category': category.value,
            'profile_used': profile.category.value,
            'raw_scores': scores,
            'weighted_total': round(weighted_total, 2),
            'adjusted_score': round(adjusted_score, 2),
            'grade': grade,
            'scoring_details': self._generate_scoring_details(scores, profile),
            'recommendations': self._generate_recommendations(scores, category)
        }
    
    def _detect_category(self, path: str, original: str, html: str) -> DocumentCategory:
        """
        Intelligently detect document category.
        
        Args:
            path: Document path
            original: Original content
            html: Converted HTML
            
        Returns:
            Detected document category
        """
        path_lower = path.lower()
        content_lower = original.lower() if original else ""
        
        # Check path-based patterns
        if 'content block' in path_lower or 'contentblock' in path_lower:
            return DocumentCategory.CONTENT_BLOCK
        
        if 'template' in path_lower:
            return DocumentCategory.TEMPLATE
        
        # Check for minimal content documents
        word_count = len(original.split()) if original else 0
        if word_count < 10:
            # Check if it's a footer or header
            if any(term in path_lower for term in ['footer', 'header', 'blank']):
                return DocumentCategory.MINIMAL
        
        # Check content-based patterns
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            if keyword_count >= 3:  # At least 3 matching keywords
                return category
        
        # Check for correspondence patterns
        if re.search(r'dear\s+\w+|sincerely|regards', content_lower, re.IGNORECASE):
            return DocumentCategory.CORRESPONDENCE
        
        # Check for template indicators
        if '{{' in original or '{%' in original or 'context.' in original:
            return DocumentCategory.TEMPLATE
        
        # Default categorization based on size and structure
        if word_count > 500:
            return DocumentCategory.FULL_DOCUMENT
        elif word_count > 100:
            return DocumentCategory.CORRESPONDENCE
        elif word_count > 0:
            return DocumentCategory.MINIMAL
        else:
            return DocumentCategory.UNKNOWN  # Empty document
    
    def _score_content(self, original: str, html: str, profile: ScoringProfile) -> float:
        """
        Score content preservation with profile awareness.
        
        Args:
            original: Original content
            html: Converted HTML
            profile: Scoring profile
            
        Returns:
            Content score (0-10)
        """
        # Handle minimal content documents
        if len(original) < profile.minimum_content_threshold:
            # For minimal documents, check if structure is preserved
            if html and len(html) > 0:
                return 8.0  # Good score for preserving minimal content
            return 5.0
        
        # Extract text from HTML for comparison
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        converted_text = soup.get_text(separator=' ', strip=True)
        
        # Calculate content similarity
        original_words = set(original.lower().split())
        converted_words = set(converted_text.lower().split())
        
        if not original_words:
            return 10.0 if not converted_words else 5.0
        
        # Calculate Jaccard similarity
        intersection = original_words & converted_words
        union = original_words | converted_words
        
        if union:
            similarity = len(intersection) / len(union)
        else:
            similarity = 1.0
        
        # Convert to 10-point scale with profile adjustment
        base_score = similarity * 10
        
        # Adjust for category expectations
        if profile.category == DocumentCategory.MINIMAL:
            # Be more lenient for minimal documents
            return min(10.0, base_score * 1.2)
        elif profile.category == DocumentCategory.CONTENT_BLOCK:
            # Content blocks should preserve content exactly
            return base_score * 0.95 if base_score > 8 else base_score
        
        return base_score
    
    def _score_structure(self, html: str, analysis: Optional[Dict], 
                        profile: ScoringProfile) -> float:
        """
        Score structural preservation with profile awareness.
        
        Args:
            html: Converted HTML
            analysis: Structure analysis results
            profile: Scoring profile
            
        Returns:
            Structure score (0-10)
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        score = 10.0
        
        # Check basic structure elements
        has_paragraphs = bool(soup.find_all('p'))
        has_headings = bool(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        has_tables = bool(soup.find_all('table'))
        has_lists = bool(soup.find_all(['ul', 'ol']))
        
        # Adjust based on what's expected for the category
        if profile.category == DocumentCategory.MINIMAL:
            # Minimal documents may not need complex structure
            if soup.body or soup.find_all(['div', 'p', 'span']):
                return 9.0
            return 7.0
        
        if profile.category == DocumentCategory.TEMPLATE:
            # Templates need good structure for placeholders
            if not has_paragraphs:
                score -= 2.0
            
            # Check for data attributes indicating structure
            if soup.find_all(attrs={'data-section': True}):
                score = min(10.0, score + 1.0)
        
        if profile.category == DocumentCategory.LEGAL:
            # Legal documents need hierarchical structure
            if not has_headings:
                score -= 1.5
            if not has_paragraphs:
                score -= 2.0
        
        # Use structure analysis if available
        if analysis:
            max_depth = analysis.get('max_depth', 0)
            if max_depth > 10:
                score -= 1.0  # Too deep nesting
            elif max_depth < 2 and profile.category != DocumentCategory.MINIMAL:
                score -= 0.5  # Too flat for non-minimal documents
        
        return max(0.0, min(10.0, score))
    
    def _score_sharedo(self, html: str, metadata: Dict, 
                      profile: ScoringProfile) -> float:
        """
        Score Sharedo element preservation with profile awareness.
        
        Args:
            html: Converted HTML
            metadata: Conversion metadata
            profile: Scoring profile
            
        Returns:
            Sharedo score (0-10)
        """
        sharedo_elements = metadata.get('sharedo_elements', {})
        
        # Count total Sharedo elements
        total_elements = sum([
            len(sharedo_elements.get('tags', [])),
            len(sharedo_elements.get('sections', [])),
            len(sharedo_elements.get('content_blocks', [])),
            len(sharedo_elements.get('conditionals', [])),
            len(sharedo_elements.get('placeholders', []))
        ])
        
        # Adjust expectations based on profile
        if not profile.requires_sharedo:
            # Document doesn't require Sharedo elements
            if total_elements == 0:
                return 9.0  # Good score for correctly identifying no Sharedo
            else:
                # Has Sharedo elements - score based on preservation
                return min(10.0, 7.0 + (total_elements * 0.3))
        
        # Document requires Sharedo elements
        if profile.category == DocumentCategory.TEMPLATE:
            # Templates should have many Sharedo elements
            if total_elements >= 10:
                return 10.0
            elif total_elements >= 5:
                return 8.5
            elif total_elements >= 2:
                return 7.0
            elif total_elements >= 1:
                return 5.0
            else:
                return 3.0  # Template without Sharedo elements is problematic
        
        if profile.category == DocumentCategory.CONTENT_BLOCK:
            # Content blocks may have few Sharedo elements
            if total_elements >= 1:
                return 9.0
            return 7.0  # Acceptable even without Sharedo
        
        # Default scoring
        if total_elements >= 5:
            return 10.0
        elif total_elements >= 3:
            return 8.0
        elif total_elements >= 1:
            return 6.0
        else:
            return 4.0
    
    def _score_formatting(self, html: str, profile: ScoringProfile) -> float:
        """
        Score formatting preservation.
        
        Args:
            html: Converted HTML
            profile: Scoring profile
            
        Returns:
            Formatting score (0-10)
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        score = 10.0
        
        # Check for formatting elements
        has_styles = bool(soup.find('style') or soup.find_all(style=True))
        has_bold = bool(soup.find_all(['b', 'strong']))
        has_italic = bool(soup.find_all(['i', 'em']))
        has_underline = bool(soup.find_all('u'))
        
        # Check for CSS classes
        has_classes = bool(soup.find_all(class_=True))
        
        # Minimal documents don't need rich formatting
        if profile.category == DocumentCategory.MINIMAL:
            return 9.0 if has_styles or has_classes else 8.0
        
        # Other documents benefit from formatting
        if not has_styles and not has_classes:
            score -= 2.0
        
        if profile.category in [DocumentCategory.LEGAL, DocumentCategory.CORRESPONDENCE]:
            # These often have text formatting
            if not (has_bold or has_italic or has_underline):
                score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _score_technical(self, metadata: Dict, profile: ScoringProfile) -> float:
        """
        Score technical quality.
        
        Args:
            metadata: Conversion metadata
            profile: Scoring profile
            
        Returns:
            Technical score (0-10)
        """
        confidence = metadata.get('confidence_score', 0)
        processing_time = metadata.get('processing_time', 0)
        
        # Base score on confidence
        if confidence >= 95:
            score = 10.0
        elif confidence >= 90:
            score = 9.0
        elif confidence >= 85:
            score = 8.0
        elif confidence >= 80:
            score = 7.0
        elif confidence >= 70:
            score = 6.0
        else:
            score = 5.0
        
        # Adjust for processing time (penalize slow conversions)
        if processing_time > 1.0:  # More than 1 second
            score -= 0.5
        elif processing_time > 2.0:  # More than 2 seconds
            score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _apply_adjustments(self, base_score: float, category: DocumentCategory,
                          original_content: str, raw_scores: Dict) -> float:
        """
        Apply intelligent adjustments to the base score.
        
        Args:
            base_score: Weighted total score
            category: Document category
            original_content: Original content
            raw_scores: Raw scores by aspect
            
        Returns:
            Adjusted score
        """
        adjusted = base_score
        
        # Boost for perfect conversions
        if all(score >= 9.0 for score in raw_scores.values()):
            adjusted = min(10.0, adjusted * 1.05)
        
        # Adjust for minimal documents
        if category == DocumentCategory.MINIMAL:
            # Don't penalize minimal documents as harshly
            if adjusted < 6.0:
                adjusted = min(7.0, adjusted * 1.3)
        
        # Adjust for content blocks
        if category == DocumentCategory.CONTENT_BLOCK:
            # Content blocks are fragments, adjust expectations
            if raw_scores['sharedo'] < 5.0:
                # Don't penalize content blocks for lack of Sharedo
                adjusted = adjusted * 0.9 + raw_scores['sharedo'] * 0.1
        
        # Track adjustment
        if adjusted != base_score:
            self.statistics['profile_adjustments'] += 1
        
        return min(10.0, max(0.0, adjusted))
    
    def _calculate_grade(self, score: float) -> str:
        """
        Calculate letter grade from numerical score.
        
        Args:
            score: Numerical score (0-10)
            
        Returns:
            Letter grade
        """
        if score >= 9.7: return "A+"
        elif score >= 9.3: return "A"
        elif score >= 9.0: return "A-"
        elif score >= 8.7: return "B+"
        elif score >= 8.3: return "B"
        elif score >= 8.0: return "B-"
        elif score >= 7.7: return "C+"
        elif score >= 7.3: return "C"
        elif score >= 7.0: return "C-"
        elif score >= 6.7: return "D+"
        elif score >= 6.3: return "D"
        elif score >= 6.0: return "D-"
        else: return "F"
    
    def _generate_scoring_details(self, scores: Dict, profile: ScoringProfile) -> Dict:
        """
        Generate detailed scoring breakdown.
        
        Args:
            scores: Raw scores
            profile: Scoring profile used
            
        Returns:
            Detailed scoring information
        """
        details = {}
        
        for aspect, score in scores.items():
            weight = getattr(profile, f"{aspect}_weight")
            details[aspect] = {
                'raw_score': round(score, 2),
                'weight': weight,
                'weighted_score': round(score * weight, 2),
                'percentage': f"{score * 10:.0f}%"
            }
        
        return details
    
    def _generate_recommendations(self, scores: Dict, 
                                 category: DocumentCategory) -> List[str]:
        """
        Generate improvement recommendations.
        
        Args:
            scores: Raw scores
            category: Document category
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check each aspect for improvements
        if scores['content'] < 7.0:
            recommendations.append(
                "Improve content extraction to preserve more original text"
            )
        
        if scores['structure'] < 7.0:
            recommendations.append(
                "Enhance structure preservation, particularly for nested elements"
            )
        
        if scores['sharedo'] < 7.0 and category == DocumentCategory.TEMPLATE:
            recommendations.append(
                "Critical: Improve Sharedo element detection and preservation"
            )
        
        if scores['formatting'] < 7.0:
            recommendations.append(
                "Preserve text formatting (bold, italic, styles) more accurately"
            )
        
        if scores['technical'] < 7.0:
            recommendations.append(
                "Optimize conversion algorithm for better confidence scores"
            )
        
        # Category-specific recommendations
        if category == DocumentCategory.CONTENT_BLOCK and scores['sharedo'] < 5.0:
            recommendations.append(
                "Note: Content blocks may not require Sharedo elements"
            )
        
        if category == DocumentCategory.MINIMAL and any(s < 6.0 for s in scores.values()):
            recommendations.append(
                "Consider: This appears to be a minimal document (header/footer)"
            )
        
        return recommendations if recommendations else ["Conversion performing well"]
    
    def get_statistics(self) -> Dict:
        """
        Get scorer statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'documents_scored': self.statistics['documents_scored'],
            'category_distribution': dict(self.statistics['category_distribution']),
            'profile_adjustments_made': self.statistics['profile_adjustments'],
            'most_common_category': (
                self.statistics['category_distribution'].most_common(1)[0][0].value
                if self.statistics['category_distribution'] else 'none'
            )
        }