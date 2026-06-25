class Skill:
    """
    Represents one skill.
    """

    def __init__(
        self,
        name,
        proficiency,
        endorsements,
        duration_months,
    ):
        self.name = name
        self.proficiency = proficiency
        self.endorsements = endorsements
        self.duration_months = duration_months