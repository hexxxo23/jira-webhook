import logging
from .base_rpc import BaseRpc

_logger = logging.getLogger(__name__)

def get_client():
    host = 'bangunindo_web'
    port = 8069
    database = 'Bangunindo_test'
    login = 'admin'
    password = 'odoo'
    rpc = BaseRpc()
    rpc.set_config(host, database, port)
    _logger.info("Odoo config: %s/%s:%s", host, database, port)
    rpc.set_auth(login, password)
    return rpc

def find_data(model_name, domain, fields):
    try:
        client = get_client()
        data = client.search_read(model_name, domain, fields)
        _logger.info("find_data %s → %s", model_name, data)
        return data
    except Exception as e:
        _logger.error("Error find_data %s: %s", model_name, e)
        return []

def create_data(model_name, values):
    try:
        client = get_client()
        rec_id = client.create(model_name, values=values)
        _logger.info("create_data %s → %s", model_name, rec_id)
        return rec_id
    except Exception as e:
        _logger.error("Error create_data %s: %s", model_name, e)
        raise
