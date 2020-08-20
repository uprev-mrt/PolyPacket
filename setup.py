import setuptools




with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='polypacket',
     version='1.0.50',
     author="Jason Berger",
     author_email="JBerger@up-rev.com",
     description="A tool for building protocol services",
     long_description=long_description,
     scripts=['polypacket/poly-packet','polypacket/poly-make'],
     long_description_content_type="text/markdown",
     url="http://www.up-rev.com/",
     packages=setuptools.find_packages(),
     package_data={
     'polypacket':['templates/*','examples/*']
     },
     install_requires=[
        'markdown',
        'mako',
        'prompt_toolkit',
        'pyyaml',
        'cobs',
        'pyserial',
        'update_notipy'
     ],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
