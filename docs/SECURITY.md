# Security Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Security Architecture](#security-architecture)
3. [Authentication](#authentication)
4. [Authorization](#authorization)
5. [Data Protection](#data-protection)
6. [Network Security](#network-security)
7. [Phase Security](#phase-security)
8. [Provider Security](#provider-security)
9. [Compliance](#compliance)
10. [Security Monitoring](#security-monitoring)
11. [Incident Response](#incident-response)
12. [Security Best Practices](#security-best-practices)
13. [Vulnerability Management](#vulnerability-management)

## Introduction

The 6-Phase Architecture implements a comprehensive, defense-in-depth security model designed to protect data, ensure privacy, and maintain system integrity across all phases of operation. This guide provides detailed information about security mechanisms, configurations, and best practices.

### Security Objectives

- **Confidentiality**: Protect sensitive data from unauthorized access
- **Integrity**: Ensure data accuracy and prevent tampering
- **Availability**: Maintain system availability and resilience
- **Accountability**: Track and audit all system activities
- **Compliance**: Meet regulatory and industry standards

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimum permissions required for operation
3. **Zero Trust**: Verify every request, trust nothing by default
4. **Security by Design**: Integrate security from the ground up
5. **Continuous Monitoring**: Real-time threat detection and response

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────┐
│                  Perimeter Security                  │
│  (WAF, DDoS Protection, Rate Limiting)              │
├─────────────────────────────────────────────────────┤
│                  Network Security                    │
│  (TLS, VPN, Network Segmentation)                   │
├─────────────────────────────────────────────────────┤
│                  Application Security                │
│  (Authentication, Authorization, Input Validation)   │
├─────────────────────────────────────────────────────┤
│                  Data Security                       │
│  (Encryption, Masking, Tokenization)                │
├─────────────────────────────────────────────────────┤
│                  Infrastructure Security             │
│  (Hardening, Patching, Monitoring)                  │
└─────────────────────────────────────────────────────┘
```

### Security Components

```python
class SecurityManager:
    """Central security management system."""
    
    def __init__(self, config: dict):
        self.auth_manager = AuthenticationManager(config)
        self.authz_manager = AuthorizationManager(config)
        self.encryption_manager = EncryptionManager(config)
        self.audit_logger = AuditLogger(config)
        self.threat_detector = ThreatDetector(config)
    
    def validate_request(self, request: dict) -> dict:
        """Validate incoming request for security."""
        # Step 1: Rate limiting check
        if not self._check_rate_limit(request):
            raise RateLimitExceededError("Rate limit exceeded")
        
        # Step 2: Authentication
        user = self.auth_manager.authenticate(request)
        
        # Step 3: Authorization
        if not self.authz_manager.is_authorized(user, request):
            raise AuthorizationError("Insufficient permissions")
        
        # Step 4: Input validation
        self._validate_input(request)
        
        # Step 5: Threat detection
        if self.threat_detector.is_threat(request):
            self.audit_logger.log_threat(request)
            raise SecurityThreatError("Potential security threat detected")
        
        return {"user": user, "validated": True}
    
    def _check_rate_limit(self, request: dict) -> bool:
        """Check if request is within rate limits."""
        client_ip = request.get("client_ip")
        return self.rate_limiter.check(client_ip)
    
    def _validate_input(self, request: dict):
        """Validate and sanitize input data."""
        for key, value in request.items():
            if isinstance(value, str):
                # Sanitize string inputs
                request[key] = self._sanitize(value)
    
    def _sanitize(self, value: str) -> str:
        """Sanitize string value."""
        import html
        # Remove potentially dangerous characters
        value = html.escape(value)
        # Remove null bytes
        value = value.replace("\x00", "")
        return value
```

## Authentication

### Multi-Factor Authentication

```python
class AuthenticationManager:
    """Manage user authentication."""
    
    def __init__(self, config: dict):
        self.config = config
        self.token_manager = TokenManager(config)
        self.mfa_manager = MFAManager(config)
    
    def authenticate(self, request: dict) -> dict:
        """Authenticate user with multi-factor authentication."""
        # Step 1: Verify primary credentials
        user = self._verify_credentials(
            request.get("username"),
            request.get("password")
        )
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Step 2: Verify MFA if enabled
        if user.get("mfa_enabled"):
            if not self.mfa_manager.verify(
                user["id"],
                request.get("mfa_code")
            ):
                raise AuthenticationError("Invalid MFA code")
        
        # Step 3: Generate session token
        token = self.token_manager.generate(user)
        
        # Step 4: Log authentication event
        self._log_auth_event(user, "success")
        
        return {
            "user": user,
            "token": token,
            "expires_at": self.token_manager.get_expiry(token)
        }
    
    def _verify_credentials(self, username: str, password: str) -> dict:
        """Verify user credentials."""
        user = self._get_user(username)
        
        if not user:
            return None
        
        # Use bcrypt for password verification
        import bcrypt
        if bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        ):
            return user
        
        return None
```

### Token-Based Authentication

```python
import jwt
import time
from typing import Optional

class TokenManager:
    """Manage JWT tokens."""
    
    def __init__(self, config: dict):
        self.secret_key = config["jwt_secret"]
        self.algorithm = config.get("jwt_algorithm", "HS256")
        self.expiry_seconds = config.get("jwt_expiry", 3600)
    
    def generate(self, user: dict) -> str:
        """Generate JWT token for user."""
        payload = {
            "sub": user["id"],
            "username": user["username"],
            "roles": user.get("roles", []),
            "iat": int(time.time()),
            "exp": int(time.time()) + self.expiry_seconds,
            "jti": self._generate_token_id()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check if token is blacklisted
            if self._is_blacklisted(payload["jti"]):
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke(self, token: str):
        """Revoke a token."""
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={"verify_exp": False}
        )
        self._blacklist(payload["jti"])
    
    def _generate_token_id(self) -> str:
        """Generate unique token ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _is_blacklisted(self, token_id: str) -> bool:
        """Check if token is blacklisted."""
        # Check Redis or database for blacklisted tokens
        pass
    
    def _blacklist(self, token_id: str):
        """Add token to blacklist."""
        # Store in Redis or database with TTL
        pass
```

### API Key Management

```python
class APIKeyManager:
    """Manage API keys."""
    
    def __init__(self, config: dict):
        self.config = config
        self.key_store = KeyStore(config)
    
    def create_key(
        self,
        name: str,
        permissions: list,
        rate_limit: str = "1000/day"
    ) -> dict:
        """Create a new API key."""
        import secrets
        
        # Generate secure API key
        api_key = f"vex_{secrets.token_urlsafe(32)}"
        
        # Hash the key for storage
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store key metadata
        key_data = {
            "name": name,
            "key_hash": key_hash,
            "permissions": permissions,
            "rate_limit": rate_limit,
            "created_at": time.time(),
            "enabled": True
        }
        
        self.key_store.store(key_hash, key_data)
        
        # Return the plain key (only time it's visible)
        return {
            "api_key": api_key,
            "name": name,
            "permissions": permissions
        }
    
    def validate_key(self, api_key: str) -> Optional[dict]:
        """Validate an API key."""
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        key_data = self.key_store.get(key_hash)
        
        if not key_data or not key_data.get("enabled"):
            return None
        
        return key_data
    
    def revoke_key(self, api_key: str):
        """Revoke an API key."""
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        self.key_store.delete(key_hash)
```

## Authorization

### Role-Based Access Control (RBAC)

```python
class AuthorizationManager:
    """Manage role-based access control."""
    
    ROLES = {
        "admin": {
            "permissions": [
                "read:all",
                "write:all",
                "execute:all",
                "manage:users",
                "manage:roles",
                "manage:configuration",
                "manage:providers",
                "view:audit_logs",
                "manage:security"
            ],
            "description": "Full system access"
        },
        "operator": {
            "permissions": [
                "read:all",
                "write:tasks",
                "execute:tasks",
                "view:own_data",
                "view:metrics"
            ],
            "description": "Task execution and monitoring"
        },
        "developer": {
            "permissions": [
                "read:all",
                "write:tasks",
                "execute:tasks",
                "write:plugins",
                "view:own_data",
                "view:logs"
            ],
            "description": "Development and testing access"
        },
        "viewer": {
            "permissions": [
                "read:own_data",
                "view:metrics",
                "view:logs"
            ],
            "description": "Read-only access to own data"
        },
        "guest": {
            "permissions": [
                "read:public"
            ],
            "description": "Limited public access"
        }
    }
    
    def is_authorized(self, user: dict, request: dict) -> bool:
        """Check if user is authorized for the request."""
        user_roles = user.get("roles", ["guest"])
        required_permission = self._get_required_permission(request)
        
        for role in user_roles:
            role_data = self.ROLES.get(role, {})
            permissions = role_data.get("permissions", [])
            
            if self._has_permission(permissions, required_permission):
                return True
        
        return False
    
    def _get_required_permission(self, request: dict) -> str:
        """Determine required permission for request."""
        method = request.get("method", "GET")
        resource = request.get("resource", "")
        
        action_map = {
            "GET": "read",
            "POST": "write",
            "PUT": "write",
            "DELETE": "write",
            "EXECUTE": "execute"
        }
        
        action = action_map.get(method, "read")
        return f"{action}:{resource}"
    
    def _has_permission(self, permissions: list, required: str) -> bool:
        """Check if permissions list includes required permission."""
        for permission in permissions:
            if permission == required:
                return True
            if permission.endswith(":all"):
                prefix = permission[:-4]
                if required.startswith(prefix):
                    return True
        return False
```

### Attribute-Based Access Control (ABAC)

```python
class ABACManager:
    """Manage attribute-based access control."""
    
    def evaluate_policy(self, user: dict, resource: dict, action: str) -> bool:
        """Evaluate ABAC policy."""
        policies = self._get_policies_for_resource(resource)
        
        for policy in policies:
            if self._evaluate_policy(policy, user, resource, action):
                return True
        
        return False
    
    def _evaluate_policy(
        self,
        policy: dict,
        user: dict,
        resource: dict,
        action: str
    ) -> bool:
        """Evaluate a single policy."""
        # Check action
        if action not in policy.get("actions", []):
            return False
        
        # Check user attributes
        user_conditions = policy.get("user_conditions", {})
        if not self._match_conditions(user, user_conditions):
            return False
        
        # Check resource attributes
        resource_conditions = policy.get("resource_conditions", {})
        if not self._match_conditions(resource, resource_conditions):
            return False
        
        # Check environment conditions
        env_conditions = policy.get("environment_conditions", {})
        if not self._match_environment(env_conditions):
            return False
        
        return True
    
    def _match_conditions(self, attributes: dict, conditions: dict) -> bool:
        """Match attributes against conditions."""
        for key, value in conditions.items():
            if key not in attributes:
                return False
            if isinstance(value, list):
                if attributes[key] not in value:
                    return False
            elif attributes[key] != value:
                return False
        return True
```

## Data Protection

### Encryption

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionManager:
    """Manage data encryption."""
    
    def __init__(self, config: dict):
        self.config = config
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt a file."""
        with open(file_path, "rb") as f:
            data = f.read()
        
        encrypted = self.cipher.encrypt(data)
        
        with open(output_path, "wb") as f:
            f.write(encrypted)
    
    def decrypt_file(self, file_path: str, output_path: str):
        """Decrypt a file."""
        with open(file_path, "rb") as f:
            encrypted = f.read()
        
        data = self.cipher.decrypt(encrypted)
        
        with open(output_path, "wb") as f:
            f.write(data)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        key_file = self.config.get("encryption_key_file", ".encryption_key")
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        
        # Generate new key
        password = self.config["encryption_password"].encode()
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        with open(key_file, "wb") as f:
            f.write(key)
        
        return key
```

### Data Masking

```python
class DataMasker:
    """Mask sensitive data."""
    
    MASKING_RULES = {
        "email": lambda v: v[:3] + "***@" + v.split("@")[1] if "@" in v else "***",
        "phone": lambda v: v[:4] + "****" + v[-4:] if len(v) >= 8 else "****",
        "credit_card": lambda v: "****-****-****-" + v[-4:] if len(v) >= 4 else "****",
        "ssn": lambda v: "***-**-" + v[-4:] if len(v) >= 4 else "***-**-****",
        "api_key": lambda v: v[:8] + "..." + v[-4:] if len(v) > 12 else "****",
        "password": lambda v: "********",
        "ip_address": lambda v: ".".join(v.split(".")[:2]) + ".*.*"
    }
    
    def mask(self, data: dict, fields_to_mask: list) -> dict:
        """Mask specified fields in data."""
        masked = data.copy()
        
        for field in fields_to_mask:
            if field in masked:
                field_type = self._detect_field_type(field)
                mask_func = self.MASKING_RULES.get(field_type, lambda v: "****")
                masked[field] = mask_func(str(masked[field]))
        
        return masked
    
    def _detect_field_type(self, field_name: str) -> str:
        """Detect field type from name."""
        field_lower = field_name.lower()
        
        type_keywords = {
            "email": ["email", "mail"],
            "phone": ["phone", "mobile", "tel"],
            "credit_card": ["card", "cc", "credit"],
            "ssn": ["ssn", "social"],
            "api_key": ["api_key", "apikey", "key"],
            "password": ["password", "passwd", "pwd"],
            "ip_address": ["ip", "ip_address"]
        }
        
        for field_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in field_lower:
                    return field_type
        
        return "default"
```

### Secure Data Storage

```python
class SecureStorage:
    """Secure data storage with encryption at rest."""
    
    def __init__(self, config: dict):
        self.encryption = EncryptionManager(config)
        self.key_store = KeyStore(config)
    
    def store(self, key: str, data: dict, sensitive_fields: list = None):
        """Store data with encryption for sensitive fields."""
        if sensitive_fields:
            for field in sensitive_fields:
                if field in data:
                    data[field] = self.encryption.encrypt(str(data[field]))
        
        self.key_store.store(key, data)
    
    def retrieve(self, key: str, sensitive_fields: list = None) -> dict:
        """Retrieve and decrypt data."""
        data = self.key_store.get(key)
        
        if not data:
            return None
        
        if sensitive_fields:
            for field in sensitive_fields:
                if field in data:
                    try:
                        data[field] = self.encryption.decrypt(data[field])
                    except Exception:
                        pass  # Field might not be encrypted
        
        return data
    
    def delete(self, key: str):
        """Securely delete data."""
        # Overwrite data before deletion
        data = self.key_store.get(key)
        if data:
            for key_field in data:
                data[key_field] = os.urandom(32).hex()
            self.key_store.store(key, data)
        
        self.key_store.delete(key)
```

## Network Security

### TLS Configuration

```python
class TLSConfig:
    """TLS/SSL configuration."""
    
    TLS_CONFIG = {
        "min_version": "TLSv1.2",
        "cipher_suites": [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES128-GCM-SHA256"
        ],
        "prefer_server_ciphers": True,
        "session_tickets": False,
        "ocsp_stapling": True,
        "hsts": {
            "enabled": True,
            "max_age": 31536000,
            "include_subdomains": True,
            "preload": True
        }
    }
    
    @staticmethod
    def get_ssl_context(cert_file: str, key_file: str):
        """Create SSL context with secure configuration."""
        import ssl
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Load certificate and key
        context.load_cert_chain(cert_file, key_file)
        
        # Set cipher suites
        context.set_ciphers(":".join(TLSConfig.TLS_CONFIG["cipher_suites"]))
        
        return context
```

### Network Policies

```yaml
# Kubernetes network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vexiscore-network-policy
  namespace: vexiscore
spec:
  podSelector:
    matchLabels:
      app: vexiscore
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: monitoring
        - podSelector:
            matchLabels:
              app: nginx-ingress
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:  # Allow DNS
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

## Phase Security

### Phase 1: Strategic Assessment Security

```python
class Phase1Security:
    """Security controls for Phase 1: Strategic Assessment."""
    
    def validate_input(self, user_input: str) -> dict:
        """Validate and sanitize user input."""
        # Check for injection attacks
        if self._detect_injection(user_input):
            raise SecurityError("Potential injection attack detected")
        
        # Sanitize input
        sanitized = self._sanitize(user_input)
        
        # Validate input length
        if len(sanitized) > 10000:
            raise ValidationError("Input exceeds maximum length")
        
        return {"input": sanitized, "valid": True}
    
    def _detect_injection(self, text: str) -> bool:
        """Detect potential injection attacks."""
        dangerous_patterns = [
            r"<script.*?>",
            r"javascript:",
            r"on\w+\s*=",
            r"SELECT\s+.*\s+FROM",
            r"INSERT\s+INTO",
            r"DELETE\s+FROM",
            r"DROP\s+TABLE",
            r"UNION\s+SELECT",
            r"exec\s*\(",
            r"eval\s*\(",
            r"__import__",
            r"os\.system",
            r"subprocess\."
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _sanitize(self, text: str) -> str:
        """Sanitize text input."""
        import html
        text = html.escape(text)
        text = text.replace("\x00", "")
        return text
```

### Phase 3: Execution Security

```python
class Phase3Security:
    """Security controls for Phase 3: Pilot Implementation."""
    
    ALLOWED_COMMANDS = [
        "ls", "cat", "echo", "mkdir", "cp", "mv", "rm",
        "grep", "find", "chmod", "chown", "tar", "gzip",
        "git", "python3", "pip", "npm", "node"
    ]
    
    BLOCKED_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs.",
        "dd if=",
        "> /dev/sda",
        "curl.*\|.*bash",
        "wget.*\|.*bash",
        "eval(",
        "exec(",
        "__import__(",
        "os.system(",
        "subprocess.call("
    ]
    
    def validate_command(self, command: str) -> dict:
        """Validate command for safe execution."""
        # Check against blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in command:
                raise SecurityError(
                    f"Command contains blocked pattern: {pattern}"
                )
        
        # Check if command is in allowed list
        cmd_base = command.split()[0] if command.split() else ""
        if cmd_base not in self.ALLOWED_COMMANDS:
            raise SecurityError(
                f"Command not in allowed list: {cmd_base}"
            )
        
        return {"command": command, "valid": True}
    
    def execute_sandboxed(self, command: str) -> dict:
        """Execute command in sandboxed environment."""
        import subprocess
        
        # Validate command first
        self.validate_command(command)
        
        # Execute with restricted permissions
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            env=self._get_restricted_env(),
            cwd="/tmp/sandbox"
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    def _get_restricted_env(self) -> dict:
        """Get restricted environment variables."""
        import os
        
        # Start with minimal environment
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp",
            "TMPDIR": "/tmp"
        }
        
        return env
```

## Provider Security

### Provider Authentication

```python
class ProviderSecurity:
    """Manage provider authentication and security."""
    
    def __init__(self, config: dict):
        self.config = config
        self.credential_store = CredentialStore(config)
    
    def get_provider_credentials(self, provider: str) -> dict:
        """Get encrypted provider credentials."""
        credentials = self.credential_store.get(f"provider:{provider}")
        
        if not credentials:
            raise ConfigurationError(
                f"No credentials found for provider: {provider}"
            )
        
        return credentials
    
    def rotate_credentials(self, provider: str):
        """Rotate provider credentials."""
        # Generate new credentials
        new_credentials = self._generate_credentials(provider)
        
        # Store new credentials
        self.credential_store.store(
            f"provider:{provider}",
            new_credentials
        )
        
        # Log rotation event
        self._log_credential_rotation(provider)
    
    def validate_provider_connection(self, provider: str) -> bool:
        """Validate provider connection security."""
        credentials = self.get_provider_credentials(provider)
        
        # Check if using HTTPS
        endpoint = credentials.get("endpoint", "")
        if not endpoint.startswith("https://"):
            raise SecurityError(
                f"Provider {provider} must use HTTPS"
            )
        
        # Verify certificate
        self._verify_certificate(endpoint)
        
        return True
```

## Compliance

### Compliance Framework

```python
class ComplianceManager:
    """Manage compliance requirements."""
    
    FRAMEWORKS = {
        "GDPR": {
            "requirements": [
                "data_minimization",
                "right_to_erasure",
                "data_portability",
                "consent_management",
                "breach_notification"
            ]
        },
        "HIPAA": {
            "requirements": [
                "phi_protection",
                "access_controls",
                "audit_trails",
                "encryption",
                "business_associate_agreements"
            ]
        },
        "SOC2": {
            "requirements": [
                "security",
                "availability",
                "processing_integrity",
                "confidentiality",
                "privacy"
            ]
        },
        "PCI_DSS": {
            "requirements": [
                "firewall_configuration",
                "encryption",
                "access_controls",
                "monitoring",
                "vulnerability_management"
            ]
        }
    }
    
    def check_compliance(self, framework: str) -> dict:
        """Check compliance for a specific framework."""
        requirements = self.FRAMEWORKS.get(framework, {}).get("requirements", [])
        
        results = {}
        for requirement in results:
            results[requirement] = self._check_requirement(requirement)
        
        return {
            "framework": framework,
            "requirements": results,
            "compliant": all(results.values()),
            "timestamp": time.time()
        }
    
    def generate_compliance_report(self, frameworks: list) -> dict:
        """Generate compliance report for multiple frameworks."""
        report = {
            "generated_at": time.time(),
            "frameworks": {}
        }
        
        for framework in frameworks:
            report["frameworks"][framework] = self.check_compliance(framework)
        
        report["overall_compliant"] = all(
            f["compliant"] for f in report["frameworks"].values()
        )
        
        return report
```

## Security Monitoring

### Audit Logging

```python
class AuditLogger:
    """Comprehensive audit logging."""
    
    def __init__(self, config: dict):
        self.config = config
        self.log_store = LogStore(config)
    
    def log_event(self, event_type: str, details: dict):
        """Log an audit event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "source_ip": details.get("source_ip"),
            "user_id": details.get("user_id"),
            "session_id": details.get("session_id"),
            "resource": details.get("resource"),
            "action": details.get("action"),
            "result": details.get("result"),
            "severity": details.get("severity", "INFO")
        }
        
        self.log_store.store(event)
    
    def log_auth_event(self, user: dict, action: str, result: str):
        """Log authentication event."""
        self.log_event("authentication", {
            "user_id": user.get("id"),
            "username": user.get("username"),
            "action": action,
            "result": result,
            "source_ip": user.get("source_ip"),
            "user_agent": user.get("user_agent")
        })
    
    def log_data_access(self, user: dict, resource: str, action: str):
        """Log data access event."""
        self.log_event("data_access", {
            "user_id": user.get("id"),
            "resource": resource,
            "action": action,
            "timestamp": time.time()
        })
    
    def log_security_event(self, event_type: str, details: dict):
        """Log security-related event."""
        self.log_event(f"security:{event_type}", {
            **details,
            "severity": "WARNING"
        })
```

### Threat Detection

```python
class ThreatDetector:
    """Detect potential security threats."""
    
    def __init__(self, config: dict):
        self.config = config
        self.rules = self._load_rules()
        self.anomaly_detector = AnomalyDetector(config)
    
    def is_threat(self, request: dict) -> bool:
        """Analyze request for potential threats."""
        # Check against known threat patterns
        for rule in self.rules:
            if self._matches_rule(request, rule):
                return True
        
        # Check for anomalous behavior
        if self.anomaly_detector.is_anomalous(request):
            return True
        
        return False
    
    def _matches_rule(self, request: dict, rule: dict) -> bool:
        """Check if request matches a threat rule."""
        conditions = rule.get("conditions", [])
        
        for condition in conditions:
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]
            
            request_value = self._get_field_value(request, field)
            
            if not self._evaluate_condition(request_value, operator, value):
                return False
        
        return True
    
    def _evaluate_condition(self, value: Any, operator: str, expected: Any) -> bool:
        """Evaluate a condition."""
        operators = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "contains": lambda a, b: b in a,
            "regex": lambda a, b: bool(re.match(b, str(a)))
        }
        
        op_func = operators.get(operator)
        if not op_func:
            return False
        
        return op_func(value, expected)
```

## Incident Response

### Incident Response Plan

```python
class IncidentResponse:
    """Manage security incident response."""
    
    SEVERITY_LEVELS = {
        "low": {"response_time": 240, "escalation": "team_lead"},
        "medium": {"response_time": 60, "escalation": "manager"},
        "high": {"response_time": 15, "escalation": "director"},
        "critical": {"response_time": 5, "escalation": "ciso"}
    }
    
    def handle_incident(self, incident: dict) -> dict:
        """Handle a security incident."""
        # Step 1: Classify incident
        severity = self._classify_severity(incident)
        
        # Step 2: Contain the threat
        containment_result = self._contain_threat(incident)
        
        # Step 3: Investigate
        investigation_result = self._investigate(incident)
        
        # Step 4: Remediate
        remediation_result = self._remediate(incident)
        
        # Step 5: Recover
        recovery_result = self._recover(incident)
        
        # Step 6: Document
        self._document_incident(incident, {
            "severity": severity,
            "containment": containment_result,
            "investigation": investigation_result,
            "remediation": remediation_result,
            "recovery": recovery_result
        })
        
        return {
            "incident_id": incident["id"],
            "status": "resolved",
            "severity": severity
        }
    
    def _classify_severity(self, incident: dict) -> str:
        """Classify incident severity."""
        impact = incident.get("impact", "low")
        scope = incident.get("scope", "limited")
        
        if impact == "critical" or scope == "widespread":
            "critical"
        elif impact == "high" or scope == "significant":
            return "high"
        elif impact == "medium":
            return "medium"
        else:
            return "low"
    
    def _contain_threat(self, incident: dict) -> dict:
        """Contain the threat."""
        threat_type = incident.get("type")
        
        containment_actions = {
            "unauthorized_access": self._revoke_access,
            "data_breach": self._isolate_affected_systems,
            "malware": self._quarantine_systems,
            "ddos": self._activate_ddos_protection
        }
        
        action = containment_actions.get(threat_type)
        if action:
            return action(incident)
        
        return {"status": "no_action_available"}
```

## Security Best Practices

### Development Security

1. **Input Validation**
   ```python
   def validate_input(data: dict, schema: dict) -> bool:
       """Validate input against schema."""
       from jsonschema import validate
       try:
           validate(instance=data, schema=schema)
           return True
       except Exception:
           return False
   ```

2. **Secure Configuration**
   ```yaml
   # Never store secrets in configuration files
   # Use environment variables or secret management
   
   database:
     password: "${DB_PASSWORD}"  # Environment variable
   
   api:
     secret_key: "${API_SECRET_KEY}"  # Environment variable
   ```

3. **Dependency Management**
   ```bash
   # Regularly audit dependencies
   safety check
   pip audit
   
   # Keep dependencies updated
   poetry update
   ```

4. **Code Review Security Checklist**
   - [ ] No hardcoded secrets or credentials
   - [ ] All inputs validated and sanitized
   - [ ] Proper error handling (no sensitive data in errors)
   - [ ] SQL queries use parameterized statements
   - [ ] File operations validate paths
   - [ ] Authentication checks on all endpoints
   - [ ] Authorization checks for all resources
   - [ ] Sensitive data encrypted at rest and in transit

## Vulnerability Management

### Vulnerability Scanning

```python
class VulnerabilityScanner:
    """Scan for vulnerabilities."""
    
    def scan_dependencies(self) -> list:
        """Scan dependencies for known vulnerabilities."""
        import subprocess
        
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return json.loads(result.stdout)
        
        return []
    
    def scan_code(self) -> list:
        """Scan code for security issues."""
        import subprocess
        
        result = subprocess.run(
            ["bandit", "-r", "app/", "-f", "json"],
            capture_output=True,
            text=True
        )
        
        return json.loads(result.stdout)
    
    def scan_infrastructure(self) -> list:
        """Scan infrastructure for vulnerabilities."""
        # Use tools like OpenVAS, Nessus, or similar
        pass
    
    def generate_report(self) -> dict:
        """Generate vulnerability report."""
        return {
            "dependencies": self.scan_dependencies(),
            "code": self.scan_code(),
            "infrastructure": self.scan_infrastructure(),
            "timestamp": time.time()
        }
```

---

**Security Version**: 2.1.0  
**Last Updated**: 2026-05-24  
**Maintainer**: VEXIS-CLI-3 Security Team