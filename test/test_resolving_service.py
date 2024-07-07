import os
import configparser
from typing import Dict
import multiprocessing

import dns
import requests
import unittest

from fastapi import FastAPI
import uvicorn

from semantic_id_resolver import resolver
from semantic_id_resolver.service import SemanticIdResolvingService, SMSRequest

from contextlib import contextmanager
import signal
import time


def run_server():
    # Load test configuration
    config = configparser.ConfigParser()
    config.read([
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_resources/config.ini")),
    ])

    # Define test configuration
    IRDI_MATCHER_DICT: Dict[resolver.IRDISources, str] = {
        resolver.IRDISources.ECLASS: config["RESOLVER"]["eclass_semantic_matching_service"],
        resolver.IRDISources.IEC_CDD: config["RESOLVER"]["cdd_semantic_matching_service"]
    }

    try:
        DEBUG_ENDPOINTS = resolver.DebugSemanticMatchingServiceEndpoints.from_file(
            config["RESOLVER"]["debug_semantic_matching_service_endpoints"]
        )
        print(f"USING DEBUG ENDPOINTS FROM {config['RESOLVER']['debug_semantic_matching_service_endpoints']}")
    except FileNotFoundError:
        DEBUG_ENDPOINTS = resolver.DebugSemanticMatchingServiceEndpoints(debug_endpoints={})

    # Mock SemanticIdResolvingService for testing
    mock_resolver = resolver.SemanticIdResolver(IRDI_MATCHER_DICT, DEBUG_ENDPOINTS)
    semantic_id_resolver_service = SemanticIdResolvingService(
        endpoint=config["SERVICE"]["endpoint"],
        fallback_semantic_matching_service_endpoint=config["RESOLVER"]["fallback_semantic_matching_service"],
        semantic_id_resolver=mock_resolver
    )

    # Mock TXT record
    class MockTXTRecord:
        def __init__(self, strings):
            self.strings = strings

    # Mock DNS resolving manually, mock for unittest does not work in this context
    def mock_dns_resolver_resolve(qname, rdtype):
        return [MockTXTRecord([b"semantic_matcher: https://example.org/iri_semantic_matching_service"])]
    dns.resolver.resolve = mock_dns_resolver_resolve

    # Run server
    app = FastAPI()
    app.include_router(semantic_id_resolver_service.router)
    uvicorn.run(app, host=str(config["SERVICE"]["ENDPOINT"]), port=int(config["SERVICE"]["PORT"]), log_level="error")


@contextmanager
def run_server_context():
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    try:
        time.sleep(2)  # Wait for the server to start
        yield
    finally:
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            os.kill(server_process.pid, signal.SIGKILL)
            server_process.join()


class TestSemanticMatchingService(unittest.TestCase):

    def test_semantic_matching_service_iri(self):
        with run_server_context():
            sms_request = SMSRequest(semantic_id="foo://example.org:1234/over/there?name=bar#page=3")
            response = requests.get(
                "http://localhost:8125/get_semantic_matching_service",
                data=sms_request.model_dump_json()
            )
            self.assertEqual(
                "https://example.org/iri_semantic_matching_service",
                response.json()["semantic_matching_service_endpoint"]
            )

    def test_semantic_matching_service_irdi_eclass(self):
        with run_server_context():
            sms_request = SMSRequest(semantic_id="0173-0001#01-ACK323#7")
            response = requests.get(
                "http://localhost:8125/get_semantic_matching_service",
                data=sms_request.model_dump_json()
            )
            self.assertEqual(
                "https://example.org/eclass_semantic_matching_service",
                response.json()["semantic_matching_service_endpoint"]
            )

    def test_semantic_matching_service_irdi_cdd(self):
        with run_server_context():
            sms_request = SMSRequest(semantic_id="0112-0001#01-ACK323#7")
            response = requests.get(
                "http://localhost:8125/get_semantic_matching_service",
                data=sms_request.model_dump_json()
            )
            self.assertEqual(
                "https://example.org/cdd_semantic_matching_service",
                response.json()["semantic_matching_service_endpoint"]
            )

    def test_semantic_matching_service_fallback(self):
        with run_server_context():
            sms_request = SMSRequest(semantic_id="nothing")
            response = requests.get(
                "http://localhost:8125/get_semantic_matching_service",
                data=sms_request.model_dump_json()
            )
            self.assertEqual(
                "https://example.org/fallback_semantic_matching_service",
                response.json()["semantic_matching_service_endpoint"]
            )

    def test_semantic_matching_service_debug(self):
        with run_server_context():
            sms_request = SMSRequest(semantic_id="https://example.org/semanticIDone")
            response = requests.get(
                "http://localhost:8125/get_semantic_matching_service",
                data=sms_request.model_dump_json()
            )
            self.assertEqual(
                "https://example.org/debug_semantic_matching_service",
                response.json()["semantic_matching_service_endpoint"]
            )


if __name__ == '__main__':
    unittest.main()
