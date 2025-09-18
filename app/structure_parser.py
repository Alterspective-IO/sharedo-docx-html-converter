"""
Advanced Structure Parser for Nested Tables and Conditionals
=============================================================
Handles complex document structures with deep nesting:
1. Multi-level tables (up to 10 levels)
2. Nested conditional blocks
3. Mixed content types
4. Complex formatting preservation

World-class implementation with state management and validation.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


class StructureType(Enum):
    """Types of document structures"""
    TABLE = "table"
    CONDITIONAL = "conditional"
    SECTION = "section"
    LIST = "list"
    MIXED = "mixed"


class ConditionalType(Enum):
    """Types of conditional structures"""
    IF_THEN = "if_then"
    IF_THEN_ELSE = "if_then_else"
    SWITCH_CASE = "switch_case"
    LOOP = "loop"
    NESTED = "nested"


@dataclass
class StructureNode:
    """Represents a node in the document structure tree"""
    type: StructureType
    depth: int
    content: Any
    children: List['StructureNode'] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    formatting: Dict[str, str] = field(default_factory=dict)
    conditional_info: Optional[Dict] = None


class AdvancedStructureParser:
    """
    Parses and preserves complex document structures.
    Handles nesting up to 10 levels with formatting preservation.
    """
    
    MAX_NESTING_DEPTH = 10
    
    # Enhanced conditional patterns
    CONDITIONAL_PATTERNS = {
        'if_simple': re.compile(r'\{\%\s*if\s+([^%]+)\s*\%\}', re.IGNORECASE),
        'if_complex': re.compile(r'if\s+(.+?)\s+(?:then|:)', re.IGNORECASE),
        'if_multiline': re.compile(r'(?:if|IF)\s*\n?\s*(.+?)\s*\n?\s*(?:then|THEN|:)', 
                                  re.IGNORECASE | re.MULTILINE),
        'endif': re.compile(r'\{\%\s*endif\s*\%\}|endif|ENDIF', re.IGNORECASE),
        'else': re.compile(r'\{\%\s*else\s*\%\}|else|ELSE', re.IGNORECASE),
        'elif': re.compile(r'\{\%\s*elif\s+([^%]+)\s*\%\}|elif\s+(.+)', re.IGNORECASE),
        'switch': re.compile(r'switch\s*\(([^)]+)\)', re.IGNORECASE),
        'case': re.compile(r'case\s+([^:]+):', re.IGNORECASE),
        'for_loop': re.compile(r'\{\%\s*for\s+(.+?)\s+in\s+(.+?)\s*\%\}', re.IGNORECASE)
    }
    
    def __init__(self):
        """Initialize the advanced structure parser"""
        self.structure_stack = []
        self.depth_counter = 0
        self.formatting_stack = []
        self.statistics = {
            'max_depth_reached': 0,
            'tables_parsed': 0,
            'conditionals_parsed': 0,
            'nested_structures': 0,
            'complex_structures': 0
        }
        
    def parse_document_structure(self, content: str) -> Tuple[StructureNode, str]:
        """
        Parse document content into a structure tree.
        
        Args:
            content: HTML or text content to parse
            
        Returns:
            Tuple of (root structure node, enhanced HTML)
        """
        # Create root node
        root = StructureNode(
            type=StructureType.SECTION,
            depth=0,
            content="document_root"
        )
        
        # Handle None or empty content
        if not content:
            return root, ""
        
        # Parse as HTML if applicable
        if '<' in content and '>' in content:
            enhanced_html = self._parse_html_structure(content, root)
        else:
            enhanced_html = self._parse_text_structure(content, root)
        
        # Update statistics
        self.statistics['max_depth_reached'] = self._calculate_max_depth(root)
        
        return root, enhanced_html
    
    def _parse_html_structure(self, html: str, parent: StructureNode) -> str:
        """
        Parse HTML content for complex structures.
        
        Args:
            html: HTML content
            parent: Parent structure node
            
        Returns:
            Enhanced HTML with structure preservation
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Process tables with nesting
        self._process_nested_tables(soup, parent)
        
        # Process conditional blocks
        self._process_conditional_blocks(soup, parent)
        
        # Process mixed content
        self._process_mixed_content(soup, parent)
        
        # Add structure metadata to HTML
        enhanced_html = self._add_structure_metadata(soup)
        
        return str(enhanced_html)
    
    def _process_nested_tables(self, soup: BeautifulSoup, parent: StructureNode, 
                              depth: int = 0):
        """
        Process nested tables maintaining structure and formatting.
        
        Args:
            soup: BeautifulSoup object
            parent: Parent structure node
            depth: Current nesting depth
        """
        if depth >= self.MAX_NESTING_DEPTH:
            logger.warning(f"Max table nesting depth {self.MAX_NESTING_DEPTH} reached")
            return
        
        tables = soup.find_all('table', recursive=False)
        
        for table in tables:
            self.statistics['tables_parsed'] += 1
            
            # Create table node
            table_node = StructureNode(
                type=StructureType.TABLE,
                depth=depth + 1,
                content=table,
                attributes=dict(table.attrs) if table.attrs else {}
            )
            
            # Extract formatting
            table_node.formatting = self._extract_formatting(table)
            
            # Check for nested tables
            nested_tables = table.find_all('table')
            if nested_tables:
                self.statistics['nested_structures'] += 1
                
                # Process each cell for nested structures
                for cell in table.find_all(['td', 'th']):
                    cell_tables = cell.find_all('table', recursive=False)
                    if cell_tables:
                        self._process_nested_tables(cell, table_node, depth + 1)
            
            # Add enhanced attributes for preservation
            table['data-nesting-level'] = str(depth + 1)
            table['data-structure-type'] = 'nested-table' if nested_tables else 'simple-table'
            
            # Preserve complex cell content
            for cell in table.find_all(['td', 'th']):
                self._preserve_cell_content(cell, depth + 1)
            
            parent.children.append(table_node)
    
    def _process_conditional_blocks(self, soup: BeautifulSoup, parent: StructureNode):
        """
        Process and enhance conditional blocks.
        
        Args:
            soup: BeautifulSoup object
            parent: Parent structure node
        """
        # Find text nodes that might contain conditionals
        text_nodes = soup.find_all(string=True)
        
        conditional_stack = []
        current_conditional = None
        
        for text_node in text_nodes:
            text = str(text_node)
            
            # Check for IF statements
            if_match = (
                self.CONDITIONAL_PATTERNS['if_simple'].search(text) or
                self.CONDITIONAL_PATTERNS['if_complex'].search(text) or
                self.CONDITIONAL_PATTERNS['if_multiline'].search(text)
            )
            
            if if_match:
                self.statistics['conditionals_parsed'] += 1
                
                # Start new conditional block
                condition = if_match.group(1) if if_match.groups() else ""
                
                current_conditional = StructureNode(
                    type=StructureType.CONDITIONAL,
                    depth=len(conditional_stack) + 1,
                    content=condition,
                    conditional_info={
                        'type': ConditionalType.IF_THEN,
                        'condition': condition,
                        'branches': []
                    }
                )
                
                conditional_stack.append(current_conditional)
                
                # Wrap in HTML element for preservation
                wrapper = soup.new_tag('div', **{
                    'data-conditional': 'if',
                    'data-condition': condition,
                    'data-depth': str(len(conditional_stack))
                })
                
                if text_node.parent:
                    text_node.wrap(wrapper)
            
            # Check for ELSE statements
            elif self.CONDITIONAL_PATTERNS['else'].search(text):
                if current_conditional:
                    current_conditional.conditional_info['type'] = ConditionalType.IF_THEN_ELSE
                    current_conditional.conditional_info['branches'].append('else')
                    
                    # Add else marker
                    wrapper = soup.new_tag('div', **{
                        'data-conditional': 'else',
                        'data-depth': str(len(conditional_stack))
                    })
                    
                    if text_node.parent:
                        text_node.wrap(wrapper)
            
            # Check for ENDIF statements
            elif self.CONDITIONAL_PATTERNS['endif'].search(text):
                if conditional_stack:
                    completed_conditional = conditional_stack.pop()
                    parent.children.append(completed_conditional)
                    
                    # Mark end of conditional
                    wrapper = soup.new_tag('div', **{
                        'data-conditional': 'endif',
                        'data-depth': str(len(conditional_stack) + 1)
                    })
                    
                    if text_node.parent:
                        text_node.wrap(wrapper)
                    
                    current_conditional = conditional_stack[-1] if conditional_stack else None
        
        # Handle nested conditionals
        if len(conditional_stack) > 1:
            self.statistics['complex_structures'] += 1
            
            # Mark as nested conditional structure
            for elem in soup.find_all(attrs={'data-conditional': True}):
                depth = int(elem.get('data-depth', 0))
                if depth > 1:
                    elem['data-nested-conditional'] = 'true'
    
    def _process_mixed_content(self, soup: BeautifulSoup, parent: StructureNode):
        """
        Process mixed content types (tables within conditionals, etc.).
        
        Args:
            soup: BeautifulSoup object
            parent: Parent structure node
        """
        # Find conditional blocks containing tables
        conditional_divs = soup.find_all('div', attrs={'data-conditional': 'if'})
        
        for cond_div in conditional_divs:
            tables_in_conditional = cond_div.find_all('table')
            
            if tables_in_conditional:
                self.statistics['complex_structures'] += 1
                
                # Create mixed structure node
                mixed_node = StructureNode(
                    type=StructureType.MIXED,
                    depth=parent.depth + 1,
                    content="conditional_with_table",
                    attributes={
                        'condition': cond_div.get('data-condition', ''),
                        'table_count': len(tables_in_conditional)
                    }
                )
                
                # Mark the structure
                cond_div['data-structure-type'] = 'mixed-conditional-table'
                
                # Enhance table handling within conditional
                for table in tables_in_conditional:
                    table['data-within-conditional'] = 'true'
                    table['data-conditional-depth'] = cond_div.get('data-depth', '1')
                
                parent.children.append(mixed_node)
    
    def _preserve_cell_content(self, cell: Tag, depth: int):
        """
        Preserve complex content within table cells.
        
        Args:
            cell: Table cell element
            depth: Current nesting depth
        """
        # Check for complex content
        has_list = cell.find(['ul', 'ol'])
        has_table = cell.find('table')
        has_multiple_paragraphs = len(cell.find_all('p')) > 1
        
        if has_list or has_table or has_multiple_paragraphs:
            cell['data-complex-content'] = 'true'
            cell['data-content-depth'] = str(depth)
            
            # Preserve formatting
            if has_list:
                for list_elem in cell.find_all(['ul', 'ol']):
                    list_elem['data-preserved-list'] = 'true'
                    
            if has_table:
                cell['data-has-nested-table'] = 'true'
    
    def _extract_formatting(self, element: Tag) -> Dict[str, str]:
        """
        Extract formatting information from an element.
        
        Args:
            element: HTML element
            
        Returns:
            Dictionary of formatting properties
        """
        formatting = {}
        
        # Extract inline styles
        if element.get('style'):
            style_str = element['style']
            styles = [s.strip() for s in style_str.split(';') if s.strip()]
            
            for style in styles:
                if ':' in style:
                    prop, value = style.split(':', 1)
                    formatting[prop.strip()] = value.strip()
        
        # Extract classes
        if element.get('class'):
            formatting['classes'] = ' '.join(element['class'])
        
        # Extract specific formatting attributes
        format_attrs = ['align', 'valign', 'width', 'height', 'bgcolor', 'border']
        for attr in format_attrs:
            if element.get(attr):
                formatting[attr] = element[attr]
        
        return formatting
    
    def _add_structure_metadata(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Add metadata to preserve structure information.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Enhanced BeautifulSoup with metadata
        """
        # Add document-level metadata
        if soup.body:
            soup.body['data-structure-parsed'] = 'true'
            soup.body['data-max-depth'] = str(self.statistics['max_depth_reached'])
            soup.body['data-table-count'] = str(self.statistics['tables_parsed'])
            soup.body['data-conditional-count'] = str(self.statistics['conditionals_parsed'])
        
        # Add CSS for structure visualization (optional)
        style_tag = soup.new_tag('style')
        style_tag.string = """
        [data-nesting-level] { position: relative; }
        [data-nesting-level="1"] { border-left: 2px solid #e0e0e0; }
        [data-nesting-level="2"] { border-left: 2px solid #d0d0d0; }
        [data-nesting-level="3"] { border-left: 2px solid #c0c0c0; }
        [data-conditional] { background-color: rgba(255, 243, 205, 0.1); }
        [data-nested-conditional] { background-color: rgba(255, 243, 205, 0.2); }
        [data-complex-content] { background-color: rgba(230, 247, 255, 0.1); }
        """
        
        if soup.head:
            soup.head.append(style_tag)
        
        return soup
    
    def _parse_text_structure(self, text: str, parent: StructureNode) -> str:
        """
        Parse plain text content for structures.
        
        Args:
            text: Plain text content
            parent: Parent structure node
            
        Returns:
            Enhanced text with structure markers
        """
        lines = text.split('\n')
        enhanced_lines = []
        
        for line in lines:
            # Check for conditional patterns
            if any(pattern.search(line) for pattern in self.CONDITIONAL_PATTERNS.values()):
                self.statistics['conditionals_parsed'] += 1
                enhanced_lines.append(f'<!-- CONDITIONAL: {line.strip()} -->\n{line}')
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _calculate_max_depth(self, node: StructureNode) -> int:
        """
        Calculate maximum depth in structure tree.
        
        Args:
            node: Root node
            
        Returns:
            Maximum depth
        """
        if not node.children:
            return node.depth
        
        return max(self._calculate_max_depth(child) for child in node.children)
    
    def validate_structure(self, root: StructureNode) -> Dict[str, Any]:
        """
        Validate the parsed structure for integrity.
        
        Args:
            root: Root structure node
            
        Returns:
            Validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'structure_summary': {}
        }
        
        # Check maximum depth
        max_depth = self._calculate_max_depth(root)
        if max_depth > self.MAX_NESTING_DEPTH:
            validation_results['warnings'].append(
                f"Structure depth {max_depth} exceeds recommended maximum {self.MAX_NESTING_DEPTH}"
            )
        
        # Check for unclosed conditionals
        open_conditionals = self._find_unclosed_conditionals(root)
        if open_conditionals:
            validation_results['is_valid'] = False
            validation_results['errors'].append(
                f"Found {len(open_conditionals)} unclosed conditional blocks"
            )
        
        # Check for invalid nesting
        invalid_nesting = self._find_invalid_nesting(root)
        if invalid_nesting:
            validation_results['warnings'].extend(invalid_nesting)
        
        # Generate structure summary
        validation_results['structure_summary'] = {
            'total_nodes': self._count_nodes(root),
            'max_depth': max_depth,
            'table_nodes': self._count_by_type(root, StructureType.TABLE),
            'conditional_nodes': self._count_by_type(root, StructureType.CONDITIONAL),
            'mixed_nodes': self._count_by_type(root, StructureType.MIXED)
        }
        
        return validation_results
    
    def _find_unclosed_conditionals(self, node: StructureNode) -> List[StructureNode]:
        """Find unclosed conditional blocks."""
        unclosed = []
        
        if node.type == StructureType.CONDITIONAL:
            if node.conditional_info and not node.conditional_info.get('closed', True):
                unclosed.append(node)
        
        for child in node.children:
            unclosed.extend(self._find_unclosed_conditionals(child))
        
        return unclosed
    
    def _find_invalid_nesting(self, node: StructureNode) -> List[str]:
        """Find invalid nesting patterns."""
        warnings = []
        
        # Check for tables nested too deeply
        if node.type == StructureType.TABLE and node.depth > 5:
            warnings.append(f"Table nested {node.depth} levels deep may cause rendering issues")
        
        # Check for conditionals in complex structures
        if node.type == StructureType.MIXED and node.depth > 3:
            warnings.append(f"Complex mixed structure at depth {node.depth}")
        
        for child in node.children:
            warnings.extend(self._find_invalid_nesting(child))
        
        return warnings
    
    def _count_nodes(self, node: StructureNode) -> int:
        """Count total nodes in tree."""
        return 1 + sum(self._count_nodes(child) for child in node.children)
    
    def _count_by_type(self, node: StructureNode, node_type: StructureType) -> int:
        """Count nodes of specific type."""
        count = 1 if node.type == node_type else 0
        return count + sum(self._count_by_type(child, node_type) for child in node.children)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get parser statistics."""
        return self.statistics.copy()