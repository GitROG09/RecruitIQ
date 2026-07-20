class Career:
    """
    Represents one employment record.
    """

    def __init__(
        self,
        company,
        title,
        start_date,
        end_date,
        duration_months,
        is_current,
        industry,
        company_size,
        description,
    ):
        self.company = company
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.duration_months = duration_months
        self.is_current = is_current
        self.industry = industry
        self.company_size = company_size
        self.description = description