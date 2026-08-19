from rest_framework.pagination import PageNumberPagination


class FlexiblePageNumberPagination(PageNumberPagination):
    """
    Standard page-number pagination that lets clients request a larger page
    via ?page_size=N (capped at MAX_PAGE_SIZE to prevent runaway queries).
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500
