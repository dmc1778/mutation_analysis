from setuptools import setup, find_packages


setup(
    name='mutC',
    version='0.0.1',
    description='Mutation analysis of C projects',
    Long_description=open('CHANGELOG.txt').read(),
    url='',
    author='Nima Shiri Harzevili',
    athor_email='nimashiri2012@gmail.com'
    keyword='Mutation testing',
    packages=find_packages(exclude=('tests*', 'testing*')),
    install_requires=['']
)
