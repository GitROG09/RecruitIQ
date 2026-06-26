class CandidateKnowledgeBuilder:
    """
    Builds a rich textual representation of a candidate.
    This document is later embedded for semantic matching.
    """

    @staticmethod
    def build(candidate):

        sections = []

        # ------------------------------------------------
        # Basic Profile
        # ------------------------------------------------

        profile = candidate.profile

        sections.append(
            f"Name: {profile.anonymized_name}"
        )

        sections.append(
            f"Headline: {profile.headline}"
        )

        sections.append(
            f"Summary: {profile.summary}"
        )

        sections.append(
            f"Experience: {profile.years_of_experience} years"
        )

        sections.append(
            f"Current Role: {profile.current_title}"
        )

        # ------------------------------------------------
        # Skills
        # ------------------------------------------------

        skill_text = ", ".join(
            skill.name
            for skill in candidate.skills
        )

        sections.append(
            f"Skills: {skill_text}"
        )

        # ------------------------------------------------
        # Career History
        # ------------------------------------------------

        for job in candidate.career_history:

            sections.append(

                f"""
Company: {job.company}

Role: {job.title}

Industry: {job.industry}

Description:
{job.description}
"""
            )

        # ------------------------------------------------
        # Education
        # ------------------------------------------------

        for edu in candidate.education:

            # Education entries may be plain dicts (from raw JSON) or objects
            if isinstance(edu, dict):
                degree  = edu.get("degree", "")
                field   = edu.get("field_of_study", "")
                inst    = edu.get("institution", "")
            else:
                degree  = getattr(edu, "degree", "")
                field   = getattr(edu, "field_of_study", "")
                inst    = getattr(edu, "institution", "")

            sections.append(

                f"""
Education:
{degree}
{field}
{inst}
"""
            )

        return "\n".join(sections)