#!/usr/bin/env python3
"""Validate and test the HTML output"""

from pathlib import Path
from bs4 import BeautifulSoup
import re

def validate_html(html_file):
    """Validate the generated HTML against our quality rubric"""
    
    html_content = Path(html_file).read_text(encoding='utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("=" * 60)
    print("📋 HTML VALIDATION REPORT")
    print("=" * 60)
    
    # Score tracking
    score = 0
    max_score = 100
    
    # 1. Template Variable Preservation (20 points)
    print("\n1️⃣ Template Variable Preservation")
    placeholders = re.findall(r'\[_+\]', html_content)
    if placeholders:
        print(f"   ✅ Found {len(placeholders)} placeholder variables")
        score += 20
    else:
        print("   ⚠️ No placeholder variables found")
    
    # 2. Email Compatibility (20 points)
    print("\n2️⃣ Email Compatibility")
    
    # Check for inline CSS
    inline_styles = soup.find_all(style=True)
    if inline_styles:
        print(f"   ✅ Inline CSS found ({len(inline_styles)} elements)")
        score += 5
    
    # Check for table-based layout
    tables = soup.find_all('table')
    if tables:
        print(f"   ✅ Table-based layout used ({len(tables)} tables)")
        score += 5
    
    # Check for viewport meta tag
    viewport = soup.find('meta', {'name': 'viewport'})
    if viewport:
        print("   ✅ Mobile viewport meta tag present")
        score += 5
    
    # Check for MSO conditionals
    if '<!--[if mso]>' in html_content:
        print("   ✅ Outlook MSO conditionals present")
        score += 5
    
    # 3. Formatting Fidelity (15 points)
    print("\n3️⃣ Formatting Fidelity")
    
    # Check for text formatting
    if soup.find_all(['strong', 'em', 'u']):
        print("   ✅ Text formatting tags present")
        score += 7
    
    # Check for style attributes
    elements_with_style = soup.find_all(style=True)
    if len(elements_with_style) > 5:
        print(f"   ✅ Rich styling preserved ({len(elements_with_style)} styled elements)")
        score += 8
    
    # 4. Structure Preservation (15 points)
    print("\n4️⃣ Structure Preservation")
    
    paragraphs = soup.find_all('p')
    if paragraphs:
        print(f"   ✅ Paragraph structure maintained ({len(paragraphs)} paragraphs)")
        score += 15
    
    # 5. Code Quality (10 points)
    print("\n5️⃣ Code Quality")
    
    # Check for DOCTYPE
    if '<!DOCTYPE html>' in html_content:
        print("   ✅ Valid HTML5 DOCTYPE")
        score += 3
    
    # Check for semantic HTML
    if soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table']):
        print("   ✅ Semantic HTML elements used")
        score += 4
    
    # Check for proper encoding
    if soup.find('meta', {'charset': 'UTF-8'}):
        print("   ✅ UTF-8 encoding specified")
        score += 3
    
    # 6. Performance (10 points)
    print("\n6️⃣ Performance")
    file_size_kb = len(html_content) / 1024
    if file_size_kb < 100:
        print(f"   ✅ Efficient file size ({file_size_kb:.2f} KB)")
        score += 10
    
    # 7. Error Handling (5 points)
    print("\n7️⃣ Error Handling")
    
    # Check for proper HTML structure
    if soup.html and soup.body:
        print("   ✅ Valid HTML structure")
        score += 5
    
    # 8. Extensibility (5 points)
    print("\n8️⃣ Extensibility")
    
    # Check for CSS classes
    elements_with_classes = soup.find_all(class_=True)
    if elements_with_classes:
        print(f"   ✅ CSS classes for extensibility ({len(elements_with_classes)} elements)")
        score += 5
    
    # Final Score
    print("\n" + "=" * 60)
    print(f"🎯 FINAL SCORE: {score}/{max_score} = {score/10:.1f}/10")
    print("=" * 60)
    
    # Quality Assessment
    if score >= 90:
        print("⭐ EXCELLENT - World-class conversion!")
    elif score >= 80:
        print("✅ VERY GOOD - High-quality conversion")
    elif score >= 70:
        print("👍 GOOD - Acceptable conversion")
    else:
        print("⚠️ NEEDS IMPROVEMENT")
    
    # Preview first 500 chars of body content
    body = soup.find('body')
    if body:
        body_text = body.get_text(strip=True)[:500]
        print("\n📄 CONTENT PREVIEW:")
        print("-" * 40)
        print(body_text)
        print("...")
    
    return score

if __name__ == "__main__":
    score = validate_html("sharedo_template_output.html")
    
    print("\n✨ Validation complete!")