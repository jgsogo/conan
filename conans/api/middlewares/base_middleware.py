class BaseMiddleware:
    def __init__(self, api_call, output):
        self._api_call = api_call
        self._output = output

    def __getattr__(self, item):
        # Any call not intercepted is forwarded to the next layer
        return getattr(self._api_call, item)
