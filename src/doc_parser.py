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
    
    # Custom split to handle headers + content better
    # We find all matches first
    matches = list(re.finditer(date_pattern, text))
    
    # Iterate matches
    for i in range(len(matches)):
        # Header Date
        current_date_str = matches[i].group(0).strip()
        
        # Content is everything until next match or end of string
        start_idx = matches[i].end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
        content_block = text[start_idx:end_idx]
        
        # Now find Time Blocks in this content block
        # Looking for "0730 - 1300 :" pattern
        # Using finditer again to capture context safely
        time_matches = list(re.finditer(time_pattern, content_block))
        
        for j in range(len(time_matches)):
            start_time = time_matches[j].group(1)
            end_time = time_matches[j].group(2)
            
            # Content for this time block
            t_start = time_matches[j].end()
            t_end = time_matches[j+1].start() if j + 1 < len(time_matches) else len(content_block)
            raw_entry_text = content_block[t_start:t_end].strip()
            
            # Parse the entry text
            lines = [l.strip() for l in raw_entry_text.split('\n') if l.strip()]
            
            if not lines:
                continue

            # 1. Check if Activity is inline with the separators (e.g. ": Activity")
            # But our Regex includes the ':' at the end.
            # So raw_entry_text STARTS with the activity usually.
            
            # 2. Extract Proof Link
            proof_link = ''
            clean_lines = []
            for line in lines:
                url_match = re.search(url_pattern, line)
                if url_match:
                    proof_link = url_match.group(0)
                    line = line.replace(proof_link, '').strip()
                if line:
                    clean_lines.append(line)
                    
            # 3. Extract Rencana Aksi (Drop Down Text)
            # Since Chips are invisible in InnerText, we might skip this
            # OR user might fix it. We keep logic just in case.
            action_plan = ""
            final_lines = []
            for line in clean_lines:
                if re.match(r'^Rencana\s+Aksi\s*[:\-\.]\s*', line, re.IGNORECASE):
                    parts = re.split(r'[:\-\.]', line, 1)
                    if len(parts) > 1:
                        action_plan = parts[1].strip()
                else:
                    # Fallback: Check if line matches known Action Plans strictly? No.
                    final_lines.append(line)
            
            # Check for numeric Action Plan (User Convention: Standalone number in lines OR trailing number)
            
            # STRATEGY 1: Check Trailing Digit on the Activity Line (e.g. "Coding 3")
            # This is key for the user's latest format.
            if final_lines:
                last_line = final_lines[-1]
                # Regex for "Activity text" + space + "digit" (1-2 chars)
                # match: "Some text 3" -> groups: ("Some text", "3")
                match = re.search(r'^(.*)\s+(\d{1,2})$', last_line)
                if match:
                    # We found a trailing digit!
                    text_part = match.group(1).strip()
                    digit_part = match.group(2)
                    
                    # Update category/description
                    final_lines[-1] = text_part # Remove digit from line
                    action_plan = digit_part
            
            # STRATEGY 2: Check Standalone Line (Fallback if not inline)
            if not action_plan:
                found_idx = -1
                for i, line in enumerate(final_lines):
                    if line.strip().isdigit() and len(line.strip()) < 3: 
                        action_plan = line.strip()
                        found_idx = i
                        break 
                
                if found_idx != -1:
                    final_lines.pop(found_idx)
            
            category = final_lines[0] if final_lines else "Kegiatan Harian"
            description = '\n'.join(final_lines[1:]) if len(final_lines) > 1 else ""
            
            entry = {
                'date_raw': current_date_str,
                'start_time': start_time,
                'end_time': end_time,
                'activity': category,
                'description': description, # Optional
                'proof_link': proof_link,
                'action_plan': action_plan
            }
            entries.append(entry)

    return entries
