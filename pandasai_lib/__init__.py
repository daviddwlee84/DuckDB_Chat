from typing import Optional, List, Union, Dict
from pandasai.helpers.logger import Logger
from pandasai.pipelines.pipeline_context import PipelineContext
from pandasai.pipelines.pipeline import Pipeline
from .cache_lookup import CacheLookup
from .cache_population import CachePopulation
from .code_execution import CodeExecution
from .code_generator import CodeGenerator
from .prompt_generation import PromptGeneration
from .result_parsing import ResultParsing
from .result_validation import ResultValidation
import pandasai
from pandasai.helpers.memory import Memory
from pandasai.schemas.df_config import Config
from pandasai.helpers.df_info import DataFrameType


class GenerateSmartDatalakePipeline:
    _pipeline: Pipeline

    def __init__(
        self,
        context: Optional[PipelineContext] = None,
        logger: Optional[Logger] = None,
    ):
        self._pipeline = Pipeline(
            context=context,
            logger=logger,
            steps=[
                CacheLookup(),
                PromptGeneration(
                    skip_if=lambda pipeline_context: pipeline_context.get_intermediate_value(
                        "is_present_in_cache"
                    )
                ),
                CodeGenerator(
                    skip_if=lambda pipeline_context: pipeline_context.get_intermediate_value(
                        "is_present_in_cache"
                    )
                ),
                # BUG: Pipeline failed on step 4: expected str, bytes or os.PathLike object, not list
                # result = {'type': 'plot', 'value': ['C:/Users/david/Documents/Program/DuckDB_Chat/static/images/85e74ce1-c737-401b-b8b3-46ad22d34ecb.png', 'C:/Users/david/Documents/Program/DuckDB_Chat/static/images/85e74ce1-c737-401b-b8b3-46ad22d34ecb.png']}
                CachePopulation(
                    skip_if=lambda pipeline_context: pipeline_context.get_intermediate_value(
                        "is_present_in_cache"
                    )
                ),
                CodeExecution(),
                ResultValidation(),
                ResultParsing(),
            ],
        )

    def run(self):
        return self._pipeline.run()


class ModifiedSmartDatalake(pandasai.SmartDatalake):
    """
    Use local GenerateSmartDatalakePipeline
    """

    def chat(self, query: str, output_type: Optional[str] = None):
        """
        Run a query on the dataframe.

        Args:
            query (str): Query to run on the dataframe
            output_type (Optional[str]): Add a hint for LLM which
                type should be returned by `analyze_data()` in generated
                code. Possible values: "number", "dataframe", "plot", "string":
                    * number - specifies that user expects to get a number
                        as a response object
                    * dataframe - specifies that user expects to get
                        pandas/polars dataframe as a response object
                    * plot - specifies that user expects LLM to build
                        a plot
                    * string - specifies that user expects to get text
                        as a response object
                If none `output_type` is specified, the type can be any
                of the above or "text".

        Raises:
            ValueError: If the query is empty
        """

        pipeline_context = self.prepare_context_for_smart_datalake_pipeline(
            query=query, output_type=output_type
        )

        try:
            result = GenerateSmartDatalakePipeline(pipeline_context, self.logger).run()
        except Exception as exception:
            self.last_error = str(exception)
            self._query_exec_tracker.success = False
            self._query_exec_tracker.publish()

            return (
                "Unfortunately, I was not able to answer your question, "
                "because of the following error:\n"
                f"\n{exception}\n"
            )

        self.update_intermediate_value_post_pipeline_execution(pipeline_context)

        # publish query tracker
        self._query_exec_tracker.publish()

        return result


class ModifiedMemory(Memory):
    def get_openai_messages(self, limit: int = None) -> List[Dict[str, str]]:
        """
        Returns the conversation messages based on limit parameter
        or default memory size
        """
        limit = self._memory_size if limit is None else limit

        return [
            {
                "role": "user" if message["is_user"] else "assistant",
                "content": message["message"],
            }
            for message in self._messages[-limit:]
        ]


class ModifiedAgent(pandasai.Agent):
    """
    Use local ModifiedSmartDatalake (GenerateSmartDatalakePipeline)
    """

    _lake: ModifiedSmartDatalake = None
    _logger: Optional[Logger] = None

    def __init__(
        self,
        dfs: List[DataFrameType],
        config: Optional[Union[Config, dict]] = None,
        logger: Optional[Logger] = None,
        memory: Optional[ModifiedMemory] = None,
        memory_size: int = 10,
    ):
        """
        Args:
            df (List[DataFrameType]): DataFrame can be Pandas,
            Polars or Database connectors
            memory_size (int, optional): Conversation history to use during chat.
            Defaults to 1.
        """
        if memory is None:
            memory = ModifiedMemory(memory_size)

        self._lake = ModifiedSmartDatalake(dfs, config, logger, memory=memory)

        # set instance type in SmartDataLake
        self._lake.set_instance_type(self.__class__.__name__)

        self._logger = self._lake.logger
