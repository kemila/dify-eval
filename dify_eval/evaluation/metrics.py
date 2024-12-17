import functools
import math
from typing import Optional, Union

import tiktoken
from dotenv import load_dotenv
from langfuse import Langfuse
from loguru import logger

load_dotenv()

langfuse = Langfuse()

def retrieve_f1(predicted_result: list, ground_truth: list):
    """
    Calculate F1 score
    """
    recall = retrieve_recall(predicted_result, ground_truth)
    precision = retrieve_precision(predicted_result, ground_truth)
    f1 = 2 * recall * precision / (recall + precision) \
        if recall + precision > 0 else 0
    return f1

def retrieve_recall(predicted_result: list, ground_truth: list):
    """
    Calculate recall
    """
    recall = len(ground_truth & predicted_result) / len(ground_truth) \
        if ground_truth else 0
    return recall

def retrieve_precision(predicted_result: list, ground_truth: list):
    """
    Calculate precision
    """
    precision = len(ground_truth & predicted_result) / len(predicted_result) \
        if predicted_result else 0
    return precision

def retrieve_iou(predicted_result: list, ground_truth: list):
    """
    Calculate Intersection over Union (IoU)
    """
    iou = len(ground_truth & predicted_result) / len(ground_truth | predicted_result) \
        if ground_truth | predicted_result else 0
    return iou

def retrieval_ndcg(predicted_result: list, ground_truth: list):
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG)
    """
    if not ground_truth:
        return 0.0

    relevance_scores = []

    for result in predicted_result:
        overlap = len(ground_truth & result)

        relevance_score = 2 ** (overlap / len(ground_truth)) - 1 \
            if len(ground_truth) > 0 else 0
        relevance_scores.append(relevance_score)

    dcg = sum(
        rel_score / math.log2(i + 2)
        for i, rel_score in enumerate(relevance_scores)
    )

    sorted_scores = sorted(relevance_scores, reverse=True)
    idcg = sum(
        rel_score / math.log2(i + 2)
        for i, rel_score in enumerate(sorted_scores)
    )

    ndcg = dcg / idcg if idcg > 0 else 0

    return ndcg

def retrieval_mrr(predicted_result: list, ground_truth: list):
    """
    Reciprocal Rank (RR) is the reciprocal of the rank of the first relevant item.
    Mean of RR in whole queries is MRR.
    """

    total = len(ground_truth)
    for i, result in enumerate(predicted_result):
        if len(ground_truth & result) / total > 0.5:
            return 1 / (i + 1)
    return 0

def retrieval_map(predicted_result: list, ground_truth: list = []):
    """
    Mean Average Precision (MAP) is the mean of Average Precision (AP) for each query.
    """

    precision_list = [
        len(ground_truth & pred) / len(pred)
        for pred in predicted_result
    ]

    ap = sum(precision_list) / len(precision_list) \
        if precision_list else 0.0

    return ap

def retrieval_evaluate(
    dataset_dict: dict[str, Union[str, list[str]]],
    metrics: list[str],
    trace_id: Optional[str] = None
):
    """
    implement retrieval evaluation
    """
    result = {
        'overall': {},
        'best': {}
    }

    retrieval_result = dataset_dict.get('contexts', [[]])[0]
    ground_truth = dataset_dict.get('ground_truth', [''])[0]

    @functools.lru_cache(maxsize=1)
    def get_tokenizer():
        return tiktoken.get_encoding('cl100k_base')

    encoding = get_tokenizer()
    retrieval_result = [encoding.encode(result) for result in retrieval_result]
    ground_truth = encoding.encode(ground_truth)

    pred_sets = [frozenset(result) for result in retrieval_result]
    pred_set = functools.reduce(lambda x, y: x | y, pred_sets, frozenset()) \
        if pred_sets else frozenset()
    gt_set = frozenset(ground_truth)

    metric_functions = {
        'retrieve_f1': retrieve_f1,
        'retrieve_recall': retrieve_recall,
        'retrieve_precision': retrieve_precision,
        'retrieve_iou': retrieve_iou,
        'retrieve_ndcg': retrieval_ndcg,
        'retrieve_mrr': retrieval_mrr,
        'retrieve_map': retrieval_map
    }

    best_metrics = {
        'retrieve_f1',
        'retrieve_recall',
        'retrieve_precision',
        'retrieve_iou'
    }

    for metric in metrics:
        func = metric_functions[metric]
        if metric in best_metrics:
            result['overall'][metric] = func(pred_set, gt_set)
        else:
            result[metric] = func(pred_sets, gt_set)

    best_scores = {metric: 0 for metric in metrics if metric in best_metrics}
    for pred_set in pred_sets:
        for metric in best_scores:
            score = metric_functions[metric](pred_set, gt_set)
            best_scores[metric] = max(best_scores[metric], score)

    result['best'] = best_scores

    logger.info(
        f" >> Finish trace {trace_id} with question {dataset_dict['question']} evaluation result: {result}"
    )

    if trace_id:
        for metric_name, score in _flatten_results(result).items():
            langfuse.score(
                trace_id=trace_id,
                name=metric_name,
                value=score
            )

    return result

def _flatten_results(results: dict) -> dict:
    flattened = {}
    for eval_type, eval_result in results.items():
        if isinstance(eval_result, dict):
            flattened.update({
                f"{eval_type}_{metric}": score 
                for metric, score in eval_result.items()
            })
        else:
            flattened[eval_type] = eval_result
    return flattened