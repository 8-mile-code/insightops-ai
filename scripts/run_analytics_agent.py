from app.agents.analytics_graph import build_analytics_agent


def main() -> None:
    agent = build_analytics_agent()

    questions = [
        "Show revenue for project 2 pipeline run 13",
        "Show orders by status for project 2 pipeline run 13",
        "Show failed payments for project 2 pipeline run 13",
        "Show top customers for project 2 pipeline run 13",
    ]

    for question in questions:
        result = agent.invoke(
            {
                "question": question,
                "project_id": None,
                "dataset_id": None,
                "pipeline_run_id": None,
                "action": "unknown",
                "tool_result": None,
                "answer": "",
            }
        )

        print("=" * 80)
        print(f"Question: {question}")
        print(result["answer"])


if __name__ == "__main__":
    main()
