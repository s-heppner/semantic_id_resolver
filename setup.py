import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="semantic_id_resolver",
    version="0.0.1",
    author="Sebastian Heppner",
    author_email="mail@s-heppner.com",
    description="A Prototype Service resolving Semantic IDs to their suiting Semantic Matching Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=["semantic_id_resolver"]
)
