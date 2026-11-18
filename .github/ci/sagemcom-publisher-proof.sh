#!/usr/bin/env bash
set -euo pipefail

base_commit=627886ece167fc3fe6c95ff0431353629b769bfb
base_index=0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd
db_blob=71ee3bcdae62762c61c1416b6f9a6978b3a2d15d53c2f5f7350f9ab46688aeac
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

case "$ARCHITECTURE/$(uname -m)" in
  amd64/x86_64)
    asset=trivy_0.70.0_Linux-64bit.tar.gz
    checksum=8b4376d5d6befe5c24d503f10ff136d9e0c49f9127a4279fd110b727929a5aa9
    ;;
  arm64/aarch64)
    asset=trivy_0.70.0_Linux-ARM64.tar.gz
    checksum=2f6bb988b553a1bbac6bdd1ce890f5e412439564e17522b88a4541b4f364fc8d
    ;;
  *)
    echo "Expected native runner architecture $ARCHITECTURE" >&2
    exit 1
    ;;
esac

test "$(git rev-parse HEAD)" = "$CANDIDATE_HEAD"
git diff --exit-code "$base_commit" "$CANDIDATE_HEAD" -- pyproject.toml README.md uv.lock sagemcom_f3896_client/
git show "$base_commit:Dockerfile" > "$tmp/original.Dockerfile"
test "$(grep -c '^FROM python:3\.15-alpine' "$tmp/original.Dockerfile")" -eq 2
# Both baseline FROMs are resolved to the exact official digest from the failing run.
sed "s|^FROM python:3\.15-alpine|FROM python:3.15-alpine@sha256:$base_index|" \
  "$tmp/original.Dockerfile" > "$tmp/baseline.Dockerfile"
test "$(grep -c "^FROM python:3.15-alpine@sha256:$base_index" Dockerfile)" -eq 2

curl --fail --silent --show-error --location --retry 2 --max-time 100 \
  "https://github.com/aquasecurity/trivy/releases/download/v0.70.0/$asset" --output "$tmp/trivy.tar.gz"
printf '%s  %s\n' "$checksum" "$tmp/trivy.tar.gz" | sha256sum --check -
tar -xzf "$tmp/trivy.tar.gz" -C "$tmp" trivy
mkdir -p "$tmp/scan/db"
curl --fail --silent --show-error --location --retry 2 --max-time 100 \
  "https://mirror.gcr.io/v2/aquasec/trivy-db/blobs/sha256:$db_blob" --output "$tmp/db.tar.gz"
printf '%s  %s\n' "$db_blob" "$tmp/db.tar.gz" | sha256sum --check -
tar -xzf "$tmp/db.tar.gz" -C "$tmp/scan/db" metadata.json trivy.db
jq -e '.Version == 2 and .UpdatedAt == "2026-11-18T13:03:23.615586156Z"' "$tmp/scan/db/metadata.json" >/dev/null

for variant in baseline candidate; do
  dockerfile=Dockerfile
  if [ "$variant" = baseline ]; then
    dockerfile="$tmp/baseline.Dockerfile"
  fi
  image="sagemcom-runtime-proof:92-$variant"
  docker buildx build --load --platform "linux/$ARCHITECTURE" --file "$dockerfile" --tag "$image" .
  test "$(docker image inspect "$image" --format '{{.Architecture}}')" = "$ARCHITECTURE"
  docker image inspect "$image" --format '{{json .Config}}' | \
    jq -cS '{Entrypoint,Cmd,User,WorkingDir,Env,ExposedPorts,Healthcheck}' > "$tmp/$variant.config.json"
  timeout 30 docker run --rm --network none -i "$image" python - \
    < .github/ci/sagemcom-runtime-smoke.py > "$tmp/$variant.smoke.json"
  image_archive="$tmp/$variant.image.tar"
  docker save "$image" --output "$image_archive"
  exit_code=0
  "$tmp/trivy" --cache-dir "$tmp/scan" image --input "$image_archive" --scanners vuln,secret \
      --severity HIGH,CRITICAL --ignore-unfixed=false --skip-db-update --skip-java-db-update \
      --skip-version-check --cache-backend memory --format json --output "$tmp/$variant.scan.json" \
      --exit-code 1 --timeout 2m || exit_code=$?
  test -s "$tmp/$variant.scan.json"
  os_type="$(jq -r '.Metadata.OS.Family' "$tmp/$variant.scan.json")"
  test "$os_type" = alpine
  echo "$variant $ARCHITECTURE scan exit $exit_code"
  test "$(jq '[.Results[] | .Secrets[]?] | length' "$tmp/$variant.scan.json")" -eq 0
  if [ "$variant" = baseline ]; then
    test "$exit_code" -eq 1
    actual="$(jq -r '[.Results[] | .Vulnerabilities[]? | .VulnerabilityID] | sort | join(",")' "$tmp/$variant.scan.json")"
    expected=CVE-2025-47273,CVE-2026-114613,CVE-2026-97687,CVE-2026-97689,GHSA-6v7p-g79w-8964
    test "$actual" = "$expected"
  else
    test "$exit_code" -eq 0
    test "$(jq '[.Results[] | .Vulnerabilities[]?] | length' "$tmp/$variant.scan.json")" -eq 0
  fi
done

cmp "$tmp/baseline.config.json" "$tmp/candidate.config.json"
cmp "$tmp/baseline.smoke.json" "$tmp/candidate.smoke.json"
jq -e '.User == "app" and .Cmd == ["python", "-m", "sagemcom_f3896_client.exporter", "-v"]' \
  "$tmp/candidate.config.json" >/dev/null
docker run --rm --network none sagemcom-runtime-proof:92-baseline /usr/local/bin/python -m pip --version
pip_rc=0
docker run --rm --network none sagemcom-runtime-proof:92-candidate /usr/local/bin/python -m pip --version \
  > "$tmp/removed-pip.log" 2>&1 || pip_rc=$?
test "$pip_rc" -eq 1
grep -q 'No module named pip' "$tmp/removed-pip.log"

# The same runtime smoke must fail when a required package is removed.
docker build --network none --pull=false --tag sagemcom-runtime-proof:92-missing-dependency - <<'DOCKERFILE'
FROM sagemcom-runtime-proof:92-candidate
USER root
RUN rm -r /usr/src/app/.venv/lib/python3.15/site-packages/prometheus_async
USER app
DOCKERFILE
missing_rc=0
timeout 30 docker run --rm --network none -i sagemcom-runtime-proof:92-missing-dependency python - \
  < .github/ci/sagemcom-runtime-smoke.py > "$tmp/missing-dependency.log" 2>&1 || missing_rc=$?
test "$missing_rc" -eq 1
grep -q "No module named 'prometheus_async'" "$tmp/missing-dependency.log"

jq -c '{uid,gid,python,required_shells,ca_anchors:(.ca_anchors|length),installed_runtime:(.installed_runtime|length),exporter_http,modem_fixture_requests}' \
    "$tmp/candidate.smoke.json"
echo "Native runtime config and smoke match. Missing-package control failed at exporter startup."
