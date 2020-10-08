from .base_middleware import BaseMiddleware


class LogRawCommandsMiddleware(BaseMiddleware):
    @staticmethod
    def _stringify(value):
        try:
            return str(value)
        except Exception:
            return repr(value)

    def inspect(self, *args, **kwargs):
        args_str = list(map(self._stringify, args)) + \
                   ["{}='{}'".format(k, self._stringify(v)) for k, v in kwargs.items()]
        self._output.info("conan_api::inspect >> {}".format(', '.join(args_str)))
        ret = self._api_call.inspect(*args, **kwargs)
        self._output.info("conan_api::inspect << {}".format(self._stringify(ret)))
        return ret
