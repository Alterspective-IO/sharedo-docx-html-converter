#!/usr/bin/env python3
"""Extract and analyze the actual XML structure with content controls"""

import zipfile
import xml.etree.ElementTree as ET
import re

def analyze_xml_structure(docx_path):
    """Extract and analyze content control structure in XML"""
    
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        if 'word/document.xml' in docx_zip.namelist():
            doc_xml = docx_zip.read('word/document.xml').decode('utf-8')
            
            # Save raw XML for inspection
            with open('document_raw.xml', 'w', encoding='utf-8') as f:
                f.write(doc_xml)
            
            print("Raw XML saved to document_raw.xml")
            
            # Parse and find SDT elements with their surrounding context
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            }
            
            root = ET.fromstring(doc_xml)
            
            # Find all paragraphs
            paragraphs = root.findall('.//w:p', namespaces)
            
            print(f"\nFound {len(paragraphs)} paragraphs")
            print("\n" + "=" * 60)
            print("PARAGRAPHS WITH CONTENT CONTROLS:")
            print("=" * 60)
            
            for p_idx, para in enumerate(paragraphs):
                # Get paragraph text
                texts = para.findall('.//w:t', namespaces)
                para_text = ''.join([t.text or '' for t in texts])
                
                # Check for SDT elements
                sdts = para.findall('.//w:sdt', namespaces)
                
                if sdts or 'Sharedo' in para_text:
                    print(f"\nParagraph {p_idx + 1}:")
                    print(f"  Full text: [{para_text}]")
                    
                    if sdts:
                        print(f"  Contains {len(sdts)} content control(s):")
                        
                        for sdt_idx, sdt in enumerate(sdts):
                            # Get SDT properties
                            sdt_pr = sdt.find('w:sdtPr', namespaces)
                            if sdt_pr:
                                tag_elem = sdt_pr.find('w:tag', namespaces)
                                alias_elem = sdt_pr.find('w:alias', namespaces)
                                
                                tag = tag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if tag_elem is not None else None
                                alias = alias_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if alias_elem is not None else None
                                
                                # Get content
                                sdt_content = sdt.find('.//w:sdtContent', namespaces)
                                content_text = ''
                                if sdt_content:
                                    content_texts = sdt_content.findall('.//w:t', namespaces)
                                    content_text = ''.join([t.text or '' for t in content_texts])
                                
                                print(f"    Control {sdt_idx + 1}:")
                                print(f"      Tag: {tag}")
                                print(f"      Alias: {alias}")
                                print(f"      Content: [{content_text}]")
                    
                    # Show run structure
                    runs = para.findall('.//w:r', namespaces)
                    if runs:
                        print(f"  Run structure ({len(runs)} runs):")
                        for r_idx, run in enumerate(runs):
                            run_texts = run.findall('.//w:t', namespaces)
                            run_text = ''.join([t.text or '' for t in run_texts])
                            if run_text:
                                # Check if this run is inside an SDT
                                parent = run.getparent()
                                in_sdt = False
                                while parent is not None:
                                    if parent.tag.endswith('sdt'):
                                        in_sdt = True
                                        break
                                    parent = parent.getparent()
                                
                                marker = " [IN SDT]" if in_sdt else ""
                                print(f"    Run {r_idx + 1}: [{run_text}]{marker}")

analyze_xml_structure("SUPLC1031.docx")