import json
import os
from pathlib import Path


def main() -> None:
    username = os.environ["AIRFLOW_API_USERNAME"]
    password = os.environ["AIRFLOW_API_PASSWORD"]

    passwords_file = Path(
        os.environ["AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE"],
    )
    passwords_file.parent.mkdir(parents=True, exist_ok=True)

    passwords_file.write_text(
        json.dumps({username: password}) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
