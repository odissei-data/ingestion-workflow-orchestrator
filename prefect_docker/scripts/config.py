from dynaconf import Dynaconf

settings = Dynaconf(
    # envvar_prefix="PREFECT_DOCKER",
    settings_files=['app/settings.toml', 'app/scripts.secrets.toml'],
    environments=True,
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
