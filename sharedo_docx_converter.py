#!/usr/bin/env python3
"""
Advanced Sharedo DOCX to HTML Converter
Handles Sharedo-specific tags, conditionals, loops, and data bindings
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from bs4 import BeautifulSoup
import html
import zipfile

class SharedoAdvancedConverter:
    """Sharedo-specific DOCX to HTML converter with full tag support"""
    
    def __init__(self):
        # Sharedo tag patterns
        self.patterns = {
            'content_control': re.compile(r'«([^»]+)»'),  # Word content controls
            'placeholder': re.compile(r'\[_+\]'),
            'handlebars': re.compile(r'\{\{([^}]+)\}\}'),
            'context_var': re.compile(r'(context\.[a-zA-Z0-9._!?&=]+)'),
            'document_var': re.compile(r'(document\.[a-zA-Z0-9._!?&=]+)'),
            'conditional': re.compile(r'#if\s+(.+?)(?:#else(.+?))?#endif', re.DOTALL),
            'loop': re.compile(r'#foreach\s+(.+?)#endforeach', re.DOTALL),
        }
        
        self.content_controls = []
    
    def extract_content_controls(self, docx_path):
        """Extract content control tags from DOCX XML"""
        controls = []
        
        with zipfile.ZipFile(docx_path, 'r') as docx_zip:
            # Check document.xml for content controls
            if 'word/document.xml' in docx_zip.namelist():
                xml_content = docx_zip.read('word/document.xml').decode('utf-8')
                
                # Find all sdtContent elements (content controls)
                sdt_pattern = re.compile(r'<w:sdt[^>]*>.*?<w:sdtContent>(.*?)</w:sdtContent>.*?</w:sdt>', re.DOTALL)
                sdt_matches = sdt_pattern.findall(xml_content)
                
                # Find tags/aliases
                tag_pattern = re.compile(r'<w:tag w:val="([^"]+)"/>')
                alias_pattern = re.compile(r'<w:alias w:val="([^"]+)"/>')
                
                for match in re.finditer(r'<w:sdt[^>]*>.*?</w:sdt>', xml_content, re.DOTALL):
                    sdt_content = match.group()
                    
                    tag_match = tag_pattern.search(sdt_content)
                    alias_match = alias_pattern.search(sdt_content)
                    
                    if tag_match or alias_match:
                        control = {
                            'tag': tag_match.group(1) if tag_match else None,
                            'alias': alias_match.group(1) if alias_match else None,
                            'text': self._extract_text_from_sdt(sdt_content)
                        }
                        controls.append(control)
        
        return controls
    
    def _extract_text_from_sdt(self, sdt_xml):
        """Extract text from SDT XML content"""
        text_pattern = re.compile(r'<w:t[^>]*>([^<]+)</w:t>')
        texts = text_pattern.findall(sdt_xml)
        return ' '.join(texts)
    
    def convert(self, docx_path, output_path=None):
        """Convert DOCX to Sharedo HTML template"""
        
        # Extract content controls first
        self.content_controls = self.extract_content_controls(docx_path)
        print(f"Found {len(self.content_controls)} content controls")
        
        # Process document
        doc = Document(docx_path)
        html_content = self._generate_sharedo_html(doc)
        
        if output_path:
            Path(output_path).write_text(html_content, encoding='utf-8')
            print(f"✅ Sharedo HTML template saved to: {output_path}")
        
        return html_content
    
    def _generate_sharedo_html(self, doc):
        """Generate Sharedo-compatible HTML"""
        html_parts = []
        
        # HTML header (email-optimized)
        html_parts.append(self._get_html_header())
        
        # Process document body with Sharedo tags
        body_content = self._process_sharedo_body(doc)
        html_parts.append(body_content)
        
        # HTML footer
        html_parts.append(self._get_html_footer())
        
        # Beautify
        soup = BeautifulSoup(''.join(html_parts), 'html.parser')
        return soup.prettify()
    
    def _get_html_header(self):
        """Sharedo-optimized HTML header"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Sharedo Email Template</title>
    <style type="text/css">
        /* Reset Styles */
        body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
        table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }
        img { -ms-interpolation-mode: bicubic; border: 0; outline: none; }
        
        /* Base Styles */
        body {
            margin: 0;
            padding: 0;
            width: 100% !important;
            min-width: 100% !important;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333333;
        }
        
        /* Container */
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Typography */
        h1, h2, h3 { margin: 0 0 10px 0; font-weight: bold; }
        p { margin: 0 0 10px 0; }
        
        /* Tables */
        .table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .table th, .table td { padding: 8px; border: 1px solid #ddd; text-align: left; }
        .table th { background-color: #f8f9fa; font-weight: bold; }
        
        /* Sharedo Tags */
        [data-tag] {
            background-color: #e6f7ff;
            padding: 1px 3px;
            border-radius: 2px;
            font-family: monospace;
            font-size: 0.9em;
        }
        
        [data-if], [data-foreach] {
            border-left: 3px solid #0969da;
            padding-left: 10px;
            margin: 10px 0;
        }
        
        [data-content-block] {
            background-color: #f0f0f0;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="email-container">'''
    
    def _get_html_footer(self):
        """HTML footer"""
        return '''    </div>
</body>
</html>'''
    
    def _process_sharedo_body(self, doc):
        """Process document with Sharedo tag preservation"""
        content_parts = []
        
        # Track if we're inside special blocks
        in_conditional = False
        in_loop = False
        block_content = []
        
        for element in self._iter_block_items(doc):
            if hasattr(element, 'text'):  # Paragraph
                para_html = self._process_sharedo_paragraph(element)
                
                # Check for block markers
                text = element.text.strip()
                
                if '#if' in text:
                    in_conditional = True
                    condition = self._extract_condition(text)
                    content_parts.append(f'<div data-if="{html.escape(condition)}">')
                elif '#endif' in text:
                    in_conditional = False
                    content_parts.append('</div>')
                elif '#foreach' in text:
                    in_loop = True
                    loop_var = self._extract_loop_variable(text)
                    content_parts.append(f'<div data-foreach="{html.escape(loop_var)}">')
                elif '#endforeach' in text:
                    in_loop = False
                    content_parts.append('</div>')
                elif para_html:
                    content_parts.append(para_html)
                    
            elif hasattr(element, 'rows'):  # Table
                table_html = self._process_sharedo_table(element)
                if table_html:
                    content_parts.append(table_html)
        
        return '\n'.join(content_parts)
    
    def _iter_block_items(self, document):
        """Yield paragraphs and tables in order"""
        from docx.document import Document as DocumentType
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        
        parent = document if isinstance(document, DocumentType) else document._element
        
        if hasattr(parent, 'element'):
            parent_elm = parent.element.body
        else:
            parent_elm = parent.body if hasattr(parent, 'body') else parent
        
        for child in parent_elm.iterchildren():
            if child.tag.endswith('p'):
                yield Paragraph(child, document if isinstance(document, DocumentType) else document._parent)
            elif child.tag.endswith('tbl'):
                yield Table(child, document if isinstance(document, DocumentType) else document._parent)
    
    def _process_sharedo_paragraph(self, paragraph):
        """Process paragraph with Sharedo tag conversion"""
        if not paragraph.text.strip():
            return ''
        
        text = paragraph.text
        
        # Skip directive lines
        if text.strip().startswith('#'):
            return ''
        
        # Process content controls (merge fields)
        for control in self.content_controls:
            if control['text'] in text:
                tag = control['tag'] or control['alias'] or control['text']
                text = text.replace(
                    control['text'],
                    f'<span data-tag="{html.escape(tag)}">{html.escape(tag)}</span>'
                )
        
        # Convert Word merge fields «field»
        text = self.patterns['content_control'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        # Convert placeholders [_____]
        text = self.patterns['placeholder'].sub(
            lambda m: f'<span data-tag="placeholder">[_____]</span>',
            text
        )
        
        # Convert {{handlebars}} variables
        text = self.patterns['handlebars'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        # Detect context variables
        text = self.patterns['context_var'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        # Detect document variables
        text = self.patterns['document_var'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        # Apply paragraph formatting
        styles = []
        
        # Alignment
        if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            styles.append('text-align: center')
        elif paragraph.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
            styles.append('text-align: right')
        
        # Process runs for formatting
        formatted_text = self._process_runs_with_formatting(paragraph)
        
        # Heading detection
        if self._is_heading(paragraph):
            level = self._get_heading_level(paragraph)
            style_str = '; '.join(styles) if styles else ''
            return f'<h{level} style="{style_str}">{formatted_text or text}</h{level}>'
        else:
            style_str = '; '.join(styles) if styles else ''
            return f'<p style="{style_str}">{formatted_text or text}</p>'
    
    def _process_runs_with_formatting(self, paragraph):
        """Process paragraph runs to preserve formatting"""
        if not paragraph.runs:
            return None
        
        formatted_parts = []
        
        for run in paragraph.runs:
            if not run.text:
                continue
            
            text = run.text
            
            # Apply Sharedo tag conversions to run text
            # Convert merge fields
            text = self.patterns['content_control'].sub(
                lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
                text
            )
            
            # Apply text formatting
            if run.bold:
                text = f'<strong>{text}</strong>'
            if run.italic:
                text = f'<em>{text}</em>'
            if run.underline:
                text = f'<u>{text}</u>'
            
            formatted_parts.append(text)
        
        return ''.join(formatted_parts) if formatted_parts else None
    
    def _process_sharedo_table(self, table):
        """Process table with Sharedo support"""
        html_parts = ['<figure class="table"><table>']
        
        # Check if table has foreach directive
        first_cell = table.rows[0].cells[0].text if table.rows else ''
        
        has_header = False
        start_row = 0
        
        # Detect header row
        if table.rows and not '#foreach' in first_cell:
            has_header = True
            html_parts.append('<thead><tr>')
            for cell in table.rows[0].cells:
                cell_text = self._convert_sharedo_tags(cell.text)
                html_parts.append(f'<th>{cell_text}</th>')
            html_parts.append('</tr></thead>')
            start_row = 1
        
        # Body rows
        html_parts.append('<tbody>')
        
        for row_idx in range(start_row, len(table.rows)):
            row = table.rows[row_idx]
            
            # Check for foreach in row
            row_text = ' '.join([cell.text for cell in row.cells])
            if '#foreach' in row_text:
                foreach_var = self._extract_loop_variable(row_text)
                html_parts.append(f'<tr data-foreach="{html.escape(foreach_var)}">')
            else:
                html_parts.append('<tr>')
            
            for cell in row.cells:
                cell_text = self._convert_sharedo_tags(cell.text)
                html_parts.append(f'<td>{cell_text}</td>')
            
            html_parts.append('</tr>')
        
        html_parts.append('</tbody>')
        html_parts.append('</table></figure>')
        
        return '\n'.join(html_parts)
    
    def _convert_sharedo_tags(self, text):
        """Convert Sharedo tags in text"""
        if not text:
            return ''
        
        # Remove directive markers
        text = re.sub(r'#(if|endif|foreach|endforeach|else)', '', text)
        
        # Convert merge fields
        text = self.patterns['content_control'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        # Convert other patterns
        text = self.patterns['placeholder'].sub('[_____]', text)
        
        # Convert context/document variables
        text = self.patterns['context_var'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        text = self.patterns['document_var'].sub(
            lambda m: f'<span data-tag="{html.escape(m.group(1))}">{html.escape(m.group(1))}</span>',
            text
        )
        
        return text.strip()
    
    def _extract_condition(self, text):
        """Extract condition from #if statement"""
        match = re.search(r'#if\s+(.+?)(?:#|$)', text)
        return match.group(1).strip() if match else ''
    
    def _extract_loop_variable(self, text):
        """Extract variable from #foreach statement"""
        match = re.search(r'#foreach\s+(.+?)(?:#|$)', text)
        return match.group(1).strip() if match else ''
    
    def _is_heading(self, paragraph):
        """Check if paragraph is a heading"""
        return paragraph.style and paragraph.style.name.startswith('Heading')
    
    def _get_heading_level(self, paragraph):
        """Get heading level from style"""
        if paragraph.style and paragraph.style.name.startswith('Heading'):
            try:
                return int(paragraph.style.name.replace('Heading ', ''))
            except:
                return 2
        return 2


def main():
    """Convert SUPLC1031.docx with Sharedo tag preservation"""
    converter = SharedoAdvancedConverter()
    
    docx_file = "SUPLC1031.docx"
    output_file = "SUPLC1031_sharedo_template.html"
    
    print("🚀 Starting Sharedo DOCX to HTML Conversion")
    print("=" * 50)
    print(f"Input: {docx_file}")
    
    # Perform conversion
    html_content = converter.convert(docx_file, output_file)
    
    # Count Sharedo elements
    soup = BeautifulSoup(html_content, 'html.parser')
    data_tags = soup.find_all(attrs={'data-tag': True})
    data_ifs = soup.find_all(attrs={'data-if': True})
    data_foreach = soup.find_all(attrs={'data-foreach': True})
    
    print("\n📊 Conversion Statistics:")
    print(f"  • Output: {output_file}")
    print(f"  • HTML Size: {len(html_content)} characters")
    print(f"  • Sharedo Data Tags: {len(data_tags)}")
    print(f"  • Conditional Blocks: {len(data_ifs)}")
    print(f"  • Foreach Loops: {len(data_foreach)}")
    
    print("\n✅ Sharedo template conversion completed!")
    print("📧 HTML optimized for Sharedo email system")
    
    return html_content


if __name__ == "__main__":
    main()