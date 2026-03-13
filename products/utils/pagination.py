
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


class ComponentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            # if page is invalid (too high)
            self.page = None
            return []

    def get_paginated_response(self, data):
        if self.page is None:
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            })

        return super().get_paginated_response(data)