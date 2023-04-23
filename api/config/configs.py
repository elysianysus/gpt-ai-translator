import os


class Config:
    TESTING = False


class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    AUDIO_BASE_PATH = os.path.join('data', 'audio')


class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False
    AUDIO_BASE_PATH = os.path.join('data', 'audio')


class ProductionForVercelConfig(Config):
    ENV = 'production'
    DEBUG = False
    AUDIO_BASE_PATH = '/tmp'
