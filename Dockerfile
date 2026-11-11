# Dev image (CPU only). Semester 2 will add a multi-stage prod image.
# Pinned to the multi-arch python:3.11-slim manifest digest resolved on
# 2026-10-26; review digest updates alongside the dependency/security checks.
FROM python:3.11-slim@sha256:b7a9e5f6a93d6d4a31f129bbd4bdee69efccb6ded0fb230d78aafaf37af98377

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Debian trixie's apt 3.0.3 is affected by CVE-2026-109518 and zlib1g
# 1.3.dfsg+really1.3.1-1+b1 by CVE-2026-76844/CVE-2026-85091. Disable retries
# while obtaining the security updates, then require the fixed package versions.
RUN apt-get -o Acquire::Retries=0 update \
    && apt-get -o Acquire::Retries=0 install -y --no-install-recommends --only-upgrade \
        apt libapt-pkg7.0 zlib1g \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' apt)" ge 3.0.4 \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' zlib1g)" ge 1:1.3.dfsg+really1.3.1-1+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

# The pinned runtime packages ship manylinux wheels; no compiler toolchain is
# kept in the final image.
COPY requirements.txt requirements-torch.txt ./
RUN python -m pip install --upgrade pip==26.2.2 \
    && python -m pip install -r requirements.txt \
    && python -m pip install -r requirements-torch.txt \
    && python -m pip check \
    && python -m pip uninstall -y pip

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser api/ api/
COPY --chown=appuser:appuser dashboard/ dashboard/
COPY --chown=appuser:appuser scripts/ scripts/
COPY --chown=appuser:appuser docs/ docs/

USER appuser

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
