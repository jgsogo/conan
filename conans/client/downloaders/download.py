from conans.client.downloaders.remote_cache_downloader import RemoteCacheDownloader
from conans.client.downloaders.cached_file_downloader import CachedFileDownloader
from conans.client.downloaders.file_downloader import FileDownloader


def run_downloader(requester, output, verify, config, user_download=False, use_cache=True,
                   use_rt_cache=None, **kwargs):
    downloader = FileDownloader(requester=requester, output=output, verify=verify, config=config)

    if use_rt_cache and config.sources_backup:
        downloader = RemoteCacheDownloader(config.sources_backup, downloader,
                                           user_download=user_download)

    if use_cache and config.download_cache:
        downloader = CachedFileDownloader(config.download_cache, downloader,
                                          user_download=user_download)
    return downloader.download(**kwargs)
