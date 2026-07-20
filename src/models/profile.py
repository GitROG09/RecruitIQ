class Profile:
    """
    Stores the basic profile information of a candidate.
    """

    def __init__(
        self,
        anonymized_name: str,
        headline: str,
        summary: str,
        location: str,
        country: str,
        years_of_experience: float,
        current_title: str,
        current_company: str,
        current_company_size: str,
        current_industry: str,
    ):
        self.anonymized_name = anonymized_name
        self.headline = headline
        self.summary = summary
        self.location = location
        self.country = country
        self.years_of_experience = years_of_experience
        self.current_title = current_title
        self.current_company = current_company
        self.current_company_size = current_company_size
        self.current_industry = current_industry