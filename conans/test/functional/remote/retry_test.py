# coding=utf-8

import os
import unittest
from collections import namedtuple, Counter

import six

from conans.client.rest.uploader_downloader import Uploader
from conans.errors import AuthenticationException, ForbiddenException
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import TestBufferConanOutput
from conans.util.files import save

response_type = namedtuple("response", "status_code content")


class _RequesterMock:
    def __init__(self, status_code, content):
        self.response = response_type(status_code, content)

    def put(self, *args, **kwargs):
        return self.response


class RetryDownloadTests(unittest.TestCase):

    def setUp(self):
        self.filename = os.path.join(temp_folder(), "anyfile")
        save(self.filename, "anything")

    def test_error_401(self):
        output = TestBufferConanOutput()
        uploader = Uploader(requester=_RequesterMock(401, "content"), output=output, verify=False)
        with six.assertRaisesRegex(self, AuthenticationException, "content"):
            uploader.upload(url="fake", abs_path=self.filename, retry=3)
        output_lines = str(output).splitlines()
        counter = Counter(output_lines)
        self.assertEqual(counter["ERROR: content"], 2)
        self.assertEqual(counter["Waiting 0 seconds to retry..."], 2)

    def test_error_403_forbidden(self):
        output = TestBufferConanOutput()
        uploader = Uploader(requester=_RequesterMock(403, "content"), output=output, verify=False)
        with six.assertRaisesRegex(self, ForbiddenException, "content"):
            auth = namedtuple("auth", "token")
            uploader.upload(url="fake", abs_path=self.filename, retry=3, auth=auth("token"))
        output_lines = str(output).splitlines()
        counter = Counter(output_lines)
        self.assertEqual(counter["ERROR: content"], 2)
        self.assertEqual(counter["Waiting 0 seconds to retry..."], 2)

    def test_error_403_authentication(self):
        output = TestBufferConanOutput()
        uploader = Uploader(requester=_RequesterMock(403, "content"), output=output, verify=False)
        with six.assertRaisesRegex(self, AuthenticationException, "content"):
            auth = namedtuple("auth", "token")
            uploader.upload(url="fake", abs_path=self.filename, retry=3, auth=auth(None))
        output_lines = str(output).splitlines()
        counter = Counter(output_lines)
        self.assertEqual(counter["ERROR: content"], 2)
        self.assertEqual(counter["Waiting 0 seconds to retry..."], 2)

    def test_error_requests(self):
        class _RequesterMock:
            def put(self, *args, **kwargs):
                raise Exception("any exception")

        output = TestBufferConanOutput()
        uploader = Uploader(requester=_RequesterMock(), output=output, verify=False)
        with six.assertRaisesRegex(self, Exception, "any exception"):
            uploader.upload(url="fake", abs_path=self.filename, retry=3)
        output_lines = str(output).splitlines()
        counter = Counter(output_lines)
        self.assertEqual(counter["ERROR: any exception"], 2)
        self.assertEqual(counter["Waiting 0 seconds to retry..."], 2)

    def test_error_500(self):
        output = TestBufferConanOutput()
        uploader = Uploader(requester=_RequesterMock(500, "content"), output=output, verify=False)
        with six.assertRaisesRegex(self, AuthenticationException, "content"):
            auth = namedtuple("auth", "token")
            uploader.upload(url="fake", abs_path=self.filename, retry=3, auth=auth(None))
        output_lines = str(output).splitlines()
        counter = Counter(output_lines)
        self.assertEqual(counter["ERROR: content"], 2)
        self.assertEqual(counter["Waiting 0 seconds to retry..."], 2)
