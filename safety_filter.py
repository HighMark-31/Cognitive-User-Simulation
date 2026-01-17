import re
import logging

class SafetyFilter:
    def __init__(self):
        self.patterns = {
            'discord_invite': re.compile(r'(discord\.(gg|io|me|li)|discordapp\.com/invite)/[a-zA-Z0-9]+', re.IGNORECASE),
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE),
            'phone': re.compile(r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'),
            'crypto_wallet': re.compile(r'(0x[a-fA-F0-9]{40})|(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}'),
            'scam_keywords': re.compile(r'\b(nitro free|steam wallet|gift card|giveaway|claim now|click here)\b', re.IGNORECASE)
        }
        
        self.blocked_words = {
            'nigger', 'faggot', 'retard', 'kys', 'kill yourself', 'rape', 
            'chink', 'tranny', 'shemale', 'dyke', 'kike'
        }

    def is_safe(self, text: str) -> tuple[bool, str]:
        """
        Checks if the text is safe to send.
        Returns (is_safe, reason).
        """
        if not text:
            return True, "empty"
            
        text_lower = text.lower()
        
        for word in self.blocked_words:
            if word in text_lower:
                return False, f"blocked_word: {word}"
        
        if self.patterns['discord_invite'].search(text):
            return False, "discord_invite"
            
        if self.patterns['email'].search(text):
            return False, "pii_email"

            
        if self.patterns['crypto_wallet'].search(text):
            return False, "crypto_wallet"
            
        if self.patterns['scam_keywords'].search(text):
            return False, "scam_keyword"
            
        return True, "safe"

    def sanitize(self, text: str) -> str:
        """
        Attempts to clean the text (e.g. removing links).
        For now, just returns the text if safe, or a fallback if unsafe.
        """
        safe, reason = self.is_safe(text)
        if safe:
            return text
        return ""  
