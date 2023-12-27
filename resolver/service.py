from typing import List, Dict

from fastapi import APIRouter
from pydantic import BaseModel


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
            endpoint: str
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

    def get_semantic_matching_service(
            self,
            request_body: SMSRequest
    ) -> SMSResponse:
        """
        Returns a Semantic Matching Service for a given semantic_id
        """
        pass


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

    SEMANTIC_ID_RESOLVING_SERVICE = SemanticIdResolvingService(
        endpoint=config["SERVICE"]["endpoint"],
    )
    APP = FastAPI()
    APP.include_router(
        SEMANTIC_ID_RESOLVING_SERVICE.router
    )
    uvicorn.run(APP, host="127.0.0.1", port=int(config["SERVICE"]["PORT"]))
