import re
from typing import Union

class TextSanitizer:
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Strips excessive whitespaces, newlines, and removes basic non-ASCII 
        characters (like emojis) for clean NLP ingestion.
        """
        if not text:
            return ""
            
        # Remove non-ASCII characters (simplistic emoji removal for hackathon constraints)
        # This regex removes anything that isn't a standard ASCII character.
        text_no_emoji = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        # Replace multiple whitespaces/newlines with a single space and strip
        cleaned_text = re.sub(r'\s+', ' ', text_no_emoji).strip()
        return cleaned_text

    @staticmethod
    def parse_metric(metric_str: Union[str, int]) -> int:
        """
        Converts shorthand string metrics (e.g., '1.2k', '1.5M') to strict integers.
        """
        if isinstance(metric_str, int):
            return metric_str
            
        if not metric_str:
            return 0
            
        # Clean the string: lowercase, remove commas and spaces
        clean_str = str(metric_str).strip().lower().replace(',', '').replace(' ', '')
        
        try:
            if clean_str.endswith('k'):
                return int(float(clean_str[:-1]) * 1000)
            elif clean_str.endswith('m'):
                return int(float(clean_str[:-1]) * 1000000)
            elif clean_str.endswith('b'):
                return int(float(clean_str[:-1]) * 1000000000)
            else:
                return int(float(clean_str))
        except (ValueError, TypeError):
            # Fallback for completely unparseable metrics
            return 0
