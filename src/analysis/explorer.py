import json


class DataExplorer:

    @staticmethod
    def explore(candidates):

        print("\n" + "=" * 60)
        print("DATASET SUMMARY")
        print("=" * 60)

        print(f"Total Candidates : {len(candidates)}")

        if not candidates:
            return

        candidate = candidates[0]

        print("\nTop-Level Keys")
        print("-" * 30)

        for key in candidate:
            print(key)

        print("\nField Summary")
        print("-" * 30)

        for key, value in candidate.items():

            if isinstance(value, list):
                print(f"{key:20} -> List ({len(value)} items)")

            elif isinstance(value, dict):
                print(f"{key:20} -> Dictionary ({len(value)} fields)")

            else:
                print(f"{key:20} -> {type(value).__name__}")

        print("\nProfile Keys")
        print("-" * 30)

        for key in candidate["profile"]:
            print(key)

        print("\nRedrob Signal Keys")
        print("-" * 30)

        for key in candidate["redrob_signals"]:
            print(key)