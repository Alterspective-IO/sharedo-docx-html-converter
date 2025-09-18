#!/usr/bin/env python3
"""
Comprehensive Document Conversion Testing Framework
Evaluates DOCX to HTML conversions with detailed scoring rubric
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re

class ConversionEvaluator:
    """Evaluates document conversions using a comprehensive rubric"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results = []
        
        # Define evaluation rubric with weights
        self.rubric = {
            "tag_preservation": {
                "weight": 0.25,
                "criteria": {
                    "context_tags": {"max_score": 10, "description": "Preservation of context.* tags"},
                    "document_tags": {"max_score": 10, "description": "Preservation of document.* tags"},
                    "env_tags": {"max_score": 10, "description": "Preservation of env.* tags"},
                    "content_blocks": {"max_score": 10, "description": "Preservation of content blocks"},
                    "custom_tags": {"max_score": 10, "description": "Preservation of custom/other tags"}
                }
            },
            "structural_integrity": {
                "weight": 0.20,
                "criteria": {
                    "paragraphs": {"max_score": 10, "description": "Paragraph structure maintained"},
                    "tables": {"max_score": 10, "description": "Table structure preserved"},
                    "lists": {"max_score": 10, "description": "List formatting retained"},
                    "headings": {"max_score": 10, "description": "Heading hierarchy preserved"},
                    "sections": {"max_score": 10, "description": "Document sections maintained"}
                }
            },
            "formatting_quality": {
                "weight": 0.15,
                "criteria": {
                    "fonts": {"max_score": 10, "description": "Font styles preserved"},
                    "spacing": {"max_score": 10, "description": "Line spacing and margins"},
                    "alignment": {"max_score": 10, "description": "Text alignment maintained"},
                    "styles": {"max_score": 10, "description": "Bold, italic, underline preserved"}
                }
            },
            "special_elements": {
                "weight": 0.20,
                "criteria": {
                    "conditionals": {"max_score": 10, "description": "If/then blocks handled"},
                    "placeholders": {"max_score": 10, "description": "Placeholder preservation"},
                    "date_formatting": {"max_score": 10, "description": "Date format expressions"},
                    "nested_refs": {"max_score": 10, "description": "Nested property references"}
                }
            },
            "technical_quality": {
                "weight": 0.20,
                "criteria": {
                    "html_validity": {"max_score": 10, "description": "Valid HTML5 structure"},
                    "email_compatibility": {"max_score": 10, "description": "Email client compatibility"},
                    "performance": {"max_score": 10, "description": "Conversion speed"},
                    "file_size": {"max_score": 10, "description": "Reasonable output size"},
                    "confidence": {"max_score": 10, "description": "API confidence score"}
                }
            }
        }
        
        # Document categories for analysis
        self.document_categories = {
            "simple": ["Acme Solutions.docx", "Igors Test Document.docx"],
            "moderate": ["Draft Agreement copy.docx", "Response copy.docx", "Contract copy.docx"],
            "complex": ["AdminOperation_Print_Task_Template.docx", "701_0048.docx"],
            "large": ["Cost Agreement.docx", "Joan Letter.docx", "iManage doc.docx"]
        }
    
    def convert_document(self, file_path: str) -> Dict[str, Any]:
        """Convert a single document via API"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                response = requests.post(f"{self.api_url}/api/v1/convert", files=files, timeout=30)
                
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_conversion(self, original_path: str, conversion_result: Dict) -> Dict[str, Any]:
        """Analyze conversion results against rubric"""
        scores = {}
        
        if "error" in conversion_result:
            return {
                "error": conversion_result["error"],
                "total_score": 0,
                "grade": "F"
            }
        
        # Extract conversion data
        sharedo_elements = conversion_result.get("sharedo_elements", {})
        content_controls = sharedo_elements.get("content_controls", [])
        placeholders = sharedo_elements.get("placeholders", [])
        conditionals = sharedo_elements.get("conditional_sections", [])
        html_content = conversion_result.get("html_content", "")
        confidence = conversion_result.get("confidence_score", 0)
        processing_time = conversion_result.get("processing_time", 0)
        
        # Score: Tag Preservation
        tag_scores = {}
        context_count = sum(1 for c in content_controls if c.get("tag", "").startswith("context."))
        document_count = sum(1 for c in content_controls if c.get("tag", "").startswith("document."))
        env_count = sum(1 for c in content_controls if c.get("tag", "").startswith("env."))
        block_count = sum(1 for c in content_controls if c.get("tag", "").startswith("dc-"))
        other_count = len(content_controls) - context_count - document_count - env_count - block_count
        
        tag_scores["context_tags"] = min(10, context_count * 2) if context_count > 0 else 0
        tag_scores["document_tags"] = min(10, document_count * 2) if document_count > 0 else 0
        tag_scores["env_tags"] = min(10, env_count * 5) if env_count > 0 else 0
        tag_scores["content_blocks"] = min(10, block_count * 5) if block_count > 0 else 0
        tag_scores["custom_tags"] = min(10, other_count * 3) if other_count > 0 else 0
        scores["tag_preservation"] = tag_scores
        
        # Score: Structural Integrity
        struct_scores = {}
        struct_scores["paragraphs"] = 10 if "<p>" in html_content else 5
        struct_scores["tables"] = 10 if "<table" in html_content or "table" not in original_path.lower() else 5
        struct_scores["lists"] = 10 if ("<ul>" in html_content or "<ol>" in html_content) or "list" not in original_path.lower() else 7
        struct_scores["headings"] = 10 if any(f"<h{i}" in html_content for i in range(1,7)) or "<strong>" in html_content else 7
        struct_scores["sections"] = 8  # Default good score
        scores["structural_integrity"] = struct_scores
        
        # Score: Formatting Quality
        format_scores = {}
        format_scores["fonts"] = 10 if "font-family" in html_content else 7
        format_scores["spacing"] = 10 if "line-height" in html_content else 7
        format_scores["alignment"] = 10 if "text-align" in html_content else 8
        format_scores["styles"] = 10 if ("<strong>" in html_content or "<em>" in html_content) else 7
        scores["formatting_quality"] = format_scores
        
        # Score: Special Elements
        special_scores = {}
        special_scores["conditionals"] = 10 if conditionals or "data-if" in html_content else (5 if "if" not in original_path.lower() else 0)
        special_scores["placeholders"] = 10 if placeholders else (8 if "[" not in str(content_controls) else 5)
        special_scores["date_formatting"] = 10 if "format=" in str(content_controls) else 8
        special_scores["nested_refs"] = 10 if any("." in c.get("tag", "") for c in content_controls) else 7
        scores["special_elements"] = special_scores
        
        # Score: Technical Quality
        tech_scores = {}
        tech_scores["html_validity"] = 10 if html_content.startswith("<!DOCTYPE html>") else 8
        tech_scores["email_compatibility"] = 10 if "inline" in html_content or "style=" in html_content else 7
        tech_scores["performance"] = 10 if processing_time < 0.1 else (8 if processing_time < 0.5 else 5)
        tech_scores["file_size"] = 10 if len(html_content) < 50000 else (7 if len(html_content) < 100000 else 5)
        tech_scores["confidence"] = min(10, confidence / 10)
        scores["technical_quality"] = tech_scores
        
        # Calculate weighted total
        total_score = 0
        for category, weight_info in self.rubric.items():
            category_score = sum(scores[category].values()) / len(scores[category])
            total_score += category_score * weight_info["weight"]
        
        # Determine grade
        if total_score >= 9:
            grade = "A+"
        elif total_score >= 8.5:
            grade = "A"
        elif total_score >= 8:
            grade = "B+"
        elif total_score >= 7.5:
            grade = "B"
        elif total_score >= 7:
            grade = "C+"
        elif total_score >= 6.5:
            grade = "C"
        elif total_score >= 6:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "scores": scores,
            "total_score": round(total_score, 2),
            "grade": grade,
            "sharedo_elements_count": len(content_controls) + len(placeholders) + len(conditionals),
            "confidence": confidence,
            "processing_time": processing_time,
            "html_size": len(html_content)
        }
    
    def categorize_document(self, file_path: str) -> str:
        """Categorize document by complexity"""
        file_name = os.path.basename(file_path)
        for category, files in self.document_categories.items():
            if any(file_name.startswith(f.split(".")[0]) for f in files):
                return category
        
        # Fallback based on file size
        size = os.path.getsize(file_path)
        if size < 20000:
            return "simple"
        elif size < 50000:
            return "moderate"
        elif size < 70000:
            return "complex"
        else:
            return "large"
    
    def test_all_documents(self, folder_path: str) -> Dict[str, Any]:
        """Test all documents in folder"""
        results_by_category = {
            "simple": [],
            "moderate": [],
            "complex": [],
            "large": []
        }
        
        # Get all DOCX files
        docx_files = [f for f in Path(folder_path).glob("*.docx") 
                      if not f.name.startswith("~$")]
        
        print(f"Found {len(docx_files)} documents to test")
        print("=" * 80)
        
        for i, file_path in enumerate(docx_files, 1):
            print(f"\n[{i}/{len(docx_files)}] Testing: {file_path.name}")
            print("-" * 40)
            
            # Categorize document
            category = self.categorize_document(str(file_path))
            print(f"Category: {category}")
            
            # Convert document
            print("Converting...", end=" ")
            start_time = time.time()
            conversion_result = self.convert_document(str(file_path))
            conversion_time = time.time() - start_time
            print(f"Done ({conversion_time:.2f}s)")
            
            # Analyze conversion
            print("Analyzing...", end=" ")
            analysis = self.analyze_conversion(str(file_path), conversion_result)
            print(f"Grade: {analysis.get('grade', 'N/A')}")
            
            # Store results
            result = {
                "file": file_path.name,
                "category": category,
                "size": file_path.stat().st_size,
                "conversion_time": conversion_time,
                "analysis": analysis
            }
            
            results_by_category[category].append(result)
            self.results.append(result)
        
        return results_by_category
    
    def generate_report(self, results: Dict[str, List]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE DOCX TO HTML CONVERSION TEST REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"API Endpoint: {self.api_url}")
        report.append("=" * 80)
        report.append("")
        
        # Overall statistics
        total_docs = sum(len(docs) for docs in results.values())
        successful = sum(1 for r in self.results if "error" not in r.get("analysis", {}))
        failed = total_docs - successful
        avg_score = sum(r["analysis"].get("total_score", 0) for r in self.results) / total_docs if total_docs > 0 else 0
        
        report.append("OVERALL STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Documents Tested: {total_docs}")
        report.append(f"Successful Conversions: {successful} ({successful/total_docs*100:.1f}%)")
        report.append(f"Failed Conversions: {failed}")
        report.append(f"Average Score: {avg_score:.2f}/10")
        report.append(f"Overall Grade: {self._score_to_grade(avg_score)}")
        report.append("")
        
        # Category breakdown
        report.append("RESULTS BY CATEGORY")
        report.append("-" * 40)
        
        for category, docs in results.items():
            if not docs:
                continue
                
            report.append(f"\n{category.upper()} DOCUMENTS ({len(docs)} files)")
            report.append("~" * 30)
            
            cat_avg_score = sum(d["analysis"].get("total_score", 0) for d in docs) / len(docs) if docs else 0
            cat_avg_time = sum(d["conversion_time"] for d in docs) / len(docs) if docs else 0
            
            report.append(f"Average Score: {cat_avg_score:.2f}/10 ({self._score_to_grade(cat_avg_score)})")
            report.append(f"Average Conversion Time: {cat_avg_time:.3f}s")
            
            # Individual files
            for doc in docs:
                analysis = doc["analysis"]
                report.append(f"\n  • {doc['file']}")
                report.append(f"    Size: {doc['size']:,} bytes")
                report.append(f"    Score: {analysis.get('total_score', 0):.2f}/10 (Grade: {analysis.get('grade', 'N/A')})")
                report.append(f"    Sharedo Elements: {analysis.get('sharedo_elements_count', 0)}")
                report.append(f"    Confidence: {analysis.get('confidence', 0):.1f}%")
                report.append(f"    Processing: {analysis.get('processing_time', 0):.3f}s")
                
                if "error" in analysis:
                    report.append(f"    ERROR: {analysis['error']}")
        
        # Detailed rubric analysis
        report.append("\n" + "=" * 80)
        report.append("RUBRIC CATEGORY ANALYSIS")
        report.append("-" * 40)
        
        category_totals = {}
        for category in self.rubric.keys():
            category_totals[category] = []
        
        for result in self.results:
            if "scores" in result["analysis"]:
                for category, scores in result["analysis"]["scores"].items():
                    avg = sum(scores.values()) / len(scores) if scores else 0
                    category_totals[category].append(avg)
        
        for category, weight_info in self.rubric.items():
            if category_totals[category]:
                avg = sum(category_totals[category]) / len(category_totals[category])
                report.append(f"\n{category.replace('_', ' ').title()} (Weight: {weight_info['weight']*100:.0f}%)")
                report.append(f"  Average Score: {avg:.2f}/10")
                
                # Show criteria performance
                for criterion, info in weight_info["criteria"].items():
                    report.append(f"    - {info['description']}")
        
        # Issues and recommendations
        report.append("\n" + "=" * 80)
        report.append("COMMON ISSUES IDENTIFIED")
        report.append("-" * 40)
        
        issues = self._identify_common_issues()
        for issue in issues:
            report.append(f"• {issue}")
        
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            report.append(f"• {rec}")
        
        return "\n".join(report)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 9:
            return "A+"
        elif score >= 8.5:
            return "A"
        elif score >= 8:
            return "B+"
        elif score >= 7.5:
            return "B"
        elif score >= 7:
            return "C+"
        elif score >= 6.5:
            return "C"
        elif score >= 6:
            return "D"
        else:
            return "F"
    
    def _identify_common_issues(self) -> List[str]:
        """Identify common issues across all conversions"""
        issues = []
        
        # Check for consistent problems
        low_confidence_count = sum(1 for r in self.results 
                                  if r["analysis"].get("confidence", 0) < 80)
        if low_confidence_count > len(self.results) * 0.3:
            issues.append(f"Low confidence scores in {low_confidence_count} documents")
        
        no_conditionals = sum(1 for r in self.results 
                             if r["analysis"].get("scores", {}).get("special_elements", {}).get("conditionals", 0) < 5)
        if no_conditionals > len(self.results) * 0.5:
            issues.append("Conditional blocks not well preserved in majority of documents")
        
        slow_conversions = sum(1 for r in self.results 
                              if r["analysis"].get("processing_time", 0) > 0.5)
        if slow_conversions > 0:
            issues.append(f"Slow processing times in {slow_conversions} documents")
        
        return issues if issues else ["No major systematic issues identified"]
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recs = []
        
        avg_score = sum(r["analysis"].get("total_score", 0) for r in self.results) / len(self.results) if self.results else 0
        
        if avg_score >= 8.5:
            recs.append("Service is performing excellently - ready for production use")
        elif avg_score >= 7.5:
            recs.append("Service is performing well - minor improvements could enhance quality")
        else:
            recs.append("Service needs improvement in several areas before production use")
        
        # Specific recommendations
        for result in self.results:
            if "scores" in result["analysis"]:
                scores = result["analysis"]["scores"]
                if scores.get("special_elements", {}).get("conditionals", 0) < 5:
                    recs.append("Improve handling of conditional (If/Then) blocks")
                    break
        
        # Performance recommendations
        avg_time = sum(r["conversion_time"] for r in self.results) / len(self.results) if self.results else 0
        if avg_time > 1.0:
            recs.append("Optimize conversion performance for large documents")
        
        return recs


# Main execution
if __name__ == "__main__":
    # API endpoint
    API_URL = "https://sharedo-docx-converter-dev.politeground-d6f68ba9.australiaeast.azurecontainerapps.io"
    
    # Initialize evaluator
    evaluator = ConversionEvaluator(API_URL)
    
    # Run tests
    print("\nStarting Comprehensive Document Conversion Testing")
    print("=" * 80)
    
    results = evaluator.test_all_documents("/Users/igorsharedo/Documents/Samples")
    
    # Generate and save report
    report = evaluator.generate_report(results)
    
    # Save report
    report_path = "/Users/igorsharedo/Documents/Prototype/Convert Docx To HTML/test_report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    
    print("\n" + "=" * 80)
    print(f"Testing complete! Report saved to: {report_path}")
    print("=" * 80)
    
    # Also print summary
    print(report)