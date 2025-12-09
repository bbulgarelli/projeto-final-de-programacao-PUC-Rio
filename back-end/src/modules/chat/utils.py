
import asyncio
from typing import Any, Coroutine, List, Optional, Tuple

from pydantic_ai import ModelMessage
from pydantic_ai.messages import ModelMessagesTypeAdapter

from src.modules.chat.schemas import MessageSchema


async def chunked_gather(
    coros: List[Coroutine[Any, Any, Any]],
    chunk_size: int = 10
) -> Tuple[List[Any], List[Optional[Exception]]]:
    """
    Run a list of coroutines in chunks, gathering results and exceptions.

    :param coros: list of coroutine objects to run
    :param chunk_size: how many tasks to run concurrently per batch
    :return: (results, errors) where results[i] corresponds to coros[i] if no error,
             otherwise results[i] is None and errors contains that exception.
    """
    results: List[Any] = []
    errors: List[Optional[Exception]] = []

    for i in range(0, len(coros), chunk_size):
        batch = coros[i : i + chunk_size]
        batch_results = await asyncio.gather(*batch, return_exceptions=True)
        for res in batch_results:
            if isinstance(res, Exception):
                errors.append(res)
                results.append(None)
            else:
                errors.append(None)
                results.append(res)
    return results, errors

def get_pydantic_message_history(message_history: List[MessageSchema]) -> List[ModelMessage]:
    history = []
    for message in message_history:
        history.extend(message.json_message_history)
    return ModelMessagesTypeAdapter.validate_python(history)