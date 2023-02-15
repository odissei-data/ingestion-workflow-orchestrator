from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['app/settings.toml', 'app/scripts.secrets.toml'],
    environments=True,
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
