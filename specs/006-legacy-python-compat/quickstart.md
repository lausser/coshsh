# Quickstart: Verify Legacy Python (<3.8) Compatibility

Runnable validation of the feature on the CentOS 7 / Python 3.6 target. These are the exact steps that were used to validate the approach (47 collection errors → 206 passed).

## Prerequisites (target = Python 3.6, CentOS 7)

Container: podman `4e89e6751911`. Playground: `/packages/coshsh/coshsh-12.2.1.1` (a copy of the `/src/coshsh` mount). Rebuild the playground with `rsync` inside the container.

Provision the runtime/test environment a real coshsh install would have:

```sh
# language + test toolchain (EPEL)
yum install -y epel-release
yum install -y python36-pytest python36-jinja2 python36-pycryptodomex   # pytest 2.9.2, jinja2 2.11.1, vault backend
pip3 install prometheus_client GitPython                                # pushgateway datarecipient + delta tests

# writable temp dirs + git identity + non-root run user
mkdir -p /tmp /var/tmp
git config --global user.email "test@coshsh.test" && git config --global user.name "coshsh test"
# run the suite as a NON-root user (test_pid checks non-writable-dir detection, which root bypasses)
```

## Build the playground and apply the compat layer

```sh
rsync -a --delete \
  --exclude .git --exclude .specify --exclude .claude --exclude specs --exclude .serena \
  /src/coshsh/ /packages/coshsh/coshsh-12.2.1.1/
cd /packages/coshsh/coshsh-12.2.1.1
rm -rf var/objects tests/var/objects        # untracked generated artifacts; a fresh checkout has none

# the three additive/edited pieces this feature delivers:
#   1) coshsh_pycompat.py        (new, at package root)
#   2) tests/conftest.py         (new)
#   3) bin/coshsh-cook & bin/coshsh-create-template-tree  (gated compat bootstrap; future-import removed)
```

See [data-model.md](./data-model.md) for what each piece contains and [contracts/compat-activation.md](./contracts/compat-activation.md) for the behavioral contract they must satisfy. (Implementation bodies are produced in the implement phase, not here.)

## Run

```sh
cd /packages/coshsh/coshsh-12.2.1.1
TMPDIR=/tmp pytest-3 -p no:cacheprovider -q
```

## Expected outcomes

| Check | Expected |
|-------|----------|
| Baseline (no compat) | 47 collection errors, 0 tests run — reproduces the problem |
| Core language compat only | `SyntaxError: future feature annotations` gone; ~186 passed |
| Full compat + provisioned env | `pytest-3` exits 0 (or only environment-specific skips) — **SC-001** |
| `git diff coshsh/` | empty — **SC-003** |
| edited pre-existing files | exactly `bin/coshsh-cook`, `bin/coshsh-create-template-tree` — **SC-004** |

## Regression check on modern Python (≥3.8)

```sh
# on a Python 3.12 checkout with the feature present:
pytest -q                       # results identical to upstream — SC-002
python -c "import coshsh_pycompat, sys; print(sys.version_info >= (3,8))"   # gate False → nothing installed — SC-005
git diff --stat coshsh/         # empty
```

## Residual environment failures (NOT compat defects)

If any of the following still fail, they are environment prerequisites, not coshsh-source incompatibilities (see [research.md](./research.md) taxonomy):

- `test_bin` temp-file errors → ensure writable `/tmp` **and** `/var/tmp`.
- `test_pid:112` → run the suite as a **non-root** user.
- `test_pushgateway` → start a Prometheus pushgateway on `127.0.0.1:9091` (or accept the skip where unavailable).
