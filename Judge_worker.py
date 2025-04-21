"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTA_Dog copilot - Judge_worker agent.
Date: 26 March  2025
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Literal, Tuple

from dotenv import load_dotenv
import os

load_dotenv()
# Ensure that your OPENAI_API_KEY is set in your environment
openai_api_key = os.getenv("OPENAI_API_KEY")

# Import the necessary components from the Agents SDK
from agents import Agent, Runner, trace, TResponseInputItem, ItemHelpers

# Define a dataclass for structured evaluation feedback from the Judge agent.
@dataclass
class EvaluationFeedback:
    feedback: str
    score: Literal["pass", "needs_improvement", "fail"]

# Define the Worker Agent.
# This agent is responsible for executing the task and incorporating feedback if provided.
worker_agent = Agent(
    name="Worker",
    instructions=(
        "You are a worker that executes the provided task accurately. "
        "Generate a detailed, correct output. If additional feedback is provided, incorporate it."
    ),
    model="gpt-4.1"  # was gpt-4o Replace with the actual worker model if different.
)

# Define the Judge Agent.
# This agent evaluates the worker’s output against the given criteria.
judge_agent = Agent[None](
    name="Judge",
    instructions=(
        "You are a judge. Evaluate the worker's output based on the task and criteria provided. "
        "Return a score of 'pass', or 'fail'. "
        "Also provide feedback on what needs to be improved to match the criteria."
    ),
    output_type=EvaluationFeedback,
    model="o3-mini-2025-01-31"  # Replace with your GPT-4.5 model if available.
)

async def human_review(worker_output: str) -> Tuple[str, dict]:
    """
    Presents the worker's output for human review. The human can choose to:
      - Continue (c)
      - Modify parameters (m)
      - Stop (s)
    If modifications are requested, return them as a dictionary.
    """
    print("\n--- Worker Output ---")
    print(worker_output)
    print("---------------------\n")
    action = input("Action? [c = continue, m = modify parameters, s = stop]: ").strip().lower()
    modifications = {}
    if action == 'm':
        new_instruction = input("Enter new worker instructions (leave blank to keep unchanged): ").strip()
        if new_instruction:
            modifications['instructions'] = new_instruction
        new_task = input("Enter new task description (leave blank to keep unchanged): ").strip()
        if new_task:
            modifications['task'] = new_task
    return action, modifications

async def judge_worker_loop(initial_task: str, evaluation_criteria: str, max_runtime: int = 600) -> None:
    start_time = time.time()
    current_task = initial_task

    # Start with an input message list that contains the initial task.
    input_items: list[TResponseInputItem] = [{"content": current_task, "role": "user"}]
    latest_output: str = ""

    # Wrap the whole process in a trace for debugging and monitoring.
    with trace("Judge-Worker Loop"):
        while True:
            # Worker Agent execution: produce an output based on current input context.
            worker_result = await Runner.run(worker_agent, input_items)
            latest_output = ItemHelpers.text_message_outputs(worker_result.new_items)
            print("\n=== Generated Worker Output ===")
            print(latest_output)
            print("================================\n")

            # Judge Agent evaluates the output.
            judge_input = (
                f"Task: {current_task}\n"
                f"Worker Output: {latest_output}\n"
                f"Evaluation Criteria: {evaluation_criteria}"
            )
            judge_result = await Runner.run(judge_agent, [{"content": judge_input, "role": "user"}])
            evaluation: EvaluationFeedback = judge_result.final_output

            print(f"Judge Score: {evaluation.score}")
            print(f"Judge Feedback: {evaluation.feedback}\n")

            # Termination conditions.
            if evaluation.score == "pass":
                print("Judge has accepted the output. Exiting loop.")
                break
            if time.time() - start_time > max_runtime:
                print("Maximum runtime exceeded. Exiting loop.")
                break

            # Human intervention: allow user to review output and optionally modify parameters.
            action, mods = await human_review(latest_output)
            if action == 's':
                print("Process stopped by human intervention.")
                break
            elif action == 'm':
                # If new task description is provided, update current_task.
                if 'task' in mods:
                    current_task = mods['task']
                    # Reset input_items to start fresh with new task.
                    input_items = [{"content": current_task, "role": "user"}]
                    print("Task description updated.")
                else:
                    # Otherwise, append the judge's feedback to the context.
                    input_items.append({"content": f"Feedback: {evaluation.feedback}", "role": "user"})
                # Also update the worker agent's instructions if provided.
                if 'instructions' in mods:
                    worker_agent.instructions = mods['instructions']
                    print("Worker instructions updated.")
            else:
                # Continue normally: append judge feedback to context for next iteration.
                input_items.append({"content": f"Feedback: {evaluation.feedback}", "role": "user"})

    print("\n=== Final Worker Output ===")
    print(latest_output)

async def main() -> None:
    # Get the initial task and evaluation criteria from the user.
    initial_task = input("Enter the task for the agents: ")
    evaluation_criteria = input("Enter the evaluation criteria: ")
    await judge_worker_loop(initial_task, evaluation_criteria)

if __name__ == "__main__":
    asyncio.run(main())
