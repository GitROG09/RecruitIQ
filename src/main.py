from core.loader import DataLoader
from factories.candidate_factory import CandidateFactory


def main():

    loader = DataLoader()

    raw_candidates = loader.load_json("sample_candidates.json")

    candidates = [
        CandidateFactory.create(candidate)
        for candidate in raw_candidates
    ]

    print(f"Loaded {len(candidates)} Candidate Objects")

    first = candidates[0]

    print("\nFirst Candidate")

    print(first.profile.anonymized_name)

    print(first.profile.current_title)

    print(first.profile.years_of_experience)

    print(len(first.skills))

    print(first.redrob_signals.github_activity_score)


if __name__ == "__main__":
    main()