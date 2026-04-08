import logging
import json
import re
import os
from logging.handlers import RotatingFileHandler

class SanitizedJSONFormatter(logging.Formatter):
    """
    Format logs as JSON and sanitize sensitive data like API keys.
    """
    # Patrones para censurar: bearer tokens, openai keys, anthropic keys, etc.
    SENSITIVE_PATTERNS = [
        re.compile(r'sk-[a-zA-Z0-9]{20,}'),           # OpenAI / general test keys
        re.compile(r'sk-ant-[a-zA-Z0-9\-_]{20,}'),    # Anthropic
        re.compile(r'Bearer\s+[a-zA-Z0-9\-\._~+/]+=*'), # Bearer tokens
        re.compile(r'x-api-key\s*:\s*[a-zA-Z0-9\-_]{20,}'), # Custom headers
    ]
    
    def sanitize(self, text: str) -> str:
        if not isinstance(text, str):
            return text
            
        sanitized = text
        for pattern in self.SENSITIVE_PATTERNS:
            sanitized = pattern.sub('[REDACTED_KEY]', sanitized)
        return sanitized

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": self.sanitize(record.getMessage())
        }
        
        if record.exc_info:
            log_obj["exception"] = self.sanitize(self.formatException(record.exc_info))
            
        # Incluir datos custom (extra) si existen
        if hasattr(record, "props"):
            log_obj["props"] = {k: self.sanitize(str(v)) for k, v in record.props.items()}
            
        return json.dumps(log_obj)


def setup_logger(name: str = "gravity", log_file: str = "bridge.log", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger with console and rotating file output."""
    logger = logging.getLogger(name)
    
    # Prevenir que agreguemos handlers múltiples si se llama varias veces
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # 1. Console Handler (Standard Text)
    # The console handler keeps standard formatting for the IDE/CLI
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # Aplicar sanitización básica envolviendo el formateador
    class SanitizeConsoleFormatter(logging.Formatter):
        def format(self, record):
            msg = super().format(record)
            formatter = SanitizedJSONFormatter()
            return formatter.sanitize(msg)
            
    console_handler.setFormatter(SanitizeConsoleFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # 2. File Handler (JSON Format)
    # Rotating file handler: 10MB max, keep 5 backups
    try:
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(SanitizedJSONFormatter())
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logger: {e}")
        
    return logger

# Instancia global por defecto
log = setup_logger()
