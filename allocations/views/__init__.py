"""The views of the application.

The views are grouped into modules. They are all imported here, so that
other code can keep using them as views.home, views.user_list, and so on.
"""

from .session_views import dashboard as dashboard
from .session_views import home as home
from .session_views import log_in as log_in
from .session_views import log_out as log_out
from .user_management_views import (
    password as password,
)
from .user_management_views import (
    profile as profile,
)
from .user_management_views import (
    superuser_required as superuser_required,
)
from .user_management_views import (
    user_create as user_create,
)
from .user_management_views import (
    user_delete as user_delete,
)
from .user_management_views import (
    user_detail as user_detail,
)
from .user_management_views import (
    user_list as user_list,
)
from .user_management_views import (
    user_update as user_update,
)
from .cohort_views import upload_cohort