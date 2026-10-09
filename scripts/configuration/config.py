from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=[
        'scripts/configuration/settings.toml',
        'scripts/configuration/odissei_settings.toml',
        'scripts/configuration/sicada_settings.toml',
        'scripts/configuration/.secrets.toml'
    ],
    environments=True,
)


def public_url(url):
    """Return url with a known internal base replaced by its public base.

    PUBLIC_URLS maps each service's internal base URL, which the worker calls,
    to the URL it is published under, so records and logs show public URLs.
    """
    for internal, public in settings.get('PUBLIC_URLS', {}).items():
        if url == internal or url.startswith(internal + '/'):
            return public + url[len(internal):]
    return url
