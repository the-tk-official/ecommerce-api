import re

import graphene
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q


def is_authenticated(function):
    """Decorator for check authentication the user from the request"""
    def wrapper(cls, info, **kwargs):
        if not info.context.user:
            raise Exception("U aren't authorized to perform operation")

        return function(cls, info, **kwargs)

    return wrapper


def paginate(model_type):
    """Create pagination query"""

    structure = {
        'page': graphene.Int(),
        'pages': graphene.Int(),
        'total_data': graphene.Int(),
        'has_next': graphene.Boolean(),
        'has_previous': graphene.Boolean(),
        'result': graphene.List(model_type)
    }

    return type(f'{model_type}Paginated', (graphene.ObjectType, ), structure)


def resolve_paginated(query_data, info, page_info):
    """Paginated data"""
    def get_paginated_data(qs, paginated_type, page):
        page_size = settings.GRAPHENE.get('PAGE_SIZE', 10)

        p = Paginator(qs, page_size)

        try:
            page_obj = p.page(page)
        except PageNotAnInteger:
            page_obj = p.page(1)
        except EmptyPage:
            page_obj = p.page(p.num_pages)

        result = paginated_type.graphene_type(
            page=page_obj.number,
            pages=p.num_pages,
            total_data=qs.count(),
            has_next=page_obj.has_next(),
            has_previous=page_obj.has_previous(),
            result=page_obj.object_list
        )

        return result

    return get_paginated_data(query_data, info.return_type, page_info)


def normalize_query(query_string, findterms=re.compile(r'"([^"]+)"|(\S+)').findall, normspace=re.compile(r'\s{2,}').sub):
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields):
    query = None  # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None  # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query
