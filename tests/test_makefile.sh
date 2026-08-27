#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT

phony_targets=$(make --no-print-directory -C "$repo_dir" -np 2>/dev/null | awk '/^\.PHONY:/{print; exit}' || true)
for target in dev-build dev-build-with-service dev-down network network-add setup-env setup-development-env; do
    grep -qw -- "$target" <<<"$phony_targets" || {
        echo "$target is not declared phony" >&2
        exit 1
    }
done

mkdir -p "$test_dir/missing-env"
cp "$repo_dir/Makefile" "$repo_dir/dot_env_example" "$test_dir/missing-env/"
if ! timeout 3 make --no-print-directory -C "$test_dir/missing-env" help >"$test_dir/missing-env-help.log" 2>&1; then
    echo "make help failed or recursed when .env was missing" >&2
    sed -n '1,20p' "$test_dir/missing-env-help.log" >&2
    exit 1
fi
if grep -Fq ".env: No such file or directory" "$test_dir/missing-env-help.log"; then
    echo "make emitted a missing .env error" >&2
    exit 1
fi
make --no-print-directory -C "$test_dir/missing-env" setup-env
cmp "$test_dir/missing-env/dot_env_example" "$test_dir/missing-env/.env"

mkdir -p "$test_dir/bin"
cat >"$test_dir/bin/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == "network inspect -f {{range .Containers}}{{.Name}} {{end}} ingest" ]]; then
    printf '%s\n' 'prefect another-container'
elif [[ "$*" == "network connect ingest prefect" ]]; then
    echo "network-add attempted a duplicate connection" >&2
    exit 42
else
    echo "unexpected docker invocation: $*" >&2
    exit 43
fi
EOF
chmod +x "$test_dir/bin/docker"

network_output=$(PATH="$test_dir/bin:$PATH" make --no-print-directory -C "$repo_dir" \
    network-add network_name=ingest container_name=prefect 2>&1)
grep -Fq "Container prefect is already connected to network ingest." <<<"$network_output"
if grep -Fq "unary operator expected" <<<"$network_output"; then
    echo "network-add emitted a shell unary-operator error" >&2
    exit 1
fi

dry_run=$(make --no-print-directory -C "$repo_dir" --dry-run dev-build-with-service)
grep -Fq "make setup-development-env" <<<"$dry_run"
grep -Fq "make setup-env" <<<"$dry_run"
grep -Fq "docker compose up --build -d" <<<"$dry_run"
grep -Fq "docker compose -f docker-compose-dev.yml up --build -d" <<<"$dry_run"
if grep -Fq "setup-dataverse-stack" <<<"$dry_run"; then
    echo "dev-build-with-service must not set up the portal" >&2
    exit 1
fi

mkdir -p "$test_dir/setup"
cp "$repo_dir/Makefile" "$repo_dir/dot_env_development_example" "$test_dir/setup/"
cp "$repo_dir/dot_env_example" "$test_dir/setup/.env"
setup_output=$(make --no-print-directory -C "$test_dir/setup" setup-development-env 2>&1)
cmp "$test_dir/setup/dot_env_development_example" "$test_dir/setup/.env.development"
if grep -Fq ".env.worker" <<<"$setup_output" || [[ -e "$test_dir/setup/.env.worker" ]]; then
    echo "setup-development-env unexpectedly handled .env.worker" >&2
    exit 1
fi

echo "Makefile regression tests passed."
