from typing import Optional
from urllib.parse import urlparse

import dns.resolver


"""
Note, is is smart not to use a cache, so that you can use the built-in
DNS cache of the machine you're running on.
"""


def uri_find_semantic_matching_service(semantic_id: str) -> Optional[str]:
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


def iri_find_semantic_matching_service(semantic_id: str) -> Optional[str]:
    pass


def is_uri_not_iri(semantic_id: str) -> Optional[bool]:
    """
    :return: `True`, if `semantic_id` is a URI, False if it is an `IRI`, None for neither
    """
    parsed_url = urlparse(semantic_id)
    # Check if the scheme is present, which indicates it's a URI
    if parsed_url.scheme:
        return True
    # Check if there is a colon in the netloc, which could indicate an IRI
    elif ':' in parsed_url.netloc:
        return False
    # If neither condition is met, return None
    else:
        return None


def find_semantic_matching_service(semantic_id: str) -> Optional[str]:
    """
    Finds the suiting Semantic Matching Service to the given `semantic_id`

    :param semantic_id:
    :return:
    """
    if is_uri_not_iri(semantic_id) is True:
        return uri_find_semantic_matching_service(semantic_id)
    elif is_uri_not_iri(semantic_id) is False:
        return iri_find_semantic_matching_service(semantic_id)
    else:
        return None


if __name__ == "__main__":
    print(uri_find_semantic_matching_service("https://s-heppner.com/foo/bar"))
