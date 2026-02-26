
from rest_framework.pagination import PageNumberPagination

class ComponentPagination(PageNumberPagination):
    page_size = 10          # items per page
    page_size_query_param = "page_size"
    max_page_size = 50