class JobDescription:
    """
    Structured representation of a Job Description.
    """

    def __init__(
        self,
        role: str = "",
        experience_min: float = 0,
        experience_max: float = 100,
        required_skills=None,
        preferred_skills=None,
        responsibilities=None,
        behaviour_traits=None,
    ):

        self.role = role

        self.experience_min = experience_min

        self.experience_max = experience_max

        self.required_skills = required_skills or []

        self.preferred_skills = preferred_skills or []

        self.responsibilities = responsibilities or []

        self.behaviour_traits = behaviour_traits or []

    def __repr__(self):

        return (
            f"JobDescription(role={self.role}, "
            f"experience={self.experience_min}-{self.experience_max}, "
            f"required_skills={len(self.required_skills)})"
        )