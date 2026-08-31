import os
from glob import glob
file_path='main.py'


os.system(str('nuitka3 --module --remove-output --no-pyi-file --clang '+file_path))



