from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=[
        'app/configuration/settings.toml',
        'app/configuration/odissei_settings.toml',
        'app/configuration/sicada_settings.toml',
        'app/configuration/.secrets.toml'
    ],
    environments=True,
)
