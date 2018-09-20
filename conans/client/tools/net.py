import sys

import os
from conans.client.output import ConanOutput
from conans.client.tools.files import unzip, check_md5, check_sha1, check_sha256
from conans.errors import ConanException
from conans.client.rest.downloader import download as download_func

_global_requester = None


def get(url, md5='', sha1='', sha256='', destination=".", filename="", keep_permissions=False,
        pattern=None):
    """ high level downloader + unzipper + (optional hash checker) + delete temporary zip
    """
    if not filename and ("?" in url or "=" in url):
        raise ConanException("Cannot deduce file name form url. Use 'filename' parameter.")

    filename = filename or os.path.basename(url)
    download(url, filename)

    if md5:
        check_md5(filename, md5)
    if sha1:
        check_sha1(filename, sha1)
    if sha256:
        check_sha256(filename, sha256)

    unzip(filename, destination=destination, keep_permissions=keep_permissions, pattern=pattern)
    os.unlink(filename)


def ftp_download(ip, filename, login='', password=''):
    import ftplib
    try:
        ftp = ftplib.FTP(ip, login, password)
        ftp.login()
        filepath, filename = os.path.split(filename)
        if filepath:
            ftp.cwd(filepath)
        with open(filename, 'wb') as f:
            ftp.retrbinary('RETR ' + filename, f.write)
    except Exception as e:
        raise ConanException("Error in FTP download from %s\n%s" % (ip, str(e)))
    finally:
        try:
            ftp.quit()
        except:
            pass


def download(url, filename, verify=True, out=None, retry=2, retry_wait=5, overwrite=False,
             auth=None, headers=None):
    # TODO: Move code out of this function
    out = out or ConanOutput(sys.stdout, True)
    download_func(requester=_global_requester, output=out, verify_ssl=verify,
                  url=url, file_path=filename, retry=retry, retry_wait=retry_wait,
                  overwrite=overwrite, auth=auth, headers=headers)
    out.writeln("")
