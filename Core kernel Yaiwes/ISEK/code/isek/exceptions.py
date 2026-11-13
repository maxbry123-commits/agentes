class NodeUnavailableError(Exception):
    """
    Custom exception raised when a required node in a distributed system is unavailable.

    This exception can be used to signal issues like network failures,
    a node not being registered, or a node not responding within an expected timeframe.

    :ivar node_name: The name or identifier of the node that was found to be unavailable.
    :vartype node_name: str
    :ivar message: The complete error message, including the node name and specific reason.
    :vartype message: str
    """

    def __init__(self, node_name: str, message: str = "Node is unavailable"):
        """
        Initializes the NodeUnavailableError.

        :param node_name: The name or identifier of the unavailable node.
        :type node_name: str
        :param message: An optional specific message detailing why the node is unavailable.
                        Defaults to "Node is unavailable". This message will be appended
                        to the standard prefix "Node '<node_name>' is unavailable: ".
        :type message: str
        """
        self.node_name: str = node_name
        # Construct the full message including the node name
        self.message: str = f"Node '{node_name}' is unavailable: {message}"
        super().__init__(self.message)

    def __str__(self) -> str:
        """
        Returns the string representation of the exception.

        :return: The detailed error message.
        :rtype: str
        """
        return self.message
