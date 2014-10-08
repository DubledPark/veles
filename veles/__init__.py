# -*- coding: utf-8 -*-
'''
.. container:: flexbox

   .. image:: _static/veles_big.png
      :class: left

   .. container::

      %s
'''


from email.utils import parsedate_tz, mktime_tz, formatdate
from os import path
from sys import version_info, modules
from types import ModuleType
from warnings import warn

__root__ = path.dirname(path.dirname(__file__))

from veles.logger import Logger
from veles.units import Unit, IUnit
from veles.workflow import Workflow
from veles.opencl_units import OpenCLUnit, OpenCLWorkflow


__project__ = "Veles Machine Learning Platform"
__version__ = "0.4.3"
__license__ = "Samsung Proprietary License"
__copyright__ = "© 2013 Samsung Electronics Co., Ltd."
__authors__ = ["Gennady Kuznetsov", "Vadim Markovtsev", "Alexey Kazantsev",
               "Lyubov Podoynitsina", "Denis Seresov", "Dmitry Senin",
               "Alexey Golovizin", "Egor Bulychev", "Ernesto Sanches"]

try:
    __git__ = "$Commit$"
    __date__ = mktime_tz(parsedate_tz("$Date$"))
except Exception as ex:
    warn("Cannot expand variables generated by Git, setting them to None")
    __git__ = None
    __date__ = None

__logo__ = \
    r" _   _ _____ _     _____ _____  " "\n" \
    r"| | | |  ___| |   |  ___/  ___| " + \
    (" Version %s" % __version__) + \
    (" %s\n" % formatdate(__date__, True)) + \
    r"| | | | |__ | |   | |__ \ `--.  " + \
    (" Copyright %s\n" % __copyright__) + \
    r"| | | |  __|| |   |  __| `--. \ " \
    " All rights reserved. Any unauthorized use of\n" \
    r"\ \_/ / |___| |___| |___/\__/ / " \
    " this software is strictly prohibited and is\n" \
    r" \___/\____/\_____|____/\____/  " \
    " a subject of your country's laws.\n"

if "sphinx" in modules:
    __doc__ %= "| %s\n      | Version %s %s\n      | %s\n\n      Authors:" \
        "\n\n      * %s" % (__project__, __version__,
                            formatdate(__date__, True), __copyright__,
                            "\n      * ".join(__authors__))
else:
    __doc__ = __logo__.replace(" ", "_", 2)  # nopep8

if version_info.major == 3 and version_info.minor == 4 and \
   version_info.micro < 1:
    warn("Python 3.4.0 has a bug which is critical to Veles OpenCL subsystem ("
         "see issue #21435). It is recommended to upgrade to 3.4.1.")


def __html__():
    """
    Opens VELES html documentation in the default web browser and builds it,
    if it does not exist.
    """
    import os
    from veles.portable import show_file

    root = os.path.dirname(__file__)
    page = os.path.join(root, "../docs/build/html/index.html")
    if not os.path.exists(page):
        from runpy import run_path
        print("Building the documentation...")
        run_path(os.path.join(root, "../docs/generate_docs.py"))
    if os.path.exists(page):
        show_file(page)


class VelesModule(ModuleType):
    """Redefined module class with added properties which are lazily evaluated.
    """
    def __init__(self, *args, **kwargs):
        super(VelesModule, self).__init__(__name__, *args, **kwargs)
        self.__dict__.update(modules[__name__].__dict__)
        self.__units_cache__ = None

    @property
    def __units__(self):
        """
        Returns the array with all Unit classes found in the package file tree.
        """
        if self.__units_cache__ is not None:
            return self.__units_cache__

        import os
        import sys

        # Temporarily disable standard output since some modules produce spam
        # during import
        stdout = sys.stdout
        with open(os.devnull, 'w') as null:
            sys.stdout = null
        for root, _, files in os.walk(os.path.dirname(__file__)):
            if root.find('tests') >= 0:
                continue
            for file in files:
                modname, ext = os.path.splitext(file)
                if ext == '.py':
                    try:
                        sys.path.insert(0, root)
                        __import__(modname)
                        del sys.path[0]
                    except:
                        pass
        sys.stdout = stdout
        from veles.units import UnitRegistry
        self.__units_cache__ = UnitRegistry.units
        return self.__units_cache__

    @property
    def __loc__(self):
        """Calculation of lines of code relies on "cloc" utility.
        """
        from subprocess import Popen, PIPE

        result = {}

        def calc(cond):
            cmd = ("cd %s && echo $(find %s -exec cloc --quiet --csv {} \; | "
                   "sed -n '1p;0~3p' | tail -n +2 | cut -d ',' -f 5 | "
                   "tr '\n' '+' | head -c -1) | bc") % (self.__root__, cond)
            discovery = Popen(cmd, shell=True, stdout=PIPE)
            num, _ = discovery.communicate()
            return int(num)

        result["core"] = \
            calc("-name '*.py' -not -name 'cpplint*' -not -path './deploy/*' "
                 "-not -path './web/*' -not -path './veles/external/*' "
                 "-not -name create-emitter-tests.py -not -path "
                 "'./veles/tests/*' -not -path './veles/znicz/tests/*'")
        result["core"] += calc("veles/external/txzmq  -name '*.py'")
        result["tests"] = calc("'./veles/tests' './veles/znicz/tests' "
                               "-name '*.py'")
        result["opencl"] = calc("-name '*.cl' -not -path './web/*'")
        result["java"] = calc("'./mastodon/lib/src/main' -name '*.java'")
        result["tests"] += calc("'./mastodon/lib/src/test' -name '*.java'")

        result["all"] = sum(result.values())
        return result


if not isinstance(modules[__name__], VelesModule):
    modules[__name__] = VelesModule()

if __name__ == "__main__":
    __html__()
