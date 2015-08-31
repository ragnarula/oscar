__author__ = 'raghavnarula'


class DeviceState():

    def __init__(self):
        pass

    def start(self, device):
        raise NotImplementedError("abstract interface")

    def stop(self, device):
        raise NotImplementedError("abstract interface")

    def enter(self, device):
        raise NotImplementedError("abstract interface")

    def exit(self, device):
        raise NotImplementedError("abstract interface")

    def send(self, device, msg):
        raise NotImplementedError("abstract interface")


class ReadyState(DeviceState):

    def __init__(self):
        DeviceState.__init__(self)

    def start(self, device):
        raise NotImplementedError("abstract interface")

    def stop(self, device):
        raise NotImplementedError("abstract interface")

    def enter(self, device):
        raise NotImplementedError("abstract interface")

    def exit(self, device):
        raise NotImplementedError("abstract interface")

    def send(self, device, msg):
        raise NotImplementedError("abstract interface")


class ConnectingState(DeviceState):

    def __init__(self):
        DeviceState.__init__(self)

    def start(self, device):
        raise NotImplementedError("abstract interface")

    def stop(self, device):
        raise NotImplementedError("abstract interface")

    def enter(self, device):
        raise NotImplementedError("abstract interface")

    def exit(self, device):
        raise NotImplementedError("abstract interface")

    def send(self, device, msg):
        raise NotImplementedError("abstract interface")


class ConnectedState(DeviceState):

    def __init__(self):
        DeviceState.__init__(self)

    def start(self, device):
        raise NotImplementedError("abstract interface")

    def stop(self, device):
        raise NotImplementedError("abstract interface")

    def enter(self, device):
        raise NotImplementedError("abstract interface")

    def exit(self, device):
        raise NotImplementedError("abstract interface")

    def send(self, device, msg):
        raise NotImplementedError("abstract interface")


class ErrorState(DeviceState):

    def __init__(self):
        DeviceState.__init__(self)

    def start(self, device):
        raise NotImplementedError("abstract interface")

    def stop(self, device):
        raise NotImplementedError("abstract interface")

    def enter(self, device):
        raise NotImplementedError("abstract interface")

    def exit(self, device):
        raise NotImplementedError("abstract interface")

    def send(self, device, msg):
        raise NotImplementedError("abstract interface")