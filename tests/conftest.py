import os


def pytest_configure():
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(os.path.dirname(__file__), 'test.db'),
                'TEST_NAME': os.path.join(os.path.dirname(__file__), 'test.db'),
            }
        },
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        TEMPLATE_LOADERS=(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ),
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework.authtoken',
            'rest_framework_services_auth',
            'tests',
        ),
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ),
        SERVICES_AUTH={
            'JWT_VERIFICATION_KEY': 'bn4J/xOrd3kIcTT6mmhNC4kXlECLQNUEYH/cLsuiZw/TkeHYcM82zzNkFa0FfmID8eO2Qmbw5lSgEsPv2ARzmhCxgRA4seWLaylVNc7x3skWe85kGCQPR/qSLtnzaWAaeRRX3zAv7ZWmpIvAzp3ruuJbzXS83rJ9vfJf4N+FG7PHJDV34kFC0240Y4IcBFkwz+qMm9F2NRWzErGhK/9DfW6LL6kSHlRploxCP/wSmPX6jDsI8XNYTjCJdmUNLWHKKOj75gMAOyK1Q3hocwtuzwkIBcOKgckPhi2WPtcHos04aKi97I3FM5869zMk5/YCvmZs/ktAlYwYok4X/UHZZw==',
            'JWT_ALGORITHM': 'HS256',
            'JWT_AUDIENCE': 'audience',
            'JWT_ISSUER': 'issuer',
            'JWT_AUTH_HEADER_PREFIX': 'JWT'
        }
    )

    try:
        import django
        django.setup()
    except AttributeError:
        pass
