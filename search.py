import re
from datetime import datetime
from django.utils import timezone

from django.db.models import Q


def normalize_query(query_string, normspace=re.compile(r'\s{2,}').sub,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall):
    """Splits the query string in invidual keywords.

    Gets rid of unecessary spaces and grouping quoted words together.

    Example:

    >>> normalize_query('  some random  words "with   quotes  " and   spaces')
    ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

    """
    return [normspace(' ',
                      (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields, exact=False):
    """Returns a query, that is a combination of Q objects.

    That combination aims to search keywords within a model
    by testing the given search fields.

    """
    query = None  # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None  # Query to search for a given term in each field
        for field_name in search_fields:
            if exact:
                q = Q(**{"%s" % field_name: term})
            else:
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


def get_date_query(query_date_from_string, query_date_to_string,
                   search_fields):
    """Returns a query, that is a range of Q objects.

    That combination aims to search keywords within a model
    by testing the given search fields.

    """
    query = None  # Query to search for every search term
    if query_date_from_string:
        try:
            date_from = datetime.strptime(str(query_date_from_string),
                                          '%m/%d/%Y')
            term_from = timezone.make_aware(date_from,
                                            timezone.get_current_timezone())
        except:
            return None
    else:
        term_from = None
    if query_date_to_string:
        try:
            date_to = datetime.strptime(str(query_date_to_string), '%m/%d/%Y')
            term_to = timezone.make_aware(date_to,
                                          timezone.get_current_timezone())
        except:
            return None
    else:
        term_to = None

    or_query = None  # Query to search for a given term in each field
    for field_name in search_fields:
        if term_from and term_to:
            q = Q(**{"%s__range" % field_name: [term_from, term_to]})
        elif term_from:
            q = Q(**{"%s__gte" % field_name: term_from})
        elif term_to:
            q = Q(**{"%s__lte" % field_name: term_to})
        else:
            q = None

        if or_query is None:
            or_query = q
        else:
            or_query = or_query | q
    query = or_query

    return query
