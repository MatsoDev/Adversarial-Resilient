"""Read-only Sprint 3 API. All file identifiers are allowlisted by the store."""

from fastapi import APIRouter, HTTPException
from src.evaluation.artifacts import ArtifactStore, ArtifactUnavailable


def artifact_router(store: ArtifactStore) -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["Research artifacts"])

    def serve(method, name=None):
        try:
            return method() if name is None else method(name)
        except KeyError as error:
            raise HTTPException(404, "Unknown artifact identifier") from error
        except ArtifactUnavailable as error:
            raise HTTPException(503, "Artifact is unavailable or invalid") from error

    @router.get("/datasets/{name}")
    def dataset(name: str):
        return serve(store.dataset, name)

    @router.get("/runs")
    def runs():
        return serve(store.runs)

    @router.get("/demo")
    def demo():
        return serve(store.demo)

    @router.get("/attacks")
    def attacks():
        return serve(store.attacks)

    @router.get("/reports/{name}")
    def report(name: str):
        return serve(store.report, name)

    @router.get("/figures/{name}")
    def figure(name: str):
        return serve(store.figure, name)

    return router
