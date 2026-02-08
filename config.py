import os
from datetime import timedelta

class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Отключаем debug на продакшене
    DEBUG = False
    TESTING = False
    
    # Лимиты для защиты от DDoS
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # CSP Headers (Content Security Policy)
    CSP = {
        'default-src': "'self'",
        'style-src': ["'self'", "https://cdn.jsdelivr.net", "'unsafe-inline'"],
        'script-src': ["'self'", "https://cdn.jsdelivr.net"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "https://cdn.jsdelivr.net"]
    }

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # В разработке может не быть HTTPS

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    # Переопределяем SECRET_KEY из переменных окружения
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Дополнительные настройки безопасности
    PREFERRED_URL_SCHEME = 'https'
    
    # Отключаем track modifications для SQLAlchemy если используется
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}