from setuptools import find_namespace_packages, setup


def get_requirements(path: str):
    return [l.strip() for l in open(path)]


setup(
    name="llm_xpu",
    version="0.0.1",
    packages=find_namespace_packages(include=["llmxpu", "llmxpu.models", "llmxpu.tools"]),
    install_requires=get_requirements("requirements.txt"),
)
