#!/usr/bin/env python
# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTA_Dog copilot - routers agents.
Date: 27 March  2025
"""
import asyncio
import uuid
import os
import subprocess
from typing import List, Dict, Any, Optional, Union

from dotenv import load_dotenv
load_dotenv()
# Ensure that your OPENAI_API_KEY is set in your environment
openai_api_key = os.getenv("OPENAI_API_KEY")

from openai.types.responses import ResponseContentPartDoneEvent, ResponseTextDeltaEvent
from agents import Agent, RawResponsesStreamEvent, Runner, TResponseInputItem, trace

"""
SMT Solver Router Implementation

This implementation creates a modular AI-Agent-based SMT Solver Router that dynamically
selects the optimal SMT solver based on analysis of incoming Luster files.
"""


class SolverResult:
    """Class to store and handle results from solver execution"""

    def __init__(self, success: bool, output: str, counterexample: Optional[Dict] = None):
        self.success = success
        self.output = output
        self.counterexample = counterexample

    def __str__(self):
        if self.success:
            return f"Solver executed successfully.\nOutput: {self.output}"
        else:
            return f"Solver execution failed.\nOutput: {self.output}"


class SolverAgent(Agent):
    """Base class for all solver agents"""

    def __init__(self, name: str, solver_path: str, instructions: str = ""):
        super().__init__(name=name, instructions=instructions)
        self.solver_path = solver_path

    async def execute(self, luster_file_path: str, timeout: int = 60) -> SolverResult:
        """Execute the solver on the given Luster file"""
        try:
            # Base implementation calls JKind with the specified solver
            cmd = ["java", "-jar", "jkind.jar",
                   "-jkind", self.solver_path,
                   luster_file_path] # ToDo 0: integrate with jkind wrapper.py module

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
                output = stdout.decode() + stderr.decode()
                success = process.returncode == 0

                # Parse counterexample if any
                counterexample = self._parse_counterexample(output) if not success else None

                return SolverResult(success, output, counterexample)
            except asyncio.TimeoutError:
                process.kill()
                return SolverResult(False, f"Solver timed out after {timeout} seconds")

        except Exception as e:
            return SolverResult(False, f"Error executing solver: {str(e)}")

    def _parse_counterexample(self, output: str) -> Dict:
        """Parse solver output to extract counterexample"""
        # This is a placeholder - #Todo 2: to implement specific parsing logic in subclasses
        counterexample = {}
        # Basic parsing logic here
        return counterexample


# Specific solver implementations
class Z3Agent(SolverAgent):
    def __init__(self):
        super().__init__(
            name="z3_agent",
            solver_path="/path/to/z3",
            instructions="You are an expert in Z3 automatic theorem proving and SMT solving. "
                         "You are the best choice for non-linear arithmetic SMT solving."
        )

    def _parse_counterexample(self, output: str) -> Dict:
        # Z3-specific counterexample parsing
        counterexample = {}
        # Z3-specific parsing logic here
        return counterexample


class CVC4Agent(SolverAgent):
    def __init__(self):
        super().__init__(
            name="cvc4_agent",
            solver_path="/path/to/cvc4",
            instructions="You are an expert in CVC4/CVC5 SMT solving. "
                         "You excel at handling quantified problems and mixed constraints."
        )


class YicesAgent(SolverAgent):
    def __init__(self):
        super().__init__(
            name="yices_agent",
            solver_path="/path/to/yices",
            instructions="You are an expert in Yices SMT solving. "
                         "You are optimized for bit-vector operations."
        )


class MathSATAgent(SolverAgent):
    def __init__(self):
        super().__init__(
            name="mathsat_agent",
            solver_path="/path/to/mathsat",
            instructions="You are an expert in MathSAT SMT solving. "
                         "You excel at floating-point arithmetic problems."
        )


class SMTInterpolAgent(SolverAgent):
    def __init__(self):
        super().__init__(
            name="smtinterpol_agent",
            solver_path="/path/to/smtinterpol",
            instructions="You are an expert in SMTInterpol. "
                         "You specialize in interpolation-based proofs."
        )


class AIClassifierAgent(Agent):
    """Agent responsible for analyzing Luster files and predicting problem characteristics"""

    def __init__(self):
        super().__init__(
            name="ai_classifier_agent",
            instructions="Analyze the Luster file content and classify the problem characteristics. "
                         "Identify if the problem involves non-linear arithmetic, bit-vectors, "
                         "floating-point operations, quantified formulas, or needs interpolation-based proofs."
        )

    async def classify(self, luster_content: str) -> Dict[str, float]:
        """
        Analyze Luster file content and return problem classification
        Returns: Dictionary mapping solver types to confidence scores
        """
        # Prepare the input for the AI model
        inputs: List[TResponseInputItem] = [
            {
                "content": f"Analyze this Luster file and classify the problem characteristics.\n\n{luster_content}",
                "role": "user"
            }
        ]

        # Run the AI classification using streaming approach
        response_text = ""
        with trace("AI SMT Problem Classification"):
            result = Runner.run_streamed(self, input=inputs)
            async for event in result.stream_events():
                if not isinstance(event, RawResponsesStreamEvent):
                    continue
                data = event.data
                if isinstance(data, ResponseTextDeltaEvent):
                    response_text += data.delta

            # Parse the AI response to extract classifications
            classifications = {
                "z3": 0.0,
                "cvc4": 0.0,
                "yices": 0.0,
                "mathsat": 0.0,
                "smtinterpol": 0.0
            }

            # Simple keyword-based classification for demonstration
            # In a real more complex classifier implementation, we'd use a more sophisticated approach
            if "non-linear arithmetic" in response_text.lower():
                classifications["z3"] += 0.7
            if "bit-vector" in response_text.lower():
                classifications["yices"] += 0.8
            if "floating-point" in response_text.lower():
                classifications["mathsat"] += 0.8
            if "quantified" in response_text.lower():
                classifications["cvc4"] += 0.7
            if "interpolation" in response_text.lower():
                classifications["smtinterpol"] += 0.9

            return classifications


class RouterAgent(Agent):
    """Agent responsible for routing problems to the appropriate solver agent"""

    def __init__(self, solvers: List[SolverAgent], classifier: AIClassifierAgent):
        instructions = """
        You are an SMT Solver Router that selects the optimal SMT solver based on Luster file analysis.

        When you receive a Luster file:
        1. Analyse the Luster file.
        2. Determine if it involves:
           - Non-linear arithmetic (route to Z3)
           - Bit-vector operations (route to Yices)
           - Floating-point arithmetic (route to MathSAT)
           - Quantified formulas (route to CVC4)
           - Interpolation-based proofs (route to SMTInterpol)
        3. Choose the most appropriate solver based on problem characteristics.
        4. Display the chosen solver and report the result in the following format: '''The likely solver of choice :  {name of solver}''' .
        

        If you're uncertain about the problem characteristics, you may use your pretraining knowledge.
        """
        # 5. To execute the chosen solver and report the result. Todo: 1- link with worker agent that execute the solver.
        super().__init__(
            name="router_agent",
            instructions=instructions,
            handoffs=[solver for solver in solvers]
        )
        self.solvers = {solver.name: solver for solver in solvers}
        self.classifier = classifier

    async def route(self, luster_file_path: str, luster_content: str) -> SolverResult:
        """Route the Luster problem to the appropriate solver"""
        # Classify the problem
        classifications = await self.classifier.classify(luster_content)

        # Select the solver with the highest confidence
        best_solver_name = max(classifications, key=classifications.get)
        confidence = classifications[best_solver_name]

        # Get the solver agent
        solver_agent = self.solvers.get(f"{best_solver_name}_agent")

        if solver_agent and confidence > 0.7:  # Threshold for confidence
            print(f"Routing to {solver_agent.name} with confidence {confidence:.2f}")
            return await solver_agent.execute(luster_file_path)
        else:
            # Fall back to Z3 if no confident classification
            print("No confident classification, falling back to Z3")
            return await self.solvers["z3_agent"].execute(luster_file_path)


async def process_luster_file(file_path: str, router: RouterAgent) -> None:
    """Process a Luster file through the router"""
    # Read the file content
    with open(file_path, "r") as f:
        content = f.read()

    # Route and execute
    result = await router.route(file_path, content)

    # Print result
    print(result)
    if result.counterexample:
        print("Counterexample found:")
        for var, value in result.counterexample.items():
            print(f"  {var} = {value}")


async def interactive_mode(router: RouterAgent) -> None:
    """Interactive mode for the SMT Solver Router"""
    conversation_id = str(uuid.uuid4().hex[:16])

    print("Welcome to the SMT Solver Router!")
    print("You can enter a path to a Luster file or enter 'q' to quit.")

    agent = router
    inputs: List[TResponseInputItem] = []

    while True:
        file_path = input("\nEnter path to Luster file (or 'q' to quit): ")
        if file_path.lower() == 'q':
            break

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        # Read the file content
        with open(file_path, "r") as f:
            content = f.read()

        # Add content to inputs
        inputs = [{"content": f"Analyze and solve this Luster file:\n\n{content}", "role": "user"}]

        # Process the file using streaming
        print(f"Processing {file_path}...")
        with trace("SMT Solver Routing", group_id=conversation_id):
            result = Runner.run_streamed(
                agent,
                input=inputs,
            )

            # Stream the response
            async for event in result.stream_events():
                if not isinstance(event, RawResponsesStreamEvent):
                    continue
                data = event.data
                if isinstance(data, ResponseTextDeltaEvent):
                    print(data.delta, end="", flush=True)
                elif isinstance(data, ResponseContentPartDoneEvent):
                    print("\n")

            # Update inputs for the next iteration
            inputs = result.to_input_list()
            agent = result.current_agent


async def main():
    # Initialize solver agents
    z3_agent = Z3Agent()
    cvc4_agent = CVC4Agent()
    yices_agent = YicesAgent()
    mathsat_agent = MathSATAgent()
    smtinterpol_agent = SMTInterpolAgent()

    # Initialize classifier agent
    classifier_agent = AIClassifierAgent()

    # Initialize router agent with all solvers
    router = RouterAgent(
        solvers=[z3_agent, cvc4_agent, yices_agent, mathsat_agent, smtinterpol_agent],
        classifier=classifier_agent
    )

    # Start interactive mode
    await interactive_mode(router)


if __name__ == "__main__":
    asyncio.run(main())