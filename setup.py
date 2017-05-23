from setuptools import setup


def readme():
    with open('README.md', 'r') as file:
        file.read()

setup(name='dartqc',
      version='0.1',
      description='Quality control for SNP data from Diversity Array Technologies (DArT)',
      url='http://github.com/esteinig/dartQC',
      author='Eike J. Steinig',
      author_email='eikejoachim.steinig@my.jcu.edu.au',
      license='MIT',
      packages=['dartqc'],
      scripts=['bin/dartqc'],
      zip_safe=False)