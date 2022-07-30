# flake8: noqa

# Import all APIs into this package.
# If you have many APIs here with many many models used in each API this may
# raise a `RecursionError`.
# In order to avoid this, import only the API that you directly need like:
#
#   from httpmq.core.api.dataplane_api import DataplaneApi
#
# or import this package, but before doing it, use:
#
#   import sys
#   sys.setrecursionlimit(n)

# Import APIs into API package:
from httpmq.core.api.dataplane_api import DataplaneApi
from httpmq.core.api.management_api import ManagementApi
