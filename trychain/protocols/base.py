"""
TryChain — Base proxy
Common interface for every protocol handler.
"""


class BaseProxy:
    """
    Base class for proxy protocols.

    A protocol handler is given an already-connected socket
    (reader/writer) to the proxy server, and its job is to
    negotiate a tunnel from that proxy to the next hop.
    """

    def __init__(self, host: str, port: int,
                 username: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.username = username or None
        self.password = password or None

    async def connect_to(self, reader, writer,
                         target_host: str, target_port: int):
        """
        Tell the proxy (already connected via reader/writer)
        to open a tunnel to target_host:target_port.

        Must be overridden by subclasses.
        """
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.host}:{self.port}>"
