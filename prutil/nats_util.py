class NatsCallbacks:
    def __init__(self, logger):
        self.logger = logger
        self.connected = False
        self.shutting_down = False

    async def on_nats_error_callback(self, error):
        if self.connected:
            self.logger.error("NATS connection error: %s", error)

    async def disconnected_callback(self):
        self.logger.error("abrupt NATS disconnection")

    async def reconnected_callback(self):
        self.logger.info("Reconnected to NATS")

    async def closed_callback(self):
        self.logger.info("Connection to NATS closed")
        
    async def on_disconnected(self):
        if not self.shutting_down:
            await self.disconnected_callback()