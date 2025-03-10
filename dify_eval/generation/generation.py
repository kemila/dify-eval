import asyncio
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.client import DatasetItemClient
from loguru import logger

from dify_eval.generation.dify_chat import send_chat_message

load_dotenv()

langfuse = Langfuse()


def get_langfuse_dataset(dataset_name: str):
    return langfuse.get_dataset(dataset_name)


async def run_dataset_item(item, run_name, semaphore):
    async with semaphore:
        response = await send_chat_message(item.input)

        item.link(
            trace_or_observation=None,
            run_name=run_name,
            trace_id=response["message_id"],
            observation_id=None,
        )
        return response


def save_results(
    results: list[dict],
    output_path: str = os.getenv("OUTPUT_FILE_PATH", ""),
    dataset_items: list[DatasetItemClient] = None,
):
    answer = []
    for result in results:
        answer.append(result["answer"].strip())

    questions = []
    for item in dataset_items or []:
        questions.append(item.input)

    if questions:
        df = pd.DataFrame({"question": questions, "answer": answer})
    else:
        df = pd.DataFrame(answer, columns=["answer"])

    if not output_path:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = f'results/{os.getenv("RUN_NAME", "")}_{current_time}.csv'
    else:
        local_path = output_path
    logger.info(f"Save results to {output_path}")
    logger.info(f"Save results to {local_path}")
    if not local_path:
        local_path = f'results/{os.getenv("RUN_NAME", "")}_{current_time}.csv'
    parent_folder = os.path.dirname(local_path)
    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)
    
    df.to_csv(local_path, index=False)


async def run_dataset_generation(
    dataset_name: str = os.getenv("DATASET_NAME", ""),
    run_name: str = os.getenv("RUN_NAME", ""),
    max_concurrency: int = 1,
    output_path: str = os.getenv("OUTPUT_FILE_PATH", ""),
    time_asc_submit: bool = True,
):

    if not dataset_name:
        raise ValueError("No dataset name provided.")

    if not run_name:
        run_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    dataset = get_langfuse_dataset(dataset_name)
    logger.info(f"Submit to dify {len(dataset.items)} items in dataset {dataset_name}")
    semaphore = asyncio.Semaphore(max_concurrency)
    tasks = []
    input_data = []

    # default items order is time desc
    items = dataset.items
    if time_asc_submit:
        items = list(reversed(items))

    # 先返回 LLM问太慢了
    return

    for item in items:
        task = asyncio.create_task(run_dataset_item(item, run_name, semaphore))
        input_data.append(item.input)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    save_results(results, output_path, items)
    return results
