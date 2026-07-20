class JobKnowledgeBuilder:
    """
    Builds a semantic representation
    of the Job Description.
    """

    @staticmethod
    def build(job):

        sections = []

        sections.append(
            f"Role: {job.role}"
        )

        sections.append(
            f"""
Required Experience:
{job.experience_min}-{job.experience_max} years
"""
        )

        sections.append(

            "Required Skills:\n"

            +

            ", ".join(job.required_skills)
        )

        sections.append(

            "Preferred Skills:\n"

            +

            ", ".join(job.preferred_skills)
        )

        sections.append(

            "Behaviour:\n"

            +

            ", ".join(job.behaviour_traits)
        )

        return "\n".join(sections)