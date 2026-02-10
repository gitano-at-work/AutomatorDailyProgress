import re
from typing import List, Dict
from utils import normalize_time

def parse_google_doc_text(text: str) -> List[Dict]:
    """
    Parse Google Doc text into structured entries.
    
    Supports flexible formats:
    Date Headers: "2 Februari 2026", "2026-02-01", "01/02/2026", "1-2-2026", "1 1 2026", etc.
    Time Blocks: "0730 - 1300:", "07:30 - 13:00:", "07.30-13.00:", "0730 1300:", etc.
    """
    entries = []
    
    # --- DATE DETECTION ---
    # Multiple patterns to match date headers in the document
    date_patterns = [
        r'(\d{1,2}\s+[a-zA-Z]+\s+\d{4})',       # "2 Februari 2026", "1 January 2026"
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',         # "2026-02-01", "2026/02/01"
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',         # "01/02/2026", "1-2-2026"
        r'(\d{1,2}\s+\d{1,2}\s+\d{4})',           # "1 1 2026"
    ]
    combined_date_pattern = '|'.join(date_patterns)
    
    # --- TIME DETECTION ---
    # Flexible: handles 0730, 07:30, 07.30, 7:30 with dash/en-dash separator
    # Trailing colon is optional
    time_pattern = r'(\d{1,2}[:\.]?\d{2})\s*[-–—]\s*(\d{1,2}[:\.]?\d{2})\s*:?'
    
    url_pattern = r'https?://[^\s]+'
    
    # Find all date header matches
    matches = list(re.finditer(combined_date_pattern, text))
    
    if not matches:
        return entries
    
    # Iterate date matches
    for i in range(len(matches)):
        # The matched group could be in any of the alternation groups
        current_date_str = matches[i].group(0).strip()
        
        # Content is everything until next date match or end of string
        start_idx = matches[i].end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
        content_block = text[start_idx:end_idx]
        
        # Find Time Blocks in this content block
        time_matches = list(re.finditer(time_pattern, content_block))
        
        for j in range(len(time_matches)):
            raw_start = time_matches[j].group(1)
            raw_end = time_matches[j].group(2)
            
            # Normalize times immediately to HH:MM
            start_time = normalize_time(raw_start)
            end_time = normalize_time(raw_end)
            
            # Content for this time block
            t_start = time_matches[j].end()
            t_end = time_matches[j+1].start() if j + 1 < len(time_matches) else len(content_block)
            raw_entry_text = content_block[t_start:t_end].strip()
            
            # Parse the entry text
            lines = [l.strip() for l in raw_entry_text.split('\n') if l.strip()]
            
            if not lines:
                continue

            # Extract Proof Link
            proof_link = ''
            clean_lines = []
            for line in lines:
                url_match = re.search(url_pattern, line)
                if url_match:
                    proof_link = url_match.group(0)
                    line = line.replace(proof_link, '').strip()
                if line:
                    clean_lines.append(line)
                    
            # Extract Rencana Aksi (Drop Down Text)
            action_plan = ""
            final_lines = []
            for line in clean_lines:
                if re.match(r'^Rencana\s+Aksi\s*[:\-\.]\s*', line, re.IGNORECASE):
                    parts = re.split(r'[:\-\.]', line, 1)
                    if len(parts) > 1:
                        action_plan = parts[1].strip()
                else:
                    final_lines.append(line)
            
            # Clean UI Noise (Google Docs footer text)
            noise_patterns = [
                r'^aktifkan dukungan pembaca',
                r'^untuk mengaktifkan dukungan',
                r'^banner disembunyikan',
                r'^minta akses edit',
                r'^bagikan',
                r'^fileedittampilan',
                r'^tab dokumen'
            ]
            
            filtered_lines = []
            for line in final_lines:
                is_noise = False
                for p in noise_patterns:
                    if re.match(p, line, re.IGNORECASE):
                        is_noise = True
                        break
                if not is_noise:
                    filtered_lines.append(line)
            
            final_lines = filtered_lines

            # Find Action Plan Index (Trailing Digit or Standalone Digit)
            if not action_plan:
                for line_idx in range(len(final_lines) - 1, -1, -1):
                    line = final_lines[line_idx]
                    
                    # Case A: Standalone Digit line (e.g. "3")
                    if line.strip().isdigit() and len(line.strip()) < 3:
                        action_plan = line.strip()
                        final_lines.pop(line_idx)
                        break
                    
                    # Case B: Trailing Digit (e.g. "Activity 3")
                    match = re.search(r'^(.*)\s+(\d{1,2})$', line)
                    if match:
                        text_part = match.group(1).strip()
                        digit_part = match.group(2)
                        
                        if text_part:
                            action_plan = digit_part
                            final_lines[line_idx] = text_part
                            break
            
            # Determine Category & Description
            category = final_lines[0] if final_lines else "Kegiatan Harian"
            description = '\n'.join(final_lines[1:]) if len(final_lines) > 1 else ""
            
            entry = {
                'date_raw': current_date_str,
                'start_time': start_time,
                'end_time': end_time,
                'category': category,
                'description': description,
                'proof_link': proof_link,
                'action_plan': action_plan
            }
            entries.append(entry)

    return entries

