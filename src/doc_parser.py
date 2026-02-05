import re
from typing import List, Dict

def parse_google_doc_text(text: str) -> List[Dict]:
    """
    Parse Google Doc text into structured entries.
    
    Structure looks for:
    Date Header (e.g. "2 Februari 2026")
    Time Block (e.g. "0730 - 1300 :")
    Content lines
    Proof link (http...)
    """
    entries = []
    
    # Regex patterns
    # Matches "2 Februari 2026" or "2 Feb 2026" etc.
    # We use a broad match for the header to split by
    date_pattern = r'(\d{1,2}\s+[a-zA-Z]+\s+\d{4})' 
    time_pattern = r'(\d{4})\s*-\s*(\d{4})\s*:'
    url_pattern = r'https?://[^\s]+'
    
    # Split by date headers
    # result will be [preamble, date1, content1, date2, content2...]
    date_sections = re.split(date_pattern, text)
    
    # Skip preamble (index 0), start from index 1 (first date)
    # We iterate with step 2: date is at i, content is at i+1
    for i in range(1, len(date_sections) - 1, 2):
        current_date = date_sections[i].strip()
        content = date_sections[i + 1]
        
        # Split by time ranges within the content of that date
        # result: [pre, start1, end1, content1, start2, end2, content2...]
        time_blocks = re.split(time_pattern, content)
        
        # Iterate through time blocks
        # time_blocks[0] is usually empty or whitespace before first time
        # so we start at 1. Group is 3 items: start, end, description
        for j in range(1, len(time_blocks) - 2, 3):
            start_time = time_blocks[j]
            end_time = time_blocks[j + 1]
            block_content = time_blocks[j + 2].strip()
            
            # Clean up block content
            lines = [l.strip() for l in block_content.split('\n') if l.strip()]
            
            if not lines:
                continue

            # Extract proof link (always a URL)
            proof_link = ''
            content_lines = []
            for line in lines:
                if re.search(url_pattern, line):
                    match = re.search(url_pattern, line)
                    if match:
                        proof_link = match.group(0)
                    # Don't add to content if it's just the link
                    clean_line = line.replace(proof_link, '').strip()
                    if clean_line:
                        content_lines.append(clean_line)
                else:
                    content_lines.append(line)
            
            # Remaining lines: first is category, rest is description
            category = content_lines[0] if len(content_lines) > 0 else ''
            
            # Description is the rest, joined
            description = '\n'.join(content_lines[1:]) if len(content_lines) > 1 else ''
            # If description is empty, maybe use category as description? 
            # PRD validation says: Warning (but allow): missing description
            
            entry = {
                'date_raw': current_date, # storing raw for debugging
                'start_time': start_time,
                'end_time': end_time,
                'category': category,
                'description': description,
                'proof_link': proof_link
            }
            entries.append(entry)
    
    return entries
