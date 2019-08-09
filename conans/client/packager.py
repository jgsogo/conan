import os
import shutil

from conans.client.file_copier import FileCopier, report_copied_files
from conans.client.output import ScopedOutput
from conans.client.tools.files import chdir
from conans.errors import (ConanException, ConanExceptionInUserConanfileMethod,
                           conanfile_exception_formatter)
from conans.model.manifest import FileTreeManifest
from conans.paths import CONANINFO
from conans.util.files import mkdir, rmdir, save
from conans.util.log import logger


def export_pkg(conanfile, package_id, src_package_folder, package_folder, hook_manager,
               conanfile_path, ref):
    output = conanfile.output
    output.info("Exporting to cache existing package from user folder")

    with packager(conanfile, package_folder, package_id, conanfile_path, ref, hook_manager) as pkger:
        copier = FileCopier([src_package_folder], package_folder)
        copier("*", symlinks=True)

    return pkger.manifest.summary_hash


def create_package(conanfile, package_id, source_folder, build_folder, package_folder,
                   install_folder, hook_manager, conanfile_path, ref, local=False,
                   copy_info=False):
    """ copies built artifacts, libs, headers, data, etc. from build_folder to
        package folder
    """
    output = conanfile.output
    output.info("Generating the package")

    conanfile.source_folder = source_folder
    conanfile.install_folder = install_folder
    conanfile.build_folder = build_folder

    with packager(conanfile, package_folder, package_id, conanfile_path, ref,
                  hook_manager, copy_info) as pkger:
        output.highlight("Calling package()")
        pkger.package_output = ScopedOutput("%s package()" % output.scope, output)

        folders = [source_folder, build_folder] if source_folder != build_folder else [build_folder]
        conanfile.copy = FileCopier(folders, package_folder)
        try:
            with conanfile_exception_formatter(str(conanfile), "package"):
                with chdir(build_folder):
                    conanfile.package()
        except Exception as e:
            if not local:
                os.chdir(build_folder)
                try:
                    rmdir(package_folder)
                except Exception as e_rm:
                    output.error("Unable to remove package folder %s\n%s" % (package_folder, str(e_rm)))
                    output.warn("**** Please delete it manually ****")
            if isinstance(e, ConanExceptionInUserConanfileMethod):
                raise
            raise ConanException(e)

    return pkger.manifest.summary_hash


def update_package_metadata(prev, layout, package_id, rrev):
    with layout.update_metadata() as metadata:
        metadata.packages[package_id].revision = prev
        metadata.packages[package_id].recipe_revision = rrev


class packager(object):
    def __init__(self, conanfile, package_folder, package_id, conanfile_path, ref, hook_manager,
                 copy_info=False):
        self.conanfile = conanfile
        self.package_id = package_id or os.path.basename(package_folder)
        self.conanfile_path = conanfile_path
        self.ref = ref
        self.hook_manager = hook_manager
        self.copy_info = copy_info

        self.output = self.conanfile.output
        self.package_output = self.output
        self.conanfile.package_folder = package_folder
        self.manifest = None

    def __enter__(self):
        # Before copying files to the package_folder
        mkdir(self.conanfile.package_folder)
        self.output.info("Exporting to cache existing package from user folder")
        self.output.info("Package folder %s" % self.conanfile.package_folder)
        self.hook_manager.execute("pre_package", conanfile=self.conanfile,
                                  conanfile_path=self.conanfile_path, reference=self.ref,
                                  package_id=self.package_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # After all files are copied to the package folder
        self.manifest = _create_aux_files(self.conanfile.package_folder,
                                          self.conanfile, copy_info=self.copy_info)
        _report_files_from_manifest(self.package_output, self.manifest)

        self.output.success("Package '%s' created" % self.package_id)
        self.hook_manager.execute("post_package", conanfile=self.conanfile,
                                  conanfile_path=self.conanfile_path, reference=self.ref,
                                  package_id=self.package_id)
        self.output.info("Created package revision %s" % self.manifest.summary_hash)


def _create_aux_files(package_folder, conanfile, copy_info):
    """ auxiliary method that creates CONANINFO and manifest in
    the package_folder
    """
    logger.debug("PACKAGE: Creating config files to %s" % package_folder)
    if copy_info:
        try:
            shutil.copy(os.path.join(conanfile.install_folder, CONANINFO), package_folder)
        except IOError:
            raise ConanException("%s does not exist inside of your %s folder. "
                                 "Try to re-build it again to solve it."
                                 % (CONANINFO, conanfile.install_folder))
    else:
        save(os.path.join(package_folder, CONANINFO), conanfile.info.dumps())

    # Create the digest for the package
    manifest = FileTreeManifest.create(package_folder)
    manifest.save(package_folder)
    return manifest


def _report_files_from_manifest(output, manifest):
    copied_files = list(manifest.files())
    copied_files.remove(CONANINFO)

    if not copied_files:
        output.warn("No files in this package!")
        return

    report_copied_files(copied_files, output, message_suffix="Packaged")
