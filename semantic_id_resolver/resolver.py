import enum
from typing import Optional, Dict
from urllib.parse import urlparse
import json

import dns.resolver
from parser.irdi_parser import IRDIParser


class DebugSemanticMatchingServiceEndpoints:
    """
    This class adds the ability to set arbitrary Semantic Matching Service
    Endpoints to overwrite whatever the DNS record would say.
    In order to use it, you need to provide a JSON file with a Dict, mapping
    a semantic ID directly to a Semantic Matching Service endpoint.

    Note: This is not the base URL of the semanticID, rather the complete
    semanticID string!
    """
    debug_endpoints: Dict[str, str]

    def __init__(self, debug_endpoints: Dict[str, str]):
        self.debug_endpoints = debug_endpoints

    @classmethod
    def from_file(cls, filename: str) -> "DebugSemanticMatchingServiceEndpoints":
        with open(filename, "r") as file:
            debug_endpoints = json.load(file)
        return DebugSemanticMatchingServiceEndpoints(debug_endpoints)

    def get_debug_endpoint(self, semantic_id: str) -> Optional[str]:
        return self.debug_endpoints.get(semantic_id)


def is_iri_not_irdi(semantic_id: str) -> Optional[bool]:
    """
    :return: `True`, if `semantic_id` is an IRI, False if it is an IRDI, None for neither
    """
    # Check IRDI
    try:
        IRDIParser().parse(semantic_id)
        return False
    except ValueError:
        pass
    # Check IRI
    parsed_url = urlparse(semantic_id)
    if parsed_url.scheme:
        return True
    # Not IRDI or IRI
    return None


class IRDISources(enum.Enum):
    ECLASS = "ECLASS"
    IEC_CDD = "IEC_CDD"


def _iri_find_semantic_matching_service(semantic_id: str) -> Optional[str]:
    # (2023-12-28, s-heppner)
    # Note, it is smart not to use a cache URI based semantic_ids,
    # so that you can use the built-in DNS cache of the machine you're running on.

    # Parse the given semantic_id and just use the main domain name
    domain = urlparse(semantic_id).netloc
    # Try to find the "semantic_matcher" DNS TXT record
    try:
        result = dns.resolver.resolve(domain, 'TXT')
        for txt_record in result:
            if txt_record.strings and txt_record.strings[0].decode().startswith("semantic_matcher"):
                semantic_matcher_record = txt_record.strings[0].decode()
                try:
                    semantic_matcher_endpoint = semantic_matcher_record.split(": ")[-1]
                    return semantic_matcher_endpoint
                # ToDo What happens if we have several services here?
                except Exception as e:
                    print(f"Cannot parse TXT record {semantic_matcher_record} for {domain}: {e}")
                    return None
        print(f"No DNS TXT record starting with 'semantic_matcher' found for {domain}")
        return None
    except dns.resolver.NXDOMAIN:
        print(f"No DNS records found for {domain}")
        return None
    except dns.resolver.NoAnswer:
        print(f"No TXT records found for {domain}")
        return None


class SemanticIdResolver:
    def __init__(
            self,
            irdi_matchers: Dict[IRDISources, str],
            debug_endpoints: DebugSemanticMatchingServiceEndpoints
    ):
        self.irdi_matchers: Dict[IRDISources, str] = irdi_matchers
        self.debug_endpoints: DebugSemanticMatchingServiceEndpoints = debug_endpoints

    def find_semantic_matching_service(self, semantic_id: str) -> Optional[str]:
        """
        Finds the suiting Semantic Matching Service to the given `semantic_id`

        :param semantic_id:
        :return:
        """
        # Check if there's a debug endpoint
        debug_endpoint: Optional[str] = self.debug_endpoints.get_debug_endpoint(semantic_id=semantic_id)
        if debug_endpoint is not None:
            return debug_endpoint

        # Check for IRI and IRDI
        is_iri = is_iri_not_irdi(semantic_id)
        if is_iri is True:
            return _iri_find_semantic_matching_service(semantic_id)
        elif is_iri is False:
            return self._irdi_find_semantic_matching_service(semantic_id)
        else:
            return None

    def _irdi_find_semantic_matching_service(self, semantic_id: str) -> Optional[str]:
        # For IRDI scheme, see: https://eclass.eu/fileadmin/_processed_/9/a/csm_IRDI_graph_14326b2ff2.png
        if semantic_id.startswith("0173"):
            # See: https://eclass.eu/support/technical-specification/structure-and-elements/irdi
            return self.irdi_matchers.get(IRDISources.ECLASS)
        elif semantic_id.startswith("0112"):
            # See: https://cdd.iec.ch/cdd/iec61360/iec61360.nsf/TreeFrameset?OpenFrameSet
            return self.irdi_matchers.get(IRDISources.IEC_CDD)
        else:
            return None


if __name__ == "__main__":
    pass
