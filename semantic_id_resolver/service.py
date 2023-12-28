from typing import Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from semantic_id_resolver import resolver


class SMSRequest(BaseModel):
    semantic_id: str


class SMSResponse(BaseModel):
    semantic_matching_service_endpoint: str
    meta_information: Dict


class SemanticIdResolvingService:
    """
    A Service, resolving semantic_ids to their respective
    Semantic Matching Service
    """
    def __init__(
            self,
            endpoint: str,
            fallback_semantic_matching_service_endpoint: str,
            semantic_id_resolver: resolver.SemanticIdResolver
    ):
        """
        Initializer of :class:`~.SemanticMatchingService`

        :ivar endpoint: The endpoint on which the service listens
        """
        self.router = APIRouter()
        self.router.add_api_route(
            "/get_semantic_matching_service",
            self.get_semantic_matching_service,
            methods=["GET"]
        )
        self.endpoint: str = endpoint
        self.fallback_semantic_matching_service_endpoint: str = fallback_semantic_matching_service_endpoint
        self.semantic_id_resolver: resolver.SemanticIdResolver = semantic_id_resolver

    def get_semantic_matching_service(
            self,
            request_body: SMSRequest
    ) -> SMSResponse:
        """
        Returns a Semantic Matching Service for a given semantic_id
        """
        found_endpoint: Optional[str] = self.semantic_id_resolver.find_semantic_matching_service(
            semantic_id=request_body.semantic_id
        )
        if found_endpoint is None:
            endpoint: str = self.fallback_semantic_matching_service_endpoint
        else:
            endpoint = found_endpoint
        return SMSResponse(
            semantic_matching_service_endpoint=endpoint,
            meta_information={}  # Todo
        )


if __name__ == '__main__':
    import os
    import configparser
    from fastapi import FastAPI
    import uvicorn

    config = configparser.ConfigParser()
    config.read([
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../config.ini.default")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../config.ini")),
    ])

    IRDI_MATCHER_DICT: Dict[resolver.IRDISources, str] = {
        resolver.IRDISources.ECLASS: config["RESOLVER"]["eclass_semantic_matching_service"],
        resolver.IRDISources.IEC_CDD: config["RESOLVER"]["cdd_semantic_matching_service"]
    }

    RESOLVER = resolver.SemanticIdResolver(IRDI_MATCHER_DICT)

    SEMANTIC_ID_RESOLVING_SERVICE = SemanticIdResolvingService(
        endpoint=config["SERVICE"]["endpoint"],
        fallback_semantic_matching_service_endpoint=config["RESOLVER"]["fallback_semantic_matching_service"],
        semantic_id_resolver=RESOLVER
    )
    APP = FastAPI()
    APP.include_router(
        SEMANTIC_ID_RESOLVING_SERVICE.router
    )
    uvicorn.run(APP, host="127.0.0.1", port=int(config["SERVICE"]["PORT"]))
