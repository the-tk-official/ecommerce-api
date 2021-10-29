from .permissions import resolve_paginated

class CustomAuthMiddleware(object):
    """Custom middleware for user authentication"""

    def resolve(self, next, root, info, **kwargs):
        """Updates the data about the authorized user in the request"""
        info.context.user = self.authorized_user(info)
        return next(root, info, **kwargs)

    @staticmethod
    def authorized_user(info):
        """Check user for authentication"""
        from .authentication import Authentication
        auth = Authentication(info.context)
        return auth.authenticate()


class CustomPaginationMiddleware(object):
    """Custom middleware for finding query with pagination and add page"""
    def resolve(self, next, root, info, **kwargs):
        try:
            is_paginated = info.return_type.name[-9:]
            is_paginated = is_paginated == 'Paginated'
        except Exception:
            is_paginated = False

        if is_paginated:
            page = kwargs.pop('page', 1)
            return resolve_paginated(query_data=next(root, info, **kwargs).value, info=info, page_info=page)

        return next(root, info, **kwargs)
