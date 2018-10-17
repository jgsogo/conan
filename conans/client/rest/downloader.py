
import os
import io
import time
from conans.errors import ConanException, NotFoundException, AuthenticationException
from conans.util.progress_bar import progress_bar, tqdm_file_defaults
from conans.util.files import exception_message_safe


def download(requester, output, verify_ssl,
             url, file_path=None, auth=None, retry=3, retry_wait=0, overwrite=False, headers=None):
    if file_path:
        file_path = os.path.abspath(file_path)
        if os.path.exists(file_path):
            if overwrite:
                output.warn("file '{}' already exists, overwritting".format(file_path))
            else:
                raise ConanException("Error, the file to download already exists: '{}'".format(
                    file_path))
        try:
            os.makedirs(os.path.dirname(file_path))  # TODO: (py3), exist_ok=True)
        except OSError:
            pass

    pb_description = "Downloading {}".format(os.path.basename(url))
    for n_retry in range(retry):
        buffer = open(file_path, 'wb') if file_path else io.BytesIO()
        try:
            r = requester.get(url, stream=True, verify=verify_ssl, auth=auth, headers=headers)
            if not r.ok:
                if r.status_code == 404:
                    raise NotFoundException("Not found: %s" % url)
                elif r.status_code == 401:
                    raise AuthenticationException()
                raise ConanException("Error %d downloading file %s" % (r.status_code, url))

            try:
                total_length = r.headers.get('content-length') or len(r.content)
                # encoding = r.headers.get('content-encoding')
                # gzip = (encoding == "gzip")

                # chunked can be a problem: https://www.greenbytes.de/tech/webdav/rfc2616.html#rfc.section.4.4
                # It will not send content-length or should be ignored

                # TODO: May disable progress bar if file is not big enough
                with progress_bar(total=int(total_length), output=output, desc=pb_description,
                                  **tqdm_file_defaults) as pb:
                    for data in r.iter_content(chunk_size=1000):
                        pb.update(len(data))
                        buffer.write(data)

                return None if file_path else bytes(buffer.getbuffer())
            finally:
                r.close()
        except NotFoundException:
            raise
        except (ConanException, ConnectionError, Exception) as e:
            msg = exception_message_safe(e)
            output.error(msg)
            if n_retry < (retry - 1):
                output.info("Waiting %d seconds to retry..." % retry_wait)
                time.sleep(retry_wait)
            else:
                raise ConanException("Error downloading file %s: '%s'" % (url, msg))
        finally:
            buffer.close()
