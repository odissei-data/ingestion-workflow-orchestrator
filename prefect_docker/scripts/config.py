from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['app/settings.toml', 'app/scripts.secrets.toml'],
    environments=True,
)
