# LLM Security Module

A comprehensive, reusable security framework for LLM-based applications that protects against prompt injection, data exfiltration, and other AI-specific vulnerabilities.

## 🎯 Overview

This module implements defense-in-depth security based on research from:
- Google's CaMeL (Capabilities for Machine Learning)
- Simon Willison's prompt injection research
- Industry best practices for AI security

## 🏗️ Architecture

```
security/
├── core/                   # Core security primitives
│   ├── data_provenance.py # Track data trust levels
│   ├── trust_boundary.py  # Define trust boundaries
│   └── security_context.py # Request security context
│
├── guardrails/            # Input/Output validation
│   ├── input_validator.py  # Multi-layer input validation
│   ├── output_sanitizer.py # Output sanitization
│   ├── pattern_detector.py # Attack pattern detection
│   └── semantic_analyzer.py # AI-based semantic analysis
│
├── capabilities/          # Capability-based access control
│   ├── capability_manager.py # Manage capabilities
│   ├── tool_access_control.py # Control tool access
│   └── approval_system.py    # Manual approval workflow
│
├── monitors/              # Security monitoring
│   ├── activity_logger.py  # Log security events
│   ├── anomaly_detector.py # Detect anomalies
│   └── audit_trail.py      # Audit trail management
│
├── exceptions.py          # Security-specific exceptions
├── config.py              # Security configuration
└── README.md              # This file
```

## 🔐 Key Concepts

### 1. Data Provenance
Track the trust level of data throughout the system:
- **TRUSTED**: From verified, internal sources
- **UNTRUSTED**: From user input or external sources
- **VERIFIED**: Untrusted data that passed validation
- **QUARANTINED**: Potentially malicious data

### 2. Dual LLM Architecture
- **Privileged LLM**: Has tool access, only processes trusted data
- **Quarantined LLM**: Processes untrusted input, no tool access

### 3. Capability-Based Access Control
- Tools require specific capabilities to execute
- Capabilities are granted based on data provenance
- Sensitive operations require manual approval

## 🚀 Quick Start

```python
from src.security import SecurityContext, InputValidator, OutputSanitizer
from src.security.capabilities import CapabilityManager

# Initialize security components
validator = InputValidator()
sanitizer = OutputSanitizer()
cap_manager = CapabilityManager()

# Validate input
validation_result = validator.validate(user_input)
if validation_result.is_blocked:
    raise SecurityError(validation_result.reason)

# Create security context
context = SecurityContext(
    trust_level=validation_result.trust_level,
    user_id=user.id,
    session_id=session.id
)

# Check tool access
if not cap_manager.can_execute("create_ticket", context):
    # Request manual approval
    await approval_system.request_approval(context, "create_ticket")

# Sanitize output
response = sanitizer.sanitize(llm_response)
```

## 📊 Implementation Phases

### Phase 1: Foundation (Immediate)
- ✅ Output sanitization (URL/markdown filtering)
- ✅ Pattern-based input detection
- ✅ Data provenance tracking
- ✅ Security event logging

### Phase 2: Advanced Protection (Short-term)
- 🔄 Quarantined LLM implementation
- 🔄 Capability-based access control
- 🔄 Manual approval system
- 🔄 Semantic threat analysis

### Phase 3: Enterprise Grade (Long-term)
- ⏳ Formal security policies DSL
- ⏳ Real-time anomaly detection
- ⏳ Automated threat response
- ⏳ Compliance reporting

## 🛡️ Defense Layers

1. **Input Validation** - Block malicious inputs before processing
2. **Quarantine Processing** - Isolate untrusted data processing
3. **Capability Control** - Restrict tool access based on trust
4. **Output Sanitization** - Remove potential exfiltration vectors
5. **Audit Trail** - Track all security-relevant events

## 📖 Usage Examples

See `/examples` directory for:
- Basic integration examples
- Custom validation rules
- Tool access policies
- Monitoring setup

## 🧪 Testing

```bash
pytest src/security/tests/
```

## 📝 Configuration

```python
# backend/src/security/config.py

SECURITY_CONFIG = {
    "enable_guardrails": True,
    "quarantine_untrusted_input": True,
    "require_approval_for_sensitive_ops": True,
    "log_all_security_events": True,
    "trust_threshold": 0.7,
    "max_approval_wait_time": 300  # seconds
}
```

## ⚠️ Important Notes

- **No silver bullet**: This module reduces but doesn't eliminate all risks
- **Defense in depth**: Use multiple layers of protection
- **Stay updated**: Monitor security research for new attack vectors
- **Fail secure**: When in doubt, block the action

## 📚 References

- [CaMeL Paper](https://arxiv.org/abs/2503.18813)
- [Simon Willison's Prompt Injection Series](https://simonwillison.net/series/prompt-injection/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

## 🤝 Contributing

This is a reusable module. When adding features:
1. Keep it framework-agnostic where possible
2. Document thoroughly
3. Add comprehensive tests
4. Follow the existing patterns

## 📄 License

[Your License Here]
