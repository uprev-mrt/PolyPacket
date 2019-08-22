import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='polypacket',
     version='0.1',
     author="Jason Berger",
     author_email="JBerger@up-rev.com",
     description="A tool for building protocol services",
     long_description=long_description,
     scripts=['polypacket/poly-packet'],
   long_description_content_type="text/markdown",
     url="https://github.com/javatechy/dokr",
     packages=setuptools.find_packages(),
     package_data={
     'polypacket':['templates/*'],
     },
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
