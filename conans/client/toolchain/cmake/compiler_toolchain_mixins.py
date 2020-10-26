from conans.client.tools import cpu_count


class VisualStudioMixin(object):
    blocks = ['blocks/visualstudio.cmake', ]

    @property
    def cpu_count(self):
        return cpu_count(output=self._conanfile.output)

    @property
    def generator_platform(self):
        compiler = self._conanfilesettings.get_safe("compiler")
        compiler_base = self._conanfilesettings.get_safe("compiler.base")
        arch = self._conanfilesettings.get_safe("arch")

        if self._conanfile.settings.get_safe("os") == "WindowsCE":
            return self._conanfile.settings.get_safe("os.platform")


        if (compiler == "Visual Studio" or compiler_base == "Visual Studio") and \
            generator and "Visual" in generator:
            return {"x86": "Win32",
                    "x86_64": "x64",
                    "armv7": "ARM",
                    "armv8": "ARM64"}.get(arch)
        return None


class IntelCompilerMixin(object):

    @property
    def architecture(self):
        arch = self._conanfile.settings.get_safe("arch")
        compiler_base = self._conanfile.settings.get_safe("compiler.base")
        if str(arch) == "x86":
            return "/Qm32" if str(compiler_base) == "Visual Studio" else "-m32"
        elif str(arch) == "x86_64":
            return "/Qm64" if str(compiler_base) == "Visual Studio" else "-m64"
        return ""


class UnixCompilerMixin(object):
    @property
    def architecture(self):
        arch = self._conanfile.settings.get_safe("arch")
        the_os = self._conanfile.settings.get_safe("os")
        if str(arch) in ['x86_64', 'sparcv9', 's390x']:
            return '-m64'
        elif str(arch) in ['x86', 'sparc']:
            return '-m32'
        elif str(arch) in ['s390']:
            return '-m31'
        elif str(the_os) == 'AIX':
            if str(arch) in ['ppc32']:
                return '-maix32'
            elif str(arch) in ['ppc64']:
                return '-maix64'
        return ""

    @property
    def glibcxx(self):
        return None


class AppleClangCompilerMixin(UnixCompilerMixin):
    @property
    def libcxx(self):
        libcxx = self._conanfile.settings.get_safe("compiler.libcxx")
        return "-stdlib={}".format(libcxx)


class ClangCompilerMixin(UnixCompilerMixin):
    @property
    def libcxx(self):
        libcxx = self._conanfile.settings.get_safe("compiler.libcxx")
        if libcxx == "libc++":
            return "-stdlib=libc++"
        elif libcxx == "libstdc++" or libcxx == "libstdc++11":
            return "-stdlib=libstdc++"
        return None


class SunCCCompilerMixin(UnixCompilerMixin):
    @property
    def libcxx(self):
        libcxx = self._conanfile.settings.get_safe("compiler.libcxx")
        lib = {"libCstd": "Cstd",
               "libstdcxx": "stdcxx4",
               "libstlport": "stlport4",
               "libstdc++": "stdcpp"
               }.get(libcxx)
        if lib:
            return "-library={}".format(lib)
        return None


class GccCompilerMixin(UnixCompilerMixin):
    @property
    def libcxx(self):
        return None

    @property
    def glibcxx(self):
        libcxx = self._conanfile.settings.get_safe("compiler.libcxx")
        if libcxx == "libstdc++11":
            return "1"
        elif libcxx == "libstdc++":
            return "0"
