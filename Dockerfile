# Dev image (CPU only). Semester 2 will add a multi-stage prod image.
# Pinned to the multi-arch python:3.11-slim manifest digest resolved on
# 2026-10-26; Dependabot can update this digest.
FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

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

USER appuser

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
