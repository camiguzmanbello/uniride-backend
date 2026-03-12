from django.utils.dateparse import parse_date

def apply_date_status_filters(queryset, request, date_field: str):
    params = request.GET

    # -------- STATUS --------
    statuses = params.getlist("status[]")
    if statuses:
        try:
            statuses = [int(s) for s in statuses]
            queryset = queryset.filter(status_id__id__in=statuses)
        except ValueError:
            pass

    # -------- DATE FROM --------
    date_from = params.get("dateFrom")
    if date_from:
        date_from = parse_date(date_from)
        if date_from:
            queryset = queryset.filter(**{f"{date_field}__date__gte": date_from})

    # -------- DATE TO --------
    date_to = params.get("dateTo")
    if date_to:
        date_to = parse_date(date_to)
        if date_to:
            queryset = queryset.filter(**{f"{date_field}__date__lte": date_to})

    return queryset
def apply_audit_filters(queryset, request, date_field="timestamp"):
    params = request.GET

    # -------- ACTION --------
    action = params.get("action")
    if action and action != "all":
        queryset = queryset.filter(action=action)

    # -------- DATE FROM --------
    date_from = params.get("dateFrom")
    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            queryset = queryset.filter(**{f"{date_field}__date__gte": parsed})

    # -------- DATE TO --------
    date_to = params.get("dateTo")
    if date_to:
        parsed = parse_date(date_to)
        if parsed:
            queryset = queryset.filter(**{f"{date_field}__date__lte": parsed})

    return queryset