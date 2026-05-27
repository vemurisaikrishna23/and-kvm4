"""
drf-spectacular hooks:
  - Postprocessing hook that auto-tags endpoints based on URL path prefix.
  - OpenAPI auth extension so the Swagger "Authorize" button works with our JWT.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ExistingUsersJWTScheme(OpenApiAuthenticationExtension):
    target_class = 'IoT_Panel.auth.ExistingUsersJWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }

TAG_MAP = [
    ('/api/auth/',                                           'Auth'),
    ('/api/customers/',                                      'Customers'),
    ('/api/dispenser-unit/',                                 'Dispenser Units'),
    ('/api/gun-unit/',                                       'Gun Units'),
    ('/api/node-unit/',                                      'Node Units'),
    ('/api/dispenser-gun-mapping-to-customer/',              'Dispenser-Gun Mapping (Customer)'),
    ('/api/dispenser-gun-mapping-to-vehicle/',               'Dispenser-Gun Mapping (Vehicle)'),
    ('/api/node-dispenser-customer-mapping/',                'Node-Dispenser-Customer Mapping'),
    ('/api/delivery-location-mapping-dispenser-unit/',       'Delivery Location Mapping'),
    ('/api/delivery-location-mapping/',                      'Delivery Location Mapping'),
    ('/api/request-fuel-dispensing/',                        'Fuel Dispensing Requests'),
    ('/api/vin-vehicle/',                                    'VIN Vehicles'),
    ('/api/dashboard/',                                      'Dashboard'),
    ('/api/order-request-fuel-dispensing/',                  'Order Fuel Dispensing'),
    ('/api/fuel-readings/',                                  'Fuel Readings'),
]


def auto_tag_by_url(result, generator, request, public):
    """Postprocessing hook: overwrite tags on every path based on URL prefix."""
    paths = result.get('paths', {})
    for path, methods in paths.items():
        tag = None
        for prefix, tag_name in TAG_MAP:
            if path.startswith(prefix):
                tag = tag_name
                break
        if tag:
            for method_detail in methods.values():
                if isinstance(method_detail, dict):
                    method_detail['tags'] = [tag]
    return result
