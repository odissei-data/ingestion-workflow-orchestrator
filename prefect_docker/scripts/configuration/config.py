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
