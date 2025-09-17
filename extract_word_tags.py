#!/usr/bin/env python3
"""Extract content controls and merge fields from Word document"""

import zipfile
import xml.etree.ElementTree as ET
import re
from pathlib import Path

def extract_word_content_controls(docx_path):
    """Extract all content controls and merge fields from Word document"""
    
    print("=" * 60)
    print(f"EXTRACTING WORD CONTENT CONTROLS FROM: {docx_path}")
    print("=" * 60)
    
    results = {
        'content_controls': [],
        'merge_fields': [],
        'custom_xml': []
    }
    
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        # List all files in the archive
        print("\n📁 Document Structure:")
        for file_name in docx_zip.namelist():
            if 'customXml' in file_name or 'document.xml' in file_name:
                print(f"  • {file_name}")
        
        # Extract and parse document.xml
        if 'word/document.xml' in docx_zip.namelist():
            doc_xml = docx_zip.read('word/document.xml').decode('utf-8')
            
            # Pretty print a sample to understand structure
            print("\n🔍 Searching for Content Controls (SDT elements)...")
            
            # Register namespaces
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
                'w15': 'http://schemas.microsoft.com/office/word/2012/wordml'
            }
            
            # Parse XML
            root = ET.fromstring(doc_xml)
            
            # Find all SDT (Structured Document Tag) elements
            sdt_count = 0
            for sdt in root.findall('.//w:sdt', namespaces):
                sdt_count += 1
                
                # Extract properties
                sdt_pr = sdt.find('w:sdtPr', namespaces)
                if sdt_pr is not None:
                    # Get tag
                    tag_elem = sdt_pr.find('w:tag', namespaces)
                    tag = tag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if tag_elem is not None else None
                    
                    # Get alias
                    alias_elem = sdt_pr.find('w:alias', namespaces)
                    alias = alias_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if alias_elem is not None else None
                    
                    # Get placeholder text
                    placeholder_elem = sdt_pr.find('.//w:docPartGallery', namespaces)
                    placeholder = placeholder_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if placeholder_elem is not None else None
                    
                    # Get content text
                    sdt_content = sdt.find('.//w:sdtContent', namespaces)
                    text_content = ''
                    if sdt_content is not None:
                        texts = sdt_content.findall('.//w:t', namespaces)
                        text_content = ' '.join([t.text for t in texts if t.text])
                    
                    if tag or alias or text_content:
                        control = {
                            'type': 'content_control',
                            'tag': tag,
                            'alias': alias,
                            'text': text_content,
                            'placeholder': placeholder
                        }
                        results['content_controls'].append(control)
                        print(f"\n  📌 Content Control {sdt_count}:")
                        print(f"     Tag: {tag}")
                        print(f"     Alias: {alias}")
                        print(f"     Text: {text_content[:50]}..." if len(text_content) > 50 else f"     Text: {text_content}")
            
            # Find merge fields (different from content controls)
            merge_field_pattern = re.compile(r'MERGEFIELD\s+([^\s]+)')
            merge_matches = merge_field_pattern.findall(doc_xml)
            if merge_matches:
                print(f"\n📮 Found {len(merge_matches)} Merge Fields:")
                for field in set(merge_matches):
                    results['merge_fields'].append(field)
                    print(f"  • {field}")
            
            # Look for simple field codes
            simple_fields = root.findall('.//w:fldSimple', namespaces)
            print(f"\n📝 Found {len(simple_fields)} Simple Fields")
            for field in simple_fields:
                instr = field.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}instr')
                if instr:
                    print(f"  • {instr[:50]}...")
        
        # Check for custom XML parts
        custom_xml_files = [f for f in docx_zip.namelist() if 'customXml' in f]
        if custom_xml_files:
            print(f"\n🔧 Found {len(custom_xml_files)} Custom XML Parts:")
            for xml_file in custom_xml_files:
                print(f"  • {xml_file}")
                if xml_file.endswith('.xml'):
                    try:
                        xml_content = docx_zip.read(xml_file).decode('utf-8')
                        # Extract first 200 chars for preview
                        preview = xml_content[:200].replace('\n', ' ')
                        print(f"    Preview: {preview}...")
                    except:
                        pass
    
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  • Content Controls: {len(results['content_controls'])}")
    print(f"  • Merge Fields: {len(results['merge_fields'])}")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    results = extract_word_content_controls("SUPLC1031.docx")
    
    # Save results for use in converter
    import json
    with open('word_tags.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Extraction complete! Results saved to word_tags.json")