from collector import rpc
from oslo.config import cfg
import yaml

CONF = cfg.CONF


class ServerClient(object):

    def __init__(self):
        self.driver_names = []
        try:
            with open(CONF.get('option_file'), 'r') as co:
                self.local_options = yaml.safe_load(co)['configurations']
                for configuration in self.local_options:
                    self.driver_names.append(configuration['name'])
        except:
            self.local_options = {}

    def option_sync(self, ctxt, **kwargs):
        """
        Get options from server.
        """
        hostname = {'hostname': CONF.get('host_ID')}
        options = rpc.call(topic=CONF.get('server_topic'),
                            ctxt={}, method='get_option', **hostname)
        option_driver_names = []
        for option in options:
            driver_name = option['name']
            option_driver_names.append(driver_name)
            if self.driver_names.count(driver_name) == 0:
                # add
                self.local_options.append(option)
                self.driver_names.append(driver_name)
                self._add(option)
            else:
                # modify
                for loption in self.local_options:
                    if loption['name'] == driver_name:
                        self.local_options.remove(loption)
                        self.local_options.append(option)
                        self._modify(option)
                        break
        for driver_name in self.driver_names:
            # remove
            if option_driver_names.count(driver_name) == 0:
                for loption in self.local_options:
                    if loption['name'] == driver_name:
                        self.local_options.remove(loption)
                        self._remove(driver_name)
                        break
        try:
            with open(CONF.get('option_file'), 'w') as co:
                yaml.safe_dump({'configurations': self.local_options}, co)
        except:
            raise

    def _modify(self, option):
        """
        If the driver configuratios changed, it should be
        reload to keep it always be synchronized with server.
        param option: The option which contains all the args about
            one driver.
            type: dict
        """
        pass

    def _remove(self, driver_name):
        """
        param driver: driver name.
            type: string
        """
        raise NotImplementedError

    def _add(self, option):
        """
        param option: The option which contains all the args about
            one driver.
            type: dict
        """

        pass


class RemoteOperate(object):
    '''
    This endpoint is used for server's remote operation, e.g.
    stop the client, restart the client and so on.
    '''

    def pause(self, ctxt, **kwargs):
        from collector import client_main
        client_main.driverManager.pause()

    def restart(self, ctxt, **kwargs):
        raise NotImplementedError


