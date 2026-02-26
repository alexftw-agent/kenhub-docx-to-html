import io
import re
from docx import Document
from lxml import etree
from typing import List, Dict, Any, Tuple, Optional

def convert_docx_to_html(content: bytes) -> Dict[str, Any]:
    """
    Main conversion function that takes DOCX bytes and returns HTML + metadata
    """
    # Parse the DOCX
    doc = Document(io.BytesIO(content))
    
    # Extract metadata and determine content type
    metadata, content_type = extract_metadata_and_type(doc)
    
    # Process the document content
    html_parts = []
    warnings = []
    
    # Track list state
    current_list = None
    current_list_type = None
    current_list_id = None
    
    # Skip metadata paragraphs at the start
    start_idx = skip_metadata_paragraphs(doc.paragraphs)
    
    for i, paragraph in enumerate(doc.paragraphs[start_idx:], start_idx):
        # Skip empty paragraphs
        if not paragraph.text.strip():
            continue
            
        # Check for special markers
        special_html, special_warnings = process_special_markers(paragraph.text)
        if special_html:
            # Close any open list before special content
            if current_list:
                html_parts.append(f"</{current_list}>")
                current_list = None
            html_parts.append(special_html)
            warnings.extend(special_warnings)
            continue
        
        # Check if this is a list item
        list_info = get_list_info(paragraph)
        
        if list_info:
            list_type, list_id = list_info
            
            # Start new list or continue existing
            if current_list_id != list_id:
                # Close previous list
                if current_list:
                    html_parts.append(f"</{current_list}>")
                
                # Start new list
                current_list = list_type
                current_list_id = list_id
                html_parts.append(f"<{list_type}>")
            
            # Add list item
            item_html = process_paragraph_content(paragraph)
            html_parts.append(f"  <li>{item_html}</li>")
        else:
            # Close any open list
            if current_list:
                html_parts.append(f"</{current_list}>")
                current_list = None
                current_list_id = None
            
            # Regular paragraph or heading
            para_html = process_regular_paragraph(paragraph)
            if para_html:
                html_parts.append(para_html)
    
    # Close any remaining open list
    if current_list:
        html_parts.append(f"</{current_list}>")
    
    # Process tables
    for table in doc.tables:
        table_html = process_table(table)
        html_parts.append(table_html)
    
    # Apply content wrappers based on type
    final_html = apply_content_wrappers(html_parts, content_type, metadata)
    
    return {
        "html": final_html,
        "metadata": metadata,
        "warnings": warnings
    }

def extract_metadata_and_type(doc: Document) -> Tuple[Dict[str, str], str]:
    """Extract metadata from document and determine content type"""
    metadata = {
        "title": "",
        "description": "",
        "type": "article",
        "seo_title": "",
        "seo_description": ""
    }
    
    # Look for metadata in first few paragraphs
    for para in doc.paragraphs[:10]:
        text = para.text.strip()
        if text.startswith("Title:"):
            metadata["title"] = text[6:].strip()
        elif text.startswith("Description:"):
            metadata["description"] = text[12:].strip()
        elif text.startswith("SEO title:"):
            metadata["seo_title"] = text[10:].strip()
        elif text.startswith("SEO description:"):
            metadata["seo_description"] = text[16:].strip()
    
    # Determine content type - study_unit if has learning objectives
    content_type = "article"
    for para in doc.paragraphs:
        if "learning objective" in para.text.lower() or "after completing this study unit" in para.text.lower():
            content_type = "study_unit"
            break
    
    metadata["type"] = content_type
    return metadata, content_type

def skip_metadata_paragraphs(paragraphs: List) -> int:
    """Skip metadata paragraphs at the start and return the index to start processing"""
    for i, para in enumerate(paragraphs):
        text = para.text.strip()
        if not text:
            continue
        if not (text.startswith("Title:") or text.startswith("Description:") or 
                text.startswith("SEO title:") or text.startswith("SEO description:") or
                text.startswith("Container:") or text.startswith("Position:")):
            return i
    return 0

def get_list_info(paragraph) -> Optional[Tuple[str, str]]:
    """Check if paragraph is a list item and return (list_type, list_id)"""
    try:
        # Access the XML to check for numPr
        p_xml = paragraph._element
        numPr = p_xml.xpath('.//w:numPr', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        
        if numPr:
            numId_elem = numPr[0].xpath('./w:numId', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
            ilvl_elem = numPr[0].xpath('./w:ilvl', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
            
            if numId_elem:
                num_id = numId_elem[0].get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                # For simplicity, treat all as unordered lists unless we detect numbers
                # TODO: Check numbering definitions to determine ul vs ol
                return ("ul", num_id)
    except:
        pass
    
    return None

def process_paragraph_content(paragraph) -> str:
    """Process the runs within a paragraph to handle formatting"""
    result_parts = []
    
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue
            
        # Apply formatting
        if run.bold and run.italic:
            text = f"<strong><em>{text}</em></strong>"
        elif run.bold:
            text = f"<strong>{text}</strong>"
        elif run.italic:
            text = f"<em>{text}</em>"
        
        result_parts.append(text)
    
    return "".join(result_parts)

def process_regular_paragraph(paragraph) -> str:
    """Process a regular paragraph (not list item)"""
    style_name = paragraph.style.name if paragraph.style else "Normal"
    text = paragraph.text.strip()
    
    if not text:
        return ""
    
    # Skip metadata lines
    if any(text.startswith(prefix) for prefix in ["Title:", "Description:", "SEO title:", "SEO description:", "Container:", "Position:"]):
        return ""
    
    # Handle headings
    if style_name == "Heading 1" or style_name == "Title":
        return ""  # Skip titles as per rules
    elif style_name == "Heading 2":
        return f"<h2>{text}</h2>"
    elif style_name == "Heading 3":
        return f"<h3>{text}</h3>"
    else:
        # Regular paragraph
        content = process_paragraph_content(paragraph)
        return f"<p>{content}</p>"

def process_special_markers(text: str) -> Tuple[str, List[str]]:
    """Process special markers like [Video:], [Table of Contents], etc."""
    warnings = []
    
    # Video markers
    video_match = re.search(r'\[Video:\s*([^\]]*)\]', text, re.IGNORECASE)
    if video_match:
        warnings.append(f"Video placeholder needs ID assignment: {video_match.group(1)}")
        return '<div class="embedded-video-container embedded-widget" data-controller="embedded_video" data-embedded_video-id-value="XXXX" isvisible="true"></div>', warnings
    
    # Table of Contents
    if re.search(r'\[Table of [Cc]ontents\]', text):
        return '<div class="article-table-of-contents" data-skip-algolia="1">Table of Contents</div>', warnings
    
    # Blue box
    blue_box_match = re.search(r'\[Blue box:\s*([^\]]*)\]', text, re.IGNORECASE)
    if blue_box_match:
        content = blue_box_match.group(1)
        return f'<div class="highlighted-box"><p>{content}</p></div>', warnings
    
    # Green highlight / Highlights gallery
    highlight_match = re.search(r'\[(Green highlight|Highlights gallery)[^\]]*\]\s*([^\n]*)', text, re.IGNORECASE)
    if highlight_match:
        slugs = highlight_match.group(2).strip()
        return f'<div class="image-gallery-container embedded-widget outset-left open" data-image-slugs="{slugs}"></div>', warnings
    
    # Gallery pattern
    gallery_match = re.search(r'Gallery:\s*([^\n]*)', text, re.IGNORECASE)
    if gallery_match:
        terms = gallery_match.group(1).strip()
        # Convert terms to slugs (simplified)
        slugs = ",".join(term.strip().lower().replace(" ", "-") for term in terms.split(","))
        return f'<div class="image-gallery-container embedded-widget open" data-image-slugs="{slugs}"></div>', warnings
    
    # Overview images [Caption]Text pattern
    caption_match = re.search(r'\[([^\]]+)\](.+)', text)
    if caption_match:
        warnings.append(f"Overview image placeholder needs ID assignment: {caption_match.group(1)}")
        return '<!-- OVERVIEW IMAGE: Manual ID assignment needed -->', warnings
    
    # Content box links
    if '/en/study/' in text or '/en/custom-quizzes/' in text:
        link = text.strip()
        return f'<div class="contentbox-container" data-contentbox-link="{link}" data-skip-algolia="1">{link}</div>', warnings
    
    return "", warnings

def process_table(table) -> str:
    """Convert DOCX table to HTML"""
    rows_html = []
    caption = ""
    
    # Check if first row is caption (merged cells)
    first_row = table.rows[0]
    if len(first_row.cells) == 1 or (len(first_row.cells) > 1 and first_row.cells[0].text.strip()):
        # Treat first row as caption if it seems like one
        cell_text = first_row.cells[0].text.strip()
        if cell_text and not any(cell.text.strip() for cell in first_row.cells[1:]):
            caption = cell_text
            start_row = 1
        else:
            start_row = 0
    else:
        start_row = 0
    
    # Process data rows
    for row in table.rows[start_row:]:
        cells_html = []
        for cell in row.cells:
            # Process cell content with line breaks
            cell_parts = []
            for para in cell.paragraphs:
                if para.text.strip():
                    cell_parts.append(process_paragraph_content(para))
            
            cell_content = "<br>".join(cell_parts)
            cells_html.append(f"<td>{cell_content}</td>")
        
        rows_html.append(f"    <tr>\n      {chr(10).join(cells_html)}\n    </tr>")
    
    # Build table HTML
    table_parts = ['<table class="facts-table">']
    if caption:
        table_parts.append(f"  <caption>{caption}</caption>")
    table_parts.append("  <tbody>")
    table_parts.extend(rows_html)
    table_parts.append("  </tbody>")
    table_parts.append("</table>")
    
    return "\n".join(table_parts)

def apply_content_wrappers(html_parts: List[str], content_type: str, metadata: Dict) -> str:
    """Apply content type specific wrappers"""
    content = "\n".join(html_parts)
    
    if content_type == "study_unit":
        # Find learning objectives section
        obj_match = re.search(r'(<h[23]>.*?learning objectives?.*?</h[23]>)(.*?)(<h[23]|$)', content, re.IGNORECASE | re.DOTALL)
        if obj_match:
            before = content[:obj_match.start()]
            objectives_section = obj_match.group(1) + obj_match.group(2)
            rest = content[obj_match.end()-len(obj_match.group(3)):]
            
            wrapped_objectives = f'<div class="highlighted-box">\n{objectives_section}\n</div>'
            wrapped_rest = f'<div class="learning-path">\n{rest}\n</div>' if rest.strip() else ''
            
            return f'{before}\n{wrapped_objectives}\n{wrapped_rest}'
    
    return content