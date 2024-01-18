from typing import Any
from pandasai.helpers.logger import Logger
from pandasai.pipelines.base_logic_unit import BaseLogicUnit
from pandasai.pipelines.pipeline_context import PipelineContext
import chainlit as cl


class CodeGenerator(BaseLogicUnit):
    """
    LLM Code Generation Stage
    """

    @cl.step(name="Code Generator")
    def execute(self, input: Any, **kwargs) -> Any:
        """
        This method will return output according to
        Implementation.

        :param input: Your input data.
        :param kwargs: A dictionary of keyword arguments.
            - 'logger' (any): The logger for logging.
            - 'config' (Config): Global configurations for the test
            - 'context' (any): The execution context.

        :return: The result of the execution.
        """
        pipeline_context: PipelineContext = kwargs.get("context")
        logger: Logger = kwargs.get("logger")

        generate_python_code_instruction = input

        code = pipeline_context.query_exec_tracker.execute_func(
            pipeline_context.config.llm.generate_code,
            generate_python_code_instruction,
        )
        pipeline_context.add_intermediate_value("last_code_generated", code)
        logger.log(
            f"""Code generated:
            ```
            {code}
            ```
            """
        )

        return code
