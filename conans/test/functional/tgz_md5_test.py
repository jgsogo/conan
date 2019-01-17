import os
import platform
import shutil
import time
import unittest

from conans.client.remote_manager import compress_files, uncompress_file
from conans.model.manifest import gather_files
from conans.paths import PACKAGE_TGZ_NAME
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import TestBufferConanOutput
from conans.util.files import save, md5sum, save_files


class TgzMd5Test(unittest.TestCase):
    """The md5 of a tgz should be the same if the files inside are the same"""

    def test_md5_compress(self):
        folder = temp_folder()
        save(os.path.join(folder, "one_file.txt"), b"The contents")
        save(os.path.join(folder, "Two_file.txt"), b"Two contents")

        files = {
            "one_file.txt": os.path.join(folder, "one_file.txt"),
            "Two_file.txt": os.path.join(folder, "Two_file.txt"),
        }

        compress_files(files, {}, PACKAGE_TGZ_NAME, dest_dir=folder)
        file_path = os.path.join(folder, PACKAGE_TGZ_NAME)

        md5_a = md5sum(file_path)
        self.assertEqual(md5_a, "df220cfbc0652e8992a89a77666c03b5")

        time.sleep(1)  # Timestamps change

        folder = temp_folder()
        compress_files(files, {}, PACKAGE_TGZ_NAME, dest_dir=folder)
        file_path = os.path.join(folder, PACKAGE_TGZ_NAME)

        md5_b = md5sum(file_path)

        self.assertEquals(md5_a, md5_b)


class CompressSymlinksTest(unittest.TestCase):

    def run(self, *args, **kwargs):
        self.tmp_folder = temp_folder()
        try:
            super(CompressSymlinksTest, self).run(*args, **kwargs)
        finally:
            shutil.rmtree(self.tmp_folder)

    @unittest.skipIf(platform.system() == "Windows", "Command line 'tar' not available in Windows")
    def test_symlinks_file(self):
        file1 = os.path.join(self.tmp_folder, "src", "one_file.txt")
        symlink = os.path.join(self.tmp_folder, 'src', "symlink.txt")

        save(file1, "Conan")
        os.symlink(file1, symlink)

        tar_gz_file = os.path.join(self.tmp_folder, PACKAGE_TGZ_NAME)
        compress_files({'one_file.txt': file1, 'symlink.txt': symlink}, {},
                       name=tar_gz_file, dest_dir=self.tmp_folder)

        # Uncompress using cli tools
        os.makedirs(os.path.join(self.tmp_folder, 'dest'))
        os.system('tar xvzf "{}" -C "{}"'.format(tar_gz_file, os.path.join(self.tmp_folder, 'dest')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_folder, 'dest', 'one_file.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_folder, 'dest', 'symlink.txt')))
        self.assertTrue(os.path.islink(os.path.join(self.tmp_folder, 'dest', 'symlink.txt')))

        # Uncompress using Conan machinery
        uncompress_file(tar_gz_file, os.path.join(self.tmp_folder, 'dest2'),
                        output=TestBufferConanOutput())
        self.assertTrue(os.path.exists(os.path.join(self.tmp_folder, 'dest2', 'one_file.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_folder, 'dest2', 'symlink.txt')))
        self.assertTrue(os.path.islink(os.path.join(self.tmp_folder, 'dest2', 'symlink.txt')))

    @unittest.skipIf(platform.system() == "Windows", "Command line 'tar' not available in Windows")
    def test_symlinks_directory(self):
        # Prepare the folder with all the files
        src_folder = os.path.join(self.tmp_folder, 'src')
        save_files(src_folder, {'file.txt': "Conan",
                                os.path.join('dir', 'file_dir.txt'): "Conan", })
        os.symlink(os.path.join(src_folder, 'dir'), os.path.join(src_folder, 'symlink'))

        # Create the zipped file
        srcs, symlinks = gather_files(src_folder)
        tar_gz_file = os.path.join(self.tmp_folder, PACKAGE_TGZ_NAME)
        compress_files(files=srcs, symlinks=symlinks, name=tar_gz_file, dest_dir=self.tmp_folder)

        # These will be the tests
        def perform_tests(folder):
            self.assertTrue(os.path.exists(os.path.join(folder, 'file.txt')))
            self.assertTrue(os.path.exists(os.path.join(folder, 'dir', 'file_dir.txt')))
            self.assertTrue(os.path.islink(os.path.join(folder, 'symlink')))
            self.assertTrue(os.path.exists(os.path.join(folder, 'symlink', 'file_dir.txt')))

        # Uncompress using CLI tools
        dest_dir = os.path.join(self.tmp_folder, 'dest_cli')
        os.makedirs(dest_dir)
        os.system('tar xvzf "{}" -C "{}"'.format(tar_gz_file, dest_dir))

        perform_tests(dest_dir)

        # Uncompress using Conan machinery
        dest_dir = os.path.join(self.tmp_folder, 'dest_conan')
        uncompress_file(tar_gz_file, dest_dir, output=TestBufferConanOutput())

        perform_tests(dest_dir)

