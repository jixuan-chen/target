from setuptools import setup, find_packages


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename) as f:
        return f.read().splitlines()


setup(
    name="target-py",
    version="0.1.6",
    author="Jixuan Chen",
    author_email="jixuan.chen@eawag.ch",
    description="Python version of the air temperature response to green/blue infrastructure evaluation tool (TARGET)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jixuan-chen/target",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=parse_requirements('requirements.txt'),
    include_package_data=True,
    package_data={'': ['example/data/*']}
)
