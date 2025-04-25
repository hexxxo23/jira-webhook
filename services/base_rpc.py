import logging
import xmlrpc.client

_logger = logging.getLogger(__name__)

class BaseRpc(object):
    rpc_model = None
    rpc_common = None
    uid = 1
    password = "not_defined"
    db = "odoo"

    def set_config(self, host, database, port):
        try:
            self.db = database
            url = f"http://{host}:{port}"
            if int(port) == 443:
                url = f"https://{host}"
            self.rpc_common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            self.rpc_model  = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        except Exception as e:
            _logger.error("Error in set_config: %s", e)

    def set_auth(self, login, password):
        self.password = password
        self.uid = self.rpc_common.authenticate(self.db, login, password, {})
        _logger.info("Set Auth With UID: %s", self.uid)

    def model(self, model, method, filters=None, **kwargs):
        if filters is None:
            filters = []
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, method, [filters])

    def create(self, model, values=None):
        if values is None:
            raise AttributeError('No values for create')
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'create', [values])

    def search(self, model, filters):
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'search', filters)

    def write(self, model, id, values=None):
        if values is None:
            raise AttributeError('No values for write')
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'write', [[id], values])

    def unlink(self, model, document_ids, context=None):
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'unlink', document_ids)

    def search_read(self, model, filters, fields=None, **kwargs):
        if fields is None:
            fields = ['name', 'id']
        params = {"fields": fields}
        params.update(kwargs)
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'search_read', [filters], params)

    def get_or_create(self, model, filters=None):
        if filters is None:
            filters = []
        query = self.search_read(model, filters, ['id'])
        if len(query) == 1:
            _logger.info("FOUND %s : %s", model, query[0])
            return query[0]['id'], False
        if not query:
            values = {f[0]: f[2] for f in filters}
            _logger.info("CREATE %s with %s", model, values)
            pk = self.create(model, values=values)
            return pk, True
        raise KeyError(f"query return {len(query)} objects")

    def update_or_create(self, model, filters=None, values=None):
        if filters is None:
            filters = []
        if values is None:
            raise AttributeError('No values for update_or_create')
        query = self.search_read(model, filters, ['id'])
        if len(query) == 1:
            _logger.info("FOUND %s : %s", model, query[0])
            result = self.write(model, query[0]['id'], values)
            return result, False
        if not query:
            all_vals = {f[0]: f[2] for f in filters}
            all_vals.update(values)
            _logger.info("CREATE %s with %s", model, all_vals)
            pk = self.create(model, values=all_vals)
            return pk, True
        raise KeyError(f"query return {len(query)} objects")
