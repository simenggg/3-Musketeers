import argparse
import asyncio
import json
from orchestrator import meal_planning_orchestrator

def parse_args():
    parser = argparse.ArgumentParser(description="Meal Planning Orchestrator CLI")
    parser.add_argument("user_id", help="User ID")
    parser.add_argument("--workflow", default="full_meal_plan", help="Workflow type (default: full_meal_plan)")
    parser.add_argument("--request", type=str, default="{}", help="Request data as JSON string")
    return parser.parse_args()

async def main():
    args = parse_args()
    try:
        request_data = json.loads(args.request)
    except Exception as e:
        print(f"Invalid JSON for --request: {e}")
        return

    result = await meal_planning_orchestrator.execute_meal_planning_workflow(
        user_id=args.user_id,
        request_data=request_data,
        workflow_type=args.workflow
    )
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())