


class ServerClient(object):
    
    def option_sync(self, ctxt, **kwargs):
        '''Get options from server.'''
        raise NotImplementedError
    
    def option_modify(self, ctxt, **kwargs):
        raise NotImplementedError
    
    def option_remove(self, ctxt, **kwargs):
        raise NotImplementedError


class RemoteOperate(object):
    '''
    This endpoint is used for server's remote operation, e.g.
    stop the client, restart the client and so on.
    '''
    
    def pause(self, ctxt, **kwargs):
        raise NotImplementedError
    
    def restart(self, ctxt, **kwargs):
        raise NotImplementedError
    
