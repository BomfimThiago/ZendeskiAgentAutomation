"""
Multi-layer input validation for LLM applications.

Combines pattern detection, heuristics, and optional semantic analysis
to validate user input before processing.
"""
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from .pattern_detector import PatternDetector, AttackType
from ..core.data_provenance import TrustLevel, DataProvenance
from ..core.security_context import SecurityContext
from ..config import security_config
from ..exceptions import PromptInjectionDetected, QuarantineRequired
from src.core.logging_config import get_logger

logger = get_logger("input_validator")


def _get_trust_level_str(trust_level: Union[TrustLevel, str]) -> str:
    """Safely get string value from TrustLevel enum or string."""
    if hasattr(trust_level, 'value'):
        return trust_level.value
    return str(trust_level)


class ValidationResult:
    """
    Result of input validation.
    
    Example:
        >>> result = validator.validate(user_input)
        >>> if result.is_blocked:
        ...     raise PromptInjectionDetected(result.block_reason)
        >>> if result.requires_quarantine:
        ...     # Process in quarantined LLM
        ...     pass
    """
    
    def __init__(
        self,
        is_valid: bool,
        trust_level: TrustLevel,
        confidence: float,
        is_blocked: bool = False,
        requires_quarantine: bool = False,
        block_reason: Optional[str] = None,
        quarantine_reasons: Optional[List[str]] = None,
        detection_details: Optional[Dict[str, Any]] = None,
        security_context: Optional[SecurityContext] = None
    ):
        self.is_valid = is_valid
        self.trust_level = trust_level
        self.confidence = confidence
        self.is_blocked = is_blocked
        self.requires_quarantine = requires_quarantine
        self.block_reason = block_reason
        self.quarantine_reasons = quarantine_reasons or []
        self.detection_details = detection_details or {}
        self.security_context = security_context
        self.validated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            'is_valid': self.is_valid,
            'trust_level': self.trust_level.value if self.trust_level else None,
            'confidence': self.confidence,
            'is_blocked': self.is_blocked,
            'requires_quarantine': self.requires_quarantine,
            'block_reason': self.block_reason,
            'quarantine_reasons': self.quarantine_reasons,
            'detection_details': self.detection_details,
            'validated_at': self.validated_at.isoformat()
        }


class InputValidator:
    """
    Validate user input using multiple security layers.
    
    Layers:
    1. Pattern-based detection (fast, catches known attacks)
    2. Heuristic analysis (length, complexity, suspicious patterns)
    3. Trust scoring (combines all signals)
    4. Optional: Semantic analysis (AI-based, slower but more accurate)
    
    Example:
        >>> validator = InputValidator()
        >>> result = validator.validate(
        ...     text=user_input,
        ...     user_id="user_123",
        ...     session_id="session_abc"
        ... )
        >>> 
        >>> if result.is_blocked:
        ...     return error_response(result.block_reason)
        >>> 
        >>> if result.requires_quarantine:
        ...     # Route to quarantined LLM
        ...     response = quarantined_llm.process(user_input)
        >>> else:
        ...     # Safe to process with privileged LLM
        ...     response = privileged_llm.process(user_input)
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize input validator.
        
        Args:
            config: Security configuration
        """
        self.config = config or security_config
        self.pattern_detector = PatternDetector(config)
    
    def validate(
        self,
        text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate input text through multiple security layers.
        
        Args:
            text: Input text to validate
            user_id: User ID (for context)
            session_id: Session ID (for context)
            metadata: Additional metadata
            
        Returns:
            ValidationResult with trust level and recommendations
        """
        # Create security context
        # Start with UNTRUSTED (conservative), will be upgraded based on validation
        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            trust_level=TrustLevel.UNTRUSTED,  # Will be updated after validation
            metadata=metadata or {}
        )
        
        # Layer 1: Pattern detection
        pattern_result = self.pattern_detector.detect(text)
        
        # Layer 2: Heuristic analysis
        heuristic_result = self._heuristic_analysis(text)
        
        # Layer 3: Trust scoring
        trust_score = self._calculate_trust_score(pattern_result, heuristic_result)
        
        # Determine trust level
        trust_level = self._determine_trust_level(trust_score, pattern_result)
        
        # Check if should be blocked
        is_blocked = pattern_result['is_attack'] and pattern_result['confidence'] >= 0.90
        
        # Check if requires quarantine
        requires_quarantine = (
            trust_score < self.config.trust_threshold or
            (pattern_result['is_attack'] and pattern_result['confidence'] >= 0.60)
        )
        
        # Build quarantine reasons
        quarantine_reasons = []
        if trust_score < self.config.trust_threshold:
            quarantine_reasons.append(f"trust_score_low: {trust_score:.2f}")
        if pattern_result['is_attack']:
            quarantine_reasons.append(f"attack_pattern_detected: {pattern_result['attack_type']}")
        if heuristic_result['has_suspicious_patterns']:
            quarantine_reasons.extend(heuristic_result['suspicious_reasons'])
        
        # Build block reason
        block_reason = None
        if is_blocked:
            attack_types = ', '.join([at.value for at in pattern_result['all_attack_types']])
            block_reason = f"High-confidence prompt injection detected: {attack_types}"
        
        # Update security context with calculated trust level and metadata
        # CRITICAL: Update the actual trust_level field, not just metadata
        initial_trust = context.trust_level

        # Update with trust level and metadata
        context = context.model_copy(update={
            "trust_level": trust_level,
            "metadata": {
                "trust_score": trust_score,
                "pattern_confidence": pattern_result.get('confidence', 0.0),
                "is_attack": pattern_result.get('is_attack', False),
                "attack_type": pattern_result.get('attack_type', 'none'),
                "requires_quarantine": requires_quarantine,
                "quarantine_reasons": quarantine_reasons,
            }
        })

        context = context.add_security_flag(
            "validation_complete",
            {"trust_score": trust_score, "trust_level": _get_trust_level_str(trust_level)}
        )

        if is_blocked:
            context = context.block_operation(block_reason)

        # Log validation with trust level changes
        # Handle both enum and string values (Pydantic may convert to string)
        initial_trust_str = initial_trust.value if hasattr(initial_trust, 'value') else str(initial_trust)
        final_trust_str = trust_level.value if hasattr(trust_level, 'value') else str(trust_level)

        logger.info(
            "Input validation complete",
            extra={
                'initial_trust': initial_trust_str,
                'final_trust': final_trust_str,
                'trust_upgraded': initial_trust != trust_level,
                'trust_score': trust_score,
                'is_blocked': is_blocked,
                'requires_quarantine': requires_quarantine,
                'user_id': user_id
            }
        )
        
        return ValidationResult(
            is_valid=not is_blocked,
            trust_level=trust_level,
            confidence=trust_score,
            is_blocked=is_blocked,
            requires_quarantine=requires_quarantine,
            block_reason=block_reason,
            quarantine_reasons=quarantine_reasons,
            detection_details={
                'pattern_detection': pattern_result,
                'heuristic_analysis': heuristic_result,
                'trust_score': trust_score
            },
            security_context=context
        )
    
    def _heuristic_analysis(self, text: str) -> Dict[str, Any]:
        """
        Perform heuristic analysis on input.
        
        Checks for:
        - Unusual length (very long or very short)
        - Excessive punctuation
        - Mixed languages
        - Suspicious keywords
        """
        analysis = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'has_suspicious_patterns': False,
            'suspicious_reasons': []
        }
        
        # Check text length
        if len(text) > 5000:
            analysis['has_suspicious_patterns'] = True
            analysis['suspicious_reasons'].append('excessive_length')
        
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.3:
            analysis['has_suspicious_patterns'] = True
            analysis['suspicious_reasons'].append('excessive_special_chars')
        
        # Check for suspicious keywords
        suspicious_keywords = [
            'admin', 'root', 'sudo', 'eval', 'exec', 'execute',
            'password', 'token', 'secret', 'api_key', 'credentials'
        ]
        lower_text = text.lower()
        found_keywords = [kw for kw in suspicious_keywords if kw in lower_text]
        if found_keywords:
            analysis['suspicious_keywords'] = found_keywords
        
        return analysis
    
    def _calculate_trust_score(
        self,
        pattern_result: Dict[str, Any],
        heuristic_result: Dict[str, Any]
    ) -> float:
        """
        Calculate overall trust score (0.0 to 1.0).
        
        Higher score = more trustworthy
        """
        base_score = 1.0
        
        # Penalize for detected attacks
        if pattern_result['is_attack']:
            penalty = pattern_result['confidence']
            base_score -= penalty
        
        # Penalize for suspicious heuristics
        if heuristic_result['has_suspicious_patterns']:
            penalty = len(heuristic_result['suspicious_reasons']) * 0.15
            base_score -= penalty
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def _determine_trust_level(
        self,
        trust_score: float,
        pattern_result: Dict[str, Any]
    ) -> TrustLevel:
        """Determine trust level based on score and detection results."""
        # Quarantine if high-confidence attack
        if pattern_result['is_attack'] and pattern_result['confidence'] >= 0.90:
            return TrustLevel.QUARANTINED
        
        # Untrusted if low score or medium-confidence attack
        if trust_score < self.config.trust_threshold or pattern_result['is_attack']:
            return TrustLevel.UNTRUSTED
        
        # Verified if passed checks
        if trust_score >= 0.85:
            return TrustLevel.VERIFIED
        
        # Default to untrusted
        return TrustLevel.UNTRUSTED
    
    def quick_check(self, text: str) -> bool:
        """
        Quick validation check (returns True if safe).
        
        Use when you need fast yes/no answer without full context.
        """
        result = self.validate(text)
        return result.is_valid and not result.requires_quarantine
