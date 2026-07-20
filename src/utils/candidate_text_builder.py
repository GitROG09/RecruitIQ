class CandidateTextBuilder:
    """
    Builds a unified searchable text representation
    of a candidate profile.
    """

    @staticmethod
    def build(candidate) -> str:

        parts = []

        # -------------------------------------------------
        # Headline
        # -------------------------------------------------

        if candidate.profile.headline:
            parts.append(candidate.profile.headline)

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        if candidate.profile.summary:
            parts.append(candidate.profile.summary)

        # -------------------------------------------------
        # Skills
        # -------------------------------------------------

        for skill in candidate.skills:
            parts.append(skill.name)

        # -------------------------------------------------
        # Career History
        # -------------------------------------------------

        for job in candidate.career_history:

            if job.title:
                parts.append(job.title)

            if job.description:
                parts.append(job.description)

        return "\n".join(parts).lower()