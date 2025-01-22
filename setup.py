from distutils.core import setup
from Cython.Build import cythonize
import Cython

setup(name='Grizzly',
      version='0.3.1',
      description='Grizzly - Fast and simple RDF graphs',
      url='https://github.com/elsevierlabs-os/grizzly',
      author='Till Bey',
      author_email='t.bey@elsevier.com',
      packages=['grizzly'],
      ext_modules = cythonize('grizzly/cy_turtle_parser.pyx'),
      license='MIT',
      install_requires=['pandas>=0.23.0', 'numpy', 'tatsu>=4.2.6', 'uplink>=0.6.1', 'cython'],
      include_package_data=True
     )
